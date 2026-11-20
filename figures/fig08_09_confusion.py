"""Draw figures/fig08_09_confusion.svg: the two method questions as confusion matrices, from the latest development run.

Each row is a body of text the model did not train on; each column is the set of candidates it came out compatible
with (Smith only, Rigdon only, both, neither). Cells are shares of the row's text, each document counting once.
  Q1  rows: Smith's and Rigdon's own held-out documents (evaluation folds). Right answer: a set containing the
      true author.
  Q2  rows: authors removed from training (removed-author runs) and the development biblical-style controls
      (averaged over the five evaluation runs). Right answer: neither.
Source: results/dev_ranks_F2.parquet (step 5), threshold 0.10.

Run: python figures/fig08_09_confusion.py
"""
from html import escape
from pathlib import Path

import polars as pl

from palette import BOTH, GREY_RAMP, INK, INK2, NEITHER, RIGDON as RIGDON_C, RULE, SMITH as SMITH_C, SURF

ROOT = Path(__file__).resolve().parents[1]
SMITH, RIGDON, TAU = "Joseph Smith", "Sidney Rigdon", 0.10
PSEUDO_BIBLICAL = ["'Eliakim the Scribe' (pseud.)", "John Ballou Newbrough", "Philemon Stewart (Shaker)", "Richard Snowden"]
OUTCOMES = ["smith_only", "rigdon_only", "both", "neither"]
HEADS = ["Smith only", "Rigdon only", "Both", "Neither"]

SWATCH = [SMITH_C, RIGDON_C, BOTH, NEITHER]          # column keys, as in the target series; cells are neutral
FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, M = 1000, 40
LABEL_W, CELL_W, ROW_H, SUM_W = 300, 112, 36, 150
CELL_X = [M + LABEL_W + i * CELL_W for i in range(4)]
SUM_X = CELL_X[-1] + CELL_W + 24

# ---------------------------------------------------------------- data
ranks = (pl.read_parquet(ROOT / "results/dev_ranks_F2.parquet")
         .filter(pl.col("class").is_in([SMITH, RIGDON]))
         .with_columns((pl.col("rank") > TAU).alias("ok"))
         .pivot(on="class", index=["chunk_id", "klass", "unit_id", "run", "group"], values="ok"))
s, r = pl.col(SMITH).fill_null(False), pl.col(RIGDON).fill_null(False)     # null: that class was removed in the run
ranks = ranks.with_columns((s & ~r).alias("smith_only"), (~s & r).alias("rigdon_only"), (s & r).alias("both"),
                           (~s & ~r).alias("neither"))


def by_document(df: pl.DataFrame) -> pl.DataFrame:
    """Outcome shares per klass, each document (unit) counting once."""
    return (df.group_by("klass", "unit_id").agg(pl.col(OUTCOMES).mean())
            .group_by("klass").agg(pl.col(OUTCOMES).mean(), pl.len().alias("units")))


q1 = by_document(ranks.filter((pl.col("group") == "same_author") & pl.col("klass").is_in([SMITH, RIGDON])))
q2 = by_document(ranks.filter(pl.col("group") == "removed_author")).sort("neither", descending=True)
q2_bib = by_document(ranks.filter((pl.col("group") == "control") & pl.col("klass").is_in(PSEUDO_BIBLICAL))
                     ).sort("neither", descending=True)
rows = lambda df: {d["klass"]: d for d in df.iter_rows(named=True)}
q1, q2, q2_bib = rows(q1), rows(q2), rows(q2_bib)

# ---------------------------------------------------------------- drawing
out = []


def text(x, y, s, size=13, color=INK, weight=400, anchor="start"):
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke="none", width=1.0, dash=None, rx=3):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
               f'stroke-width="{width}"{d}/>')


def step(v):
    return min(int(v * len(GREY_RAMP)), len(GREY_RAMP) - 1)


