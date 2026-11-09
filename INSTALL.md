# Installing scicomm-skills

The reference for coding agents asked to install these skills, and for anyone
who prefers to do it by hand. For what the skills do and how to use them, see
the [README](README.md).

## For an agent: the whole job

1. **Clone** into `~/scicomm-skills` unless the user names another place. If a
   clone already exists there, `git -C ~/scicomm-skills pull` instead.
2. **Run the installer**: `~/scicomm-skills/install.sh`. Add a project
   directory as the argument only if the user wants the skills for one project
   rather than for every session.
3. **Check poppler**: `command -v pdftoppm pdfinfo`. If either is missing, tell
   the user the one command for their system (below). Do not install it with
   `sudo` on their behalf.
4. **Tell the user** to start a new session (or restart the current one) so the
   agent discovers the skills, then `/master-of-slides` or `/master-of-poster`
   in Claude Code, `$master-of-slides` or `$master-of-poster` in Codex, and
   `/` then the skill name in Cursor's Agent chat.

Nothing else needs installing by hand: the Python environment is set up by the
skills themselves on first use (see [Requirements](#requirements)).

## Install

Symlink rather than copy, so `git pull` updates the skills in place and no
machine can quietly run a stale version. The installer links the same source
folders into two discovery directories used by all three agents:

```bash
git clone https://github.com/mengysun/scicomm-skills.git ~/scicomm-skills
~/scicomm-skills/install.sh
```

`install.sh` works out its own location, so the clone can live anywhere — the
symlinks it creates point wherever you actually put it. It is idempotent, backs
up anything it would replace, and prints what it did.

| Agent | Personal skills | Project skills |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `<project>/.claude/skills/` |
| Codex | `~/.agents/skills/` | `<project>/.agents/skills/` |
| Cursor | `~/.agents/skills/` | `<project>/.agents/skills/` |

Cursor also supports `.cursor/skills/`, but the installer deliberately uses
the shared `.agents/skills/` location so Codex and Cursor load the same links
without duplicate installations.

For a project-local installation, pass the project directory:

```bash
~/scicomm-skills/install.sh /path/to/project
```

This creates symlinks in both project skill directories. To install by hand
instead:

```bash
mkdir -p ~/.claude/skills ~/.agents/skills

ln -s ~/scicomm-skills/master-of-poster ~/.claude/skills/master-of-poster
ln -s ~/scicomm-skills/master-of-slides ~/.claude/skills/master-of-slides

ln -s ~/scicomm-skills/master-of-poster ~/.agents/skills/master-of-poster
ln -s ~/scicomm-skills/master-of-slides ~/.agents/skills/master-of-slides
```

To update, pull; the links already point at the clone:

```bash
git -C ~/scicomm-skills pull
```

To remove only the symlinks created by this repository, from all three agents:

```bash
~/scicomm-skills/install.sh --uninstall
~/scicomm-skills/install.sh --uninstall /path/to/project
```

## Requirements

The skills set their own environment up — you should not have to. On first use
each one runs:

```bash
<skill>/scripts/ensure_env.sh
```

which creates a **shared** environment at `~/.local/share/scicomm-skills/venv`
(override with `$SCICOMM_VENV`), installs playwright, a headless Chromium and
matplotlib into it, and prints the path to its python. Both skills use the same
one: the build tooling is identical for every poster and every deck on a machine,
and Chromium alone is ~180 MB, so per-project installs buy nothing. First run
takes about a minute; afterwards it is a two-second check.

Deliberately *not* the project's venv. Analysis code keeps its repo-local
environment beside the results it produced; this is a tool, and tools are shared.

Two things it cannot install, and reports instead:

- **poppler** — `pdfinfo`, `pdftoppm`, `pdfimages`
  (`conda install -c conda-forge poppler`, `apt install poppler-utils`,
  `brew install poppler`)
- **LibreOffice** — only for `pptxcheck.py --pdf`, which renders a `.pptx` to see
  what PowerPoint actually does to its text boxes

For the `.pptx` output path, `ensure_env.sh --pptx` adds `python-pptx`.

## Layout

```
master-of-poster/
├── SKILL.md          the workflow, and why each step is there
├── references/       consulted as needed, not loaded up front
├── scripts/          render · audit · probe · svgcheck · contact_sheet
└── assets/           the stylesheet and the matplotlib figure engine

master-of-slides/
├── SKILL.md
├── references/
├── scripts/          render · audit · notes · review · pptxcheck · svgcheck
└── assets/
```

`docs/` holds only the README's images and example decks, and is not installed.

Scripts take a build directory as their first argument, so they work on any
project:

```bash
python ~/scicomm-skills/master-of-poster/scripts/render.py <build-dir>
python ~/scicomm-skills/master-of-poster/scripts/audit.py  <build-dir>
python ~/scicomm-skills/master-of-slides/scripts/audit.py  <build-dir> --titles
```

## The palette

Both skills ship with the same warm sheet — named in `assets/poster.css` /
`assets/slides.css` and mirrored in `assets/posterfig.py` / `assets/slidefig.py`,
so a figure and the page it sits on draw from one set.

It is there to be drawn from, not to dictate meaning: which swatch encodes what
depends on your data. It applies to what you author — grounds, chrome, and any
figure you generate. Figures and logos you were merely handed are placed as
supplied and never recoloured. `setup()` installs a sensible ordering of the saturated
members as matplotlib's colour cycle, so plots match without being told to.
Swapping the whole sheet for another is one edit in each file —
`references/palette-and-type.md` covers it, along with what actually separates
well and where colour stops carrying the load.

## The review room and its access key

`master-of-slides/scripts/review.py` serves the review room on `127.0.0.1`
only, and every request must carry a per-user access key. The link the server
prints includes it; the key itself lives in
`~/.local/share/scicomm-skills/review-token` (mode 600) and is reused across
servers, so a restart does not strand an open page. The server also refuses
requests whose `Host` or `Origin` is not its own, accepts writes only as JSON,
and serves nothing from the build folder except `review/` and `preview/`.

This matters because the agent treats a comment in the room as an instruction
from you. Without the key, any web page open in the same browser — or any
other user on a shared machine — could read the deck or post comments in your
name. Share the link only with reviewers on the same machine; delete the key
file to revoke it (a new one is made on the next start).
