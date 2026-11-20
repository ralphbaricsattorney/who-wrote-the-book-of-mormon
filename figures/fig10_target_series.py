"""Draw figures/fig10_target_series.svg: the Book of Mormon, chunk by chunk, as scored once (step 6).

Rows, all on one x-axis of 1000-word chunks in text order (books shaded):
  A  share of nearby chunks compatible with Smith and with Rigdon (15-chunk centred window), with reference rates
     for development texts scored by the same procedure: each man's own scripture-style text, and the
     highest biblical-style control
  B  each chunk's compatibility set: Smith only, Rigdon only, both, neither
  C  compatible with the KJV class
  D  similarity to Spalding, Pratt and Cowdery (0.5 = no more like them than the biblical-style controls)
Hovering a cell shows its chunk, book, chapters and values.

Source: results/target_series_{kind}.csv and results/target_references_{kind}.parquet (step 6).
Run: python figures/fig10_target_series.py [F2|F1]
"""
import sys
from html import escape
from pathlib import Path

import polars as pl

from palette import BAND, BOTH as BOTH_C, INK, INK2, NEITHER as NEITHER_C, RIGDON as RIGDON_C, RULE, SMITH as SMITH_C, SURF

ROOT = Path(__file__).resolve().parents[1]
KIND = sys.argv[1] if len(sys.argv) > 1 else "F2"
OUT = ROOT / "results"
SMITH, RIGDON = "Joseph Smith", "Sidney Rigdon"
WINDOW = 15

KJV_C = "#3d3b36"
POS = ["#f4f1ea", "#cfe8e0", "#8fcbb9", "#4ea893", "#1f7f6b"]     # above 0.5: more like the candidate
NEG = ["#f4f1ea", "#ece4d6", "#dccfb8", "#c6b493"]                  # below 0.5: less like the candidate
FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"

s = pl.read_csv(OUT / f"target_series_{KIND}.csv").sort("position")
n = s.height
refs = pl.read_parquet(OUT / f"target_references_{KIND}.parquet")


def control_rate(text: str, cls: str) -> float:
    """Share of a development control compatible with `cls`, scored by the same procedure as the target;
    each document counts once."""
    return float(refs.filter(pl.col("klass") == text).group_by("unit_id")
                 .agg(pl.col(f"compatible {cls}").mean())[f"compatible {cls}"].mean())


BIBLICAL = {"Philemon Stewart (Shaker)": "Shaker roll", "Richard Snowden": "Snowden",
            "'Eliakim the Scribe' (pseud.)": "Eliakim", "John Ballou Newbrough": "Newbrough"}


def top_control(cls: str) -> tuple[str, float]:
    """The development biblical-style control most often compatible with `cls`: name and rate."""
    full, short = max(BIBLICAL.items(), key=lambda t: control_rate(t[0], cls))
    return f"{short} as {cls.split()[-1]}", control_rate(full, cls)


REF = {SMITH: [("Smith's revelations as Smith", control_rate("Joseph Smith (revelations)", SMITH)), top_control(SMITH)],
       RIGDON: [("Rigdon's revelations as Rigdon", control_rate("Sidney Rigdon (revelations, 1856-76)", RIGDON)),
                top_control(RIGDON)]}

# ---------------------------------------------------------------- geometry
W, L, R = 1400, 200, 250
PW = W - L - R
cw = PW / n
x = lambda i: L + i * cw
out = []


def text(xx, y, t, size=12.5, color=INK, weight=400, anchor="start"):
    out.append(f'<text x="{xx:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{escape(t)}</text>')


def rect(xx, y, w, h, fill, title=None, opacity=1.0):
    t = f"<title>{escape(title)}</title>" if title else ""
    out.append(f'<rect x="{xx:.2f}" y="{y:.1f}" width="{w:.2f}" height="{h}" fill="{fill}" fill-opacity="{opacity}">{t}</rect>')


def label(row_y, h, name, sub=None):
    text(L - 12, row_y + h / 2 + (0 if sub else 4), name, 13, INK, 600, "end")
    if sub:
        text(L - 12, row_y + h / 2 + 15, sub, 11.5, INK2, anchor="end")


def tip(row) -> str:
    ch = f"ch. {row['chapter_from']}" + (f"–{row['chapter_to']}" if row["chapter_to"] != row["chapter_from"] else "")
    return (f"Chunk {row['position'] + 1}: {row['bom_book']} {ch}\nSet: {row['set']}\n"
            f"Rank Smith {row[f'rank {SMITH}']:.2f}, Rigdon {row[f'rank {RIGDON}']:.2f}\n"
            + "".join(f"{k.split()[-1]} similarity {row[f'similarity {k}']:.2f}\n"
                      for k in ("Solomon Spalding", "Parley P. Pratt", "Oliver Cowdery") if f"similarity {k}" in row))


rows = list(s.iter_rows(named=True))
books = s.group_by("bom_book", maintain_order=True).agg(pl.col("position").min().alias("a"), pl.col("position").max().alias("b"))

text(40, 36, "The Book of Mormon, chunk by chunk", 20, INK, 700)
text(40, 58, f"{n} chunks of 1000 words in text order, scored once "
             f"(features {KIND}, threshold 0.10). "
             "Hover a cell for its values.", 13, INK2)

top = 108                      # the line legend sits above the book names
plot_bottom_guess = 640
for k, (book, a, b) in enumerate(books.iter_rows()):
    if k % 2:
        rect(x(a), top, (b - a + 1) * cw, plot_bottom_guess - top, BAND)
for book, a, b in books.iter_rows():
    if (b - a + 1) * cw > 34:
        text(x((a + b + 1) / 2), top + 14, book, 11.5, INK2, 600, "middle")

