"""Build preview/contact_sheet.png — every poster in a build side by side,
labelled with its size and audit numbers.

Thumbnails are scaled to a common HEIGHT so sheets of different aspect ratios
(1:1, 1:1.5, A0) sit on a shared baseline and their real proportions stay
visible. Useful when a build carries several variants and the user is choosing.

    python contact_sheet.py <build-dir> [--title "Poster variants, round 3"]

Reads `<build-dir>/pdf/*.pdf` (run render.py first) and, when present, the
numbers audit.py left in `<build-dir>/qa/audit_*.json`. Needs Pillow, which
the shared environment already has as a matplotlib dependency.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

THUMB_H = 900
PAD, LABEL_H, HEAD_H, COLS = 26, 78, 70, 2
BG, INK, MUTED, HAIR = "#FFFFFF", "#2E2A26", "#8A8078", "#C9C0B6"


def font(font_dir, size, bold=False):
    """The poster's own face if the build pinned one, else Pillow's default."""
    name = "NimbusSans-Bold.otf" if bold else "NimbusSans-Regular.otf"
    try:
        return ImageFont.truetype(str(font_dir / name), size)
    except OSError:
        pass
    try:
        return ImageFont.load_default(size=size)       # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def load_audit(root):
    """Merge whatever per-poster audit files exist."""
    out = {}
    for f in (root / "qa").glob("audit_*.json"):
        try:
            for r in json.loads(f.read_text()):
                out[r["name"]] = r
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build_dir")
    ap.add_argument("--title", help="heading for the sheet (default: the build "
                                    "folder's name and the poster count)")
    args = ap.parse_args(argv)

    root = Path(args.build_dir).resolve()
    pdf_dir, preview = root / "pdf", root / "preview"
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"no PDFs in {pdf_dir} — run render.py first")
    audit = load_audit(root)
    fonts = root / "assets" / "fonts"
    preview.mkdir(parents=True, exist_ok=True)

    thumbs = []
    for p in pdfs:
        png = preview / f"{p.stem}.png"
        if not png.exists():
            subprocess.run(["pdftoppm", "-png", "-r", "40", "-singlefile",
                            str(p), str(preview / p.stem)], check=True)
        im = Image.open(png).convert("RGB")
        im = im.resize((max(1, round(im.width * THUMB_H / im.height)), THUMB_H),
                       Image.LANCZOS)
        thumbs.append((p.stem, im))

    cell_w = max(im.width for _, im in thumbs) + PAD * 2
    cell_h = THUMB_H + LABEL_H + PAD * 2
    cols = min(COLS, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows + HEAD_H), BG)
    d = ImageDraw.Draw(sheet)
    n = len(thumbs)
    title = args.title or f"{root.name} · {n} poster{'s' if n != 1 else ''}"
    d.text((PAD, 20), title, font=font(fonts, 30, True), fill=INK)

    for i, (name, im) in enumerate(thumbs):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h + HEAD_H
        x = cx + (cell_w - im.width) // 2
        y = cy + PAD
        d.rectangle([x - 2, y - 2, x + im.width + 1, y + im.height + 1],
                    outline=HAIR, width=2)
        sheet.paste(im, (x, y))
        d.text((x, y + im.height + 12), name, font=font(fonts, 26, True), fill=INK)
        a = audit.get(name, {})
        if a:
            d.text((x, y + im.height + 44),
                   f"{a.get('size', '')}  ·  figures {a.get('figFrac', 0) * 100:.0f}%"
                   f"  ·  {a.get('words', '?')} words",
                   font=font(fonts, 22), fill=MUTED)
    out = preview / "contact_sheet.png"
    sheet.save(out)
    print(f"wrote {out}  ({sheet.width}x{sheet.height}px, {n} poster"
          f"{'s' if n != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
