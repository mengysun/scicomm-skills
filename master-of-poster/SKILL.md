---
name: master-of-poster
description: Build print-ready conference posters from a manuscript, slide deck, codebase, or figure set — authored in HTML/CSS, rendered to PDF through headless Chromium at exact trim size, then measured (figure area, type floors, contrast, overflow, clipping) so layout defects fail the build instead of reaching the printer. Use this whenever the user mentions a poster, a poster session, a conference or symposium sheet, A0 / 36×48 / 36×54 output, "turn this paper into a poster", or wants an existing poster revised, retitled, re-laid-out, or re-measured — including small follow-up tweaks to a poster built earlier in the session. Also use it when someone asks for a large-format single-sheet summary of a paper or project even if they never say the word "poster".
---

# Master of Poster

A poster is not a paper on a wall. Someone will walk up while you are mid-sentence
with somebody else, spend ninety seconds, and leave with one idea or none. The
whole method below follows from that: large type, few words, figures doing the
work, and a build that measures itself so nothing broken reaches the printer.

## First: what size is the sheet?

The venue sets the trim, not taste, and every layout decision downstream — how
many rows fit, how large a figure can get, what the type floors work out to —
is computed against it. Changing it once a layout exists is a re-layout, not a
resize. So if the user has not said, ask before anything else:
**"What size and orientation — e.g. 36 × 48 in landscape, A0 portrait?"** is
enough.

- Record it as **width × height** and set exactly that in `@page` and
  `--page-w`/`--page-h` (Phase 3). "48 × 36" and "36 × 48" are different
  boards; if the user gives two numbers and no orientation, confirm which way up.
- Metric sizes convert exactly: A0 is 33.1 × 46.8 in (841 × 1189 mm), A1 is
  23.4 × 33.1 in. Use the venue's own figure rather than rounding.
- A revision of an existing poster keeps its size unless told otherwise — read
  it from that poster's `@page`.
- If they do not know yet, carry on: recon and the content spine do not depend
  on the sheet. Ask again when you show the spine, because Phase 3 needs it.
  `references/layout-geometry.md` § "Sizing the sheet" says what each size
  holds, which is worth passing on if they are choosing.

## Non-negotiables

**Author in HTML/CSS, render through headless Chromium.** Generating PDF directly
gives poor typography and no way to measure the result. The browser gives exact
trim size, real text metrics, and a DOM you can interrogate — which is what makes
everything else in this skill possible.

**Never modify the source materials, and leave nothing behind in them.** A
research codebase is the canonical record of the analysis; a poster is a
downstream artifact, and the build should be deletable without touching it.

- **Read, do not edit.** If figure code has to run, copy it into the build
  folder's `figsrc/` and run it there.
- **Check where it writes before you run it.** Analysis scripts commonly save to
  a relative `figures/` or `../results/`, so a *copied* script can still deposit
  output back into the original tree. Redirect those paths into the build folder.
- **Intermediate results live with the build** — cached data, re-run outputs,
  converted figures, extracted vectors. They belong beside the poster that needs
  them, not beside the analysis that produced them.
- **Each revision is a new folder**, so the version the user already looked at
  still exists and the two can be compared.

Verify at the end rather than assuming it:

```bash
touch /tmp/build-start                                   # before you begin
find <source-dirs> -newer /tmp/build-start -type f       # must be empty at the end
```

**Every number traces.** To the source, or to a cached re-run you can point at. No
invented figures, no misleading rounding, no placeholder text — leave a visible
`[[TODO: ...]]` marker instead, because a marker gets fixed and a plausible
invention gets printed.

## Before anything else — the environment

The scripts and the figure engine run in a **shared environment**, set up once
per machine rather than once per project. Get its interpreter now, before Phase 2
needs matplotlib, and use it for everything the skill runs:

```bash
PY=$(<skill>/scripts/ensure_env.sh)     # first time ~1 min, thereafter ~2 s
```

Do this yourself. Do not ask the user to install anything — the whole point of
the script is that they should never have to think about it.

It lives at `~/.local/share/scicomm-skills/venv` (override with `$SCICOMM_VENV`)
and holds playwright, a headless Chromium and matplotlib: the same tooling for
every poster and deck on the machine, and Chromium alone is ~180 MB, so there is no
reason to install it per project.

**This is deliberately not the project's environment.** Analysis code keeps its
repo-local venv beside the results it produced; this one only runs build scripts.
The exception is figure code copied into `figsrc/` that imports the project's own
modules — run that with the project's python, and everything else with `$PY`.

One thing it cannot install and reports instead: **poppler**
(`pdfinfo`/`pdftoppm`/`pdfimages`, which `render.py` needs to verify the emitted
PDF). If it is missing, say so to the user early rather than
discovering it at the point of failure.

## Phase 0 — Recon

