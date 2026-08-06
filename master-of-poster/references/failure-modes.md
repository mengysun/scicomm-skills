# Failure modes

Each of these produced a wrong poster that looked right. They are ordered by how
much time they cost before being found.

## Silent measurement failures

**Quirks mode.** Without `<!DOCTYPE html>` the page renders in quirks mode, where
`body.clientWidth` returns the viewport rather than the page box. Every
measurement is then wrong while looking entirely plausible — a 36 in poster
reports 1600 px and every derived inch value is off by the same hidden factor.
`render.py` refuses to build without the doctype.

**`documentElement` in print media.** Even in standards mode,
`document.documentElement.clientWidth` reports the *viewport* under
`emulate_media("print")`. Measure `document.body`. This one is easy to "fix"
wrongly, because swapping between the two changes the number and both look
reasonable.

**Silently clipped blocks.** A flex child compressed below its content clips its
last line while the page box stays clean — so an overflow check passes and a
caption has quietly lost a sentence. Detect it with
`scrollHeight > clientHeight + 1` per element, which `render.py` does.

**Letterboxed figures counted as full.** With `object-fit: contain`, the layout
box and the drawn image differ. Measuring the box inflates the figure fraction
and hides exactly the problem you are trying to find. Compute the drawn rect
from `naturalWidth`/`naturalHeight` and the contain scale.

## Layout traps

**A wrapped heading is invisible in source and expensive on the sheet.** It costs
~0.6 in from every cell in its row. Count characters against the cell width
before choosing a heading size (see `layout-geometry.md`).

**Widening columns can lose figure area.** If plates become height-limited in the
wider cell, the extra width buys nothing and the row got taller for free. Always
re-probe after changing column proportions rather than assuming the direction.

**String-editing structural HTML.** Patching a nested layout with find-and-replace
eventually closes a column early or leaves a section outside its container, and
the symptom appears somewhere unrelated. When a layout edit gets fiddly, rewrite
the file cleanly instead of patching further.

**Applying edits non-atomically.** When patching several strings at once, assert
every match *before* writing anything. A half-applied patch on a file you have
already re-rendered is worse than a failed one.

## Figure traps

**Cropping a raster without checking its ppi.** `pdfimages -list` first; a 100 ppi
embedded panel will print soft. Regenerate from data instead.

**Re-binning a distribution.** Bin width is a claim. Reproduce the source recipe;
check your regeneration against the original panel's peak values.

**Authoring a plate at the wrong width.** In-figure type scales with the plate.
A plate authored at 15 in and shown at 8 in has 14 pt axis labels, and no DOM
audit will catch it because the text is paths.

**Rotated y-labels longer than the panel is tall.** They overrun into the panel
above. Wrap or shorten the label; do not shrink the type.

**Spacing tick positions and widening `xlim` together.** A no-op — the labels stay
the same fraction of the axes apart. Rotate them instead.

**XML comment syntax in SVG.** `<!-- ---- section ---- -->` is invalid: XML
forbids `--` inside comments, and the whole file fails to parse silently,
rendering as a tiny broken image. Keep rule-lines out of SVG comments.

**Assuming a rasterizer supports what Chromium supports.** `<use href="#id">`
without the `xlink:` prefix, and `baseline-shift="sub"`, both behave differently
across renderers. Check plates through the same engine that renders the poster
(`scripts/svgcheck.py`), not a convenient viewer.

## Content traps

**A label that names the wrong quantity.** "measured" when the number is
"significant", "links" when the source says "papers". Check each label against
the sentence in the source that reports the number.

**A caption quoting one p-value for a two-panel figure.** Report by symbol and
key the symbols that appear.

**Orphans after a cut.** Removing panels leaves behind the counts they consumed,
the metric definitions they needed, and the references cited only for them. After
any cut, sweep for every term that the removed panels defined.

**A cross-reference the reader cannot follow.** "Table S1", "Supplementary
Fig. 3" — either state the claim without it or drop the claim.

## Process

**Never modify source materials.** Read them; if figure code must run, copy it
into your own scratch directory first. Each revision goes in a new folder so the
previous deliverable stays intact and comparable — and so "the version I
printed" always still exists.

**Verify that at the end**, don't just intend it:

```bash
find <sources> -newer <marker-file> -type f -print   # should be empty
```

**Check the delivered PDF, not the HTML.** `pdfimages -list <pdf>` should report
zero embedded rasters for a fully vector sheet, and `pdfinfo` should report the
exact trim size.
