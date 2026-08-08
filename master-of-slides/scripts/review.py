"""Build and serve the review room: each page's slide beside its speaker note,
with a comment thread anchored to that page.

    python review.py <build-dir>                      # build review/, serve on 127.0.0.1:7788
    python review.py <build-dir> --port 7799
    python review.py <build-dir> --build-only         # (re)write review/, no server
    python review.py <build-dir> --from-pptx pptx/deck.pptx   # a .pptx-only build

Run `render.py` first: the room shows `preview/*.png`, and the note shown next
to each page is re-extracted from the deck source (the `.notes` div, or the
notes slide of a .pptx), so what the reviewer reads is what the presenter will
actually rehearse from.

Everything the reviewer types lands in **`<build-dir>/review/comments.json`** —
one plain JSON file, one entry per comment, each pinned to a deck and a page.
That file is the record; the server is just the door to it. Reading the
feedback later is a single file read, and the server also prints each comment
to stdout as it arrives, so a process watching the log sees feedback live.

The server is stdlib-only and stateless: every request re-reads the manifest
and the comments from disk. So `--build-only` can refresh the manifest under a
running server after a re-render, and replies posted through the API appear on
the next poll without a restart. Writes go tmp-then-rename behind a lock, so a
comment arriving mid-write cannot truncate the file.

API (JSON over HTTP, bound to 127.0.0.1 only):

    GET  /api/state                             # {manifest, comments}
    POST /api/comments            {deck?, page, text, author?, re?}
    POST /api/comments/resolve    {id, resolution?, status?}

`author` is "user" (default) or "agent"; `re` threads a reply under an earlier
comment's id. User comments start with `status: "open"`; resolve flips one to
"addressed" once the deck actually changed — not before.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_PORT = 7788
LOCK = threading.Lock()

# Same extraction the notes script uses, so the room and the rehearsal script
# cannot disagree about what a slide's note says. `.notes` is display:none, so
# innerText hands back source whitespace; keep blank-line paragraph breaks and
# collapse the rest.
JS = r"""
() => {
  const norm = t => t.trim().split(/\n\s*\n/)
      .map(p => p.replace(/\s+/g, ' ').trim()).filter(Boolean).join('\n\n');
  return [...document.querySelectorAll('.slide')].map((s, i) => {
    const t = s.querySelector('h1, h2, .stitle');
    const n = s.querySelector('.notes');
    return {n: i + 1,
            title: t ? (t.innerText || t.textContent).trim().replace(/\s+/g, ' ') : '',
            note: n ? norm(n.innerText || n.textContent || '') : ''};
  });
}
"""


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path, obj):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


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
        rows.append({"n": i, "title": title, "note": note})

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
                               "note": r["note"], "image": images[r["n"]]}
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

    n_open = sum(1 for c in json.loads((rdir / "comments.json").read_text())["comments"]
                 if c.get("status") == "open")
    for d in out:
        noteless = sum(1 for p in d["pages"] if not p["note"])
        print(f"review: {d['deck']}  {len(d['pages'])} pages"
              + (f"  ({noteless} without a note)" if noteless else ""))
    print(f"review: {n_open} open comment(s) in review/comments.json")


class Handler(SimpleHTTPRequestHandler):
    server_version = "review-room/1"

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

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/review/")
            self.end_headers()
            return
        if path == "/api/state":
            rdir = Path(self.directory) / "review"
            try:
                manifest = json.loads((rdir / "manifest.json").read_text())
                comments = json.loads((rdir / "comments.json").read_text())["comments"]
            except (OSError, json.JSONDecodeError, KeyError) as e:
                return self._json({"error": f"cannot read review state: {e}"}, 500)
            return self._json({"manifest": manifest, "comments": comments})
        super().do_GET()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= 65536:
            raise ValueError("body missing or too large")
        return json.loads(self.rfile.read(n))

    def do_POST(self):
        path = self.path.split("?")[0]
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

        return self._json({"error": "unknown endpoint"}, 404)


def serve(root, port):
    handler = partial(Handler, directory=str(root))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as e:
        raise SystemExit(
            f"cannot bind 127.0.0.1:{port} ({e.strerror}) — an earlier review "
            "server is probably still running. Kill it if it serves a stale "
            "build, or pick another port with --port.")
    print(f"review room:  http://127.0.0.1:{port}/")
    print(f"serving:      {root}")
    print(f"comments:     {root / 'review' / 'comments.json'}")
    print("comments are printed here as they arrive; Ctrl-C stops the server "
          "(the file keeps everything).", flush=True)
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
