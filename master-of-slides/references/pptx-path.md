# The .pptx path

Choose the deliverable before building anything, because it changes the pipeline.
Ask if the user has not said.

| | HTML → PDF | .pptx |
|---|---|---|
| Typography | full control | PowerPoint's |
| Measurement loop | complete | partial — see below |
| Editable by a collaborator | no (they edit HTML) | yes, which is often the whole reason |
| Projects reliably | anywhere, fonts embedded | depends on the machine and its fonts |
| Builds/animation | repeated slides | native |

**Recommend PDF when** the deck is yours to present and nobody else needs to edit
it. **Use .pptx when** a co-author, PI, or conference organiser needs the file —
that requirement is not negotiable and no amount of typographic argument beats
it. **Both** is occasionally right (present from the PDF, hand over the .pptx),
at the cost of the two drifting once anyone edits one.

Everything upstream of the file format is shared: the outline, the title track,
what goes in the notes, the figures, the numbers discipline. Do that work first,
in `content.md`, and only then choose how to emit it.

## Building a .pptx

Use `python-pptx` (`<skill>/scripts/ensure_env.sh --pptx` adds it to the shared
environment). If the user has a house template
(a `.potx`, or an existing deck with their layouts), start from it —
`Presentation("template.pptx")` keeps their masters, and matching an institutional
template by hand is a bad use of anyone's time.

The parts worth being careful about:

**Set the canvas before the first slide.** A bare `Presentation()` is 4:3
(10 × 7.5 in). If the deck was agreed at 16:9, set `prs.slide_width` and
`prs.slide_height` to 13.333 × 7.5 in — or start from a 16:9 template — before
adding anything, because placements do not survive a later resize.

**Place figures as vector.** `add_picture` accepts EMF/PDF poorly across versions;
the reliable path is a high-resolution PNG (300 dpi at final placed size) or an
SVG on PowerPoint versions that accept it. Emit both from the figure script and
place whichever the user's PowerPoint handles — check by opening it if you can.

**Set every font size explicitly.** A run that inherits from the layout will
render at whatever the template says, which may be 12 pt. `pptxcheck.py` reports
these as `INHERITED-SIZE` because they are the most common way a .pptx ends up
illegible.

**Put the script in the notes slide**, not in a text box off-canvas:
`slide.notes_slide.notes_text_frame.text = "..."`. The slide-by-slide script
pass (SKILL.md Phase 5) applies unchanged here — the full spoken script goes
into each notes slide, where PowerPoint's presenter view will actually show
it; `pptxcheck.py` counts the words per page, so an empty one is visible.

**Keep one shape per idea.** Deeply nested groups are what make a deck
un-editable by the collaborator you built it for.

## Measuring a .pptx anyway

The reason to prefer HTML is that a DOM can be measured. Most of that is
recoverable:

```bash
python scripts/pptxcheck.py deck.pptx          # static: XML-level checks
python scripts/pptxcheck.py deck.pptx --pdf    # plus a LibreOffice render
```

Static checks catch what actually goes wrong: type under the floor, runs
inheriting an unknown size, slides over the word budget, missing titles, shapes
hanging off the canvas, and the title track.

`--pdf` converts through LibreOffice and reports the page geometry, so you can
rasterize and *look* at it. This matters because PowerPoint reflows text that
python-pptx merely places — a text box that looked fine in the XML can autofit
down to 10 pt when opened. Nothing but a render will tell you that. If LibreOffice
is not available, say so plainly and ask the user to open the file once and
confirm, rather than shipping unmeasured.

The review room works on this path too: `review.py <build-dir> --from-pptx
pptx/deck.pptx` pulls titles and notes from the file and previews from the
LibreOffice render — see `references/review-room.md`.

## The hybrid

If the user wants both, build the HTML deck first and treat it as the source of
truth: it is the one you can measure and the one where the design lives. Then
emit the .pptx from the same `content.md` and the same figure files, and say
explicitly in the handover which is canonical — because the moment someone edits
the .pptx, one of them is stale, and it should be clear which.
