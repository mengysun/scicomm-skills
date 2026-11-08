"""Build and serve the review room: each page's slide beside its script,
with the script editable in place and a comment thread anchored to that page.

    python review.py <build-dir>                      # build review/, serve on 127.0.0.1:7788
    python review.py <build-dir> --port 7799
    python review.py <build-dir> --build-only         # (re)write review/, no server
    python review.py <build-dir> --from-pptx pptx/deck.pptx   # a .pptx-only build

Run `render.py` first: the room shows `preview/*.png`, and the script shown
next to each page is re-extracted from the deck source (the `.notes` div, or
the notes slide of a .pptx), so what the reviewer reads is what the presenter
will actually say.

Comments land in **`<build-dir>/review/comments.json`**; script edits land in
**`<build-dir>/review/scripts.json`** — plain JSON files, one entry per
comment or per edited page, each pinned to a deck and a page. The files are
the record; the server is just the door to them. Reading the feedback later is
a file read, and the server prints each comment and edit to stdout as it
arrives, so a process watching the log sees feedback live.

The server is stdlib-only and stateless: every request re-reads the manifest
and the comments from disk. So `--build-only` can refresh the manifest under a
running server after a re-render, and replies posted through the API appear on
the next poll without a restart. Writes go tmp-then-rename behind a lock, so a
comment arriving mid-write cannot truncate the file.

Access. The server binds 127.0.0.1 only, and that alone is not enough: any
web page open in the reviewer's browser can send requests to localhost, and on
a shared machine (a cluster login node) every other user can reach the port.
Comments here carry the user's authority, so every request must present the
room's access key. The key is made once per user and kept in
`~/.local/share/scicomm-skills/review-token` (mode 600), so restarting the
server onto a new build folder does not lock out a page that is already open.

  * the browser gets it from the link the server prints
    (`http://127.0.0.1:7788/?token=...`), which sets a cookie and redirects
    to the room — share that link only with someone on this machine;
  * scripts send it as a header:
    `-H "X-Review-Token: $(cat ~/.local/share/scicomm-skills/review-token)"`.

Requests whose Host or Origin is not this server are refused, a POST must be
`Content-Type: application/json`, and only `review/` and `preview/` are
served — not the rest of the build folder.

API (JSON over HTTP; every call needs the access key):

    GET  /api/state                             # {manifest, comments, scripts}
    POST /api/comments            {deck?, page, text, author?, re?, about?}
    POST /api/comments/resolve    {id, resolution?, status?}
    POST /api/script              {deck?, page, text, baseTime?}
    POST /api/script/merged       {deck?, page}

`author` is "user" (default) or "agent"; `re` threads a reply under an earlier
comment's id; `about` optionally aims a comment at "slide" or "script". User
comments start with `status: "open"`; resolve flips one to "addressed" once
the deck actually changed — not before.

A script edit upserts one entry per (deck, page) with `status: "pending"`; the
user's text is authoritative and waits to be folded verbatim into the deck
source, after which the agent posts /api/script/merged. `baseTime` is the
`time` of the entry the client loaded (null for none): if the entry on disk is
newer, the save is refused with 409 instead of silently clobbering it — a
stale page must never overwrite newer work. An empty `text` discards the
pending edit.
"""
import argparse
import hmac
import json
import os
import posixpath
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote

DEFAULT_PORT = 7788
LOCK = threading.Lock()
TOKEN_FILE = Path.home() / ".local" / "share" / "scicomm-skills" / "review-token"
COOKIE = "review_token"
SERVED = ("/review", "/preview")      # the only folders the room needs
LOCKED = ("This review room needs its access key. Open the link review.py "
          "printed (http://127.0.0.1:<port>/?token=...).")

