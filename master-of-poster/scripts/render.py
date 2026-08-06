"""Render poster HTML to PDF at exact trim size, and fail the build on defects.

    python render.py <build-dir> [name-filter ...]

`<build-dir>` is the poster folder — the one holding `html/`. PDFs land in
`<build-dir>/pdf/`, inspection PNGs in `<build-dir>/preview/`.

Four things are checked, each of which has silently ruined a poster before:

  * **missing `<!DOCTYPE html>`** — without it the page renders in quirks mode,
    where `body.clientWidth` reports the viewport instead of the page box. Every
    measurement downstream is then wrong while looking entirely plausible.
  * **content past the trim** — anything whose box extends beyond the page.
  * **a block compressed below its content** — a flex child squeezed under its
    natural height clips its last line while the page box stays clean. Nothing
    looks wrong until you read the printed caption and a sentence is missing.
  * **page-size mismatch** — the emitted PDF is measured against the size the
    HTML declared, so a silent scale cannot reach the printer.

Exit status is non-zero if anything failed, so this can gate a build.
"""
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PREVIEW_DPI = 40          # ~1450 px on the long edge of a 36x54 in poster
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


def render(page, html_path, pdf_dir, preview_dir):
    w_in, h_in = declared_size(html_path)
    page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
    page.emulate_media(media="print")
    # fonts, then images, then a paint tick — nothing is measured mid-layout
    page.evaluate("() => document.fonts.ready")
    page.evaluate("""() => Promise.all(
        [...document.images].filter(i => !i.complete)
            .map(i => new Promise(r => { i.onload = i.onerror = r; })))""")
    page.wait_for_timeout(600)

    overflow = page.evaluate("""() => {
        const d = document.documentElement, b = document.body;
        // body, not documentElement: in print media documentElement.clientWidth
        // reports the *viewport*, while body carries the real page box. Correct
        // only in standards mode, hence the doctype guard.
        const PW = b.clientWidth, PH = b.clientHeight;
        const out = [];
        for (const el of document.querySelectorAll('*')) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (r.right > PW + 1.5 || r.bottom > PH + 1.5 ||
                r.left < -1.5 || r.top < -1.5) {
                out.push({tag: el.tagName,
                          cls: el.className && el.className.toString().slice(0, 60),
                          right: Math.round(r.right), bottom: Math.round(r.bottom),
                          txt: (el.textContent || '').trim().slice(0, 48)});
            }
        }
        const clipped = [];
        for (const el of document.querySelectorAll(
                '.block, .hero, .action, .actionstrip, .footer, figure, section, div, p')) {
            const st = getComputedStyle(el);
            if (st.overflow === 'visible' && st.overflowY === 'visible') {
                if (el.scrollHeight <= el.clientHeight + 1) continue;
            }
            if (el.scrollHeight > el.clientHeight + 1 && el.clientHeight > 0) {
                clipped.push({tag: el.tagName,
                              cls: (el.className || '').toString().slice(0, 46),
                              need: el.scrollHeight, got: el.clientHeight,
                              txt: (el.textContent || '').trim().slice(0, 44)});
            }
        }
        return {scrollW: d.scrollWidth, scrollH: d.scrollHeight,
                clientW: PW, clientH: PH, bad: out.slice(0, 12),
                clipped: clipped.slice(0, 12)};
    }""")

    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / (html_path.stem + ".pdf")
    page.pdf(path=str(pdf_path), width=f"{w_in}in", height=f"{h_in}in",
             print_background=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
             prefer_css_page_size=True)

    info = subprocess.run(["pdfinfo", str(pdf_path)],
                          capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
    got = (round(float(m.group(1)) / 72, 3), round(float(m.group(2)) / 72, 3)) if m else None
    size_ok = got is not None and abs(got[0] - w_in) < 0.02 and abs(got[1] - h_in) < 0.02

    preview_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", str(PREVIEW_DPI), "-singlefile",
                    str(pdf_path), str(preview_dir / html_path.stem)], check=True)

    ok = size_ok and not overflow["bad"] and not overflow["clipped"]
    print(f"{'OK ' if ok else '!! '}{html_path.stem}  {w_in}x{h_in}in  pdf={got}  "
          f"scroll={overflow['scrollW']}x{overflow['scrollH']} "
          f"client={overflow['clientW']}x{overflow['clientH']}")
    if not size_ok:
        print(f"    PAGE SIZE MISMATCH: declared {w_in}x{h_in}in, pdf {got}")
    for b in overflow["bad"]:
        print(f"    OVERFLOW <{b['tag']} class='{b['cls']}'> "
              f"right={b['right']} bottom={b['bottom']}  {b['txt']!r}")
    for c in overflow["clipped"]:
        print(f"    CLIPPED  <{c['tag']} class='{c['cls']}'> "
              f"needs {c['need']}px, has {c['got']}px  {c['txt']!r}")
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
        page = browser.new_page(viewport={"width": 1600, "height": 2400})
        for f in files:
            ok &= render(page, f, root / "pdf", root / "preview")
        browser.close()
    print("\nall clean" if ok else "\nissues above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
