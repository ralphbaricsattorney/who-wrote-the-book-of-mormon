"""Fetch the centerplace.org transcriptions of the Messenger and Advocate (Kirtland, 1834-37) and The Evening
and the Morning Star (1832-34), then build Oliver Cowdery's signed periodical writings from them.

Per periodical, in data/raw/<dir>/:
  html/<issue>.htm         pages as served (windows-1252)
  text/<issue>.txt         one paragraph per line; navigation, "(page N)" markers and the site's bracketed
                           modern spellings removed (original spelling kept)
  articles.jsonl           heuristic split into articles at centred headings and right-aligned signatures
  by_author/<author>/<issue>_<nn>.txt  articles whose signature matches Cowdery, Rigdon or Smith
Then data/raw/oliver_cowdery_periodical_writings/text/<doc_id>.txt and documents.json: Cowdery's Letters I-VIII
(hand-checked line ranges of the issue texts) and his signed articles.

Run:  python fetch/centerplace.py
"""
from __future__ import annotations

import json
import re

from lxml import html as LH

from common import RAW, download

PERIODICALS = {  # site folder: (directory under data/raw, volume index pages)
    "ma": ("messenger_and_advocate_centerplace", ["vol1.htm", "vol2.htm", "vol3.htm"]),
    "ems": ("evening_and_morning_star_centerplace", ["vol1.htm", "vol2.htm"]),
}
TARGETS = [  # signature line -> author
    (re.compile(r"^(OLIVER COWDERY|O\.? ?COWDERY|O\. C\.|OLIVER)\W*$", re.I), "oliver_cowdery"),
    (re.compile(r"^(SIDNEY RIGDON|S\.? RIGDON|S\. R\.|SIDNEY)\W*$", re.I), "sidney_rigdon"),
    (re.compile(r"^(JOSEPH SMITH,? JR\.?|JOSEPH SMITH,? JUN\.?|J\. SMITH,? JR\.?|JOSEPH SMITH JUNIOR|JOSEPH)\W*$", re.I),
     "joseph_smith"),
]
BRACKET_FIX = re.compile(r"\s?\[[a-z][a-z'\- ]{0,40}\]")


def clean_line(t):
    t = t.replace(" ", " ")
    t = BRACKET_FIX.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def paragraphs(raw):
    doc = LH.fromstring(raw.decode("windows-1252", errors="replace"))
    for bad in doc.xpath("//a[img]|//img|//script|//style"):
        bad.drop_tree()
    out = []
    for p in doc.xpath("//body//p|//body//h1|//body//h2|//body//h3|//body//h4"):
        if p.xpath("ancestor::p"):
            continue
        txt = clean_line(p.text_content())
        if not txt or re.fullmatch(r"\(page \d+\)", txt, re.I):
            continue
        if txt.lower().startswith(("table of contents", "previous chapter", "next chapter")):
            continue
        out.append(((p.get("align") or "").upper(), txt, p.tag))
    return out


def segment(paras):
    arts, cur = [], []
    for al, txt, tag in paras:
        if al == "RIGHT":
            cur.append(("SIG", txt))
            continue
        if cur and cur[-1][0] == "SIG":       # a signature block ended an article
            arts.append(cur)
            cur = []
        if (al == "CENTER" or tag.startswith("h")) and cur and any(k == "P" for k, _ in cur):
            arts.append(cur)
            cur = []
        cur.append(("H" if (al == "CENTER" or tag.startswith("h")) else "P", txt))
    if cur:
        arts.append(cur)
    return arts


def classify(sigs):
    for s in sigs:
        for rx, name in TARGETS:
            if rx.match(s.strip()):
                return name
    return None


def fetch_periodical(which):
    name, vols = PERIODICALS[which]
    out = RAW / name
    base = f"https://www.centerplace.org/history/{which}/"
    for d in ("html", "text", "by_author"):
        (out / d).mkdir(parents=True, exist_ok=True)
    issues = []
    for v in vols:
        for m in re.findall(rb'href="(v\d+n\d+\w*\.htm)"', download(base + v, out / "html" / v), re.I):
            if m.decode() not in issues:
                issues.append(m.decode())
    download(base + "about.htm", out / "html" / "about.htm")
    with open(out / "articles.jsonl", "w") as artf:
        for iss in issues:
            paras = paragraphs(download(base + iss, out / "html" / iss))
            stem = iss[:-4]
            (out / "text" / f"{stem}.txt").write_text("\n".join(t for _, t, _ in paras) + "\n")
            for i, art in enumerate(segment(paras), 1):
                heads = [t for k, t in art if k == "H"]
                sigs = [t for k, t in art if k == "SIG"]
                body = [t for k, t in art if k == "P"]
                author = classify(sigs)
                rec = {"issue": stem, "n": i, "url": base + iss, "headings": heads[:4], "signature": sigs,
                       "author_by_signature": author, "words": len(" ".join(body).split()),
                       "first_words": " ".join(" ".join(body).split()[:12])}
                artf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if author:
                    d = out / "by_author" / author
                    d.mkdir(exist_ok=True)
                    (d / f"{stem}_{i:02d}.txt").write_text("\n".join(body) + "\n")
    print(name, len(issues), "issues")


