---
name: master-of-slides
description: Build presentation decks from a manuscript, poster, codebase, or set of results — outline first with claim-shaped slide titles and speaker notes, then either HTML/CSS rendered to a multi-page PDF through headless Chromium (fully measurable: per-slide overflow, type floors, contrast, word budget, figure area) or a .pptx via python-pptx when a collaborator needs to edit it. Use this whenever the user mentions slides, a deck, a talk, a presentation, a seminar, a lab meeting, a conference talk, a job talk, a thesis defence, PowerPoint or Keynote, speaker notes, or asks to turn a paper, poster, or project into something they can present — including follow-up edits to a deck built earlier in the session. Also use it when someone asks for "something to present" or wants figures re-cut for projection even if they never say the word "slides".
---

# Master of Slides

A slide is not a small poster. A poster must stand alone; a slide has you
standing next to it, and the audience reads it faster than you can talk. So the
craft is different in one structural way: **the slide carries the claim and the
evidence, and you carry everything else** — which means the speaker notes are
part of the deliverable, not an afterthought.

Everything else — measure the build, author figures at display size, two colours
encode data, number figures by appearance, every number traces — carries over
from careful print work and is worth the same effort here.

## First: what is the deliverable?

This changes the pipeline, so settle it before building. If the user has not
said, ask:

- **PDF** (recommended when the deck is theirs to present) — HTML/CSS → headless
  Chromium → one multi-page PDF. Keeps the whole measurement loop, embeds fonts,
  projects anywhere. A collaborator cannot edit it without editing HTML.
- **.pptx** — when a co-author, PI, or organiser needs the file. That requirement
  is not negotiable and no typographic argument beats it. See
  `references/pptx-path.md`, including how to keep measuring it anyway.
- **Both** — present from the PDF, hand over the .pptx, and say which is
  canonical, because the moment someone edits one it is stale.

Everything upstream of that choice is shared. Do the outline first.

## Non-negotiables

**Never modify the source materials.** Read them; copy figure code into a scratch
directory if it must run. Each revision goes in a **new folder** so the version
the user already reviewed still exists. Verify at the end:
`find <sources> -newer <marker> -type f` should be empty.

**Every number traces** — to the source or to a cached re-run you can point at.
No invented figures, no misleading rounding. If something is missing, leave a
visible `[[TODO: ...]]` marker rather than fabricating.

## Phase 0 — Recon

Read the source, and settle three things before writing a slide:

- **The one sentence** you want repeated at lunch. Everything else serves it.
- **The audience and the slot.** A 12-minute conference talk, a 50-minute
  seminar, and a lab meeting are three different decks from the same work. About
  **one minute per content slide** is the planning number.
- **The figures and their provenance.** Can you re-plot from code or data? A
  journal figure dropped onto a slide is illegible — it was authored 3.5–7 in
  wide with 7–9 pt type. Plan to re-emit at slide size.

Sources vary; the job does not:

| Source | Where the spine comes from |
|---|---|
| Manuscript | the abstract is usually the talk in miniature; results order is a *candidate*, not the answer |
| Poster | the section titles are often already claim-shaped — reuse them, re-cut every plate |
| Codebase | README and tests say what it does; a demo of it running is usually the best "figure" |
| Results only | ask what the claim is; you cannot infer an argument from plots |

## Phase 1 — Outline, in claim titles

Write `content.md` first: the ordered slides, each with **the claim it makes as
its title**, the evidence on it, and the note you will say. Titles assert —
"Positives pay off more", not "Results". Read the titles in order with nothing
else; if they do not tell the story on its own, fix that before building.

This is the cheapest moment to be wrong, and slide order is the user's call, so
unless it is obvious or specified, show them the title track and pause there.

`references/deck-architecture.md` covers the arc, one-idea-per-slide, what
belongs in the notes rather than on the slide, builds, and timing. Read it now if
you have not.

Carry over from print discipline: **number figures by appearance in the deck**,
not by the source's numbering — a slide reading "Fig. 1A,B" quotes a document the
audience does not have — and no "Table S1" style cross-references at all.

## Phase 2 — Design system

Copy `assets/slides.css` and `assets/slidefig.py` into the build folder. They
carry the palette, type scale, slide layouts and figure style as one system so
the deck and its figures agree.

Two rules from the stylesheet worth knowing without reading it: **only two
colours ever encode data, always beside a word label**, and **emphasis inside a
saturated band must be light** — ink-dark bold on the accent is ~2.4:1 and
disappears at the back of the room.

Type floors, sizes and density targets are in `references/slide-craft.md`.

## Phase 3 — Build (HTML path)

One HTML file is one deck. Each `<section class="slide">` is exactly one page, so
the browser paginates and every slide can be measured on its own.

