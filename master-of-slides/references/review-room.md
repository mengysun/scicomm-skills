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
give the user the URL it prints, **token included**
(`http://127.0.0.1:7788/?token=...`). The room only answers requests that carry
its access key: binding to 127.0.0.1 keeps it off the network but not away
from other web pages open in the same browser, or from other users on a shared
machine, and a comment here carries the user's authority. The key is one per
user, kept in `~/.local/share/scicomm-skills/review-token`, so the link stays
valid across restarts and new build folders. Never paste it anywhere public.

`render.py` must have run since the last edit: the room
shows `preview/*.png`, and it refuses to build when a page has no image,
because a stale render collects stale comments. Titles and scripts are
re-extracted from the deck source with the same code `notes.py` uses, so the
script the reviewer reads is the script the presenter will say.

What the user gets, one page at a time: the rendered slide, its script — with
word count, a time estimate at 130 wpm per page and for the whole deck, and an
**Edit** button — and a comment thread pinned to that page, each comment
optionally aimed at the slide or at the script; arrow keys to move; a
thumbnail strip with a dot on every page that still has an open comment; an
overview of everything open, click to jump. A build folder with several decks
gets a deck switcher, and comments carry the deck name.

The server is stdlib-only and stateless — every request re-reads the disk. So
`--build-only` refreshes what a running server shows without a restart, and
killing it at any moment loses nothing but the connection. It prints each
comment as it arrives, which makes its log a live feed while the user reviews.

## The record

Two files, same standing: `comments.json` is what the user *asked for*;
`scripts.json` is what the user *wrote*. Read both before starting a round.

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

A comment may carry `about: "slide"` or `about: "script"` when the user aimed
it; absent means the whole page. User comments carry `status`: `"open"` until
the deck has actually changed — or a reason not to change it has been given —
then `"addressed"`, optionally with a one-line `resolution`. Agent replies are
ordinary comments with `author: "agent"` and `re` naming what they answer.

`<build-dir>/review/scripts.json` — one entry per edited page, newest text
only (the deck source keeps the original):

```json
{"edits": [
  {"deck": "talk", "page": 4,
   "text": "So what does this buy us? [CLICK — cost panel] About a tenth of…",
   "time": "2026-08-10T21:40:12-04:00", "status": "pending"}
]}
```

`"pending"` means the words on disk in the deck source are older than what the
user wants said. **The edit is authoritative text, not a suggestion** — the
user rewriting their own talk in their own voice. Fold it into the deck source
verbatim (fix outright typos, nothing else — see
`references/script-voice.md` § "Polishing a draft"), and only after the fold
is rendered, mark it `"merged"`. Read the files directly; **write through the
API**, so the open page updates on its next poll and two writers cannot
interleave. Every call sends the access key and a JSON content type:

```bash
KEY=$(cat ~/.local/share/scicomm-skills/review-token)

curl -s -X POST http://127.0.0.1:7788/api/comments \
  -H 'Content-Type: application/json' -H "X-Review-Token: $KEY" \
  -d '{"deck":"talk","page":4,"author":"agent","re":"c1",
       "text":"Moved the legend under the axis."}'

curl -s -X POST http://127.0.0.1:7788/api/comments/resolve \
  -H 'Content-Type: application/json' -H "X-Review-Token: $KEY" \
  -d '{"id":"c1","resolution":"legend moved below the axis"}'

curl -s -X POST http://127.0.0.1:7788/api/script/merged \
  -H 'Content-Type: application/json' -H "X-Review-Token: $KEY" \
  -d '{"deck":"talk","page":4}'
```

The room's own saves go through `POST /api/script` with a `baseTime` guard: a
page that loaded an older entry gets a 409 instead of silently clobbering a
newer one — the same rule protects you, so never edit `scripts.json` by hand
while the server is up.

## The loop

1. **Wait.** Watch the server log or the file; do not start resolving while
   the user is still typing their way through the deck. When they say they are
   done in chat, or in the thread, the round begins.
2. **Read every open comment and every pending script edit before editing
   anything.** They interact: two comments about one figure are one edit; a
   comment asking to cut a slide collides with a script edit on it. Plan the
   round, then touch the deck.
3. **A comment on a slide is a comment on its script.** If the slide changes,
   the words over it almost always move too — re-read them every time. And a
   pending script edit is folded **verbatim** into the deck source; grammar
   fixes only, never a rewrite toward your own phrasing.
4. **Revise in a new build folder** — the non-negotiable applies to review
   rounds — and copy `review/comments.json` **and `review/scripts.json`**
   forward, so the reviewed version keeps its record and the new version
   continues the thread.
5. **Re-measure what you touched** (render, audit, notes), then
   `review.py <new-build-dir> --build-only`, kill the old server, and serve
   the new folder **on the same port**. The user's open page reconnects on its
   next poll: same URL, new round.
6. **Reply and resolve each comment, after the fix is rendered** — never
   before, because resolving is the claim that the change exists. Name what
   changed and where, especially when it moved: "now p.9 in this round."
   Script edits follow the same rule: `POST /api/script/merged` only after the
   rebuilt room is serving the folded text, so "merged" is never a promise.
7. **Disagreement gets a reply too.** The reason goes in the thread, where the
   disagreement happened, and then the comment is resolved with it — leaving
   feedback to age out unanswered is not a revision strategy.
8. **Close the round in chat**: what was addressed, what was left alone and
   why, and the new title track if it changed.

## When pages shift

Comments and script edits pin to the page numbers of the build they were
written against. A revision that splits, cuts, or reorders slides renumbers
everything after the change, so a carried-forward thread can point at pages
that moved — fold pending script edits into the pages they *meant*, and say
where the text landed. Never edit
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
- **The page says "No access key", or a call returns 403** — the browser was
  opened without the token link (or the key file was deleted and remade):
  reopen the URL the server printed. From a script, check the
  `X-Review-Token` header.
- **"refused a write from another site" in the log** — something other than
  the room's own page tried to post to it, and was turned away. Nothing was
  recorded; mention it to the user.
- **A call returns 415** — the request was not sent as
  `Content-Type: application/json`.
