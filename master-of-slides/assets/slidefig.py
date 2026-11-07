"""Slide figure style and emitters.

Every panel is authored at the size it will occupy on the slide, in inches, with
font sizes in real points — so a figure placed at its authored width has exactly
the type size declared here. Nothing is scaled after the fact, which matters more
on slides than anywhere else: a plate authored 12 in wide and shown at 7 in has
had all its type multiplied by 0.58, and no DOM audit will catch it because
figure text is drawn as paths.

The sizes below assume a 13.33 x 7.5 in canvas and a figure occupying roughly
7-11 in of it. The floor is ~16 pt, which is about 3% of slide height — the
point at which the back of a room stops being able to read an axis.

Colour comes from one palette (below) so that everything you make looks like it
belongs together. Which colour means what is yours to decide — it depends on the
data. `CYCLE` holds the members that stay distinguishable from each other, in a
sensible order for a categorical encoding; the pale tints are for fills, bands
and grounds, where separation matters less than not shouting.

Text is emitted as paths (``svg.fonttype='path'``) so the rendered PDF is
identical regardless of what fonts the rendering host has installed.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
OUTDIR = HERE.parent / "assets" / "figures"
# Cache whatever you recomputed for the deck next to this file and load it
# here. Recomputing inside a plotting function is how a deck ends up with a
# number the paper does not have.
DATA_PATH = HERE / "plotdata.json"
DATA = json.loads(DATA_PATH.read_text()) if DATA_PATH.exists() else {}

# ------------------------------------------------------------- the palette ---
# The full sheet. Draw from it; assign meaning to suit your data.
TERRA, TERRA_MID, TERRA_PALE = "#D56C55", "#E8B19D", "#F1D4C9"
BLUE,  BLUE_MID,  BLUE_PALE  = "#738FC1", "#A9BFE3", "#C9D7EE"
GREEN, GREEN_DEEP, GREEN_PALE = "#BFD598", "#7AA974", "#DCECCB"
PLUM,  PLUM_PALE  = "#AB85AC", "#D4C2D9"
GOLD,  SAND       = "#EAC264", "#F3DAA9"
SAGE,  UMBER      = "#7E9D90", "#905426"

# A default order for categorical series: the saturated members first, because
# they hold apart at small sizes and in print. Slice it, reorder it, or ignore
# it — `setup()` installs it as the matplotlib colour cycle so unstyled plots
# already look like the rest of your work.
CYCLE = [TERRA, BLUE, GREEN_DEEP, GOLD, PLUM, SAGE, UMBER, BLUE_MID]

# Convenient aliases for the very common two-group comparison. Nothing requires
# you to use them, and nothing stops you adding a third.
POS = TERRA          # e.g. the "more/positive/treatment" group
NEG = BLUE           # e.g. the "less/negative/control" group
ACCENT = UMBER      # chrome, and single-series points
INK = "#2E2A26"
MUTED = "#8A8078"
FAINT = "#C9C0B6"
CREAM = "#FFEDCE"
STONE = "#E3DCD0"

# ------------------------------------------------------------- type scale ---
FS_TICK = 17
FS_LABEL = 20
FS_ANNOT = 18
FS_PANEL = 26
FS_LEGEND = 18

FS_MIN = 16      # the back of the room stops reading below ~3% of slide height

LW = 2.4
CAP = 7


def fs(size):
    """Clamp any derived font size to the authored floor."""
    return max(size, FS_MIN)
MS = 18          # marker size in points


def setup():
    matplotlib.rcParams.update({
        "axes.prop_cycle": matplotlib.cycler(color=CYCLE),
        "svg.fonttype": "path",
        "pdf.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Nimbus Sans", "Liberation Sans", "DejaVu Sans"],
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.linewidth": 1.6,
        "xtick.major.width": 1.6,
        "ytick.major.width": 1.6,
        "xtick.major.size": 6,
        "ytick.major.size": 6,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "axes.labelsize": FS_LABEL,
        "legend.fontsize": FS_LEGEND,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.transparent": True,
    })


def stars(p):
    return ("****" if p < 1e-4 else "***" if p < 1e-3 else "**" if p < 1e-2
            else "*" if p < 0.05 else "NS")


def panel_letter(ax, letter):
    """Left-aligned to the axes, above it — never collides with the y-axis label."""
    ax.set_title(letter, loc="left", fontsize=FS_PANEL, fontweight="bold",
                 color=INK, pad=16)


def subtitle(ax, text, y=1.015):
    ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=fs(FS_ANNOT - 2), color=MUTED)


def legend(ax, loc="best", labels=(("Positive", POS), ("Negative", NEG)), **kw):
    ax.legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=c,
                              markersize=14, label=l) for l, c in labels],
              loc=loc, fontsize=FS_LEGEND, frameon=False, handletextpad=0.4,
              borderpad=0.2, labelspacing=0.3, **kw)


def sig_bracket(ax, x0, x1, y, h, text):
    ax.plot([x0, x0, x1, x1], [y, y + h, y + h, y], lw=2.5, color=INK,
            solid_capstyle="round")
    ax.text((x0 + x1) / 2, y + h * 1.05, text, ha="center", va="bottom",
            fontsize=FS_ANNOT + 3, fontweight="bold", color=INK)


def two_point(ax, neg, pos, ref, ylab, p, xlabels=("Negative", "Positive")):
    """Two group means with SE bars, a reference line and a significance bracket.

    The workhorse comparison panel. `p` is a p-value; it is rendered as a star
    symbol rather than printed, because a poster reports significance by symbol
    and explains the symbols once in the caption — see references/content-rules.md.
    """
    pts = []
    for x, (m, se, _n), c in ((0, neg, NEG), (1, pos, POS)):
        ax.scatter([x], [m], s=260, color=c, zorder=3, clip_on=False)
        ax.errorbar([x], [m], yerr=[se], fmt="none", ecolor=INK, capsize=CAP,
                    elinewidth=LW, capthick=LW, zorder=2)
        pts.append((m, se))
    ax.axhline(ref, color=MUTED, ls=(0, (5, 5)), lw=2.2, alpha=0.85, zorder=0)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(list(xlabels))
    ax.set_xlim(-0.62, 1.62)
    lo = min([m - s for m, s in pts] + [ref])
    hi = max([m + s for m, s in pts] + [ref])
    span = hi - lo
    by, bh = hi + span * 0.22, span * 0.09
    sig_bracket(ax, 0, 1, by, bh, stars(p))
    ax.set_ylim(lo - span * 0.40, by + bh + span * 0.52)
    ax.set_ylabel(ylab, fontsize=FS_LABEL)
    return ax


# ====================================================== reusable panel bits ==


# ================================================================ emitters ==
def emit(name, panels, figsize, letters=True):
    """Compose panels left-to-right into one figure and write SVG + PDF + PNG."""
    setup()
    fig, axes = plt.subplots(1, len(panels), figsize=figsize)
    axes = np.atleast_1d(axes)
    for i, (ax, fn) in enumerate(zip(axes, panels)):
        fn(ax)
        if letters and len(panels) > 1:
            panel_letter(ax, "ABCDEFGH"[i])
    # tight_layout alone — a prior subplots_adjust fights it and clips outer labels
    fig.tight_layout(pad=0.9, w_pad=3.4)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf"):
        fig.savefig(OUTDIR / f"{name}.{ext}", bbox_inches="tight",
                    pad_inches=0.12, transparent=True)
    fig.savefig(OUTDIR / f"{name}.png", bbox_inches="tight",
                pad_inches=0.12, transparent=True, dpi=200)
    plt.close(fig)
    print(f"  {name}.svg  {figsize[0]}x{figsize[1]} in")


def emit_stack(name, panels, figsize, letters=True):
    """Stack panels vertically. A tall, narrow figure fills a poster column
    without letterboxing, which a wide two-panel figure cannot do — and it lets
    a column carry two ideas in one figure slot."""
    setup()
    fig, axes = plt.subplots(len(panels), 1, figsize=figsize)
    axes = np.atleast_1d(axes)
    for i, (ax, fn) in enumerate(zip(axes, panels)):
        fn(ax)
        if letters and len(panels) > 1:
            panel_letter(ax, "ABCDEFGH"[i])
    fig.tight_layout(pad=0.9, h_pad=3.2)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf"):
        fig.savefig(OUTDIR / f"{name}.{ext}", bbox_inches="tight",
                    pad_inches=0.12, transparent=True)
    fig.savefig(OUTDIR / f"{name}.png", bbox_inches="tight",
                pad_inches=0.12, transparent=True, dpi=200)
    plt.close(fig)
    print(f"  {name}.svg  {figsize[0]}x{figsize[1]} in  (stacked)")


def emit_grid(name, panels, figsize, ncols=2, letters=True):
    """Lay panels out on a grid — for the slide where the comparison across
    panels *is* the point. Otherwise split the panels across slides, one claim
    each (see references/figures-and-numbers.md)."""
    setup()
    nrows = -(-len(panels) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = np.atleast_1d(axes).ravel()
    for i, (ax, fn) in enumerate(zip(axes, panels)):
        fn(ax)
        if letters:
            panel_letter(ax, "ABCDEFGH"[i])
    for ax in axes[len(panels):]:
        ax.set_visible(False)
    fig.tight_layout(pad=0.9, w_pad=3.4, h_pad=3.0)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf"):
        fig.savefig(OUTDIR / f"{name}.{ext}", bbox_inches="tight",
                    pad_inches=0.12, transparent=True)
    fig.savefig(OUTDIR / f"{name}.png", bbox_inches="tight",
                pad_inches=0.12, transparent=True, dpi=200)
    plt.close(fig)
    print(f"  {name}.svg  {figsize[0]}x{figsize[1]} in  ({nrows}x{ncols} grid)")
