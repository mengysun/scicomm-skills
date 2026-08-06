# Palette and type

## The palette

One set of colours, used for the deck's chrome and for any figure you generate,
so that everything you make looks like it belongs together. **Which swatch means
what is yours to decide** — that is a property of your data, not of the palette.

It governs what you author. A figure you were supplied rather than made keeps its
own colours, and a logo is placed exactly as given — see
`figures-and-numbers.md`. When the supplied figures are colourful, keep your
chrome neutral so the two systems do not fight.

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

`slides.css` names all of these and then assigns a few **roles** from them —
`--pos`, `--neg`, `--accent`, `--paper-warm`, `--band`. Those are a starting
assignment for the common case of a two-group comparison, not a restriction:
rename them, reassign them, add more when your data has more classes.
`slidefig.py` mirrors the same names, and `CYCLE` is a default ordering for
categorical series, installed as matplotlib's colour cycle by `setup()` so
unstyled plots already match.

### Choosing within it

- **Saturated members separate; pale ones do not.** terra, blue-deep,
  green-deep, gold, plum, sage and umber hold apart at small sizes and, more to
  the point here, through a projector with its own colour cast. The pale tints
  are for fills, bands and grounds.
- **Beyond about five categories**, colour stops doing the work. On a slide the
  limit is lower than in print, because the audience gets one look — think three
  or four, then small multiples or direct labels.
- **A word beside the colour is usually free**, and it buys a figure that
  survives a bad projector, a photograph taken from the third row, and
  colour-vision deficiency. Direct-label the series next to the data rather than
  sending the eye to a legend and back. A habit worth having, not a law.
- **Keep a colour's meaning fixed across the whole deck.** If terra means one
  thing on slide 8 it cannot mean another on slide 12 — the audience has been
  learning it for ten minutes and you get no chance to correct them.

### Swapping in another palette

Replace the named swatches at the top of `slides.css` and the same names in
`slidefig.py`; the roles and `CYCLE` follow. If the user has an institutional
template, take its colours and keep the same shape: a handful of saturated
members for encoding, the tints for grounds.

## Type, as a fraction of slide height

Points are a poor guide across canvas sizes; the fraction of slide height is what
predicts whether the back row can read it. On a 7.5 in slide:

| Element | Fraction | Points | Note |
|---|---|---|---|
| Deck title | 7% | 54 pt | |
| Slide title (the claim) | 4.5% | 34 pt | one line if you can; two is fine, three means rewrite |
| Body | 3.2% | 24 pt | |
| Caption, axis label | 2.4% | 18 pt | |
| Absolute floor | **2.8%** | **16 pt** | one line at this size, never a paragraph |

`audit.py` reports both the point size and the fraction, and flags anything under
the floor. The floor is not a preference: below it the people at the back stop
reading and start waiting for you to say it, which is the failure a slide exists
to avoid.

The rule of thumb behind the number: about one inch of projected letter height
per ten feet of viewing distance. A 24 pt line on a 13.3 in slide thrown onto a
10 ft screen is roughly 3 in tall, which carries about 30 ft.

Two traps `audit.py` catches for you: `<sup>` renders at 0.7 em and quietly drops
an 18 pt caption to 12.6 pt — write `0.0001`, not `10<sup>-4</sup>` — and any
element inheriting a smaller size than intended shows up as a `minPt` well under
the floor, with the offending selector named.

## Contrast

`audit.py` reports the lowest text contrast on each slide and flags anything
under 3:1. Watch one pattern in particular: **a rule written for one context
following an element into another.** Bold text coloured for a pale card keeps
that colour inside a saturated band, and the emphasis then recedes instead of
advancing — typically on the one line that most needs to carry across a room.
Emphasis inside an accent band should be `--butter` or white, never ink.

Projectors are worse than screens: they lift blacks, wash out mid-tones, and
vary wildly by room. Treat 3:1 as the floor rather than the target, and prefer
more separation than the number strictly requires.
