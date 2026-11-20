"""Draw figures/fig03_open_set.svg: why an attribution must be open-set (Schaalje et al. 2011).

Schematic, with made-up points: two candidates' own texts and the Book of Mormon, in a two-feature space.
  A  closed set: the text is assigned to the nearest candidate, however far away it is
  B  open set: the text must sit as close to a candidate as that candidate's own texts do

Run: python figures/fig03_open_set.py
"""
from html import escape
from pathlib import Path

import numpy as np

from palette import GREY, GREY_DARK, INK, INK2, RULE, SURF

STYLE = {"A": (GREY_DARK, "circle"), "B": (GREY, "square")}   # generic candidates: neutral, told apart by shape
FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, H, M = 1200, 570, 40
out = []

# ---------------------------------------------------------------- made-up data, in unit coordinates
rng = np.random.default_rng(7)
centre = {"A": np.array([0.30, 0.66]), "B": np.array([0.72, 0.62])}
own = {k: c + rng.normal(scale=0.055, size=(30, 2)) for k, c in centre.items()}
target = np.array([0.40, 0.14])
dist = {k: np.linalg.norm(own[k] - own[k].mean(0), axis=1) for k in own}
ring = {k: float(np.quantile(dist[k], 0.90)) for k in own}               # 90% of the candidate's own texts
t_dist = {k: float(np.linalg.norm(target - own[k].mean(0))) for k in own}
assert t_dist["A"] < t_dist["B"], "the target should be nearer A"


def text(x, y, s, size=13, color=INK, weight=400, anchor="start", lh=None):
    lines = s if isinstance(s, list) else [s]
    lh = lh or round(size * 1.38)
    sp = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(t)}</tspan>' for i, t in enumerate(lines))
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{sp}</text>')


def heading(x, y, letter, title, sub):
    out.append(f'<circle cx="{x + 11}" cy="{y - 5}" r="11" fill="{INK}"/>')
    text(x + 11, y, letter, 13, "#ffffff", 700, "middle")
    text(x + 30, y, title, 16, INK, 650)
    text(x + 30, y + 22, sub, 13, INK2)


def diamond(x, y):
    out.append(f'<path d="M {x} {y - 9} L {x + 9} {y} L {x} {y + 9} L {x - 9} {y} Z" fill="{INK}" '
               f'stroke="{SURF}" stroke-width="2"/>')


def scatter(x0, y0, size, open_set: bool):
    """One feature-space panel, unlabelled. Unit coordinates map to a size x size square at (x0, y0)."""
    px = lambda p: (x0 + p[0] * size, y0 + (1 - p[1]) * size)
    out.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="none" stroke="{RULE}"/>')
    for k, (color, shape) in STYLE.items():
        if open_set:
            cx, cy = px(own[k].mean(0))
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ring[k] * size:.1f}" fill="{color}" '
                       f'fill-opacity="0.08" stroke="{color}" stroke-width="2" stroke-dasharray="6 4"/>')
        for p in own[k]:
            mark(*px(p), color, shape)
    tx, ty = px(target)
    if not open_set:                       # the closed-set assignment: an arrow to the nearest candidate
        c = own["A"].mean(0)
        ax, ay = px(c + (target - c) / np.linalg.norm(target - c) * (ring["A"] + 0.03))
        out.append(f'<line x1="{tx:.1f}" y1="{ty - 10:.1f}" x2="{ax:.1f}" y2="{ay:.1f}" stroke="{INK}" '
                   f'stroke-width="2" marker-end="url(#ah)"/>')
    diamond(tx, ty)


def mark(x, y, color, shape):
    if shape == "circle":
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="{SURF}" stroke-width="2"/>')
    else:
        out.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{color}" stroke="{SURF}" '
                   f'stroke-width="2"/>')


def legend(x, y):
    """One row identifying the marks, since the panels carry no labels."""
    items = [("A", None, "Candidate A's own texts"), ("B", None, "Candidate B's own texts"),
             ("diamond", INK, "Book of Mormon"), ("ring", INK2, "90% of a candidate's own texts")]
    for kind, color, label in items:
        if kind in STYLE:
            mark(x, y - 4, *STYLE[kind])
        elif kind == "diamond":
            diamond(x, y - 4)
        else:
            out.append(f'<circle cx="{x}" cy="{y - 4}" r="8" fill="none" stroke="{color}" stroke-width="2" '
                       f'stroke-dasharray="4 3"/>')
        text(x + 16, y, label, 13, INK2)
        x += 34 + len(label) * 7.2


# ---------------------------------------------------------------- page
out.append(f'<rect width="{W}" height="{H}" fill="{SURF}"/>')
out.append(f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 Z" fill="{INK}"/></marker></defs>')
text(M, 34, "Closed set against open set: the same text, two rules", 20, INK, 700)

size, top = 380, 120
heading(M, 80, "A", "Closed set (Jockers et al. 2008)", "Every text goes to the nearest candidate, however far away.")
scatter(M + 30, top, size, open_set=False)
heading(W / 2 + 10, 80, "B", "Open set (Schaalje et al. 2011)",
        "The text must be as close to a candidate as that candidate's own texts are.")
scatter(W / 2 + 40, top, size, open_set=True)
legend(M + 30, top + size + 40)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="{FONT}">' + "".join(out) + "</svg>")
path = Path(__file__).with_name("fig03_open_set.svg")
path.write_text(svg)
print("wrote", path)
