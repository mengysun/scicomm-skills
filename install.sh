#!/usr/bin/env bash
# Symlink the skills in this repo into a Claude Code skills directory.
#
#   ./install.sh                  # user-wide, into ~/.claude/skills
#   ./install.sh /path/to/project # project-local, into <project>/.claude/skills
#   ./install.sh --uninstall      # remove only the symlinks this script made
#
# Symlinks rather than copies, so `git pull` updates the installed skills and no
# machine can quietly run a stale version. Existing real directories are moved
# to a sibling `.claude/skills-backup/` rather than deleted — if you had local
# edits, they are still there.
#
# The backup goes *outside* the skills directory on purpose: Claude Code loads
# every subdirectory of `.claude/skills/` that contains a SKILL.md, so a backup
# left in place registers as a second, confusingly-named copy of the skill.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(master-of-poster master-of-slides)

UNINSTALL=0
TARGET_ROOT="$HOME"
for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=1 ;;
    -h|--help)   sed -n '2,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)           TARGET_ROOT="$(cd "$arg" && pwd)" ;;
  esac
done
DEST="$TARGET_ROOT/.claude/skills"
# outside DEST: anything with a SKILL.md inside DEST is loaded as a skill
BACKUP="$TARGET_ROOT/.claude/skills-backup"

if [[ "$UNINSTALL" == 1 ]]; then
  for s in "${SKILLS[@]}"; do
    link="$DEST/$s"
    if [[ -L "$link" && "$(readlink "$link")" == "$REPO/$s" ]]; then
      rm "$link"; echo "removed  $link"
    elif [[ -e "$link" ]]; then
      echo "left     $link  (not a link into this repo)"
    fi
  done
  exit 0
fi

mkdir -p "$DEST"
stamp="$(date +%Y%m%d-%H%M%S)"

for s in "${SKILLS[@]}"; do
  src="$REPO/$s"
  link="$DEST/$s"
  [[ -d "$src" ]] || { echo "missing  $src — skipping"; continue; }

  if [[ -L "$link" && "$(readlink "$link")" == "$src" ]]; then
    echo "ok       $link"
    continue
  fi
  if [[ -L "$link" ]]; then
    echo "relink   $link  (was -> $(readlink "$link"))"
    rm "$link"
  elif [[ -e "$link" ]]; then
    # a real directory: keep it, do not delete anything the user may have edited
    mkdir -p "$BACKUP"
    mv "$link" "$BACKUP/$s.bak-$stamp"
    echo "backed   $link -> $BACKUP/$s.bak-$stamp"
  fi
  ln -s "$src" "$link"
  echo "linked   $link -> $src"
done

echo
echo "Installed into $DEST"
echo "Skills load on the next Claude Code session in that scope."
echo
echo "The scripts need: playwright (+ chromium), matplotlib, and poppler."
echo "  uv pip install playwright matplotlib && playwright install chromium"
