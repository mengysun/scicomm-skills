# Failure modes

Each of these ships a deck that looks right in the editor and fails in the room.

## Silent measurement failures

**Quirks mode.** Without `<!DOCTYPE html>` the page renders in quirks mode, where
`body.clientWidth` returns the viewport rather than the page box, so every derived
inch and point value is wrong while looking plausible. `render.py` refuses to
build without the doctype.

**`documentElement` in print media.** Even in standards mode,
`documentElement.clientWidth` reports the *viewport* under
`emulate_media("print")`. Measure `document.body`.

**Overset slides.** A slide's content taller than the slide is hidden by
`overflow: hidden`, so the last line of a build or the bottom row of a table
simply is not there. Nothing errors. `render.py` reports it as `OVERSET`.

**A slide that does not break.** If a `.slide` is not exactly one page tall, the
browser paginates where it likes and one slide becomes two — or two become one.
`render.py` compares the PDF page count against the number of `.slide` elements.

**Letterboxed figures counted as full.** With `object-fit: contain` the layout box
and the drawn image differ; measuring the box inflates the figure fraction and
hides the very gap you are looking for. `audit.py` computes the drawn rect.

## Type and colour

**A plate authored at the wrong width.** In-figure type scales with the plate, and
figure text is drawn as paths, so no DOM audit sees it. Author at display size.

**Journal figures dropped onto slides.** Authored around 3.5–7 in with 7–9 pt
type; on a slide they are illegible, and scaled up they are comically heavy. Re-emit.

**Type below the floor.** Anything under ~2.8% of slide height stops being read
from the back. Watch `<sup>`, which renders at 0.7 em and quietly drops an 18 pt
caption to 12.6 pt — write `0.0001`, not `10<sup>-4</sup>`.

**Emphasis that recedes.** Bold coloured for a pale ground keeps that colour
inside a saturated band: ink-dark on the accent measures ~2.4:1 and disappears at
the back. `audit.py` flags anything under 3:1.

**Colour meaning drifting between slides.** Warm means one thing in the deck, and
it must mean that thing on every slide it appears.

## Content

**Topic titles.** "Results" tells the audience nothing and wastes the one line
they are guaranteed to read. Assert the claim.

**A slide with six numbers.** Nobody retains six. Two is a lot; the rest go in
the notes.

**Text competing with you.** Anything the audience must hear but should not have
to read belongs in the notes. Slides are read faster than you talk, so every
sentence on screen is attention taken from what you are saying.

**A cross-reference the audience cannot follow** — "Fig. 1A,B", "Table S1", "see
the supplement". Either state the claim or drop it.

**Orphans after a cut.** Removing a slide leaves behind the term it defined, the
number the next slide quotes, and the colour key it introduced. After any cut,
check what the removed slide was carrying for the ones after it.

**A backup slide you cannot find.** Title them as answers, not topics; under
question-time pressure you will look for the claim.

## Process

**Never modify the source materials — and leave no output in them either.**
Copying a script out is only half of it: analysis code usually writes to a
relative `figures/` or `../results/`, so the copy still lands its output in the
original tree unless you redirect it. Read the script's output paths before you
run it. Cached data and re-run outputs belong in the build folder.

Each revision goes in a new folder so the version the user already reviewed still
exists. Verify rather than assume:
`find <sources> -newer <marker> -type f` should come back empty.

**Check the delivered file, not the source.** `pdfinfo` for the page count and
geometry; rasterize and look at the slides. For a .pptx, run `pptxcheck.py`, and
open it if you possibly can — PowerPoint autofits text that python-pptx merely
placed, and only a render shows you that.

**Do not reuse a poster's plates in a deck.** The authored widths differ by a
factor of two or more, so the type is wrong in one of them. Share the figure
*script*, not the emitted files.
