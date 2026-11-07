# Content rules — labelling, numbering, and what may appear on a sheet

A poster is not a paper on a wall. The reader has no bibliography, cannot look
anything up, and will spend perhaps ninety seconds. Everything below follows
from that.

## Figure numbering follows the poster, not the source

**Number the figures in the order they appear on the poster, starting at 1.**

The temptation is to carry the manuscript's numbers across so the two stay in
correspondence. Resist it. A reader at the board is not holding the paper, so a
caption reading "Fig. 1A,B" followed by "Fig. 4" tells them only that they are
missing something. Worse, a poster usually *reorders* the results — leading with
the payoff, or with the disagreement — and the source numbering then runs
backwards down the sheet.

Keep the correspondence in the build folder's `content.md`, where it serves the
author, not on the sheet, where it serves nobody.

The same applies to any source-side pointer: "Table S1", "see Supplementary
Fig. 3", "as in Methods §2.4". If the thing is not on the sheet, either state
the claim without the pointer or drop the claim.

## Section numbers and figure numbers will not always agree

If some sections hold no figure (a method panel, a take-home), the two sequences
drift apart. Two defensible options:

- **Number every section, number figures sequentially.** Section 4 carries
  Fig. 3. This is ordinary journal convention and reads fine.
- **Leave figure-less sections unnumbered.** Then section *n* always carries
  Fig. *n*, which is a small, real gain in scannability.

Pick one, say which in the build notes, and never produce a sheet with a gap in
the figure sequence (Fig. 1, 2, 4, 5…) — that reads as a missing figure.

## Every label must name the quantity it actually is

This is the failure that survives review longest, because the labels look fine
in isolation. Check each one against the source:

| Written | Actually | Why it matters |
|---|---|---|
| "Plots measured — 1,240" | the count *after* a quality filter; 7,400 were measured | misstates the denominator by 6× |
| "Farms surveyed — 312" | *fields*, per the source's own sentence | wrong unit |
| "41% of measured plots" | 41% of *filtered* plots | same slip, in a headline number |

(Illustrative numbers.)

The test: for each label, find the sentence in the source that reports that
number and check the noun. If the source does not report it, see the traceability
section below.

## Every count and claim needs a consumer

Sweep the sheet and ask, of each number in an inventory or method panel:
**what on this sheet uses it?** A count that backs no panel and appears in no
caption is decoration, and it invites the question "what is that for?" at
exactly the wrong moment.

The same sweep in reverse: every claim in a caption should be supported by a
panel on the sheet, or be a number the reader can check. When panels are cut
from a figure, the claims and counts they supported must go with them — and so
must any reference cited only for them. An orphaned reference is a small thing
that a careful visitor will notice.

## Traceability

**Every number on the sheet traces to the source or to a cached re-run.** Do not
invent, do not round misleadingly, and do not use placeholder text. If something
is missing, leave a visible `[[TODO: ...]]` marker rather than fabricating —
a marker gets fixed, a plausible invention gets printed.

Cache whatever you recompute (a `plotdata.json` beside the figure code) so the
poster and its numbers can be regenerated and checked later. When a re-run
disagrees with the source, quote the source on the sheet and record the
discrepancy in the build notes; do not silently prefer either.

Some numbers legitimately come from the analysis rather than the write-up — a
sample size the paper never printed, say. That is fine, but note it, because
"traces to the manuscript" and "traces to the cached run" are different claims.

## Report significance by symbol, explain the symbols once

Quoting individual p-values in captions goes wrong in a specific, recurring way:
a two-panel figure has *two* p-values, the caption quotes one, and now the
caption is wrong about half the figure.

Use the standard ladder in the panels — `*` < 0.05, `**` < 0.01, `***` < 0.001,
`****` < 0.0001, `NS` otherwise — and end each caption with the key for the
symbols **that appear in that figure**. Not the full ladder every time; just what
is drawn. Then the caption cannot mis-state a panel it does not mention.

Two things to watch:
- The key must attach to the right quantity. If a caption names a statistic the
  panel never draws, a reader will bind the nearby `NS` to it. Name what is
  drawn.
- Keep an inequality from breaking across lines (`&nbsp;` around `<`), and avoid
  `<sup>` in captions — at 0.7 em it drops below the type floor. Write `0.0001`,
  not `10<sup>-4</sup>`.

## Hedges are part of the number

If the source says "slightly but significantly higher", the poster should too.
Dropping the hedge makes a +0.5% effect read like the +4.2% one next to
it. Carry the source's own qualifiers, especially when two panels with
very different effect sizes sit side by side.

## Audience

Write for the audience in the room, not the one that wrote the paper. If the
poster is going to a venue outside its home field, every domain term needs to be
defined on the sheet or avoided, and the "so what" needs to be in the language
of the people reading it. A concept primer as section 1 costs a cell and buys
every subsequent section a reader who can follow it.
