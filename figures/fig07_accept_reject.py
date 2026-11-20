"""Draw figures/fig07_accept_reject.svg: the compatibility rule for one candidate author, framed by the two method
questions. A cartoon: real scores are skewed, not bell-shaped.

A text is not compatible with author A if it looks less like A than 90% of A's own writing that the model never
saw. The line is set from A's own unseen writing alone.
  Q1  Given an author A the model was trained on, is A's unseen work accepted as compatible with A?
      About 90% by construction; Smith's held-out documents, from results/dev_ranks_F2.parquet (step 5).
  Q2  Given an author B the model never saw, is B's writing declined as not compatible with A?
      Not fixed by the rule: it depends on how far B's writing sits from A's. Accepted as Smith: Cowdery and
      Hamilton with their class removed (same file). The curves are placed to match those rates.

Run: python figures/fig07_accept_reject.py
"""
from html import escape
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import norm

from palette import GREY, GREY_PALE, INK, INK2, RULE, SURF

ERROR = GREY                                     # the share the line gets wrong, in both panels
FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, M = 1000, 40
PANEL_H = 430
X0, X1 = 70, 930                                 # z from Z_MIN to Z_MAX maps to X0..X1
Z_MIN, Z_MAX, CUT = -3.2, 7.6, 1.2816            # CUT: 90th percentile of A's own unseen writing (standard normal)
ROOT = Path(__file__).resolve().parents[1]
ranks = (pl.read_parquet(ROOT / "results/dev_ranks_F2.parquet")
         .filter(pl.col("class") == "Joseph Smith")
         .with_columns((pl.col("rank") > 0.10).alias("ok")))
unit_rate = lambda df: float(df.group_by("unit_id").agg(pl.col("ok").mean())["ok"].mean())
OWN = unit_rate(ranks.filter((pl.col("group") == "same_author") & (pl.col("klass") == "Joseph Smith")))
COWDERY = unit_rate(ranks.filter((pl.col("group") == "removed_author") & (pl.col("klass") == "Oliver Cowdery")))
HAMILTON = unit_rate(ranks.filter((pl.col("group") == "removed_author") & (pl.col("klass") == "Hamilton")))
NEAR = CUT - norm.ppf(COWDERY)                   # outsiders' centres, placed so their share left of the line matches
FAR = 4.9 if HAMILTON < 0.005 else CUT - norm.ppf(HAMILTON)
out = []

px = lambda z: X0 + (z - Z_MIN) / (Z_MAX - Z_MIN) * (X1 - X0)


def text(x, y, s, size=13, color=INK, weight=400, anchor="start", lh=None):
    lines = s if isinstance(s, list) else [s]
    lh = lh or round(size * 1.38)
    sp = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(t)}</tspan>' for i, t in enumerate(lines))
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{sp}</text>')


def arrow(x1, y1, x2, y2):
    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK2}" stroke-width="1.5" '
               f'marker-end="url(#ah)"/>')


class Panel:
    def __init__(self, top, label, question):
        self.top, self.base, self.peak = top, top + 330, top + 140
        out.append(f'<rect x="{M}" y="{top}" width="30" height="24" rx="5" fill="{INK}"/>')
        text(M + 15, top + 17, label, 13, "#ffffff", 700, "middle")
        text(M + 42, top + 18, question, 16, INK, 650)
        # the line, and the two sides it makes
        cx = px(CUT)
        out.append(f'<line x1="{cx:.1f}" y1="{top + 52}" x2="{cx:.1f}" y2="{self.base}" stroke="{INK}" '
                   f'stroke-width="1.5" stroke-dasharray="5 4"/>')
        text(cx - 12, top + 72, "Compatible with A  ←", 13, INK, 700, "end")
        text(cx + 12, top + 72, "→  Not compatible with A", 13, INK, 700)
        text(cx, top + 48, "The line: 90% of A's own unseen writing is to its left", 12, INK2, anchor="middle")

    def y(self, z, mu=0.0):
        return self.base - np.exp(-(z - mu) ** 2 / 2) * (self.base - self.peak)

    def fill(self, z_from, z_to, color, mu=0.0, opacity=1.0):
        zs = np.linspace(max(z_from, Z_MIN), min(z_to, Z_MAX), 160)
        pts = " ".join(f"{px(z):.1f},{self.y(z, mu):.1f}" for z in zs)
        out.append(f'<polygon points="{px(zs[0]):.1f},{self.base} {pts} {px(zs[-1]):.1f},{self.base}" fill="{color}" '
                   f'fill-opacity="{opacity}"/>')

    def curve(self, mu=0.0, color=INK, width=2.0, dash=None):
        zs = np.linspace(Z_MIN, Z_MAX, 400)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline fill="none" stroke="{color}" stroke-width="{width}"{d} points="'
                   + " ".join(f"{px(z):.1f},{self.y(z, mu):.1f}" for z in zs) + '"/>')

    def axis(self):
        out.append(f'<line x1="{X0}" y1="{self.base}" x2="{X1}" y2="{self.base}" stroke="{INK}" stroke-width="1.2"/>')
        text(X0, self.base + 24, "← looks more like A", 12.5, INK2)
        text(X1, self.base + 24, "looks less like A →", 12.5, INK2, anchor="end")
        text((X0 + X1) / 2, self.base + 24, "Score: how unlike A a text looks", 12.5, INK, 600, "middle")