# Same extraction the notes script uses (noteText and norm are copied from
# notes.py; keep them identical), so the room and the rehearsal script cannot
# disagree about what a slide's note says.
JS = r"""
() => {
  // `.notes` is display:none, so innerText degrades to textContent: it keeps
  // the source's own line breaks and indentation but puts nothing between
  // elements, and <p>A.</p><p>B.</p> would read "A.B.". So mark the markup's
  // breaks in a clone first, with characters source text never holds: PARA
  // around block elements, LINE for <br> and before each list item or row.
  // A paragraph then ends at a blank line in the source, a PARA, or two LINEs
  // in a row (<br><br>); a single LINE stays a line break; any other run of
  // whitespace collapses to one space.
  const PARA = '\uE000', LINE = '\uE001';
  const noteText = el => {
    const c = el.cloneNode(true);
    c.querySelectorAll('br').forEach(x => x.replaceWith(LINE));
    c.querySelectorAll('li, tr').forEach(x => x.before(LINE));
    c.querySelectorAll('p, div, section, blockquote, pre, h1, h2, h3, h4, h5, h6, ul, ol, table')
        .forEach(x => { x.before(PARA); x.after(PARA); });
    return c.textContent;
  };
  const norm = t => t.split(/\n\s*\n|\uE000|\uE001\s*\uE001/)
      .map(p => p.split(LINE).map(l => l.replace(/\s+/g, ' ').trim())
                 .filter(Boolean).join('\n'))
      .filter(Boolean).join('\n\n');
  return [...document.querySelectorAll('.slide')].map((s, i) => {
    const t = s.querySelector('h1, h2, .stitle');
    const n = s.querySelector('.notes');
    return {n: i + 1,
            title: t ? (t.innerText || t.textContent).trim().replace(/\s+/g, ' ') : '',
            script: n ? norm(noteText(n)) : ''};
  });
}
"""


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path, obj):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def load_token():
    """The room's access key: one per user, kept between servers.

    Kept rather than made fresh per run because a review round ends by
    restarting the server on a new build folder, and the reviewer's open page
    must reconnect without a new link."""
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        if TOKEN_FILE.exists():
            tok = TOKEN_FILE.read_text().strip()
            if len(tok) >= 20:
                os.chmod(TOKEN_FILE, 0o600)
                return tok
        tmp = TOKEN_FILE.with_name(f"{TOKEN_FILE.name}.{os.getpid()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(24) + "\n")
        tmp.replace(TOKEN_FILE)
        return TOKEN_FILE.read_text().strip()
    except OSError as e:
        print(f"note: cannot keep the access key in {TOKEN_FILE} ({e.strerror}); "
              "using one for this server only", file=sys.stderr)
        return secrets.token_urlsafe(24)


def preview_map(root, stem):
    """page number -> path (relative to build dir), from pdftoppm's naming."""
    pages = {}
    for p in (root / "preview").glob(f"{stem}-*.png"):
        m = re.fullmatch(re.escape(stem) + r"-(\d+)", p.stem)
        if m:
            pages[int(m.group(1))] = f"preview/{p.name}"
    return pages


def extract_html(root, which):
    files = sorted((root / "html").glob("*.html"))
    if which:
        files = [f for f in files if any(w in f.stem for w in which)]
    if not files:
        raise SystemExit(f"no matching html in {root / 'html'} — this room reviews "
                         "a built deck; for a .pptx-only build use --from-pptx")
    from playwright.sync_api import sync_playwright
    decks = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 900})
        for f in files:
            page.goto(f.resolve().as_uri(), wait_until="networkidle")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_timeout(300)
            rows = page.evaluate(JS)
            decks.append((f.stem, rows))
        b.close()
    return decks


def extract_pptx(root, pptx_path):
    try:
        from pptx import Presentation
    except ImportError:
        raise SystemExit("needs python-pptx:  ensure_env.sh --pptx")
    pptx_path = pptx_path if pptx_path.is_absolute() else (root / pptx_path)
    if not pptx_path.exists():
        raise SystemExit(f"no such file: {pptx_path}")
    prs = Presentation(str(pptx_path))
    rows = []
    for i, slide in enumerate(prs.slides, 1):
        title = ""
        if slide.shapes.title is not None:
            title = (slide.shapes.title.text or "").strip()
        note = ""
        if slide.has_notes_slide:
            note = (slide.notes_slide.notes_text_frame.text or "").strip()
        rows.append({"n": i, "title": title, "script": note})

    # Previews need a PDF. Reuse one if a render already exists (render.py for
    # the hybrid path, pptxcheck --pdf for pptx-only), else convert here.
    stem = pptx_path.stem
    pdf = next((p for p in (root / "pdf" / f"{stem}.pdf",
                            pptx_path.parent / "pdf" / f"{stem}.pdf") if p.exists()), None)
    if pdf is None:
        if shutil.which("soffice") is None:
            raise SystemExit("no PDF of this .pptx and no `soffice` to make one — "
                             "run pptxcheck.py --pdf on a machine that has LibreOffice")
        (root / "pdf").mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                            "--outdir", str(root / "pdf"), str(pptx_path)],
                           capture_output=True, text=True)
        pdf = root / "pdf" / f"{stem}.pdf"
        if r.returncode != 0 or not pdf.exists():
            raise SystemExit("LibreOffice conversion failed:\n" + r.stderr.strip()[:400])
    (root / "preview").mkdir(parents=True, exist_ok=True)
    for p in (root / "preview").glob(f"{stem}-*.png"):
        p.unlink()
    subprocess.run(["pdftoppm", "-png", "-r", "96", str(pdf),
                    str(root / "preview" / stem)], check=True)
    return [(stem, rows)]