```html
<!DOCTYPE html>
<link rel="stylesheet" href="../css/slides.css">
<style>
  @page { size: 13.333in 7.5in; margin: 0; }
  :root { --slide-w: 13.333in; --slide-h: 7.5in; }
</style>

<section class="slide">
  <h2 class="stitle">Positives pay off more</h2>
  <figure class="fig">
    <img src="../assets/figures/impact.svg" alt="citation rank by class">
    <figcaption><b>*</b> <i>p</i>&nbsp;&lt;&nbsp;0.05 · <i>n</i> = 1,981</figcaption>
  </figure>
  <div class="notes">Point at the gap first, then the error bars. Mann–Whitney,
    p = 0.0099. If asked about magnitude: +3.6 percentile points.</div>
</section>
```

`<div class="notes">` never projects — it is pulled into a rehearsal script by
`scripts/notes.py`. Anything the audience must hear but should not have to read
goes there. A slide with no note usually has text doing the presenter's job.

Layout patterns (claim+figure, two-up, full bleed, statement, divider) are in
`assets/slides.css` and explained in `references/slide-craft.md`.

## Phase 4 — Measure

```bash
python <skill>/scripts/render.py <build-dir>          # → PDF + per-slide PNGs
python <skill>/scripts/audit.py  <build-dir>          # → title track + per-slide table
python <skill>/scripts/audit.py  <build-dir> --titles # → just the title track
python <skill>/scripts/notes.py  <build-dir>          # → notes/<deck>.md
```

`render.py` fails the build on a missing doctype, content past the slide edge, a
slide whose content is taller than the slide (silently clipped, because overflow
is hidden), and a page count that does not match the slide count. Read
`references/failure-modes.md` once so you recognise these.

`audit.py` prints **the title track first** — read it as prose; it is the cheapest
quality check the deck has — then per slide: word count, notes word count,
smallest type in points *and* as a fraction of slide height, lowest contrast, and
figure area. Flags: over 55 words, type under 16 pt or 2.8% of height, contrast
under 3:1, no title.

Then **look at the slides.** `preview/*.png` is one PNG per slide. Measurement
catches geometry; it does not catch a legend sitting on a bracket, a colour that
changed meaning between slides, or a claim title that does not match the figure
under it. Flip through them in order — that is also the only way to feel the
pace.

For the .pptx path, `scripts/pptxcheck.py <deck.pptx>` recovers most of these
checks from the XML, and `--pdf` renders through LibreOffice so you can see what
PowerPoint will actually do to your text boxes.

## Phase 5 — Verify and hand over

- **The title track is the argument**, read alone.
- **Every claim on a slide is supported** by the figure under it, and every term
  is defined before it is used — checked against the *audience*, not the paper.
- **Nothing orphaned** by a cut: a term the removed slide defined, a number the
  next slide quotes, a colour key it introduced.
- **Type, contrast, word budget** clean, or a stated exception.
- **Slide count against the slot**, with builds counted honestly ("18 slides, 24
  pages with builds").
- **The delivered file**, not the source: `pdfinfo` for geometry and page count;
  for a .pptx, open it if you possibly can.
- **Nothing outside the build folder changed.**

Deliver the PDF (or .pptx) *and* the extracted notes — the notes are half of what
makes a deck usable, and the user cannot rehearse from slides alone.

```
deck_build_<n>/
├── content.md      the outline: claim titles, evidence, notes, number provenance
├── README.md       what changed, what was measured, what was left alone
├── assets/         figures/ (emitted at slide size), logos, fonts
├── css/slides.css
├── figsrc/         figure code + cached plot data
├── html/*.html     one file per deck
├── pdf/*.pdf       one multi-page PDF per deck
├── notes/*.md      extracted speaker notes
└── preview/*.png   one PNG per slide
```

## Working with the user

Decks converge through revisions and the user's ear is what they converge to.

- **Send the file every round**, plus the title track in the message — it is the
  fastest thing for them to react to.
- **Report the measurements honestly**, including the ones that flatter you less.
- **When they ask for one change, make it** — and if it orphans something (a
  definition, a number, a colour key), fix the consequence and say you did.
- **Surface what you left alone**, so they can overrule you cheaply.
- **Offer the lever, do not pull it.** When a constraint costs something
  measurable — a 12-minute slot cannot hold the method detail they want — name
  the trade and let them choose.

## Reference index

| File | Read it when |
|---|---|
| `references/deck-architecture.md` | outlining: the arc, claim titles, slide/notes division, builds, timing |
| `references/slide-craft.md` | canvas, type floors, density, layout patterns, consistency |
| `references/figures-and-numbers.md` | re-cutting figures for projection, how many numbers, significance |
| `references/pptx-path.md` | the user needs an editable file |
| `references/failure-modes.md` | before the first build, and when something measures wrong |

Scripts take the build directory as their first argument (`pptxcheck.py` takes a
file). They need `playwright` with Chromium and `matplotlib`, plus poppler's
`pdfinfo`/`pdftoppm`; the .pptx path additionally needs `python-pptx`, and
`pptxcheck.py --pdf` needs `soffice` on PATH.
