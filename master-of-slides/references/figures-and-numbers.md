# Figures and numbers on slides

Most of this is shared with poster work; the differences are called out.

## Author at display size

Type inside a figure scales with the figure. A plate authored 12 in wide and
shown at 7 in has had every label multiplied by 0.58 — an 18 pt axis label
becomes 10 pt, and no audit catches it because figure text is drawn as paths, not
DOM text.

So author each plate at the width it will occupy: usually **7–11 in** on a 16:9
slide. `assets/slidefig.py` is set up for that, with an in-figure floor of 16 pt.

The corollary is that a plate made for a paper is almost never right for a slide.
Journal figures are authored around 3.5–7 in wide with 7–9 pt type; dropped onto
a slide they are either illegible or, if scaled up, comically heavy-lined. Re-emit
at slide size rather than scaling.

## Match the plate to the box it lands in

A figure scaled with `object-fit: contain` letterboxes: whichever dimension binds
first caps its area and the rest is dead space. On a claim+figure slide the box
is predictable, so you can author straight to it:

```
box width  = slide width  − 2 × padding                    ≈ 12.1 in on 16:9
box height = slide height − 2 × padding − title − caption  ≈ 4.4 in
box aspect ≈ 0.36
```

A plate authored at 8.4 × 4.6 in (aspect 0.55) dropped into that box is
width-limited: it draws at about 8 × 4.4 in and leaves 4 in of slide unused, which
`audit.py` reports as a low `fig%`. Authoring the same panel at 12 × 4.3 in fills
it. When a slide's figure fraction looks low, this is almost always why — check
the plate's aspect against the box before touching anything else.

Two-up slides halve the width, so their plates want roughly 5.8 × 4.4 in
(aspect 0.76) — nearly square, and a different cut of the same figure.

## One figure, one point

A paper figure earns four panels because the reader can dwell. A slide audience
gets one look. Split a multi-panel figure across slides, one panel per claim, and
let the build show them accumulating if the comparison matters.

When you must show a four-panel figure whole — because the comparison *is* the
point — say what to look at first, and consider dimming the panels you are not on
yet (`.dim`).

## Simplify what a paper figure carries

Things a paper figure needs and a slide figure usually does not:

- **Grid lines and minor ticks.** Drop them; they add ink at exactly the sizes
  that blur on a projector.
- **A legend box.** Direct-label the series next to the data instead. A legend
  costs a saccade the audience does not have.
- **Every tick.** Three or four labelled ticks per axis is plenty when the point
  is a comparison rather than a lookup.
- **Full statistical apparatus.** See below.

Things a slide figure needs more of: line weight, marker size, and white space
around the plotting area.

## Numbers

**Two numbers per slide is a lot.** A slide with six numbers on it has none,
because nobody retains six. Put the one or two that carry the claim on the slide,
set large enough to read from the back, and leave the rest for the notes and the
questions.

When a number is the point, make it the object: `.stat` sets it at 84 pt with a
caption under it. "+3.6 percentile points" at 84 pt is remembered; the same number
inside a sentence at 24 pt is not.

Round to the precision the claim needs, and no further. If the claim is "positives
do better", `+3.6 points` is the claim; `+3.64 points` is noise, and `+3.6357` is
noise that invites a question about your error bars.

## Significance

Same discipline as a poster: **report by symbol, key the symbols once.** Use the
standard ladder — `*` < 0.05, `**` < 0.01, `***` < 0.001, `****` < 0.0001, `NS`
otherwise — put the symbol on the panel, and put the key in the caption or the
notes.

The failure this avoids is specific: a figure with two panels has two p-values,
and a caption that quotes one is wrong about half the figure. On a slide there is
even less room to quote them, so the symbol does the work and the exact values
live in the notes where you can answer "what was the p-value?" precisely.

State the test somewhere — the caption if it fits, otherwise the notes. "What
test is that?" is the most common question a results slide gets.

## Provenance, without cluttering the slide

Everything on a slide should trace to a source or a cached run, exactly as on a
poster. The difference is where the trace lives: a slide has no room for an
inventory table, so put the sample sizes, the tests and the caveats **in the
notes**, and keep on the slide only what the claim needs.

Two things that do belong on the slide:
- the **unit and the sample** when they are not obvious from the axis;
- a **source line** (`.source`, 16 pt, muted) for data you did not generate.

And two rules that carry over unchanged:
- **Number figures in deck order**, not in the source's order. A slide reading
  "Fig. 1A,B" is quoting a document the audience does not have. If you number at
  all — many decks do not need to — number by appearance.
- **No cross-references the audience cannot follow**: "Table S1", "see the
  supplement". Either state the claim or drop it.

## Reusing plates across a poster and a deck

Tempting, and usually wrong: the authored widths differ by a factor of two or
more, so the type is wrong in one of them. Keep one figure *script* with a size
argument and emit both — that way the data and the styling stay identical and
only the geometry differs, which is the thing that should differ.