# ---------------------------------------------------------------- page
text(M, 36, "Two questions, one line", 20, INK, 700)
text(M, 58, "For each candidate author A, the line is set from A's own writing that the model never saw. "
            "Each curve is a body of writing.", 13, INK2)

# Q1: A's own unseen work
a = Panel(84, "Q1", "Is unseen work by an author the model knows accepted as compatible with that author?")
a.fill(Z_MIN, CUT, GREY_PALE)
a.fill(CUT, Z_MAX, ERROR, opacity=0.6)
a.curve()
a.axis()
lx = px(4.1)                                       # notes sit in the open space right of the curve
text(lx, a.peak + 20, ["A's own unseen work: about 90%", "compatible with A, by design"], 13, INK, 600, "middle", lh=18)
text(lx, a.peak + 60, f"Smith's held-out documents: {OWN:.0%}", 12.5, INK2, anchor="middle")
arrow(lx - 120, a.peak + 50, px(-0.2), a.y(-0.2) + 40)
text(lx, a.peak + 125, ["About 10% of A's own work is not", "compatible: the cost of the line"], 12.5, INK2, anchor="middle", lh=17)
arrow(lx - 110, a.peak + 140, px(1.7), a.base - 12)

# Q2: authors the model never saw
b = Panel(84 + PANEL_H, "Q2", "Is an author the model never saw declined as not compatible with A?")
b.curve(color=RULE, width=1.5, dash="5 4")
text(px(0) - 16, b.peak - 8, "A's own unseen work", 12, INK2, anchor="end")
b.fill(Z_MIN, CUT, ERROR, mu=NEAR, opacity=0.6)
b.curve(mu=NEAR, color=INK)
b.curve(mu=FAR, color=INK)
b.axis()
text(px(NEAR) + 14, b.peak - 26, "A close author", 13, INK, 600)
text(px(NEAR) + 14, b.peak - 9, f"e.g. Cowdery vs. Smith: {COWDERY:.0%}", 12.5, INK2)
text(px(FAR), b.peak - 26, "A distant author", 13, INK, 600, "middle")
text(px(FAR), b.peak - 9, f"e.g. Hamilton vs. Smith: {HAMILTON:.0%}", 12.5, INK2, anchor="middle")
nx, ny = px(-2.4), b.base - 80
text(nx, ny, ["Mistaken as", "compatible with A"], 12.5, INK, 600, "middle", lh=17)
arrow(nx + 20, ny + 24, px(0.5), b.base - 40)

text(M, 84 + 2 * PANEL_H - 22, "Q1's answer is fixed by where the line is drawn. Q2's is not: it depends on how far "
     "the outsider's writing sits from A's, which is what the test measures.", 12.5, INK2)
H = 84 + 2 * PANEL_H - 2

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="{SURF}"/>'
       f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
       f'<path d="M0,0 L10,5 L0,10 Z" fill="{INK2}"/></marker></defs>' + "".join(out) + "</svg>")
path = Path(__file__).with_name("fig07_accept_reject.svg")
path.write_text(svg)
print("wrote", path, f"({W}x{H})")
