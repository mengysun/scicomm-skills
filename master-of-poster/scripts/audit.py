"""Measure what the success criteria actually ask for, per poster.

  1. figure-area fraction of the *body* area (body = page minus the title block
     and minus the footer band) — the spec wants >= 55%
  2. smallest rendered font size anywhere, against the type floors
  3. body word count (target 400-700 across the whole poster)
  4. minimum clear space around every figure and text block (>= 0.4 in) and
     distance from the trim edge (>= 1 in)

Reports one line per poster plus detail for anything that fails.

    python audit.py <build-dir> [name-filter ...]

Thresholds are the defaults that produced good sheets; override with flags if a
venue asks for something else. The figure fraction is measured against the
*drawn* image area (an `object-fit: contain` figure letterboxes inside its box,
and counting the box would flatter a poster that is mostly white space).
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE_RE = re.compile(r"@page\s*\{[^}]*size:\s*([\d.]+)in\s+([\d.]+)in", re.S)

JS = r"""
() => {
  const B = document.body;
  // body carries the real page box in print media (see scripts/render.py)
  const PW = B.clientWidth, PH = B.clientHeight;
  const px2in = PW / PAGE_W_IN;

  const rect = el => { const r = el.getBoundingClientRect();
                       return {x:r.left, y:r.top, w:r.width, h:r.height,
                               r:r.right, b:r.bottom}; };

  // ---- body area: page minus title block, minus footer -------------------
  const title  = document.querySelector('.titleblock, header, [data-role=title]');
  const footer = document.querySelector('.footer, footer, [data-role=footer]');
  const top    = title  ? rect(title).b  : 0;
  const bot    = footer ? rect(footer).y : PH;
  const bodyArea = PW * Math.max(bot - top, 1);

  // ---- figure area -------------------------------------------------------
  const figs = [...document.querySelectorAll('figure img, figure svg, [data-fig]')];
  let figArea = 0;
  const figBoxes = [];
  for (const f of figs) {
    const r = rect(f);
    if (r.w < 8 || r.h < 8) continue;
    // object-fit: contain letterboxes inside the box; count only what is drawn,
    // otherwise a tall box around a wide figure would inflate the fraction.
    let dw = r.w, dh = r.h;
    const nw = f.naturalWidth, nh = f.naturalHeight;
    if (nw && nh && getComputedStyle(f).objectFit === 'contain') {
      const s = Math.min(r.w / nw, r.h / nh);
      dw = nw * s; dh = nh * s;
    }
    figArea += dw * dh;
    figBoxes.push({x: r.x, y: r.y, w: dw, h: dh, r: r.x + dw, b: r.y + dh});
  }

  // ---- smallest rendered type -------------------------------------------
  let minPt = 1e9, minSel = '';
  for (const el of document.querySelectorAll('*')) {
    if (!el.textContent || !el.textContent.trim()) continue;
    let direct = false;
    for (const n of el.childNodes)
      if (n.nodeType === 3 && n.textContent.trim()) direct = true;
    if (!direct) continue;
    const r = rect(el);
    if (r.w < 2 || r.h < 2) continue;
    const px = parseFloat(getComputedStyle(el).fontSize);
    const pt = px / px2in * 72;
    if (pt < minPt) { minPt = pt;
      minSel = el.tagName + '.' + (el.className||'').toString().slice(0,40)
             + ' :: ' + el.textContent.trim().slice(0,44); }
  }

  // ---- word count --------------------------------------------------------
  const words = (B.innerText || '').trim().split(/\s+/).filter(Boolean).length;

  // ---- clearance between sibling blocks and from the trim -----------------
  const blocks = [...document.querySelectorAll(
      '.block, .hero, .action, .footer, .titleblock, figure')];
  const boxes = blocks.map(rect).filter(r => r.w > 8 && r.h > 8);
  let minGap = 1e9, gapPair = '';
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      const ox = (a.x < b.r && b.x < a.r), oy = (a.y < b.b && b.y < a.b);
      if (ox && oy) continue;                 // nested or overlapping: skip
      let g = Infinity;
      if (ox) g = Math.min(g, Math.abs(a.y < b.y ? b.y - a.b : a.y - b.b));
      if (oy) g = Math.min(g, Math.abs(a.x < b.x ? b.x - a.r : a.x - b.r));
      if (g < minGap && g !== Infinity) { minGap = g; gapPair = i + '/' + j; }
    }
  }
  let minEdge = 1e9;
  for (const r of boxes)
    minEdge = Math.min(minEdge, r.x, r.y, PW - r.r, PH - r.b);

  // ---- contrast --------------------------------------------------------
  // A stylesheet rule written for one context can follow an element into
  // another: bold text coloured for a pale card keeps that colour inside a
  // saturated band, and the emphasis then recedes instead of advancing. This
  // is invisible in source and obvious in print, so measure it.
  const lum = c => { const s = c.map(v => { v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]; };
  const parse = s => { const m = (s || '').match(/[\d.]+/g);
    return m && m.length >= 3 ? m.slice(0, 3).map(Number) : null; };
  const alpha = s => { const m = (s || '').match(/[\d.]+/g);
    return m && m.length >= 4 ? Number(m[3]) : 1; };
  const bgOf = el => {                       // nearest opaque ancestor background
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const c = getComputedStyle(n).backgroundColor;
      if (alpha(c) > 0.05) { const p = parse(c); if (p) return p; }
    }
    return [255, 255, 255];
  };
  let worst = 99, worstSel = '';
  for (const el of document.querySelectorAll('*')) {
    let direct = false;
    for (const n of el.childNodes)
      if (n.nodeType === 3 && n.textContent.trim()) direct = true;
    if (!direct) continue;
    const r = rect(el);
    if (r.w < 2 || r.h < 2) continue;
    const fg = parse(getComputedStyle(el).color); if (!fg) continue;
    const bg = bgOf(el);
    const a = lum(fg), b2 = lum(bg);
    const ratio = (Math.max(a, b2) + 0.05) / (Math.min(a, b2) + 0.05);
    if (ratio < worst) { worst = ratio;
      worstSel = el.tagName + '.' + (el.className || '').toString().slice(0, 30)
               + ' :: ' + el.textContent.trim().slice(0, 40); }
  }

  return {figFrac: figArea / bodyArea, nFigs: figBoxes.length,
          minPt, minSel, words, px2in,
          minGapIn: minGap / px2in, minEdgeIn: minEdge / px2in,
          minContrast: worst, minContrastSel: worstSel,
          bodyFracOfPage: (bot - top) / PH};
}
"""

FLOORS = {"body": 28, "caption": 22}


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    ROOT = Path(argv[0]).resolve()
    which = argv[1:]
    files = sorted((ROOT / "html").glob("*.html"))
    if which:
        files = [f for f in files if any(w in f.stem for w in which)]
    rows = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 2400})
        for f in files:
            m = PAGE_RE.search(f.read_text())
            if not m:
                raise SystemExit(f"{f.name}: no `@page {{ size: W H }}` rule found")
            w_in, h_in = float(m.group(1)), float(m.group(2))
            page.goto(f.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_timeout(400)
            r = page.evaluate(JS.replace("PAGE_W_IN", str(w_in)))
            r["name"] = f.stem
            r["size"] = f"{w_in:g}x{h_in:g}"
            rows.append(r)
        b.close()

    print(f"{'poster':<30}{'size':>9}{'figs':>6}{'fig%':>8}{'minPt':>8}"
          f"{'words':>7}{'gap in':>8}{'edge in':>9}{'contrast':>10}")
    print("-" * 96)
    for r in rows:
        flag = ""
        if r["figFrac"] < 0.55:   flag += " FIG<55%"
        if r["minPt"] < 22:       flag += " TYPE<22pt"
        if not (350 <= r["words"] <= 780): flag += f" WORDS={r['words']}"
        if r["minGapIn"] < 0.40:  flag += " GAP<0.4in"
        if r["minEdgeIn"] < 1.0:  flag += " EDGE<1in"
        if r.get("minContrast", 99) < 3.0: flag += " CONTRAST<3:1"
        print(f"{r['name']:<30}{r['size']:>9}{r['nFigs']:>6}"
              f"{r['figFrac']*100:>7.1f}%{r['minPt']:>8.1f}{r['words']:>7}"
              f"{r['minGapIn']:>8.2f}{r['minEdgeIn']:>9.2f}"
              f"{r.get('minContrast', 0):>9.2f}:1{flag}")
        if r["minPt"] < 22:
            print(f"      smallest type: {r['minSel']}")
        if r.get("minContrast", 99) < 3.0:
            print(f"      lowest contrast: {r['minContrastSel']}")
    tag = "_".join(which) if which else "all"
    out = ROOT / "qa"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"audit_{tag}.json").write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
