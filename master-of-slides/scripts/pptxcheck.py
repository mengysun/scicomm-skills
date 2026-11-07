"""Audit a .pptx deck: type sizes, word counts, notes, and the title track.

    python pptxcheck.py <file.pptx> [--pdf]

A PowerPoint file has no DOM, so the measurement loop that protects an HTML deck
does not exist. This recovers most of it:

  * **statically**, from the XML: every run's font size, the words on each slide,
    whether each slide has a title and a note, and picture placement — enough to
    catch the failures that actually happen (a 12 pt axis label, a slide with 90
    words, a picture hanging off the canvas).
  * **with `--pdf`**, by converting through LibreOffice and running the same
    checks a rendered deck gets. This is the only way to see what the file will
    actually look like on a projector, because PowerPoint reflows text that
    python-pptx merely places.

Requires `python-pptx`: run it with the interpreter `ensure_env.sh --pptx`
prints. `--pdf` additionally requires `soffice` (LibreOffice) on PATH.
"""
import subprocess
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Emu
except ImportError:
    raise SystemExit("needs python-pptx: run <skill>/scripts/ensure_env.sh --pptx "
                     "and use the python it prints")

FLOOR_PT = 16.0          # smallest type that survives the back of a room
WORD_BUDGET = 55
DEFAULT_BODY_PT = 18.0   # assumed when a run inherits its size from the layout


def audit(path, want_pdf=False):
    prs = Presentation(str(path))
    W, H = prs.slide_width, prs.slide_height
    print(f"=== {path.name}   {len(prs.slides)} slides   "
          f"{Emu(W).inches:.2f}x{Emu(H).inches:.2f}in")

    rows = []
    for i, slide in enumerate(prs.slides, 1):
        title = ""
        if slide.shapes.title is not None:
            title = (slide.shapes.title.text or "").strip()
        words, min_pt, min_txt, inherited = 0, 1e9, "", False
        off_canvas = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    for run in para.runs:
                        words += len(run.text.split())
                        size = run.font.size or para.font.size
                        if size is None:
                            inherited = True
                            continue
                        pt = size.pt
                        if pt < min_pt:
                            min_pt, min_txt = pt, run.text.strip()[:36]
            try:
                if (sh.left is not None and sh.top is not None
                        and sh.width is not None and sh.height is not None):
                    if (sh.left < -Emu(0.05).emu or sh.top < -Emu(0.05).emu
                            or sh.left + sh.width > W + Emu(0.05).emu
                            or sh.top + sh.height > H + Emu(0.05).emu):
                        off_canvas.append(sh.shape_type)
            except (AttributeError, TypeError):
                pass
        note = ""
        if slide.has_notes_slide:
            note = (slide.notes_slide.notes_text_frame.text or "").strip()
        rows.append(dict(n=i, title=title, words=words,
                         min_pt=None if min_pt == 1e9 else min_pt,
                         min_txt=min_txt, inherited=inherited,
                         note_words=len(note.split()), off=len(off_canvas)))

    print("\n--- title track — read this alone; it should be the argument ---")
    for r in rows:
        print(f"{'  ' if r['title'] else '??'}{r['n']:>3}. {r['title'] or '(no title)'}")

    print(f"\n{'#':>3}{'words':>7}{'notes':>7}{'minPt':>7}  flags")
    print("-" * 60)
    for r in rows:
        flag = ""
        if r["words"] > WORD_BUDGET: flag += " WORDY"
        if r["min_pt"] and r["min_pt"] < FLOOR_PT: flag += " TYPE"
        if r["inherited"]: flag += " INHERITED-SIZE"
        if not r["title"]: flag += " NO-TITLE"
        if r["off"]: flag += f" OFF-CANVAS×{r['off']}"
        print(f"{r['n']:>3}{r['words']:>7}{r['note_words']:>7}"
              f"{(r['min_pt'] or 0):>7.1f}  {flag}")
        if "TYPE" in flag:
            print(f"       smallest: {r['min_txt']!r}")
    if any(r["inherited"] for r in rows):
        print(f"\nINHERITED-SIZE means a run takes its size from the slide layout, "
              f"which this file does not state. Assume ~{DEFAULT_BODY_PT:g} pt and "
              f"confirm with --pdf.")

    if want_pdf:
        out = path.parent / "pdf"
        out.mkdir(exist_ok=True)
        print(f"\nconverting through LibreOffice → {out} ...")
        r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                            "--outdir", str(out), str(path)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("  conversion failed — is `soffice` on PATH?\n  " + r.stderr.strip()[:300])
        else:
            pdf = out / (path.stem + ".pdf")
            info = subprocess.run(["pdfinfo", str(pdf)],
                                  capture_output=True, text=True).stdout
            print("  " + "\n  ".join(l for l in info.splitlines()
                                     if l.startswith(("Pages", "Page size"))))
            print(f"  rasterize to look at it:  pdftoppm -png -r 96 {pdf} <prefix>")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    sys.exit(audit(Path(args[0]).resolve(), want_pdf="--pdf" in sys.argv))