# ---------------------------------------------------------------- A: rolling share compatible
ay, ah = top + 34, 200
label(ay, ah, "Compatible", f"share of {WINDOW} nearby chunks")
for v in (0, 0.5, 1):
    yy = ay + ah * (1 - v)
    out.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L + PW}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
    text(L + PW + 6, yy + 4, f"{v:.0%}", 11, INK2)
ends = []
for cand, color in ((SMITH, SMITH_C), (RIGDON, RIGDON_C)):
    for (name, v), dash in zip(REF[cand], ("6 4", "2 3")):
        yy = ay + ah * (1 - v)
        out.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L + PW}" y2="{yy:.1f}" stroke="{color}" stroke-width="1.4" '
                   f'stroke-dasharray="{dash}" stroke-opacity="0.8"/>')
        ends.append((yy, f"{name} {v:.0%}", color))
    comp = s[f"compatible {cand}"].cast(pl.Float64).to_numpy()
    roll = pl.Series(comp).rolling_mean(WINDOW, center=True, min_samples=1).to_numpy()
    pts = " ".join(f"{x(i + 0.5):.1f},{ay + ah * (1 - v):.1f}" for i, v in enumerate(roll))
    out.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" points="{pts}"/>')
# reference labels at the right, spread so they don't collide
ends.sort()
bottom = -1.0
for yy, t, color in ends:
    bottom = max(yy + 4, bottom + 14)
    text(L + PW + 40, bottom, t, 11, color, 600)
lx, ly = L, top - 14
for name, color in (("Smith", SMITH_C), ("Rigdon", RIGDON_C)):
    out.append(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 22}" y2="{ly - 4}" stroke="{color}" stroke-width="2.2"/>')
    text(lx + 28, ly, f"Compatible with {name}", 12, INK2)
    lx += 190
out.append(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 22}" y2="{ly - 4}" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="6 4"/>')
text(lx + 28, ly, "own scripture-style text", 12, INK2)
lx += 200
out.append(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 22}" y2="{ly - 4}" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="2 3"/>')
text(lx + 28, ly, "highest biblical-style control, same procedure", 12, INK2)

# ---------------------------------------------------------------- B: compatibility set
by = ay + ah + 26
bh = 30
label(by, bh, "Compatible with")
SET_C = {"Smith only": SMITH_C, "Rigdon only": RIGDON_C, "both": BOTH_C, "neither": NEITHER_C}
for row in rows:
    rect(x(row["position"]) + 0.2, by, cw - 0.4, bh, SET_C[row["set"]], tip(row))
counts = s.group_by("set").len()
cnt = dict(zip(counts["set"], counts["len"]))
lx = L
for name, color in SET_C.items():
    rect(lx, by + bh + 10, 12, 12, color)
    text(lx + 18, by + bh + 21, f"{name} ({cnt.get(name, 0)}, {cnt.get(name, 0) / n:.0%})", 12, INK2)
    lx += 175

# ---------------------------------------------------------------- C: KJV
cy = by + bh + 44
ch = 14
if "compatible KJV" in s.columns:
    label(cy, ch, "KJV")
    for row in rows:
        rect(x(row["position"]) + 0.2, cy, cw - 0.4, ch, KJV_C if row["compatible KJV"] else NEITHER_C, tip(row))
    text(L + PW + 6, cy + 11, f"{s['compatible KJV'].mean():.0%} compatible", 11, INK2)
    dy = cy + ch + 22
else:
    dy = cy


# ---------------------------------------------------------------- D: similarity
def sim_color(v):
    if v >= 0.5:
        return POS[min(int((v - 0.5) / 0.5 * len(POS)), len(POS) - 1)]
    return NEG[min(int((0.5 - v) / 0.5 * len(NEG)), len(NEG) - 1)]


dh = 18
dy += 8
text(L - 12, dy - 6, "Similarity", 13, INK, 600, "end")
for k in ("Solomon Spalding", "Parley P. Pratt", "Oliver Cowdery"):
    col = f"similarity {k}"
    if col not in s.columns:
        continue
    text(L - 12, dy + 13, k.split()[-1], 12.5, INK2, anchor="end")
    for row in rows:
        rect(x(row["position"]) + 0.2, dy, cw - 0.4, dh, sim_color(row[col]), tip(row))
    text(L + PW + 6, dy + 13, f"mean {s[col].mean():.2f}", 11, INK2)
    dy += dh + 6
lx = L
for v, t in ((0.1, "less like the candidate than the controls"), (0.5, "no different (0.5)"), (0.95, "more like")):
    rect(lx, dy + 6, 12, 12, sim_color(v))
    text(lx + 18, dy + 17, t, 12, INK2)
    lx += 18 + len(t) * 6.6 + 24

# ---------------------------------------------------------------- notes
ny = dy + 46
short = [b for b, a, bb in books.iter_rows() if (bb - a + 1) * cw <= 34]
notes = ["Development reference rates are what known texts score on the same scale. Shaded bands mark books"
         + (f"; unlabelled narrow ones: {', '.join(short)}." if short else "."),
         "Similarity: probability that a chunk looks more like the candidate than a development biblical-style control "
         "chunk does; Spalding, Pratt and Cowdery have no compatibility rule."]
for i, t in enumerate(notes):
    text(40, ny + i * 18, t, 12, INK2)
H = int(ny + len(notes) * 18 + 10)

body = "".join(out).replace(f'height="{plot_bottom_guess - top}"', f'height="{dy - top}"')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="{SURF}"/>' + body + "</svg>")
path = Path(__file__).with_name("fig10_target_series.svg" if KIND == "F2" else f"fig10_target_series_{KIND}.svg")
path.write_text(svg)
print("wrote", path, f"({W}x{H})")
