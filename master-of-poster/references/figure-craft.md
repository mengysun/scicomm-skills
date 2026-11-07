# Figure craft — plates that survive being printed at 36 inches

The plates are the poster. Everything here is about making them legible at
arm's length and honest at any distance.

## What you can actually do depends on what you were given

Settle this per figure, before planning any layout around it.

| What you have | What you can do |
|---|---|
| The plotting code, or the data | Re-plot at display size, in the palette. Full control. |
| A vector figure (PDF, SVG, EPS) | Extract as vector and place **as supplied**. Sharp at any size. |
| A raster only | Check its ppi first, then place **as supplied** — or ask for better. |
| A logo or institutional mark | Place **exactly as supplied**. Nothing else. |

### Figures you cannot regenerate are not yours to restyle

Most of the time the user has the artifacts and not the source. Then:

**Use the figure as supplied. Do not recolour it to the palette.** Colour inside
a result figure usually carries meaning — a class, a scale, a threshold, a
condition — and from the outside you cannot verify which. Recolouring by image
manipulation also degrades the file. A figure that arrives in its own colours and
stays in them is honest; one you have tinted is a claim you did not check.

**Logos and institutional marks are untouchable.** No recolouring, no restyling,
no redrawing, no cropping beyond choosing among lockups the owner already
provides. They are governed by someone else's brand rules, and they are the one
element on the sheet a viewer will recognise as wrong.

**The palette still governs everything you author** — grounds, section headers,
bands, rules, callouts, the take-home, the title block. That is what lets a sheet
carrying foreign figures still read as one thing.

When the supplied figures bring loud colours of their own, **turn your own chrome
down**: neutral grounds, the accent used sparingly. Two colour systems competing
on one surface is worse than either alone.

### Minimal, disclosed intervention

Occasionally a supplied vector figure has one element below the legibility floor
— a label set at 10 pt inside an otherwise fine drawing. Scaling just that
element, in the vector source, is defensible. Three conditions make it so: it is
the smallest change that fixes the problem, it touches nothing that carries data,
and **you tell the user you did it** and offer to revert. Silent restyling of
someone's figure is not the same thing.

### When a supplied figure will not survive

You cannot fix a low-resolution raster or 8 pt axis labels without the source.
Say so plainly and early — "this panel is embedded at 100 ppi and will print near
128 dpi; can you send the source or a higher-resolution export?" — rather than
upscaling it silently or shipping something illegible. A poster or slide with one
soft figure on it is a problem the user can solve if they know about it in time,
and cannot if they find out at the printer.

### Mixed provenance

If some figures are regenerated and others supplied, the sheet will look like two
styles. Better to regenerate all of them or none of them within one surface. When
that is not possible, group the supplied ones together rather than alternating,
and keep your own chrome neutral so the seam reads as sections rather than as
inconsistency.

## When you can regenerate

With the source in hand, prefer in this order:

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

A rotated y-label is as long as its string. "Yield relative to control" sets
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
