"""Measure a deck slide by slide, and print its title track.

    python audit.py <build-dir> [name-filter ...]
    python audit.py <build-dir> --titles       # just the title track

Per slide: word count, smallest rendered type (as points and as a fraction of
slide height, which is what actually determines legibility from the back of a
room), lowest text contrast, and the fraction of the slide the figures occupy.

The **title track** is the cheapest quality check a deck has. Read the titles in
order with nothing else: if they do not tell the argument on their own, the deck
does not either, and no amount of layout work will fix that. Slides whose titles
name a topic ("Results", "Methods") rather than assert a claim ("Treated plots
yield more") show up immediately when you read them as a list.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE_RE = re.compile(r"@page\s*\{[^}]*size:\s*([\d.]+)in\s+([\d.]+)in", re.S)

# Defaults for a 16:9 deck shown in a room. Expressed as a fraction of slide
# height as well as points, because the fraction is what ports across canvas
# sizes: 18 pt on a 7.5 in slide is 3.3% of its height, and that is the number
# that predicts whether the back row can read it.
FLOOR_PT = 16.0
FLOOR_FRAC = 0.028
WORD_BUDGET = 55

JS = r"""
() => {
  const B = document.body;
  const px2in = B.clientWidth / PAGE_W_IN;
  const slideH = SLIDE_H_IN * px2in;

  const lum = c => { const s = c.map(v => { v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]; };
  const parse = s => { const m = (s || '').match(/[\d.]+/g);
    return m && m.length >= 3 ? m.slice(0, 3).map(Number) : null; };
  const alphaOf = s => { const m = (s || '').match(/[\d.]+/g);
    return m && m.length >= 4 ? Number(m[3]) : 1; };
  const bgOf = el => {
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const c = getComputedStyle(n).backgroundColor;
      if (alphaOf(c) > 0.05) { const p = parse(c); if (p) return p; }
    }
    return [255, 255, 255];
  };

  return [...document.querySelectorAll('.slide')].map((s, i) => {
    const sr = s.getBoundingClientRect();
    const titleEl = s.querySelector('h1, h2, .stitle');
    const notes = s.querySelector('.notes');

    // words that will be projected — speaker notes are deliberately excluded,
    // they are the presenter's script and are not on the slide
    const clone = s.cloneNode(true);
    clone.querySelectorAll('.notes').forEach(n => n.remove());
    const words = (clone.innerText || clone.textContent || '')
        .trim().split(/\s+/).filter(Boolean).length;
    const noteWords = notes
        ? (notes.innerText || notes.textContent || '').trim().split(/\s+/).filter(Boolean).length
        : 0;

    let minPt = 1e9, minSel = '';
    let worst = 99, worstSel = '';
    for (const el of s.querySelectorAll('*')) {
      if (el.closest('.notes')) continue;
      const st = getComputedStyle(el);
      if (st.display === 'none' || st.visibility === 'hidden') continue;
      let direct = false;
      for (const n of el.childNodes)
        if (n.nodeType === 3 && n.textContent.trim()) direct = true;
      if (!direct) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      const pt = parseFloat(st.fontSize) / px2in * 72;
      if (pt < minPt) { minPt = pt;
        minSel = el.tagName + ' :: ' + el.textContent.trim().slice(0, 36); }
      const fg = parse(st.color);
      if (fg) {
        const a = lum(fg), b = lum(bgOf(el));
        const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        if (ratio < worst) { worst = ratio;
          worstSel = el.tagName + ' :: ' + el.textContent.trim().slice(0, 36); }
      }
    }

    // figure area: count what is drawn, not the layout box — an
    // object-fit: contain image letterboxes and the box would flatter it
    let figArea = 0;
    for (const f of s.querySelectorAll('img, svg, canvas, [data-fig]')) {
      const r = f.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      let dw = r.width, dh = r.height;
      const nw = f.naturalWidth, nh = f.naturalHeight;
      if (nw && nh && getComputedStyle(f).objectFit === 'contain') {
        const k = Math.min(r.width / nw, r.height / nh);
        dw = nw * k; dh = nh * k;
      }
      figArea += dw * dh;
    }

    return {n: i + 1,
            title: titleEl ? (titleEl.innerText || titleEl.textContent)
                     .trim().replace(/\s+/g, ' ') : '',
            kind: (s.className || '').toString().replace('slide', '').trim(),
            words, noteWords,
            minPt: minPt === 1e9 ? null : minPt,
            minFrac: minPt === 1e9 ? null : (minPt / 72 * px2in) / slideH,
            minSel, contrast: worst === 99 ? null : worst, contrastSel: worstSel,
            figFrac: figArea / (sr.width * sr.height)};
  });
}
"""


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    root = Path(argv[0]).resolve()
    rest = [a for a in argv[1:] if not a.startswith("--")]
    titles_only = "--titles" in argv
    files = sorted((root / "html").glob("*.html"))
    if rest:
        files = [f for f in files if any(w in f.stem for w in rest)]
    if not files:
        raise SystemExit(f"no matching html in {root / 'html'}")

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 900})
        for f in files:
            m = PAGE_RE.search(f.read_text())
            if not m:
                raise SystemExit(f"{f.name}: no `@page {{ size: W H }}` rule found")
            w_in, h_in = float(m.group(1)), float(m.group(2))
            page.goto(f.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_timeout(400)
            js = JS.replace("PAGE_W_IN", str(w_in)).replace("SLIDE_H_IN", str(h_in))
            rows = page.evaluate(js)

            print(f"\n=== {f.stem}   {len(rows)} slides   {w_in}x{h_in}in")
            print("\n--- title track — read this alone; it should be the argument ---")
            for r in rows:
                mark = "  " if r["title"] else "??"
                print(f"{mark}{r['n']:>3}. {r['title'] or '(no title)'}")
            if titles_only:
                continue

            print(f"\n{'#':>3}  {'words':>5}{'scrpt':>6}{'minPt':>7}{'%h':>6}"
                  f"{'contrast':>10}{'fig%':>7}  flags")
            print("-" * 76)
            for r in rows:
                flag = ""
                if r["words"] > WORD_BUDGET:      flag += f" WORDY"
                if r["minPt"] and r["minPt"] < FLOOR_PT:    flag += " TYPE"
                if r["minFrac"] and r["minFrac"] < FLOOR_FRAC: flag += " TYPE%"
                if r["contrast"] and r["contrast"] < 3.0:  flag += " CONTRAST"
                if not r["title"]:                flag += " NO-TITLE"
                print(f"{r['n']:>3}  {r['words']:>5}{r['noteWords']:>6}"
                      f"{(r['minPt'] or 0):>7.1f}{(r['minFrac'] or 0)*100:>5.1f}%"
                      f"{(r['contrast'] or 0):>9.2f}:1{r['figFrac']*100:>6.0f}%  {flag}")
                if flag and "TYPE" in flag:
                    print(f"        smallest: {r['minSel']}")
                if flag and "CONTRAST" in flag:
                    print(f"        lowest contrast: {r['contrastSel']}")

            out = root / "qa"
            out.mkdir(parents=True, exist_ok=True)
            (out / f"audit_{f.stem}.json").write_text(json.dumps(rows, indent=2))
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
