# scicomm-skills

Portable [Agent Skills](https://agentskills.io/) for
[Claude Code](https://claude.com/claude-code) and
[Codex](https://developers.openai.com/codex/) that make things for print and
projection.

| Skill | What it does |
|---|---|
| [`master-of-poster`](master-of-poster/) | Conference posters from a manuscript, deck, codebase or figure set — authored in HTML/CSS, rendered to PDF at exact trim size, then measured so layout defects fail the build instead of reaching the printer. |
| [`master-of-slides`](master-of-slides/) | Presentation decks from the same kinds of source — outlined in claim-shaped slide titles with speaker notes, delivered as a measurable multi-page PDF or as `.pptx` when a collaborator needs to edit it. Finished decks get a page-by-page speaker script and a local review room: each slide beside its note with a comment thread, every comment recorded in a JSON file the agent works through on the next round. |

Both share a method: **build it, then measure it.** The bundled scripts render
through headless Chromium and interrogate the DOM for the things that are
invisible in source and obvious in print — content past the trim, a block
silently clipped, type under the legibility floor, emphasis that disappears into
its own background, a figure letterboxing away a third of its cell.

## Install

Symlink rather than copy, so `git pull` updates the skills in place and no
machine can quietly run a stale version. The installer links the same source
folders into both agents' personal skill directories:

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

To remove only the symlinks created by this repository, from both agents:

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

Scripts take a build directory as their first argument, so they work on any
project:

```bash
python ~/scicomm-skills/master-of-poster/scripts/render.py <build-dir>
python ~/scicomm-skills/master-of-poster/scripts/audit.py  <build-dir>
python ~/scicomm-skills/master-of-slides/scripts/audit.py  <build-dir> --titles
```

## Provenance

These came out of building one poster seven times, with a real author saying
what was wrong each round. Most of what is in `references/` is a mistake that
cost a version — the contrast bug that survived six of them, the histogram
binned eight times too coarse, the caption quoting one p-value for a two-panel
figure. The `why` is written down next to each rule because the rule alone does
not transfer.
