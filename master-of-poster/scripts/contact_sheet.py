"""Build preview/contact_sheet.png — all ten posters side by side, labelled.

Thumbnails are scaled to a common HEIGHT so the 1:1 and 1:1.5 variants sit on a
shared baseline and their real proportions stay visible.

    source venv/bin/activate
    python revision_display/poster_build/qa/contact_sheet.py
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
PDF, PREVIEW = ROOT / "pdf", ROOT / "preview"
THUMB_H = 900
PAD, LABEL_H, COLS = 26, 78, 2
BG, INK, MUTED, ACCENT = "#FFFFFF", "#2E2A26", "#8A8078", "#905426"
FONT_DIR = ROOT / "assets" / "fonts"


def _font(size, bold=False):
    f = FONT_DIR / ("NimbusSans-Bold.otf" if bold else "NimbusSans-Regular.otf")
    try:
        return ImageFont.truetype(str(f), size)
    except Exception:
        return ImageFont.load_default()


def load_audit():
    """Merge whatever per-poster audit files exist."""
    out = {}
    for f in (ROOT / "qa").glob("audit_*.json"):
        try:
            for r in json.loads(f.read_text()):
                out[r["name"]] = r
        except Exception:
            continue
    return out


def main():
    pdfs = sorted(PDF.glob("poster_*.pdf"))
    if not pdfs:
        raise SystemExit("no PDFs in pdf/ — run qa/render.py first")
    audit = load_audit()

    thumbs = []
    for p in pdfs:
        png = PREVIEW / f"{p.stem}.png"
        if not png.exists():
            subprocess.run(["pdftoppm", "-png", "-r", "40", "-singlefile",
                            str(p), str(PREVIEW / p.stem)], check=True)
        im = Image.open(png).convert("RGB")
        im = im.resize((max(1, round(im.width * THUMB_H / im.height)), THUMB_H),
                       Image.LANCZOS)
        thumbs.append((p.stem, im))

    cell_w = max(im.width for _, im in thumbs) + PAD * 2
    cell_h = THUMB_H + LABEL_H + PAD * 2
    rows = (len(thumbs) + COLS - 1) // COLS
    sheet = Image.new("RGB", (cell_w * COLS, cell_h * rows + 70), BG)
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 20), "“The strength of weird ties” · Sun & McCandlish   ·   v2 suite: "
           "6 posters at three aspect ratios, manuscript figure order",
           font=_font(30, True), fill=INK)

    for i, (name, im) in enumerate(thumbs):
        cx, cy = (i % COLS) * cell_w, (i // COLS) * cell_h + 70
        x = cx + (cell_w - im.width) // 2
        y = cy + PAD
        d.rectangle([x - 2, y - 2, x + im.width + 1, y + im.height + 1],
                    outline="#C9C0B6", width=2)
        sheet.paste(im, (x, y))
        a = audit.get(name, {})
        d.text((x, y + im.height + 12), name.replace("poster_", "Poster "),
               font=_font(26, True), fill=INK)
        if a:
            d.text((x, y + im.height + 44),
                   f"{a.get('size','')}  ·  figures {a.get('figFrac',0)*100:.0f}%"
                   f"  ·  {a.get('words','?')} words",
                   font=_font(22), fill=MUTED)
    out = PREVIEW / "contact_sheet.png"
    sheet.save(out)
    print(f"wrote {out}  ({sheet.width}x{sheet.height}px, {len(thumbs)} posters)")


if __name__ == "__main__":
    main()
