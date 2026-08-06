# Figure craft — plates that survive being printed at 36 inches

The plates are the poster. Everything here is about making them legible at
arm's length and honest at any distance.

## Regenerate; do not scale up, and do not crop

Three sources of figures, in descending order of preference:

1. **Re-plot from the analysis code or cached data.** Full control of size, type
   and palette. Author at the width the plate is displayed at.
2. **Vector-extract** an existing drawing you cannot reproduce (a hand-made
   schematic in a slide deck or PDF). It stays sharp at any size:
   ```bash
   gs -o crop.pdf -sDEVICE=pdfwrite -dDEVICEWIDTHPOINTS=W -dDEVICEHEIGHTPOINTS=H \
      -dFIXEDMEDIA -c "<</PageOffset [-x -y]>> setpagedevice" -f source.pdf
   pdftocairo -svg crop.pdf crop.svg
   ```
3. **Crop a raster** — only after checking it can survive the enlargement.

**Always check the ppi before cropping.** `pdfimages -list source.pdf` reports
the embedded resolution. A panel embedded at 100 ppi, cropped and printed at
poster size, lands near 128 dpi — visibly soft next to vector type. When that
happens, regenerate from the data instead; it is usually an hour's work and it
is the difference between a sharp sheet and a blurry one.

If you regenerate a panel that exists in a source artifact, **reproduce its
recipe, not just its data**. Bin width, axis limits and transforms are claims
about the distribution: re-binning a histogram eight times coarser turns a sharp
spike into a broad hill and moves the y-axis peak by a factor of seven. Read the
original plotting code where it exists, and check your regeneration against the
original panel — matching peak heights is a strong signal you got it right.

## Author at display size

Type inside a figure scales with the figure. A plate authored 15 in wide and
displayed at 8 in has all its type multiplied by 0.53 — a 26 pt axis label
becomes 14 pt, and the audit will not catch it because in-figure text is drawn
as paths, not DOM text.

So: **author each plate at the width its cell actually offers** (from
`probe.py`), and keep the in-figure floor at ~25 pt so it survives a small
display scale and still clears 22 pt.

## Axis labels must be shorter than the panel is tall

A rotated y-label is as long as its string. "Percentile citation rank" sets
about 5 in; in a stacked pair where each panel has 3.5 in of axes height, it runs
straight through the panel above. Nothing errors — matplotlib just draws it.

Rule of thumb: **each line of a rotated y-label needs ≈ 0.21 in per character at
30 pt.** Wrap to two or three short lines, or shorten the wording, before
shrinking the type. A wrapper that swaps in a shorter label without touching the
data keeps the change auditable:

```python
def relabel(fn, ylab=None, ylim=None):
    def panel(ax):
        fn(ax)
        if ylab is not None: ax.set_ylabel(ylab, fontsize=P.FS_LABEL)
        if ylim is not None: ax.set_ylim(*ylim)   # headroom for legends/notes
        return ax
    return panel
```

## Annotations need room that scales with the panel

Text placed in data coordinates moves when the panel changes shape. Two habits
that avoid the usual collisions:

- Place free-standing notes in **axes fractions** (`transform=ax.transAxes`) so
  they stay where you put them at any aspect.
- Give the axes explicit headroom (`ax.set_ylim(0, peak * 1.4)`) when annotation
  columns sit above the data, rather than relying on autoscale margins.

Two annotation blocks set either side of a shaded band will not both clear it on
a narrow plate — the text is simply wider than the gaps. Stack them in a corner
instead; it reads the same and never collides.

When a panel gets short and wide, side-by-side annotations collide before you
expect. Wrap them to narrow stacked columns, or move the words into the caption
where the type floor is guaranteed and there is room.

## Significance markers

Put stars **above** their points, centred on them. A star set off to the right
reads as belonging to the gap between two points rather than to either one.

```python
ax.text(x, y + se + pad, stars(p), ha="center", va="bottom", fontweight="bold")
```

Use the same ladder everywhere on the sheet, and let the panel state `NS` rather
than printing its own p-value — the caption's key then covers everything drawn.

## Text as paths

Set `svg.fonttype = "path"` so figure text renders identically regardless of what
fonts the rendering host has. The cost is that you cannot grep an SVG for its
labels; to check what a plate says, rasterize it through the same engine that
renders the poster (`scripts/svgcheck.py`) rather than trusting a different
viewer.

Also set `pdf.fonttype = 42`, transparent backgrounds, and
`bbox_inches="tight", pad_inches=0.12` so nothing sits flush against the plate
edge.

## Panel width floors

Roughly, per panel in a multi-panel plate:

| Panel width | Works for |
|---|---|
| ≥ 8 in | anything, including two-line tick labels and a legend |
| 5–8 in | comfortable for 2–3 category comparisons |
| 4–5 in | tight; shorten tick labels, rotate, drop the legend for direct labels |
| < 4 in | use a single panel instead |

If a cell can only carry one panel, put the *headline* panel there and move the
second result into the caption as a number — with its own significance symbol if
it has one.

## Small typography things that show at 36 inches

- Use a typographic minus (−) in annotations so they match the axis tick labels,
  which matplotlib already sets that way.
- Direct-label series next to the data instead of a legend box where you can; a
  legend competes with the data for the same corner.
- Rotate crowded categorical tick labels ~20° rather than trying to widen them:
  spacing tick positions and widening `xlim` together is a no-op, because the
  labels stay the same fraction of the axes apart.
