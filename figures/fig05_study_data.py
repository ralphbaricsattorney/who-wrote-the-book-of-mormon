"""Draw figures/fig05_study_data.svg: the text each study used, in one unit (words), and what it did with it.

Sources:
  Jockers et al. 2008  data/raw/jockers_witten_criddle_2008_supplement/dataMatrix.txt: words per author, summed
  Schaalje et al. 2011 the paper's Appendix B, which gives only the number of blocks per author and the smallest
                       and largest block. The total lies between (n-1) x smallest + largest and
                       smallest + (n-1) x largest; the bar shows that range.
  RBA's Analysis       data/processed/chunks.parquet (step 4): whole 1,000-word chunks, so words = chunks x 1,000

Run: python figures/fig05_study_data.py
"""
import re
from html import escape
from pathlib import Path

import polars as pl

from palette import BAND, GREY_DARK, GREY_LIGHT, INK, INK2, SURF, TARGET as TARGET_C

ROOT = Path(__file__).resolve().parents[1]
FONT = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, M, LABEL_W, COL_W = 1200, 40, 254, 288
COL_X = [M + LABEL_W + i * COL_W for i in range(3)]
ROW_H, BAR_H, BAR_MAX, SCALE_K = 48, 12, 170, 270          # BAR_MAX px = SCALE_K thousand words
CAND, OTHER, TEST, TARGET = "cand", "other", "test", "target"
COLOR = {CAND: GREY_DARK, OTHER: GREY_LIGHT, TEST: GREY_DARK, TARGET: TARGET_C}   # test only: hollow, never learned

# ---------------------------------------------------------------- the numbers
jockers = {}
with open(ROOT / "data/raw/jockers_witten_criddle_2008_supplement/dataMatrix.txt") as f:
    f.readline()
    for line in f:
        label, *counts = line.rstrip("\n").split("\t")
        author = re.sub(r"\d+$", "", label.strip('"'))
        jockers[author] = jockers.get(author, 0) + sum(int(float(x)) for x in counts if x)
J = {k: v / 1000 for k, v in jockers.items()}


def blocks(n, smallest, largest):
    """Range of the total for n blocks, given the smallest and the largest (Schaalje et al., Appendix B)."""
    return ((n - 1) * smallest + largest) / 1000, (smallest + (n - 1) * largest) / 1000


chunks = pl.read_parquet(ROOT / "data/processed/chunks.parquet")
k = lambda e: chunks.filter(e).height                   # 1,000 words per chunk, so chunks = thousands of words
klass = lambda *names: pl.col("klass").is_in(names)
OWN = ["Sidney Rigdon", "Solomon Spalding", "Oliver Cowdery", "Parley P. Pratt", "Joseph Smith", "KJV"]

# (row label, [(role, thousand words or (low, high) or None, note) for Jockers, Schaalje, RBA's Analysis])
ROWS = [
    ("Sidney Rigdon, prose 1831–46",
     [(CAND, J["Rigdon"], "one class: 1833–35 articles + 1864 revelations"),
      (CAND, blocks(25, 2214, 8747), ""),
      (CAND, k(klass("Sidney Rigdon")), "")]),
    ("Sidney Rigdon, revelations 1856–76",
     [(None, None, "in the class above"),
      (CAND, blocks(15, 3678, 6784), "a class of its own"),
      (TEST, k(klass("Sidney Rigdon (revelations, 1856-76)")), "held out: tests scripture style")]),
    ("Solomon Spalding",
     [(CAND, J["Spaulding"], ""), (CAND, blocks(7, 4030, 6767), ""), (CAND, k(klass("Solomon Spalding")), "")]),
    ("Oliver Cowdery",
     [(CAND, J["Cowdrey"], ""), (CAND, blocks(8, 3342, 6167), ""), (CAND, k(klass("Oliver Cowdery")), "")]),
    ("Parley P. Pratt",
     [(CAND, J["Pratt"], ""), (CAND, blocks(28, 3443, 5994), ""), (CAND, k(klass("Parley P. Pratt")), "")]),
    ("Joseph Smith",
     [(None, None, "not used: \"no reliable corpus\""),
      (CAND, blocks(5, 2081, 3362), "his own hand only"),
      (CAND, k(klass("Joseph Smith")), "what he composed alone")]),
    ("Joseph Smith, revelations 1828–43",
     [(None, None, "not used"), (None, None, "not used"),
      (TEST, k(klass("Joseph Smith (revelations)")), "held out: tests scripture style")]),
    ("King James Bible",
     [(OTHER, J["Isaiah"] + J["Malachi"], "Isaiah and Malachi: a \"pseudo-control\""),
      (OTHER, blocks(8, 3903, 5429), "Isaiah"),
      (OTHER, k(klass("KJV")), "all 66 books; its quotations masked")]),
    ("Other authors",
     [(OTHER, J["Longfellow"] + J["Barlow"], "Longfellow, Barlow"),
      [(TEST, blocks(51, 960, 5716), "Hamilton, in a separate demonstration"),   # their section 3: scored only
       (OTHER, blocks(51, 960, 5716), "Hamilton, a class in one Book of Mormon run")],   # section 6 variant
      (OTHER, k((pl.col("role") == "class") & ~klass(*OWN)), "Hamilton, Madison and 4 more")]),
    ("Biblical-style texts by others",
     [(None, None, ""), (None, None, ""),
      (TEST, k(pl.col("role") == "pseudo_biblical"), "6 texts: can the style alone pass?")]),
    ("Authors writing in both styles",
     [(None, None, ""), (None, None, ""),
      (TEST, k(pl.col("role") == "two_register"), "5 authors: recognized in both?")]),
    ("Book of Mormon",
     [(TARGET, J["Unknown"], "239 chapters"), (TARGET, J["Unknown"], "239 chapters, same text"),
      (TARGET, k(klass("Book of Mormon")), "quotations of the Bible masked")]),
]