# (doc_id, M&A issue, first and last body line (1-based, inclusive), date, description)
COWDERY_LETTERS = [
    ("letter_01", "v1n01", 153, 168, "Oct 1834", "Letter I to W. W. Phelps (Norton, Ohio, 7 Sep 1834), signed O. Cowdery"),
    ("letter_02", "v1n02", 125, 153, "Nov 1834", "Letter II to W. W. Phelps; closes '-Editor.'"),
    ("letter_03", "v1n03", 112, 127, "Dec 1834", "Letter III to W. W. Phelps (unsigned in transcription)"),
    ("letter_04", "v1n05", 114, 141, "Feb 1835", "Letter IV to W. W. Phelps, signed Oliver Cowdery, 27 Feb 1835"),
    ("letter_05", "v1n06", 144, 171, "Mar 1835", "Letter V to W. W. Phelps (unsigned in transcription)"),
    ("letter_06", "v1n07", 144, 169, "Apr 1835", "Letter VI to W. W. Phelps (unsigned in transcription)"),
    ("letter_07", "v1n10", 94, 124, "Jul 1835", "Letter VII to W. W. Phelps, signed Oliver Cowdery"),
    ("letter_08", "v2n01", 36, 66, "Oct 1835", "Letter VIII to W. W. Phelps, signed Oliver Cowdery"),
]
# (doc_id, issue, article number in articles.jsonl, date, description)
COWDERY_SIGNED_MA = [
    ("editorial_address_1834", "v1n01", 1, "Oct 1834", "Opening 'Address' of M&A, signed OLIVER COWDERY"),
    ("travel_letter_pontiac_1834", "v1n01", 3, "Oct 1834", "Travel letter from Pontiac, M.T., 20 Oct 1834, signed OLIVER COWDERY"),
    ("editorial_to_patrons_1835", "v1n08", 9, "May 1835", "'To the Patrons', signed OLIVER COWDERY"),
    ("statement_1836_v2n03", "v2n03", 8, "Dec 1835", "Signed statement, Oliver Cowdery"),
    ("editorial_v3n01_a", "v3n01", 1, "Oct 1836", "Editorial, signed O. COWDERY"),
    ("editorial_v3n01_b", "v3n01", 5, "Oct 1836", "Article, signed O. COWDERY"),
    ("valedictory_1837", "v3n11", 4, "Aug 1837", "Valedictory, signed OLIVER COWDERY"),
]
COWDERY_SIGNED_EMS = [
    ("ems_letter_to_wa_cowdery_1834", "v2n16_10.txt", "Jan 1834",
     "EMS 2:16, letter 'Dear Brother' to W. A. Cowdery (Kirtland, 23 Jan 1834 heading), signed OLIVER COWDERY"),
    ("ems_address_to_patrons_1834", "v2n24_01.txt", "Sep 1834",
     "EMS 2:24, closing 'Address to the Patrons of The Evening and the Morning Star', signed O. COWDERY"),
]


def build_cowdery():
    ma = RAW / "messenger_and_advocate_centerplace"
    out = RAW / "oliver_cowdery_periodical_writings"
    (out / "text").mkdir(parents=True, exist_ok=True)
    recs = []

    def keep(did, body, **info):
        (out / "text" / f"{did}.txt").write_text(body)
        w = body.split()
        recs.append({"doc_id": did, **info, "words": len(w), "first": " ".join(w[:10]), "last": " ".join(w[-8:])})

    for did, iss, a, b, date, desc in COWDERY_LETTERS:
        lines = (ma / "text" / f"{iss}.txt").read_text().split("\n")
        keep(did, "\n".join(lines[a - 1:b]).strip() + "\n", issue=iss, lines=[a, b], date=date, desc=desc)
    for did, iss, n, date, desc in COWDERY_SIGNED_MA:
        body = (ma / "by_author" / "oliver_cowdery" / f"{iss}_{n:02d}.txt").read_text()
        keep(did, body, issue=iss, segment=n, date=date, desc=desc)
    ems = RAW / "evening_and_morning_star_centerplace" / "by_author" / "oliver_cowdery"
    for did, f, date, desc in COWDERY_SIGNED_EMS:
        keep(did, (ems / f).read_text(), issue="EMS " + f[:-4], date=date, desc=desc)
    json.dump(recs, open(out / "documents.json", "w"), indent=1)
    print("oliver_cowdery_periodical_writings", len(recs), "documents")


if __name__ == "__main__":
    fetch_periodical("ma")
    fetch_periodical("ems")
    build_cowdery()
