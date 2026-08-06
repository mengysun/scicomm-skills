"""Render an HTML deck to a multi-page PDF, and fail the build on defects.

    python render.py <build-dir> [name-filter ...]

`<build-dir>` holds `html/`. One HTML file is one deck: each
`<section class="slide">` becomes exactly one PDF page. PDFs land in
`<build-dir>/pdf/`, one PNG per slide in `<build-dir>/preview/`.

Checked, because each of these has shipped a broken deck before:

  * **missing `<!DOCTYPE html>`** — quirks mode makes `body.clientWidth` report
    the viewport instead of the page box, so every measurement downstream is
    wrong while looking plausible.
  * **content past the slide edge** — text or a figure running off the canvas.
    On a poster you would see it; on slide 23 of 40 you will not, until you are
    standing in front of the room.
  * **a slide whose content is taller than the slide** — the overflow is hidden,
    so the bottom line of a build or the last row of a table silently vanishes.
  * **page count ≠ slide count** — a slide that failed to break, or one that
    split across two pages.
"""
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PREVIEW_DPI = 96
PAGE_RE = re.compile(r"@page\s*\{[^}]*size:\s*([\d.]+)in\s+([\d.]+)in", re.S)


def declared_size(html_path):
    text = html_path.read_text()
    if not text.lstrip()[:15].upper().startswith("<!DOCTYPE HTML"):
        raise SystemExit(f"{html_path.name}: missing <!DOCTYPE html> — quirks mode "
                         "silently breaks page-box measurement")
    m = PAGE_RE.search(text)
    if not m:
        raise SystemExit(f"{html_path.name}: no `@page {{ size: W H }}` rule found")
    return float(m.group(1)), float(m.group(2))


JS = r"""
() => {
  const slides = [...document.querySelectorAll('.slide')];
  const px2in = document.body.clientWidth / PAGE_W_IN;
  const bad = [];
  slides.forEach((s, i) => {
    const sr = s.getBoundingClientRect();
    const title = (s.querySelector('h1, h2, .stitle') || {}).textContent || '';
    // content taller than the slide: overflow is hidden, so this is silent
    if (s.scrollHeight > s.clientHeight + 1)
      bad.push({n: i + 1, kind: 'OVERSET', title: title.trim().slice(0, 40),
                detail: `content ${Math.round(s.scrollHeight)}px in ${Math.round(s.clientHeight)}px`});
    if (s.scrollWidth > s.clientWidth + 1)
      bad.push({n: i + 1, kind: 'OVERSET-W', title: title.trim().slice(0, 40),
                detail: `content ${Math.round(s.scrollWidth)}px in ${Math.round(s.clientWidth)}px`});
    for (const el of s.querySelectorAll('*')) {
      const st = getComputedStyle(el);
      if (st.display === 'none' || st.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      if (r.right > sr.right + 1.5 || r.bottom > sr.bottom + 1.5 ||
          r.left < sr.left - 1.5 || r.top < sr.top - 1.5) {
        bad.push({n: i + 1, kind: 'OFF-SLIDE', title: title.trim().slice(0, 40),
                  detail: `<${el.tagName} class="${(el.className||'').toString().slice(0,30)}"> `
                        + (el.textContent || '').trim().slice(0, 34)});
        break;                      // one report per slide is enough to act on
      }
      // a flex/grid child squeezed under its content clips its last line
      if (el.scrollHeight > el.clientHeight + 1 && el.clientHeight > 0 &&
          st.overflow !== 'visible') {
        bad.push({n: i + 1, kind: 'CLIPPED', title: title.trim().slice(0, 40),
                  detail: `<${el.tagName}> needs ${el.scrollHeight}px has ${el.clientHeight}px`});
        break;
      }
    }
  });
  return {count: slides.length, bad: bad.slice(0, 20), px2in};
}
"""


def render(page, html_path, pdf_dir, preview_dir):
    w_in, h_in = declared_size(html_path)
    page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
    page.emulate_media(media="print")
    page.evaluate("() => document.fonts.ready")
    page.evaluate("""() => Promise.all(
        [...document.images].filter(i => !i.complete)
            .map(i => new Promise(r => { i.onload = i.onerror = r; })))""")
    page.wait_for_timeout(500)

    info = page.evaluate(JS.replace("PAGE_W_IN", str(w_in)))

    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / (html_path.stem + ".pdf")
    page.pdf(path=str(pdf_path), width=f"{w_in}in", height=f"{h_in}in",
             print_background=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
             prefer_css_page_size=True)

    out = subprocess.run(["pdfinfo", str(pdf_path)],
                         capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", out).group(1))
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
    got = (round(float(m.group(1)) / 72, 3), round(float(m.group(2)) / 72, 3)) if m else None
    size_ok = got is not None and abs(got[0] - w_in) < 0.02 and abs(got[1] - h_in) < 0.02
    count_ok = pages == info["count"]

    preview_dir.mkdir(parents=True, exist_ok=True)
    for f in preview_dir.glob(f"{html_path.stem}-*.png"):
        f.unlink()
    subprocess.run(["pdftoppm", "-png", "-r", str(PREVIEW_DPI),
                    str(pdf_path), str(preview_dir / html_path.stem)], check=True)

    ok = size_ok and count_ok and not info["bad"]
    print(f"{'OK ' if ok else '!! '}{html_path.stem}  {info['count']} slides  "
          f"{w_in}x{h_in}in  pdf={pages}pp {got}")
    if not size_ok:
        print(f"    PAGE SIZE MISMATCH: declared {w_in}x{h_in}in, pdf {got}")
    if not count_ok:
        print(f"    PAGE COUNT: {info['count']} .slide elements produced {pages} pages "
              f"— a slide is splitting or not breaking")
    for b in info["bad"]:
        print(f"    {b['kind']:<10} slide {b['n']:>2}  {b['title']!r}  {b['detail']}")
    return ok


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    root = Path(argv[0]).resolve()
    which = argv[1:]
    files = sorted((root / "html").glob("*.html"))
    if which:
        files = [f for f in files if any(w in f.stem for w in which)]
    if not files:
        raise SystemExit(f"no matching html in {root / 'html'}")
    ok = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        for f in files:
            ok &= render(page, f, root / "pdf", root / "preview")
        browser.close()
    print("\nall clean" if ok else "\nissues above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