Read the source before designing anything. What you are looking for:

- **The claim chain.** What is the one sentence a visitor should leave with, and
  what is the shortest path of evidence to it?
- **The figures and their provenance**, per figure. Do you have the plotting
  code or the data, a vector artifact, or only a raster? This decides what you
  are allowed to do: a figure you can regenerate you author at display size in
  the palette; a figure you were merely given you place **as supplied**, without
  recolouring it — and logos are placed exactly as given, never restyled. Run
  `pdfimages -list` on any PDF you might crop from; an embedded 100 ppi panel
  will print soft, and that is worth raising before you build a layout on it.
  `references/figure-craft.md` has the decision table.
- **The numbers**, and the exact sentence in the source that reports each one.
  You will need those sentences later to check that your labels name the right
  quantity.
- **The audience.** A poster going to a venue outside the paper's home field
  needs its domain terms defined on the sheet or avoided entirely, and the "so
  what" written in the language of the people reading it.

Different sources, same job:

| Source | Where the spine comes from | Where the figures come from |
|---|---|---|
| Manuscript | abstract → claim; results section order → candidate section order | figure scripts if present; otherwise the PDF, checked for ppi |
| Slide deck | the build order of the argument; speaker notes are often the plainest prose on hand | slide graphics vector-extract well; charts usually need re-plotting |
| Codebase | README and tests state what it does; the entry points state how | generate them — a codebase rarely has poster-ready figures |
| Figure set alone | ask; you cannot infer a claim chain from plots | already have them, but check authored size |

## Phase 1 — Content spine, before any layout

Write `content.md` in the build folder first: the title, the one-sentence
take-home, the ordered sections with the claim each makes, and the figure each
carries. Then the numbers, each with the sentence it came from.

**This is the cheapest moment to be wrong.** Section order is the user's call and
reordering after the layout is built is expensive, so unless the order is obvious
or already specified, show them the spine and stop for a moment before building.

Numbering rules — these matter more than they look, see `references/content-rules.md`:

- **Figures are numbered in poster order, from 1.** Not the manuscript's numbers.
  A visitor is not holding the paper, so "Fig. 1A,B" followed by "Fig. 4" only
  tells them something is missing. Keep the correspondence in `content.md`.
- **No cross-references the reader cannot follow** — "Table S1", "Supplementary
  Fig. 3". State the claim without the pointer, or drop the claim.
- **Significance by symbol, keyed once per caption.** Quoting a p-value in a
  caption goes wrong the moment a figure has two panels with two p-values.

## Phase 2 — Design system

Copy `assets/poster.css` and `assets/posterfig.py` into the build folder. They
carry the palette, type scale, and layout primitives as one system, so the page
and the figures agree without being kept in sync by hand.

Colour comes from one palette, used for the page chrome and for any figure you
generate, so the whole sheet looks like one thing. Which swatch means what is
yours to decide — that is a property of the data, not of the palette. Figures
and logos you were supplied rather than made keep their own colours; the palette
governs what you author around them. See
`references/palette-and-type.md` for the sheet, for how to swap in another, for
choosing within it, and for the type floors.

## Phase 3 — Build

Each poster is one standalone HTML file: a `<!DOCTYPE html>`, a link to the
shared stylesheet, and a `<style>` block with this sheet's `@page` size and its
own layout. Structure:

```html
<!DOCTYPE html>
<style>
  @page { size: 36in 54in; margin: 0; }
  :root { --page-w: 36in; --page-h: 54in; }   /* must match @page */
</style>
<div class="poster reg-classic">
  <header class="titleblock"> logo · title · authors · affiliation </header>
  <div class="main">
    <div class="row r1"> …sections… </div>
    <div class="row r2"> … </div>
  </div>
  <footer class="footer closing"> take-home band · contacts · references </footer>
</div>
```

A section is a `<section class="block figblk bleed">` holding a `<h2 class="pill">`,
an `<img>`, and a `<figcaption>`. `figblk` makes the figure claim the leftover
height of its cell; `bleed` lets it span the card edge to edge while the header
and caption stay inset. Add `natural` when a wide-and-short plate should set its
row's height rather than stretch to it.

Layout choices worth making deliberately:

- **Row-major** (bands read left to right) suits a board people walk along, and
  lets each band be a complete step.
- **Column-major** is the conventional reading order and suits a tall board.
- **Fewer, taller rows beat more, shorter rows** — every row costs ~2.4 in of
  overhead before any figure. See `references/layout-geometry.md`.

## Phase 4 — The measurement loop

This is the part that makes the difference, and it is not optional. Build,
measure, re-cut, repeat:

```bash
"$PY" <skill>/scripts/render.py <build-dir>    # → pdf/, preview/, fails on defects
"$PY" <skill>/scripts/probe.py  <build-dir>    # → the box each cell offers
"$PY" <skill>/scripts/audit.py  <build-dir>    # → fig%, type, words, gaps, contrast
```

