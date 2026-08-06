# Slide craft — geometry, type, density

## Canvas

| Ratio | Size | Use |
|---|---|---|
| 16:9 | 13.333 × 7.5 in | the default; every modern projector and Zoom |
| 4:3 | 10 × 7.5 in | older rooms, some seminar series that ask for it |

Set it in both places or the measurement will lie:

```css
@page { size: 13.333in 7.5in; margin: 0; }
:root { --slide-w: 13.333in; --slide-h: 7.5in; }
```

Keep 0.6 in of margin. The bottom ~1 in of a projected slide is the first thing
lost to a head, a lectern, or a screen hung too low — do not put anything you
need read down there, and never a caption.

## Type

Floors, sizes and the reasoning are in `palette-and-type.md`. The number to carry
in your head: **the absolute floor is 2.8% of slide height** (16 pt on a 7.5 in
slide), and 3.2% (24 pt) is a comfortable body size. `audit.py` reports both the
points and the fraction.

## Density

**25–40 words on a content slide; 55 is the ceiling** `audit.py` flags. A slide
with 90 words is a document, and the room will read it instead of listening to
you.

Ways to get there that do not lose content:
- Move the sentence into the speaker notes. Most of the time this is the answer.
- Replace a sentence with the number it contains, set large.
- Let the figure make the point and put only the claim in the title.
- Cut the qualifier from the slide and say it out loud — but only if it is a
  qualifier; if it changes the claim it stays.

Bullets are usually a symptom of a slide that has not decided what it is saying.
When one is genuinely right — a short parallel set — keep it to 3–5 items of one
line each, and give them a claim title anyway.

## Layout patterns

Five shapes cover most decks. They are in `assets/slides.css`.

**Claim + figure** (`.slide` with `.stitle` then `figure.fig`) — the workhorse.
The title asserts, the figure shows, a caption of one line carries the sample or
the star key. The figure claims all the leftover height, so it scales to whatever
the title leaves.

**Two-up** (`.cols.cols-2`) — a comparison, or a figure with its interpretation
beside it. Resist three columns on 16:9: each becomes about 3.9 in wide, which is
below what most plates survive.

**Full bleed** (`.slide.bleed`) — one image with the title floated over it. Use
when the image *is* the point.

**Statement** — a claim in `--fs-hero` with nothing else, or one big number
(`.stat`). Good for the turn and for the closing slide. A slide with six words on
it is not wasted space; it is the pause that makes the next slide land.

**Divider** (`.slide.section`) — accent ground, section name, nothing else.

## Figure area

There is no 55% target here as there is on a poster. A slide is usually *one*
figure with a claim over it, and the right measure is whether the figure owns the
slide: on a claim+figure slide expect 45–65%. Much below that and the slide is
probably text pretending to be a figure slide; near 90% with no title means the
audience has to work out what they are looking at.

`audit.py` reports the fraction per slide so you can see the shape of the deck —
a run of five text-heavy slides in the middle shows up as a dip.

## Consistency is a feature

The same claim in the same place on every slide, the same colour meaning the same
thing throughout, the same plate style. Every inconsistency is a small tax on
attention, paid at exactly the moment you want the audience thinking about the
result.

Two specific ones worth policing, because they are invisible while you build and
obvious in the room:

- **Colour meaning must not drift.** If warm means "positive" on slide 8, it
  cannot mean "treatment" on slide 12.
- **Emphasis on a saturated band must advance, not recede.** Ink-dark bold on the
  accent measures about 2.4:1 and disappears at the back; the stylesheet sets
  `.takeaway b` to butter for this reason. See `palette-and-type.md`.

## Backup slides

Put them after the closing slide, titled as answers ("Yes, it survives dropping
the 2001 cohort") rather than as topics. You will find them under pressure by
their claim, not their number.
