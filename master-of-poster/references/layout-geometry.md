# Layout geometry — where figure area actually comes from

Read this before tuning a layout. Almost every instinct about "making the
figures bigger" is wrong, and the arithmetic below explains why.

## The one equation

A poster body is a stack of rows. For each row:

```
figure area in the row  =  (sum of cell widths)  ×  (row height − row overhead)
```

Two consequences that are not obvious:

**The number of columns barely matters.** Splitting a row into three cells
instead of two changes the summed width only by one extra gutter (~0.5 in out of
34). A three-column row holds essentially as much figure area as a two-column
row of the same height. So do not merge cells hoping to gain area — you gain a
gutter.

**Rows are expensive.** Every row pays its overhead once: block padding, the
section header, the caption, the gaps between them. That is typically
**2.2–2.6 in per row**, gone before a single pixel of figure. Four rows instead
of three costs ~2.4 in of figure height across the whole sheet.

So: **fewer, taller rows beat more, shorter rows** — until the cells get so
narrow that panels stop working. That trade is the whole game.

## Aspect matching — the single biggest lever

A figure scaled with `object-fit: contain` letterboxes: whichever dimension
binds first caps its area, and the rest of the box is white space that looks
deliberate and is not.

```
cell box aspect   = box height / box width
plate aspect      = natural height / natural width
```

When these differ, you lose the difference. `probe.py` reports it as `waste%`.

**The loop that fixes it:**

1. Build the HTML with any placeholder plate.
2. `probe.py <build-dir>` — read the `fig box` and `boxAsp` columns. That is the
   box the layout actually offers, in inches.
3. Re-author each plate at that aspect (matplotlib `figsize`).
4. Re-render, re-probe. `waste%` should be ≤ 2.

Do not skip to step 3 from a mental model of the layout. Caption line counts and
header wrapping move the box by half an inch, and half an inch is 4% of area.

**`bbox_inches="tight"` does not preserve your figsize aspect** — it crops to the
ink, and rotated tick labels or a long y-label shift it. Expect one correction
pass: author, measure the emitted plate's aspect, scale the figsize by
`target / achieved`, re-emit. Two passes converge to ≤ 1%.

## What a wrapped heading costs

A section header that wraps to two lines costs ~0.6 in **from every cell in that
row**, because grid rows are as tall as their tallest cell. A three-line caption
does the same. On a three-row poster that single wrap can cost 2–3 points of
figure fraction.

This is why headings should be short enough to set on one line at the chosen
size, and why it is worth measuring rather than assuming:

```
characters that fit ≈ (cell width − padding − badge) / (0.5 × font size in inches)
```

At 44 pt (0.61 in em) in a 10.95 in cell with a number badge, that is about 30
characters. Count them.

## Keep caption line counts equal within a row

Cells in a grid row stretch to the row height, so a cell with a two-line caption
gets a taller image box than its three-line neighbour. Either equalise the
captions, or author that one plate to its own measured aspect. Both are fine;
silently letterboxing is not.

## Width-limited plates and `natural` blocks

A wide-and-short plate (a schematic, a distribution) in a tall cell is
width-limited: it cannot use the extra height, and the space below it is dead.
Two fixes:

- give it a **wider cell** — span two columns — so its width-limited height is
  larger; area grows as width², so this is very effective;
- mark the block `natural` (`flex: 0 0 auto`, image at `height: auto`) so the
  row takes only the height the plate needs and the other rows get the rest.

Deciding between "give row 1 more height" and "give it to the evidence rows" is
a one-line calculation: compare (sum of widths in row 1) against (sum of widths
in the rows that would gain). Height flows to the larger number.

## Sizing the sheet

| Trim | Body height after front matter and closing | Realistic rows |
|---|---|---|
| 36 × 54 in | ~43 in | 3 rows comfortably |
| 33.1 × 46.8 in (A0) | ~36 in | 3 rows, tighter |
| 36 × 36 in | ~22–25 in | **2 rows**, three only if starved |

A square sheet with the same content as a 1:1.5 sheet will carry visibly smaller
figures. That is arithmetic, not a design failure — say so rather than fighting
it.

## Where the body starts and ends

`audit.py` measures the figure fraction against the span between the header
element and the footer element. That means **what you put inside `<header>` or
`<footer>` is excluded from the denominator**. A method strip in the masthead
and the same strip as a numbered body section give very different numbers for
the same sheet.

Neither placement is dishonest — front matter really is front matter — but the
number moves by 10+ points, so state which one you used. When a text panel has
to live in the body, expect 50% rather than 60% and explain why instead of
quietly reporting the flattering figure.

## Target band

**55–70% figures, 15–20% white space.** Below 55 the sheet reads as a paper on a
wall; above 70 there is usually not enough text to carry a reader who arrives
without you standing there.
