---
name: master-of-poster
description: Build print-ready conference posters from a manuscript, slide deck, codebase, or figure set — authored in HTML/CSS, rendered to PDF through headless Chromium at exact trim size, then measured (figure area, type floors, contrast, overflow, clipping) so layout defects fail the build instead of reaching the printer. Use this whenever the user mentions a poster, a poster session, a conference or symposium sheet, A0 / 36×48 / 36×54 output, "turn this paper into a poster", or wants an existing poster revised, retitled, re-laid-out, or re-measured — including small follow-up tweaks to a poster built earlier in the session. Also use it when someone asks for a large-format single-sheet summary of a paper or project even if they never say the word "poster".
---

# Master of Poster

A poster is not a paper on a wall. Someone will walk up while you are mid-sentence
with somebody else, spend ninety seconds, and leave with one idea or none. The
whole method below follows from that: large type, few words, figures doing the
work, and a build that measures itself so nothing broken reaches the printer.

## Non-negotiables

**Author in HTML/CSS, render through headless Chromium.** Generating PDF directly
gives poor typography and no way to measure the result. The browser gives exact
trim size, real text metrics, and a DOM you can interrogate — which is what makes
everything else in this skill possible.

**Never modify the source materials.** Read them. If figure code must run, copy it
into a scratch directory first. Each revision goes in a **new folder**, so the
version the user already looked at still exists and the two can be compared.
Verify this at the end rather than assuming it:
`find <sources> -newer <marker> -type f` should come back empty.

**Every number traces.** To the source, or to a cached re-run you can point at. No
invented figures, no misleading rounding, no placeholder text — leave a visible
`[[TODO: ...]]` marker instead, because a marker gets fixed and a plausible
invention gets printed.

## Phase 0 — Recon

Read the source before designing anything. What you are looking for:

- **The claim chain.** What is the one sentence a visitor should leave with, and
  what is the shortest path of evidence to it?
- **The figures and their provenance.** For each, can you re-plot it from code or
  data, or must you extract it from a PDF/deck? Run `pdfimages -list` on any PDF
  you might crop from — an embedded 100 ppi panel will print soft at poster size.
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

The colour rule, in one line: **only two colours ever encode data, and every use
is paired with a word.** Everything else is neutral plus one warm accent. See
`references/palette-and-type.md` for why, for the default hexes, for how to swap
in a supplied palette, and for the type floors.

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
python <skill>/scripts/render.py <build-dir>     # → pdf/, preview/, fails on defects
python <skill>/scripts/probe.py  <build-dir>     # → the box each cell offers
python <skill>/scripts/audit.py  <build-dir>     # → fig%, type, words, gaps, contrast
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
├── figsrc/           figure code + cached plot data
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
`contact_sheet.py`. They need `playwright` (with Chromium installed),
`matplotlib`, and poppler's `pdfinfo` / `pdftoppm` / `pdfimages`.