def build(root, which, from_pptx):
    decks = (extract_pptx(root, from_pptx) if from_pptx
             else extract_html(root, which))
    out = []
    for stem, rows in decks:
        images = preview_map(root, stem)
        missing = [r["n"] for r in rows if r["n"] not in images]
        if missing:
            raise SystemExit(f"{stem}: no preview PNG for page(s) "
                             f"{', '.join(map(str, missing))} — run render.py first, "
                             "and re-run it after any edit so the room shows the "
                             "deck being reviewed, not a stale one")
        out.append({"deck": stem,
                    "title": rows[0]["title"] if rows and rows[0]["title"] else stem,
                    "pages": [{"page": r["n"], "title": r["title"],
                               "script": r["script"], "image": images[r["n"]]}
                              for r in rows]})

    rdir = root / "review"
    rdir.mkdir(parents=True, exist_ok=True)
    write_json(rdir / "manifest.json",
               {"generated": now(), "root": root.name, "decks": out})
    # The app is a template, copied fresh each build so fixes propagate.
    # The record — comments.json — is never overwritten.
    shutil.copy(Path(__file__).resolve().parent.parent / "assets" / "review.html",
                rdir / "index.html")
    if not (rdir / "comments.json").exists():
        write_json(rdir / "comments.json", {"comments": []})
    if not (rdir / "scripts.json").exists():
        write_json(rdir / "scripts.json", {"edits": []})

    n_open = sum(1 for c in json.loads((rdir / "comments.json").read_text())["comments"]
                 if c.get("status") == "open")
    n_pend = sum(1 for e in json.loads((rdir / "scripts.json").read_text())["edits"]
                 if e.get("status") == "pending")
    for d in out:
        unscripted = sum(1 for p in d["pages"] if not p["script"])
        print(f"review: {d['deck']}  {len(d['pages'])} pages"
              + (f"  ({unscripted} without a script)" if unscripted else ""))
    print(f"review: {n_open} open comment(s), {n_pend} pending script edit(s)")