def heading(y, label, question, sum_head):
    rect(M, y - 18, 32, 24, INK, rx=5)
    text(M + 16, y - 1, label, 13, "#ffffff", 700, "middle")
    text(M + 44, y, question, 16, INK, 650)
    y += 34
    text(CELL_X[0], y, "Came out compatible with", 12.5, INK2, 600)
    text(SUM_X, y, sum_head, 12.5, INK2, 600)
    y += 20
    for x, h, c in zip(CELL_X, HEADS, SWATCH):
        tw = len(h) * 7.4
        rect(x + CELL_W / 2 - tw / 2 - 16, y - 10, 10, 10, c, rx=2)
        text(x + CELL_W / 2 + 7, y, h, 13, INK, 650, "middle")
    out.append(f'<line x1="{M}" y1="{y + 9}" x2="{W - M}" y2="{y + 9}" stroke="{INK}" stroke-width="1"/>')
    return y + 16


def row(y, label, d, right, solid, dashed=(), blank=()):
    """One matrix row. right: the share to show at the right; solid/dashed: outlined cells; blank: cells that
    cannot occur in this run."""
    text(M + 6, y + ROW_H / 2 + 5, label, 13, INK)
    text(CELL_X[0] - 12, y + ROW_H / 2 + 5, f"{d['units']} doc{'s' if d['units'] != 1 else ''}", 11.5, INK2,
         anchor="end")
    for i, (x, o) in enumerate(zip(CELL_X, OUTCOMES)):
        cx, cy, cw, ch = x + 3, y + 3, CELL_W - 6, ROW_H - 6
        if i in blank:
            rect(cx, cy, cw, ch, SURF, RULE)
            text(x + CELL_W / 2, y + ROW_H / 2 + 5, "—", 13, INK2, anchor="middle")
            continue
        v = d[o]
        rect(cx, cy, cw, ch, GREY_RAMP[step(v)])
        text(x + CELL_W / 2, y + ROW_H / 2 + 5, f"{v:.0%}", 13, "#ffffff" if step(v) >= 4 else INK, 600, "middle")
        if i in solid:
            rect(cx - 1.5, cy - 1.5, cw + 3, ch + 3, "none", INK, 2.5)
        elif i in dashed:
            rect(cx - 1.5, cy - 1.5, cw + 3, ch + 3, "none", INK, 2, "4 3")
    text(SUM_X, y + ROW_H / 2 + 5, f"{right:.0%}", 15, INK, 700)
    return y + ROW_H


text(M, 36, "Where text the model never trained on lands", 20, INK, 700)
text(M, 58, "Each row is one body of text; each cell is the share of it that came out compatible with that set of "
            "candidates. Darker = larger share.", 13, INK2)

# Q1
y = heading(110, "Q1", "Is unseen work by a known author accepted as that author?", "Own author in the set")
for k, own, label in ((SMITH, 0, "Smith's held-out documents"), (RIGDON, 1, "Rigdon's held-out documents")):
    d = q1[k]
    y = row(y, label, d, d[OUTCOMES[own]] + d["both"], solid=(own,), dashed=(2,))
y += 18
text(M, y, "Right answer: the true author's own column (solid outline). \"Both\" (dashed) includes the true author "
           "but does not single them out.", 12, INK2)

# Q2
y = heading(y + 56, "Q2", "Is an author the model never saw declined by both candidates?", "Declined by both")
text(M + 6, y + 14, "Authors left out of training", 12, INK2, 600)
y += 20
for k, d in q2.items():
    blank = (1, 2) if k == RIGDON else (0, 2) if k == SMITH else ()   # the removed candidate has no class
    label = {SMITH: "Smith (tested against Rigdon)", RIGDON: "Rigdon (tested against Smith)"}.get(k, k)
    y = row(y, label, d, d["neither"], solid=(3,), blank=blank)
text(M + 6, y + 20, "Biblical-style texts by other authors", 12, INK2, 600)
y += 26
for k, d in q2_bib.items():
    y = row(y, k, d, d["neither"], solid=(3,))
y += 18
for i, n in enumerate(["Right answer: Neither (solid outline). \"—\": not possible, because that candidate's class "
                       "was the one left out.",
                       "Development text only; features F2, threshold 0.10. Spalding and Whitmer are one "
                       "document each, Pratt three: read those rows as examples, not rates."]):
    text(M, y + i * 18, n, 12, INK2)
H = y + 2 * 18 + 6

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="{SURF}"/>' + "".join(out) + "</svg>")
path = Path(__file__).with_name("fig08_09_confusion.svg")
path.write_text(svg)
print("wrote", path, f"({W}x{H})")
