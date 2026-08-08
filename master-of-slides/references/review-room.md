# The review room

Decks converge through someone else's eyes, and feedback is only useful if it
survives being given: anchored to the page it is about, recorded where a later
session can find it without asking. The room does both. **The file is the
record; the server is just the door to it.**

## Serving

```bash
PY=$(<skill>/scripts/ensure_env.sh)
"$PY" <skill>/scripts/review.py <build-dir>                 # build review/, serve :7788
"$PY" <skill>/scripts/review.py <build-dir> --port 7799
"$PY" <skill>/scripts/review.py <build-dir> --build-only    # refresh review/, no server
"$PY" <skill>/scripts/review.py <build-dir> --from-pptx pptx/deck.pptx
```

Run the serving form **in the background** — it stays up until killed — and
give the user the URL. `render.py` must have run since the last edit: the room
shows `preview/*.png`, and it refuses to build when a page has no image,
because a stale render collects stale comments. Titles and notes are
re-extracted from the deck source with the same code `notes.py` uses, so the
note the reviewer reads is the note the presenter will rehearse.

What the user gets, one page at a time: the rendered slide, its speaker note,
and a comment thread pinned to that page; arrow keys to move; a thumbnail
strip with a dot on every page that still has an open comment; an overview of
everything open, click to jump. A build folder with several decks gets a deck
switcher, and comments carry the deck name.

The server is stdlib-only and stateless — every request re-reads the disk. So
`--build-only` refreshes what a running server shows without a restart, and
killing it at any moment loses nothing but the connection. It prints each
comment as it arrives, which makes its log a live feed while the user reviews.

## The record

`<build-dir>/review/comments.json`:

```json
{"comments": [
  {"id": "c1", "deck": "talk", "page": 4, "author": "user",
   "text": "Legend is sitting on the significance bracket",
   "time": "2026-08-07T14:03:22-04:00", "status": "addressed",
   "resolution": "legend moved below the axis"},
  {"id": "c2", "deck": "talk", "page": 4, "author": "agent", "re": "c1",
   "text": "Moved the legend under the axis; nothing else on the page shifted.",
   "time": "2026-08-07T14:19:40-04:00"}
]}
```

User comments carry `status`: `"open"` until the deck has actually changed —
or a reason not to change it has been given — then `"addressed"`, optionally
with a one-line `resolution`. Agent replies are ordinary comments with
`author: "agent"` and `re` naming what they answer. Read the file directly;
**write through the API**, so the open page updates on its next poll and two
writers cannot interleave:

```bash
curl -s -X POST http://127.0.0.1:7788/api/comments \
  -H 'Content-Type: application/json' \
  -d '{"deck":"talk","page":4,"author":"agent","re":"c1",
       "text":"Moved the legend under the axis."}'

curl -s -X POST http://127.0.0.1:7788/api/comments/resolve \
  -H 'Content-Type: application/json' \
  -d '{"id":"c1","resolution":"legend moved below the axis"}'
```

## The loop

1. **Wait.** Watch the server log or the file; do not start resolving while
   the user is still typing their way through the deck. When they say they are
   done in chat, or in the thread, the round begins.
2. **Read every open comment before editing anything.** Comments interact:
   two about one figure are one edit; "make it bigger" and "add the CI" on the
   same page collide. Plan the round, then touch the deck.
3. **A comment on a slide is a comment on its note.** If the slide changes,
   its speaker note almost always has to move with it — re-read it every time.
4. **Revise in a new build folder** — the non-negotiable applies to review
   rounds — and copy `review/comments.json` forward, so the reviewed version
   keeps its record and the new version continues the thread.
5. **Re-measure what you touched** (render, audit, notes), then
   `review.py <new-build-dir> --build-only`, kill the old server, and serve
   the new folder **on the same port**. The user's open page reconnects on its
   next poll: same URL, new round.
6. **Reply and resolve each comment, after the fix is rendered** — never
   before, because resolving is the claim that the change exists. Name what
   changed and where, especially when it moved: "now p.9 in this round."
7. **Disagreement gets a reply too.** The reason goes in the thread, where the
   disagreement happened, and then the comment is resolved with it — leaving
   feedback to age out unanswered is not a revision strategy.
8. **Close the round in chat**: what was addressed, what was left alone and
   why, and the new title track if it changed.

## When pages shift

Comments pin to the page numbers of the build they were written against. A
revision that splits, cuts, or reorders slides renumbers everything after the
change, so a carried-forward thread can point at pages that moved. Never edit
the user's comment text to compensate — it is the record — put the new
location in the reply and resolve. The room clamps out-of-range page numbers
instead of dropping them.

## A .pptx deck

`--from-pptx pptx/deck.pptx` reads titles from the title placeholders and
notes from the notes slides, and rasterizes previews from a PDF it can find
(one made by `pptxcheck.py --pdf`, or in the build's `pdf/`) or converts
through LibreOffice itself. Without LibreOffice and without a PDF there are no
page images and no room — say so plainly rather than reviewing blind. On the
hybrid path, review the HTML twin: it is the canonical one, and its room needs
no conversion.

## Trouble

- **`cannot bind 127.0.0.1:7788`** — an earlier round's server still owns the
  port. Kill it if it serves a stale folder; use `--port` only if two rooms
  genuinely need to run at once.
- **Refuses to build, "no preview PNG"** — `render.py` has not run since the
  last edit.
- **The page says "Server unreachable"** — the server died or is mid-restart
  onto a new folder; the page reconnects by itself once something is listening
  again.
