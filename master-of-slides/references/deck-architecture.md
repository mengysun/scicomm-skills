# Deck architecture — the part that is not layout

A deck fails in the outline far more often than in the typography. This file is
about the outline.

## The title is the claim

Give every content slide a title that **asserts what the slide shows**, not one
that names its topic:

| Topic title | Claim title |
|---|---|
| Results | Treated plots yield more |
| Methods | Every plot was scored blind to its treatment |
| Discussion | The gain is real, but small next to the weather |
| Follow-on analysis | The gain carries into the second season |

Two reasons this matters more than it looks. The audience reads the title before
you finish the sentence you are on, so a claim title lets them spend the rest of
the slide checking it rather than waiting to find out why they are looking at a
figure. And a deck whose titles assert things can be read as an argument — which
is exactly the check `audit.py --titles` prints.

**Read the title track aloud before building anything else.** If it does not tell
the story on its own, no amount of layout will rescue the deck; go back to the
outline. If two adjacent titles make the same claim, you have one slide.

## One idea per slide

If a slide needs "and" in its title, it is two slides. This is nearly free —
slides cost nothing to add, unlike poster area — and it is the main lever you
have on pace. A talk that lands is usually more slides with less on each, not
fewer slides that are dense.

The corollary: a slide that takes more than ~60 seconds to talk through is
usually hiding a build (see below) or a second idea.

## What goes on the slide, and what goes in your mouth

**This is the structural inversion from a poster.** A poster must stand alone —
everything the reader needs is on the sheet. A slide has you standing next to it,
so anything the audience must *hear* but should not have to *read* belongs in the
speaker notes:

| On the slide | In the notes |
|---|---|
| The claim, as the title | How you'll say it |
| The figure | What to point at first |
| The one or two numbers that carry the claim | The other numbers, the exact test, the *n* |
| A word label on each encoded colour | Caveats and the honest limitations |
| The unit and the sample, if not obvious | The answer to the question you expect |

Slides are read faster than you can talk, so text on a slide competes with you.
Every word you can move into a note is attention you get back.

Notes live in `<div class="notes">` inside the slide, hidden in print, and
`scripts/notes.py` pulls them into a script you can rehearse from. A slide with
no note is worth a second look: usually its text is doing the presenter's job.

### The script pass

The note written while building a slide is a stage direction — "point at the
gap first" — enough to check the division of labour, not enough to deliver.
So after the deck measures clean, walk the pages **in final order** and write
the script: the words to actually say over each page — the transition in from
the previous slide, the claim in speakable sentences, `[CLICK]` cues where the
builds advance, what to point at and when, the numbers that stayed off the
slide (the exact test, the *n*, the effect size) as backup lines, and — on the
slides that predictably raise a question — the answer. Write it in the
speaker's register, speech rather than prose — `references/script-voice.md`
is the rulebook, and it is short. One minute of speaking is roughly 130 words;
aim the deck total at 70–80% of the slot, and a page far past a minute usually
means the slide is carrying two ideas. If the user drafted any of it, their
text is authoritative — polish grammar only.

The pass is also the last structural check, which is why it is worth doing as
its own step rather than while laying out: a transition you cannot write is a
mis-ordered deck; a script entry that repeats the previous one is a slide that
should not exist; an empty one belongs to a slide whose text is doing the
presenter's job. Fix those *before* anyone reviews, and the review is about
the argument instead.

## The arc

Most research talks are a variant of this. Adapt the names, keep the shape:

1. **Title** — title, authors, venue. Say the one-sentence version out loud here.
2. **The hook** — why anyone should care, in the audience's own terms. If you are
   speaking outside your field, this is where the field-specific vocabulary gets
   defined or avoided.
3. **The question**, stated so that both possible answers are interesting.
4. **What we did** — enough that the results are interpretable, no more. Method
   detail is the most common place a talk loses the room; put the rest in the
   notes and the backup slides.
5. **Results**, one claim per slide, in the order that builds the argument — which
   is often *not* the order the paper uses.
6. **The turn** — the objection you expect, met head on. Doing this before the
   questions is worth more than any extra result.
7. **So what** — one slide, one sentence, the thing you want repeated at lunch.
8. **Backup slides** after the closing slide, for the questions you can predict.

Section dividers earn their place when the deck is longer than ~15 slides: they
give the audience a place to re-enter if they have drifted.

## Builds

Progressive disclosure works — revealing a comparison after the audience has read
the baseline is genuinely easier to follow. In a PDF deck, a build is the same
slide repeated with more revealed, using `.dim` on what is not yet live.

Duplicate the whole slide rather than moving elements between steps, so the
geometry is identical and nothing shifts under the audience's eye. Two or three
steps is usually the useful limit; past that you are animating, not explaining.

Builds inflate the page count, so state the real slide count ("18 slides, 24
pages with builds") when the venue asks.

## Timing

About **one minute per content slide** for a conference talk, less for a title or
divider. A 12-minute slot is therefore roughly 10–12 content slides plus front
and back matter — and the way to fit is to cut ideas, not to compress slides.

Rehearse from the extracted script rather than the slides. If a page's entry
is longer than what you can say in a minute, the slide is carrying too much.

## Deck-level review, before you look at any single slide

- Read the **title track**. Is it the argument?
- Count the slides against the slot.
- Find the slide you would cut if you lost two minutes. Then decide whether to
  cut it now.
- Check that every term you use is defined the first time it appears — and check
  that against the *audience*, not the paper.
- Check that the last slide is the sentence you want repeated. It is the one the
  room will be looking at during the questions.
