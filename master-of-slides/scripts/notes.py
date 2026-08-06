"""Extract speaker notes from an HTML deck into a markdown script.

    python notes.py <build-dir> [name-filter ...]

Writes `<build-dir>/notes/<deck>.md`: one entry per slide, with the slide's
title, the words that will be projected, and the note beneath it.

Notes live inside each slide in the source (`<div class="notes">`), hidden in
print, so the script and the slide cannot drift apart. Pulling them out gives
the presenter something to rehearse from, and gives you a way to check the
division of labour: anything the audience must hear but should not have to read
belongs in the note, and a slide whose note is empty is usually a slide whose
text is doing the presenter's job.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

JS = r"""
() => [...document.querySelectorAll('.slide')].map((s, i) => {
  const t = s.querySelector('h1, h2, .stitle');
  const n = s.querySelector('.notes');
  const clone = s.cloneNode(true);
  clone.querySelectorAll('.notes').forEach(x => x.remove());
  return {n: i + 1,
          title: t ? (t.innerText || t.textContent).trim().replace(/\s+/g, ' ') : '',
          onslide: (clone.innerText || clone.textContent || '').trim(),
          note: n ? (n.innerText || n.textContent || '').trim() : ''};
})
"""


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    root = Path(argv[0]).resolve()
    which = argv[1:]
    files = sorted((root / "html").glob("*.html"))
    if which:
        files = [f for f in files if any(w in f.stem for w in which)]
    outdir = root / "notes"
    outdir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 900})
        for f in files:
            page.goto(f.resolve().as_uri(), wait_until="networkidle")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_timeout(300)
            rows = page.evaluate(JS)
            lines = [f"# Speaker notes — {f.stem}", ""]
            missing = []
            for r in rows:
                lines.append(f"## {r['n']}. {r['title'] or '(untitled)'}")
                lines.append("")
                if r["onslide"]:
                    body = re.sub(r"\n{2,}", "\n", r["onslide"]).replace("\n", " · ")
                    lines.append(f"*On the slide:* {body}")
                    lines.append("")
                if r["note"]:
                    lines.append(r["note"])
                else:
                    lines.append("_(no note)_")
                    missing.append(r["n"])
                lines.append("")
            (outdir / f"{f.stem}.md").write_text("\n".join(lines))
            print(f"wrote {outdir / (f.stem + '.md')}  ({len(rows)} slides)")
            if missing:
                print(f"  no note on slides: {', '.join(map(str, missing))}")
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
