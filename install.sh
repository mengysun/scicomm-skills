#!/usr/bin/env bash
# Symlink the skills for Claude Code, Codex, and Cursor.
#
#   ./install.sh                  # user-wide; Cursor shares ~/.agents/skills with Codex
#   ./install.sh /path/to/project # project-local, into both discovery directories
#   ./install.sh --uninstall      # remove only the symlinks this script made
#
# Symlinks rather than copies, so `git pull` updates the installed skills and no
# machine can quietly run a stale version. Existing real directories are moved
# to a sibling `skills-backup/` rather than deleted — if you had local edits,
# they are still there.
#
# Backups go *outside* the skills directories on purpose: agents load every
# subdirectory that contains a SKILL.md, so a backup left inside registers as a
# second, confusingly-named copy of the skill.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(master-of-poster master-of-slides)

UNINSTALL=0
TARGET_ROOT="$HOME"
for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=1 ;;
    -h|--help)   sed -n '2,15p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)           TARGET_ROOT="$(cd "$arg" && pwd)" ;;
  esac
done

DESTS=(
  "$TARGET_ROOT/.claude/skills"
  "$TARGET_ROOT/.agents/skills"
)
BACKUPS=(
  "$TARGET_ROOT/.claude/skills-backup"
  "$TARGET_ROOT/.agents/skills-backup"
)

if [[ "$UNINSTALL" == 1 ]]; then
  for dest in "${DESTS[@]}"; do
    for s in "${SKILLS[@]}"; do
      link="$dest/$s"
      if [[ -L "$link" && "$(readlink "$link")" == "$REPO/$s" ]]; then
        rm "$link"; echo "removed  $link"
      elif [[ -e "$link" ]]; then
        echo "left     $link  (not a link into this repo)"
      fi
    done
  done
  exit 0
fi

stamp="$(date +%Y%m%d-%H%M%S)"

for i in "${!DESTS[@]}"; do
  dest="${DESTS[$i]}"
  backup="${BACKUPS[$i]}"
  mkdir -p "$dest"

  for s in "${SKILLS[@]}"; do
    src="$REPO/$s"
    link="$dest/$s"
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
      mkdir -p "$backup"
      mv "$link" "$backup/$s.bak-$stamp"
      echo "backed   $link -> $backup/$s.bak-$stamp"
    fi
    ln -s "$src" "$link"
    echo "linked   $link -> $src"
  done
done

echo
echo "Installed for Claude Code in ${DESTS[0]}"
echo "Installed for Codex and Cursor in ${DESTS[1]}"
echo "Restart an existing session if it does not detect the new skills."
echo
echo "Nothing else to install by hand: on first use each skill runs its own"
echo "scripts/ensure_env.sh, which sets up playwright, Chromium and matplotlib in"
echo "a shared environment. Only poppler (pdfinfo, pdftoppm) must come from the system:"
echo "  apt install poppler-utils  |  brew install poppler  |  conda install -c conda-forge poppler"