`render.py` fails the build on a missing doctype, a page-size mismatch, content
past the trim, or a block compressed below its content. Those four have each
produced a poster that looked fine and was not — read
`references/failure-modes.md` once so you recognise them.

`probe.py` prints, per cell: the box in inches, its aspect, the plate's aspect,
and the percentage being letterboxed. **Use it to cut the plates.** A figure
scaled with `object-fit: contain` loses whatever the two aspects differ by, so:

1. build the layout with any plate,
2. probe it and read the real box aspect,
3. re-author the plate at that aspect,
4. re-render and re-probe — `waste%` should be ≤ 2.

Do not skip step 2 by reasoning about the layout. Caption line counts and header
wrapping move the box by half an inch, and half an inch is several points of
figure fraction. `bbox_inches="tight"` also does not preserve your figsize
aspect, so expect one correction pass scaling by `target / achieved`.

`audit.py` reports against the floors: **figures ≥ 55% of body area**, type ≥ 22 pt,
400–700 words, gaps ≥ 0.4 in, edges ≥ 1 in, contrast ≥ 3:1. Treat a flag as a
build failure, not a style preference. If a layout genuinely cannot meet one —
a text-heavy method panel in the body of a square sheet will not reach 55% —
say which floor you missed and why, rather than letting it pass unmentioned.

Then **look at the rendered PNG.** Measurement catches geometry; it does not
catch a legend sitting on a bracket, an annotation crossing a spine, or a
letterform lost under a strike-through. Read `preview/*.png`, and crop regions
at higher dpi (`pdftoppm -r 200 -x -y -W -H`) for anything that looks tight.

## Phase 5 — Verify and hand over

A final sweep, each item of which has caught something real:

- **Numbers.** Every numeral on the sheet traces. No `[[TODO]]` left.
- **Labels name the right quantity.** Check each against the source's own
  sentence — "measured" when the number is "significant" is the classic.
- **Every count and claim has a consumer.** A number in a method panel that backs
  no panel and appears in no caption is decoration. Conversely, after cutting any
  panel, sweep for the counts, metric definitions and references that went with
  it — orphans are what a careful visitor notices.
- **The PDF, not the HTML.** `pdfinfo` for the exact trim; `pdfimages -list`
  should report zero embedded rasters for a fully vector sheet.
- **Nothing outside the build folder changed.**

Then write the build folder's `README.md`: what changed and why, the measured
numbers, what you deliberately left alone, and any number that is *not* in the
source (an n the paper never printed, say) — "traces to the manuscript" and
"traces to the cached run" are different claims and the user should know which.

Deliverable layout:

```
poster_build_<n>/
├── content.md        the spine: sections, claims, figure map, number provenance
├── README.md         what changed, what was measured, what was left alone
├── assets/           logos, fonts, figures/ (the emitted plates)
├── css/poster.css
├── figsrc/           figure code (copied here, never run in place) + cached data
├── html/*.html
├── pdf/*.pdf
└── preview/*.png
```

## Working with the user

Poster work converges through revisions, and the user's eye is the thing being
converged to. A few habits that make that loop cheap:

- **Deliver the PDF, not a description of it.** Send the file every round.
- **Report the measurement honestly**, including the number that flatters you
  less. If a figure fraction depends on whether a panel counts as front matter or
  body, give both and say which the headline is.
- **When they ask for one change, make that change** — but if it orphans
  something (a count, a definition, a reference, a term in a section title),
  fix the consequence too and say you did.
- **Surface what you left alone.** "The crossed A in §1 is hard to read; that is
  your artwork, say the word" is more useful than either silently changing it or
  silently ignoring it.
- **Offer the lever, do not pull it.** When a constraint they asked for costs
  something measurable, name the trade and let them decide.

## Reference index

Read the one you need; they are written to be consulted, not memorised.

| File | Read it when |
|---|---|
| `references/layout-geometry.md` | choosing rows/columns, tuning figure area, anything about size |
| `references/figure-craft.md` | authoring or extracting plates, panel sizing, annotations, significance markers |
| `references/content-rules.md` | numbering, labelling, traceability, what may appear on a sheet |
| `references/palette-and-type.md` | palette roles, swapping palettes, type floors, contrast |
| `references/failure-modes.md` | before the first build, and whenever something looks right but measures wrong |

Scripts take the build directory as their first argument:
`render.py`, `probe.py`, `audit.py`, `svgcheck.py <in.svg> <out.png> [scale]`,
`contact_sheet.py [--title "..."]`. Run them with the interpreter `scripts/ensure_env.sh` prints;
it installs what they need apart from poppler, which it checks for and reports.