class Handler(SimpleHTTPRequestHandler):
    server_version = "review-room/1"
    token = ""          # set per server by serve()
    _last_warn = 0.0

    def end_headers(self):
        # Everything here changes underfoot (previews re-render, manifest
        # refreshes); make the browser revalidate rather than trust a copy.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass  # static chatter is noise; comments are printed explicitly

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, msg, code):
        body = (msg + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ------------------------------------------------------------ access ----
    def _ours(self):
        port = self.server.server_address[1]
        return (f"127.0.0.1:{port}", f"localhost:{port}")

    def _host_ok(self):
        # A page served from any other name (DNS rebinding) is not this room,
        # even when it resolves to 127.0.0.1.
        return self.headers.get("Host", "") in self._ours()

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        return origin is None or origin in tuple(f"http://{h}" for h in self._ours())

    def _key_ok(self, offered):
        return bool(offered) and hmac.compare_digest(offered.encode(),
                                                     self.token.encode())

    def _authorised(self):
        # Split the Cookie header by hand: every app on 127.0.0.1 shares it,
        # and http.cookies gives up at the first one it finds malformed.
        offered = [v.strip() for k, _, v in
                   (p.strip().partition("=") for p in
                    self.headers.get("Cookie", "").split(";"))
                   if k == COOKIE]
        offered.append(self.headers.get("X-Review-Token", ""))
        return any(self._key_ok(t) for t in offered)

    def _warn(self, msg):
        # Fixed text only: never echo request content into the log an agent
        # reads. At most once a minute, so a probe cannot flood it.
        t = time.monotonic()
        if t - Handler._last_warn > 60:
            Handler._last_warn = t
            print(f"[{now()[11:16]}] {msg}", flush=True)

    def list_directory(self, path):
        self.send_error(404)            # the room never needs a listing
        return None

    def do_HEAD(self):
        self.send_error(405)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if not self._host_ok():
            self._warn("refused a request addressed to another host name")
            return self._text("wrong Host", 403)
        if path in ("", "/"):
            offered = parse_qs(query).get("token", [""])[0]
            if not (self._key_ok(offered) or self._authorised()):
                return self._text(LOCKED, 403)
            self.send_response(302)
            if self._key_ok(offered):
                self.send_header("Set-Cookie",
                                 f"{COOKIE}={self.token}; Path=/; HttpOnly; "
                                 "SameSite=Lax; Max-Age=2592000")
            self.send_header("Location", "/review/")
            self.end_headers()
            return
        if not self._authorised():
            return self._text(LOCKED, 403)
        if path == "/api/state":
            rdir = Path(self.directory) / "review"
            try:
                manifest = json.loads((rdir / "manifest.json").read_text())
                comments = json.loads((rdir / "comments.json").read_text())["comments"]
                spath = rdir / "scripts.json"
                scripts = (json.loads(spath.read_text())["edits"]
                           if spath.exists() else [])
            except (OSError, json.JSONDecodeError, KeyError) as e:
                return self._json({"error": f"cannot read review state: {e}"}, 500)
            return self._json({"manifest": manifest, "comments": comments,
                               "scripts": scripts})
        clean = posixpath.normpath(unquote(path))
        if not any(clean == d or clean.startswith(d + "/") for d in SERVED):
            return self._text("not part of the review room", 404)
        super().do_GET()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= 65536:
            raise ValueError("body missing or too large")
        return json.loads(self.rfile.read(n))

    def do_POST(self):
        path = self.path.split("?")[0]
        if not (self._host_ok() and self._origin_ok()):
            self._warn("refused a write from another site")
            return self._json({"error": "cross-site request refused"}, 403)
        if not self._authorised():
            return self._json({"error": LOCKED}, 403)
        # A JSON content type cannot be sent cross-site without a CORS
        # preflight, which this server never grants.
        if self.headers.get_content_type() != "application/json":
            return self._json({"error": "Content-Type must be application/json"}, 415)
        rdir = Path(self.directory) / "review"
        cpath = rdir / "comments.json"
        try:
            body = self._body()
        except (ValueError, json.JSONDecodeError) as e:
            return self._json({"error": str(e)}, 400)

        if path == "/api/comments":
            text = str(body.get("text") or "").strip()[:8000]
            try:
                page = int(body.get("page"))
            except (TypeError, ValueError):
                page = 0
            author = body.get("author") or "user"
            if not text or page < 1 or author not in ("user", "agent"):
                return self._json({"error": "need text, page >= 1, author user|agent"}, 400)
            with LOCK:
                data = json.loads(cpath.read_text())
                nid = 1 + max((int(c["id"][1:]) for c in data["comments"]
                               if re.fullmatch(r"c\d+", str(c.get("id")))), default=0)
                comment = {"id": f"c{nid}", "deck": str(body.get("deck") or ""),
                           "page": page, "author": author, "text": text,
                           "time": now()}
                if body.get("re"):
                    comment["re"] = str(body["re"])
                if body.get("about") in ("slide", "script"):
                    comment["about"] = body["about"]
                if author == "user":
                    comment["status"] = "open"
                data["comments"].append(comment)
                write_json(cpath, data)
            print(f"[{comment['time'][11:16]}] {author} on "
                  f"{comment['deck'] or 'deck'} p.{page}: {text[:90]!r}", flush=True)
            return self._json({"ok": True, "comment": comment})

        if path == "/api/comments/resolve":
            cid, status = str(body.get("id") or ""), body.get("status") or "addressed"
            if status not in ("open", "addressed"):
                return self._json({"error": "status must be open|addressed"}, 400)
            with LOCK:
                data = json.loads(cpath.read_text())
                hit = next((c for c in data["comments"] if c.get("id") == cid), None)
                if hit is None:
                    return self._json({"error": f"no comment {cid!r}"}, 404)
                hit["status"] = status
                if body.get("resolution"):
                    hit["resolution"] = str(body["resolution"])[:2000]
                write_json(cpath, data)
            print(f"[{now()[11:16]}] {cid} -> {status}", flush=True)
            return self._json({"ok": True, "comment": hit})

        if path == "/api/script":
            spath = rdir / "scripts.json"
            text = str(body.get("text") if body.get("text") is not None else "")
            text = text.replace("\r\n", "\n").strip()[:20000]
            try:
                page = int(body.get("page"))
            except (TypeError, ValueError):
                page = 0
            deck = str(body.get("deck") or "")
            if page < 1:
                return self._json({"error": "need page >= 1"}, 400)
            base = body.get("baseTime")   # entry time the client loaded; None = none
            with LOCK:
                data = (json.loads(spath.read_text()) if spath.exists()
                        else {"edits": []})
                hit = next((e for e in data["edits"]
                            if e.get("deck") == deck and e.get("page") == page), None)
                # A stale page must never clobber unfolded user text: refuse
                # when the PENDING entry on disk is newer than the one the
                # client based its edit on. A merged entry is history — its
                # text is already in the deck — so writing over it is the
                # normal next-edit flow, not a clobber.
                pending = hit is not None and hit.get("status") == "pending"
                if pending and (hit.get("time") or "") != (base or ""):
                    return self._json({"error": "stale",
                                       "entry": hit}, 409)
                if not text:              # discard the pending edit
                    if pending:
                        data["edits"].remove(hit)
                        write_json(spath, data)
                        print(f"[{now()[11:16]}] script edit on {deck or 'deck'} "
                              f"p.{page} discarded", flush=True)
                    return self._json({"ok": True, "entry": None})
                entry = {"deck": deck, "page": page, "text": text,
                         "time": now(), "status": "pending"}
                if hit is None:
                    data["edits"].append(entry)
                else:
                    hit.update(entry)
                    entry = hit
                write_json(spath, data)
            print(f"[{entry['time'][11:16]}] script edit on {deck or 'deck'} "
                  f"p.{page} ({len(text.split())} words)", flush=True)
            return self._json({"ok": True, "entry": entry})

        if path == "/api/script/merged":
            spath = rdir / "scripts.json"
            try:
                page = int(body.get("page"))
            except (TypeError, ValueError):
                page = 0
            deck = str(body.get("deck") or "")
            with LOCK:
                data = (json.loads(spath.read_text()) if spath.exists()
                        else {"edits": []})
                hit = next((e for e in data["edits"]
                            if e.get("deck") == deck and e.get("page") == page), None)
                if hit is None:
                    return self._json({"error": f"no edit for {deck!r} p.{page}"}, 404)
                hit["status"] = "merged"
                write_json(spath, data)
            print(f"[{now()[11:16]}] script edit on {deck or 'deck'} "
                  f"p.{page} -> merged", flush=True)
            return self._json({"ok": True, "entry": hit})

        return self._json({"error": "unknown endpoint"}, 404)


def serve(root, port):
    class Room(Handler):
        token = load_token()
    handler = partial(Room, directory=str(root))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as e:
        raise SystemExit(
            f"cannot bind 127.0.0.1:{port} ({e.strerror}) — an earlier review "
            "server is probably still running. Kill it if it serves a stale "
            "build, or pick another port with --port.")
    print(f"review room:  http://127.0.0.1:{port}/?token={Room.token}")
    print("              (the link carries the access key; share it only with "
          "reviewers on this machine)")
    print(f"access key:   {TOKEN_FILE}  — send as X-Review-Token when writing "
          "through the API")
    print(f"serving:      {root}")
    print(f"comments:     {root / 'review' / 'comments.json'}")
    print(f"script edits: {root / 'review' / 'scripts.json'}")
    print("comments and edits are printed here as they arrive; Ctrl-C stops "
          "the server (the files keep everything).", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build_dir")
    ap.add_argument("names", nargs="*", help="only decks whose stem contains this")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--build-only", action="store_true",
                    help="refresh review/ and exit (a running server picks it up)")
    ap.add_argument("--from-pptx", type=Path, metavar="FILE.pptx",
                    help="extract titles/notes from a .pptx and rasterize its PDF")
    args = ap.parse_args(argv)

    root = Path(args.build_dir).resolve()
    if not root.is_dir():
        raise SystemExit(f"no such build dir: {root}")
    build(root, args.names, args.from_pptx)
    if args.build_only:
        return 0
    return serve(root, args.port)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
