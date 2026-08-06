"""Rasterize an SVG through Chromium — the same engine that renders the posters —
so a figure check never disagrees with the printed result.

    python .../qa/svgcheck.py assets/figures/G0_interaction.svg out.png [scale]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.4
html = f"""<!DOCTYPE html><meta charset=utf-8>
<style>html,body{{margin:0;padding:0;background:#fff}} img{{display:block}}</style>
<img src="{src.as_uri()}">"""
tmp = out.with_suffix(".probe.html")
tmp.write_text(html)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(device_scale_factor=scale)
    pg.goto(tmp.as_uri(), wait_until="networkidle")
    pg.wait_for_timeout(300)
    box = pg.evaluate("""() => {const i=document.images[0];
        return {w: i.clientWidth, h: i.clientHeight};}""")
    pg.set_viewport_size({"width": max(box["w"], 10), "height": max(box["h"], 10)})
    pg.wait_for_timeout(150)
    pg.screenshot(path=str(out))
    b.close()
tmp.unlink(missing_ok=True)
print(f"{out}  ({box['w']}x{box['h']} css px at {scale}x)")
