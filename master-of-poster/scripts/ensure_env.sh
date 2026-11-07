#!/usr/bin/env bash
# Find or create the shared environment the build scripts run in, then print the
# path to its python on the last line so a caller can capture it:
#
#     PY=$(.../ensure_env.sh) && "$PY" .../render.py <build-dir>
#
#     ensure_env.sh            create if missing, install the core tooling
#     ensure_env.sh --pptx     also install python-pptx (decks that must be editable)
#     ensure_env.sh --check    print the path if it is ready; exit 1 if not
#
# WHY SHARED, and why this is not the project's venv.
#
# The build tooling is the same for every poster and every deck on a machine:
# a headless browser, matplotlib, a PDF toolchain. Chromium alone is ~150 MB.
# Installing that per project wastes time and disk for no benefit, because none
# of it is project-specific.
#
# The *analysis* is a different matter and keeps its own repo-local environment.
# The split is: code that produced the results lives with the results; code that
# turns results into a printed artifact is a tool, and tools are shared. So this
# never touches, activates, or installs into a project's venv.
#
# Location: $SCICOMM_VENV if set, else ~/.local/share/scicomm-skills/venv —
# outside every project, so it survives deleting any of them.
set -euo pipefail

VENV="${SCICOMM_VENV:-$HOME/.local/share/scicomm-skills/venv}"
PY="$VENV/bin/python"
# Major-version bounds: a new major release cannot change the toolchain under
# a poster or deck unless someone raises the bound here on purpose.
PLAYWRIGHT_SPEC="playwright>=1.40,<2"
MATPLOTLIB_SPEC="matplotlib>=3.7,<4"
PPTX_SPEC="python-pptx>=1.0,<2"
WANT_PPTX=0
CHECK_ONLY=0
for a in "$@"; do
  case "$a" in
    --pptx)  WANT_PPTX=1 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,26p' "$0" | sed 's/^# \?//'; exit 0 ;;
  esac
done

have_core() {
  [[ -x "$PY" ]] && "$PY" - <<'EOF' >/dev/null 2>&1
import playwright, matplotlib          # noqa: F401
from playwright.sync_api import sync_playwright
with sync_playwright() as p:           # browsers installed, not just the package
    p.chromium.launch().close()
EOF
}

if have_core; then
  if [[ "$WANT_PPTX" == 1 ]] && ! "$PY" -c "import pptx" >/dev/null 2>&1; then
    echo "adding python-pptx to $VENV" >&2
    if command -v uv >/dev/null 2>&1; then uv pip install --python "$PY" -q "$PPTX_SPEC"
    else "$PY" -m pip install -q "$PPTX_SPEC"; fi
  fi
  echo "$PY"; exit 0
fi

if [[ "$CHECK_ONLY" == 1 ]]; then
  echo "not ready: $VENV" >&2; exit 1
fi

echo "setting up the shared scicomm environment at $VENV" >&2
mkdir -p "$(dirname "$VENV")"
if [[ ! -x "$PY" ]]; then
  if command -v uv >/dev/null 2>&1; then uv venv "$VENV" >&2
  else python3 -m venv "$VENV" >&2; fi
fi

PKGS=("$PLAYWRIGHT_SPEC" "$MATPLOTLIB_SPEC")
[[ "$WANT_PPTX" == 1 ]] && PKGS+=("$PPTX_SPEC")
if command -v uv >/dev/null 2>&1; then uv pip install --python "$PY" -q "${PKGS[@]}" >&2
else "$PY" -m pip install -q --upgrade pip >&2; "$PY" -m pip install -q "${PKGS[@]}" >&2; fi

# Browsers live in a machine-level cache (~/.cache/ms-playwright), shared by
# every venv, so this is a no-op if any other environment already fetched them.
"$PY" -m playwright install chromium >&2

# poppler supplies pdfinfo / pdftoppm / pdfimages, which pip cannot provide.
missing=()
for t in pdfinfo pdftoppm pdfimages; do command -v "$t" >/dev/null 2>&1 || missing+=("$t"); done
if (( ${#missing[@]} )); then
  cat >&2 <<EOF

  NOTE: missing ${missing[*]} — these come from poppler, not from pip:
      conda install -c conda-forge poppler   |   apt install poppler-utils
      brew install poppler
  render.py needs them to confirm the emitted PDF's page size and to rasterize
  previews; without them it will fail rather than print something unverified.
EOF
fi

have_core || { echo "environment created but chromium did not launch — see errors above" >&2; exit 1; }
echo "ready" >&2
echo "$PY"
