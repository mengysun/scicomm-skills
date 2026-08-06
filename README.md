# scicomm-skills

Personal [Claude Code](https://claude.com/claude-code) skills for making things
that get printed or projected.

| Skill | What it does |
|---|---|
| [`master-of-poster`](master-of-poster/) | Conference posters from a manuscript, deck, codebase or figure set — authored in HTML/CSS, rendered to PDF at exact trim size, then measured so layout defects fail the build instead of reaching the printer. |
| [`master-of-slides`](master-of-slides/) | Presentation decks from the same kinds of source — outlined in claim-shaped slide titles with speaker notes, delivered as a measurable multi-page PDF or as `.pptx` when a collaborator needs to edit it. |

Both share a method: **build it, then measure it.** The bundled scripts render
through headless Chromium and interrogate the DOM for the things that are
invisible in source and obvious in print — content past the trim, a block
silently clipped, type under the legibility floor, emphasis that disappears into
its own background, a figure letterboxing away a third of its cell.

## Install

Symlink rather than copy, so `git pull` updates the skills in place and no
machine can quietly run a stale version:

```bash
git clone <this-repo> ~/scicomm-skills
~/scicomm-skills/install.sh
```

`install.sh` is idempotent, backs up anything it would replace, and prints what
it did. To install by hand instead:

```bash
ln -s ~/scicomm-skills/master-of-poster ~/.claude/skills/master-of-poster
ln -s ~/scicomm-skills/master-of-slides ~/.claude/skills/master-of-slides
```

Per-project rather than per-user: symlink into `<project>/.claude/skills/`.

## Requirements

The skills work as prose without any of this, but the scripts — which are most
of the value — need:

```bash
uv pip install playwright matplotlib
playwright install chromium
```

plus **poppler** for `pdfinfo`, `pdftoppm` and `pdfimages`
(`apt install poppler-utils`, `brew install poppler`, or `conda install poppler`).

Only for the `.pptx` path in `master-of-slides`:

```bash
uv pip install python-pptx      # to build .pptx
                                # LibreOffice (`soffice`) for pptxcheck.py --pdf
```

Install into whatever environment you run Claude Code's Bash tool in — a
repo-local `venv/` is fine, and the skills call scripts by path, so nothing has
to be on `$PATH`.

## The palette is a starting point, not a rule

Both skills ship with a specific warm palette in `assets/poster.css` /
`assets/slides.css` and mirrored in `assets/posterfig.py` / `assets/slidefig.py`.
It is one particular sheet, and you should swap it.

What is worth keeping is the *rule* rather than the hexes: **only two colours
ever encode data, and every use is paired with a word label.** Everything else
is neutral plus one accent. That survives colour-vision deficiency, greyscale
printing, a bad projector, and a photograph taken at an angle — which a
categorical set of five pastels does not. `references/palette-and-type.md`
explains the swap and the reasoning.

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
├── scripts/          render · audit · notes · pptxcheck · svgcheck
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