# ---------------------------------------------------------------- drawing
out = []


def text(x, y, s, size=13, color=INK, weight=400, anchor="start"):
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
               f'text-anchor="{anchor}">{escape(s)}</text>')


def rect(x, y, w, h, fill, opacity=1.0, rx=2, hollow=False):
    paint = (f'fill="{SURF}" stroke="{fill}" stroke-width="1.5" stroke-opacity="{opacity}"' if hollow
             else f'fill="{fill}" fill-opacity="{opacity}"')
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h}" rx="{rx}" {paint}/>')


px = lambda v: min(v, SCALE_K) / SCALE_K * BAR_MAX


def bar(x, y, role, value):
    """A bar of `value` thousand words; a range is solid to its low end and pale to its high end."""
    low, high = value if isinstance(value, tuple) else (value, value)
    color, hollow = COLOR[role], role == TEST
    rect(x, y, px(high), BAR_H, color, 0.3, hollow=hollow)
    rect(x, y, px(low), BAR_H, color, hollow=hollow)
    end = x + px(high)
    if high > SCALE_K:                                  # off the scale: a break, and the number says how far
        out.append(f'<line x1="{end - 9}" y1="{y + BAR_H + 2}" x2="{end - 3}" y2="{y - 2}" stroke="{SURF}" stroke-width="3"/>')
    label = f"{low:.0f}k" if low == high else f"{low:.0f}–{high:.0f}k"
    text(end + 6, y + BAR_H - 1, label, 12.5, INK, 600)


text(M, 36, "The Data each Study Uses", 20, INK, 700)
text(M, 58, "Bar length is words of text, on one scale for all three studies (thousands of words; k = 1,000).", 13, INK2)
lx = M
for role, label in ((CAND, "Candidate author"), (OTHER, "Other class the model learns"),
                    (TEST, "Test only, never learned"), (TARGET, "Text being attributed")):
    rect(lx, 76, 14, 12, COLOR[role], hollow=role == TEST)
    text(lx + 20, 87, label, 13, INK2)
    lx += 44 + len(label) * 7.1

top = 112
for x, (name, unit) in zip(COL_X, (("Jockers et al. 2008", "Unit: a passage of 100 to 18,000 words"),
                                   ("Schaalje et al. 2011", "Unit: a block of 2,100 to 8,700 words"),
                                   ("RBA's Analysis", "Unit: a 1,000-word chunk"))):
    text(x, top + 16, name, 15, INK, 700)
    text(x, top + 35, unit, 12.5, INK2)
y0 = top + 50
out.append(f'<line x1="{M}" y1="{y0}" x2="{W - M}" y2="{y0}" stroke="{INK}" stroke-width="1.2"/>')

y = y0
for r, (label, cells) in enumerate(ROWS):
    cells = [c if isinstance(c, list) else [c] for c in cells]   # a cell may hold several bars, stacked
    h = ROW_H * max(len(c) for c in cells)
    if r % 2:
        rect(M, y, W - 2 * M, h, BAND, rx=0)
    text(M + 8, y + h / 2 + 5, label, 13, INK, 600)
    for x, stack in zip(COL_X, cells):
        for i, (role, value, note) in enumerate(stack):
            cy = y + (h - ROW_H * len(stack)) / 2 + i * ROW_H     # this bar's slot, the stack centred in the row
            if role is None:
                text(x, cy + 29, note or "—", 12.5, INK2)
                continue
            by = cy + 10 if note else cy + (ROW_H - BAR_H) / 2   # a bar without a note sits on its slot's centre
            bar(x, by, role, value)
            if note:
                text(x, by + BAR_H + 15, note, 11.5, INK2)
    y += h
y_end = y
out.append(f'<line x1="{M}" y1="{y_end}" x2="{W - M}" y2="{y_end}" stroke="{INK}" stroke-width="1.2"/>')

notes = ["Pale bars: Schaalje et al. give only how many blocks each author has and the smallest and largest block, so "
         "the pale part is the range of totals those allow.",
         "A break at the end of a bar: off the scale. RBA's Analysis counts whole 1,000-word chunks; text left over "
         "at the end of a document is not used."]
for i, n in enumerate(notes):
    text(M, y_end + 24 + i * 18, n, 12, INK2)

H = y_end + 24 + len(notes) * 18 + 8
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="{SURF}"/>' + "".join(out) + "</svg>")
path = Path(__file__).with_name("fig05_study_data.svg")
path.write_text(svg)
print("wrote", path, f"({W}x{H})")
