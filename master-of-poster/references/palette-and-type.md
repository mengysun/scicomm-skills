# Palette and type

## The palette

One set of colours, used for the page chrome and for any figure you generate, so
that everything you make looks like it belongs together. **Which swatch means
what is yours to decide** — that is a property of your data, not of the palette.

It governs what you author. A figure you were supplied rather than made keeps its
own colours, and a logo is placed exactly as given — see `figure-craft.md`. When
the supplied figures are colourful, keep your chrome neutral so the two systems
do not fight.

| Swatch | Hex | | Swatch | Hex |
|---|---|---|---|---|
| terra | `#D56C55` | | plum | `#AB85AC` |
| terra-mid | `#E8B19D` | | plum-pale | `#D4C2D9` |
| terra-pale | `#F1D4C9` | | gold | `#EAC264` |
| blue-deep | `#738FC1` | | sand-mid | `#F3DAA9` |
| blue-mid | `#A9BFE3` | | sage | `#7E9D90` |
| blue-pale | `#C9D7EE` | | umber | `#905426` |
| green-mid | `#BFD598` | | stone | `#E3DCD0` |
| green-deep | `#7AA974` | | cream | `#FFEDCE` |
| green-pale | `#DCECCB` | | butter | `#FFEDC0` |

Neutrals alongside it: ink `#2E2A26`, ink-soft `#574F47`, muted `#8A8078`,
hair `#C9C0B6`, paper `#FFFFFF`, paper-tint `#FAF4E9`.

`poster.css` names all of these and then assigns a few **roles** from them —
`--pos`, `--neg`, `--accent`, `--paper-warm`, `--band`. Those are a starting
assignment for the common case of a two-group comparison, not a restriction:
rename them, reassign them, add more when your data has more classes.
`posterfig.py` mirrors the same names, and `CYCLE` is a default ordering for
categorical series, installed as matplotlib's colour cycle by `setup()` so
unstyled plots already match.

### Choosing within it

- **Saturated members separate; pale ones do not.** terra, blue-deep,
  green-deep, gold, plum, sage and umber hold apart at small sizes and in print.
  The pale tints are for fills, bands and grounds, where the job is not to
  shout.
- **Beyond about five categories**, colour stops doing the work no matter which
  palette you use. Small multiples, direct labels, or ordering by value carry
  more than a sixth hue.
- **A word beside the colour is usually free**, and it buys a figure that still
  reads photocopied, photographed under bad light, or by someone with
  colour-vision deficiency. Direct-label the series next to the data where the
  panel allows it rather than sending the reader to a legend. This is a habit
  worth having, not a law — a four-category scatter with a legend is fine.
- **Keep a colour's meaning fixed** across a sheet or a deck. Whatever terra
  means in the first figure it must mean in the last.

### Swapping in another palette

Replace the named swatches at the top of `poster.css` and the same names in
`posterfig.py`; the roles and `CYCLE` follow. If the user hands you a palette
sheet, extract the hexes and keep the same shape: a handful of saturated members
for encoding, the tints for grounds.

## Contrast

`audit.py` reports the lowest text contrast on the sheet and flags anything
under 3:1. Watch one pattern in particular: **a rule written for one context
following an element into another.** Bold text coloured for a pale card keeps
that colour inside a saturated band, and the emphasis then recedes instead of
advancing — on, typically, the one sentence that most needs to carry across a
room. Emphasis inside an accent band should be `--butter` or white, never ink.

## Type floors, at final print size

| Element | Floor | Comfortable |
|---|---|---|
| Title | 90 pt | 92–110 pt |
| Authors | 40 pt | 40–44 pt |
| Section headers | 48 pt | 38–46 pt when a layout is genuinely narrow — say so |
| Body | 28 pt | 28–32 pt |
| Captions, axis labels | 22 pt | 24–26 pt |
| Hero / take-home | 60 pt | 40–48 pt in a band with much text — say so |
| In-figure text | 22 pt | author at 25–30 pt |

The floors are what a visitor can read standing back; treat a violation as a
build failure, not a style preference. Where a layout genuinely cannot hold the
comfortable size — four columns on a square sheet will not take a 48 pt heading
without wrapping, and a wrap costs more than the smaller type does — go below,
but say which floor you went under and why, rather than letting it pass silently.

Two traps the audit catches for you: `<sup>` at 0.7 em drops a 25 pt caption to
17.5 pt, and any element inheriting a smaller size than you intended shows up as
`minPt` well below the floor. When the audit flags type, read the reported
selector — it names the offender.

## Rhythm

```
--margin  1.05in     ≥ 1 in clear of the trim on every side
--gutter  0.52in     column gutter, also the gap between rows
--pad     0.52in     inside a text block (0.14in for a bleed figure block)
--clear   0.42in     ≥ 0.4 in clear around every figure
--radius  0.16in
```

Word count: **400–700 across the whole sheet.** Below 400 a reader who arrives
while you are talking to someone else cannot follow it; above 700 nobody
finishes.
