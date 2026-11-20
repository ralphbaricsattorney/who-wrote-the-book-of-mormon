"""Draw figures/fig06_study_partition.svg: how each study held text back from its model. Schematic.

Each row shows one study's known-author text as works (separated by gaps) cut into the pieces the study used.
Hollow pieces are the ones held out in one cross-validation fold.
  Jockers et al. 2008   passages split at random (paper, section 4), so a work's passages fall on both sides
  Schaalje et al. 2011  cross-validation over blocks (fold scheme not reported); a single manuscript, such as
                        Spalding's seven blocks, necessarily falls on both sides
  RBA's Analysis        folds take whole documents; an author with few long works has each work cut into
                        contiguous blocks with a 1,000-word gap (pipeline/openset_partition.py)

Run: python figures/fig06_study_partition.py
"""
from html import escape
from pathlib import Path

from palette import BAND, GREY_DARK, GREY_LIGHT, GREY_PALE, INK, INK2, SURF, TARGET

FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, M = 1200, 40
LEFT_W = 250                      # study names
BAR_X, BAR_W, BAR_H = M + LEFT_W + 10, 400, 34
OUT_X = BAR_X + BAR_W + 70        # what is scored after training
ROW_H = 158
out = []


def text(x, y, s, size=13, color=INK, weight=400, anchor="start", lh=None):
    lines = s if isinstance(s, list) else [s]
    lh = lh or round(size * 1.4)
    sp = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(t)}</tspan>' for i, t in enumerate(lines))
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{sp}</text>')


def rect(x, y, w, h, fill, stroke="none", width=1.5, rx=3):
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{rx}" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="{width}"/>')


def arrow(x1, y, x2):
    out.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK2}" stroke-width="1.5" marker-end="url(#ah)"/>')


def works_bar(y, works, held, width=BAR_W, whole=False):
    """Works side by side; work i is cut into works[i] pieces. `held`: (work, piece) pairs held out in one fold.
    With whole=True a work is drawn as one piece and held out entirely."""
    gap, x = 6, BAR_X
    unit = (width - gap * (len(works) - 1)) / sum(works)
    for i, n in enumerate(works):
        for j in range(n):
            out_fold = (i, j) in held or (whole and (i, 0) in held)
            px = x + j * unit
            if out_fold:
                rect(px + 1.5, y + 1.5, unit - 3, BAR_H - 3, SURF, GREY_DARK, 2.5, 2)
            else:
                rect(px + 1, y, unit - 2, BAR_H, GREY_PALE, GREY_LIGHT, 1, 2)
        x += n * unit + gap


def bom(x, y, w, caption):
    rect(x, y, w, BAR_H, TARGET)
    text(x + w / 2, y + BAR_H / 2 + 5, "Book of Mormon", 13, "#ffffff", 650, "middle")
    text(x, y + BAR_H + 20, caption, 12.5, INK2, lh=17)


# ---------------------------------------------------------------- page
text(M, 36, "How each study held text back from its model", 20, INK, 700)
text(M, 58, "Each box is a piece of known-author text; gaps separate works. Filled: trained on. Hollow: held out of "
            "training in one cross-validation round.", 13, INK2)
y0 = 86

rows = [
    ("Jockers et al. 2008", ["Closed set: every chapter", "goes to the nearest author"]),
    ("Schaalje et al. 2011", ["Open set: nearest author,", "or \"an unobserved author\""]),
    ("RBA's Analysis", ["Open set: as close to an author", "as that author's own texts, or none"]),
]
for r, (name, rule) in enumerate(rows):
    y = y0 + r * ROW_H
    if r % 2:
        rect(M, y, W - 2 * M, ROW_H, BAND, rx=0)
    text(M + 10, y + 38, name, 16, INK, 700)
    text(M + 10, y + 60, rule, 12.5, INK2, lh=17)

# Jockers: passages split at random
y = y0 + 22
text(BAR_X, y - 6 + 12, "Known-author text, cut into passages of 100 to 18,000 words", 12.5, INK, 600)
works_bar(y + 16, [6, 4, 6, 4], {(0, 1), (0, 4), (1, 2), (2, 0), (2, 3), (3, 1)})
text(BAR_X, y + 16 + BAR_H + 22, ["Passages are split at random, so passages of one work sit on both sides",
                                  "of the split: the error rate is measured on works the model has partly seen."],
     12.5, INK2, lh=17)
arrow(BAR_X + BAR_W + 12, y + 16 + BAR_H / 2, OUT_X - 10)
bom(OUT_X, y + 16, 180, ["Each chapter goes to the nearest", "author. Nothing checks whether it", "resembles any of them."])

# Schaalje: blocks, cross-validated
y = y0 + ROW_H + 22
text(BAR_X, y + 6, "Known-author text, joined into blocks of 2,100 to 8,700 words", 12.5, INK, 600)
works_bar(y + 16, [5, 3, 7, 3], {(0, 3), (1, 0), (2, 2), (2, 5), (3, 1)})
text(BAR_X, y + 16 + BAR_H + 22, ["Cross-validation over blocks (fold scheme not reported). Spalding's one",
                                  "manuscript is 7 blocks, so it cannot avoid sitting on both sides."],
     12.5, INK2, lh=17)
arrow(BAR_X + BAR_W + 12, y + 16 + BAR_H / 2, OUT_X - 10)
bom(OUT_X, y + 16, 180, ["Nearest author, or \"unobserved\"", "if it fits none of them."])
rect(OUT_X + 200, y + 16, 150, BAR_H, SURF, GREY_DARK, 2.5)
text(OUT_X + 275, y + 16 + BAR_H / 2 + 5, "Hamilton papers", 13, INK, 650, "middle")
text(OUT_X + 200, y + 16 + BAR_H + 20, ["A separate demonstration:", "an outsider the method", "should reject."], 12.5, INK2, lh=17)

# RBA's Analysis: whole documents, then an audit set, then the target once
y = y0 + 2 * ROW_H + 22
dev_w = 300
text(BAR_X, y + 6, "Development text, in 1,000-word chunks", 12.5, INK, 600)
works_bar(y + 16, [2, 3, 1, 2, 4, 2, 1], {(1, 0), (4, 0)}, width=dev_w, whole=True)
ax = BAR_X + dev_w + 14
rect(ax, y + 16, BAR_W - dev_w - 14, BAR_H, "none", INK2, 1.5)
text(ax + (BAR_W - dev_w - 14) / 2, y + 16 + BAR_H / 2 + 5, "Audit", 13, INK, 650, "middle")
text(ax, y + 6, "Held back", 12.5, INK, 600)
text(BAR_X, y + 16 + BAR_H + 22, ["Folds take whole documents. One long work is cut into contiguous",
                                  "blocks with a 1,000-word gap. Folds nest three deep: settings, each",
                                  "author's own range, and the error rate. The audit set is opened once."],
     12.5, INK2, lh=17)
arrow(BAR_X + BAR_W + 12, y + 16 + BAR_H / 2, OUT_X - 10)
bom(OUT_X, y + 16, 180, ["Scored once, after every setting", "is fixed: compatible with each", "author, or with none."])

H = y0 + 3 * ROW_H + 10
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="{SURF}"/>'
       f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
       f'<path d="M0,0 L10,5 L0,10 Z" fill="{INK2}"/></marker></defs>' + "".join(out) + "</svg>")
path = Path(__file__).with_name("fig06_study_partition.svg")
path.write_text(svg)
print("wrote", path, f"({W}x{H})")
