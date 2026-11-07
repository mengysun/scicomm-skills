"""Measure the boxes a layout actually produces, in inches.

Two questions this answers that render.py and audit.py do not:

  * what aspect does each figure cell want?  A plate is scaled with
    `object-fit: contain`, so the cell's *available* box — not the plate — sets
    the ceiling. Author the plate to that aspect and nothing is letterboxed.
  * how much of a text block is actually filled?  A block that reaches only
    70% of its box reads as a hole in the sheet; render.py only catches the
    opposite failure (content that does not fit).

    python probe.py <build-dir> [name-filter ...]
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE_RE = re.compile(r"@page\s*\{[^}]*size:\s*([\d.]+)in\s+([\d.]+)in", re.S)

JS = r"""
() => {
  const B = document.body;
  const px2in = B.clientWidth / PAGE_W_IN;
  const inch = v => Math.round(v / px2in * 100) / 100;
  const out = [];
  for (const s of document.querySelectorAll('section.block, .sowhat, .method')) {
    const r = s.getBoundingClientRect();
    const pill = s.querySelector('.pill');
    const img  = s.querySelector('figure.fig > img');
    const cap  = s.querySelector('figcaption');
    const row = {cls: (s.className || '').toString(),
                 head: (pill ? pill.textContent : s.textContent).trim().slice(0, 26),
                 w: inch(r.width), h: inch(r.height),
                 fill: Math.round(s.scrollHeight / Math.max(s.clientHeight, 1) * 100)};
    if (img) {
      const ir = img.getBoundingClientRect();
      const s2 = Math.min(ir.width / img.naturalWidth, ir.height / img.naturalHeight);
      const dw = img.naturalWidth * s2, dh = img.naturalHeight * s2;
      row.box = inch(ir.width) + 'x' + inch(ir.height);
      row.boxAsp = Math.round(ir.height / ir.width * 1000) / 1000;
      row.drawn = inch(dw) + 'x' + inch(dh);
      row.plateAsp = Math.round(img.naturalHeight / img.naturalWidth * 1000) / 1000;
      row.waste = Math.round((1 - (dw * dh) / (ir.width * ir.height)) * 100);
      row.capLines = cap ? Math.round(cap.getBoundingClientRect().height /
                          parseFloat(getComputedStyle(cap).lineHeight)) : 0;
    }
    out.push(row);
  }
  const hdr = document.querySelector('header');
  const ftr = document.querySelector('footer, .footer');
  return {blocks: out,
          header: hdr ? inch(hdr.getBoundingClientRect().height) : 0,
          footer: ftr ? inch(ftr.getBoundingClientRect().height) : 0};
}
"""


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    ROOT = Path(argv[0]).resolve()
    which = argv[1:]
    files = sorted((ROOT / "html").glob("*.html"))
    if which:
        files = [f for f in files if any(w in f.stem for w in which)]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 2400})
        for f in files:
            m = PAGE_RE.search(f.read_text())
            if not m:
                raise SystemExit(f"{f.name}: no `@page {{ size: W H }}` rule found")
            w_in = float(m.group(1))
            page.goto(f.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_timeout(400)
            r = page.evaluate(JS.replace("PAGE_W_IN", str(w_in)))
            print(f"\n=== {f.stem}   header {r['header']}in   footer {r['footer']}in")
            print(f"{'section':<28}{'block wxh':>14}{'fill%':>7}"
                  f"{'fig box':>14}{'boxAsp':>8}{'plateAsp':>10}{'waste%':>8}{'cap':>5}")
            for x in r["blocks"]:
                print(f"{x['head']:<28}{x['w']:>7}x{x['h']:<6}{x['fill']:>7}"
                      f"{x.get('box',''):>14}{x.get('boxAsp',''):>8}"
                      f"{x.get('plateAsp',''):>10}{x.get('waste',''):>8}"
                      f"{x.get('capLines',''):>5}")
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
