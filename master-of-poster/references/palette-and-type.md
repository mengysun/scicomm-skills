# Palette and type

## The colour rule that matters

**Only two colours ever encode data, and every use is paired with a word.**

Everything else — section chrome, bands, rules, grounds — is neutral plus one
warm accent. This is not minimalism for its own sake: a categorical set of four
or five pastel accents fails colour-vision separation (plum against blue reads
at ΔE ≈ 10 to a normal observer, sage against terracotta at ΔE ≈ 3 under
protanopia), while a single warm/cool pair passes — but only if the word is
there too, so the reader never has to resolve the colour to read the result.

Word-labelling also means the sheet still works photocopied, photographed under
bad light, or seen from an angle. Direct-label the series next to the data
rather than relying on a legend box wherever the panel allows it.

## The default palette

Defined once as CSS variables in `assets/poster.css`, and mirrored in
`assets/posterfig.py` so figures and page agree.

| Role | Hex | Use |
|---|---|---|
| `--pos` | `#D56C55` | data encoding — class A, always beside its word |
| `--neg` | `#738FC1` | data encoding — class B, always beside its word |
| `--accent` | `#905426` | section chrome, before/after states, single-series points |
| `--ink` | `#2E2A26` | body text |
| `--ink-soft` | `#574F47` | captions |
| `--muted` | `#8A8078` | secondary notes |
| `--hair` | `#C9C0B6` | rules, block borders |
| `--paper` | `#FFFFFF` | cards |
| `--paper-warm` | `#FFEDCE` | sheet ground |
| `--paper-tint` | `#FAF4E9` | panel ground |
| `--band` | `#E3DCD0` | footer strip |
| `--butter` | `#FFEDC0` | emphasis *on* the accent band |

Inert tints available for grounds and fills, never for encoding: `#BFD598`
`#7AA974` `#DCECCB` `#EAC264` `#F3DAA9` `#A9BFE3` `#C9D7EE` `#E8B19D` `#F1D4C9`
`#AB85AC` `#D4C2D9` `#7E9D90`.

### Swapping in another palette

Change `--pos`, `--neg`, `--accent` in `poster.css` and `POS`, `NEG`, `ACCENT`
in `posterfig.py`. Keep the rule, not the hexes: two encoding colours, one
accent, everything else neutral. If the user supplies a palette sheet, extract
the hexes and assign roles by warmth and saturation — the two most separated
mid-saturation hues become the encoding pair.

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
