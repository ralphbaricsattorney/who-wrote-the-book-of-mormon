"""Step 1: one cleaned, labelled, quotation-masked table of documents, from data/raw and data/prepared.

Each source's text is cut to the author's own words (front matter, editors' notes and documents by others removed).
Then any run of 15+ words a text shares with the KJV, with the Book of Mormon, or with another source is removed from
the later of the two, so quotations don't count as anyone's style. The Book of Mormon's KJV quotations are removed
from it and kept as a control of their own.

`source_id` names the original document: every hand, copy and edition of it shares one id.
`source_type` is its provenance: single_author, attributed, mixed_collection or composite.

Output: data/processed/documents.parquet
"""
from __future__ import annotations

import csv
import html
import json
import re
import unicodedata
from pathlib import Path

import polars as pl

from config import PREPARED, PROC as OUT, RAW, ROOT

DOCS: list[dict] = []                 # every document, in the order added; add() appends here
SEEN_IDS: set[str] = set()
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
MONTHS |= {"spring": 4, "summer": 7, "fall": 10, "autumn": 10, "winter": 1}
MONTH_PAT = "|".join(MONTHS)


def date_key(date: str | None, year: int | None) -> int | None:
    """yyyymmdd for sorting documents in date order; month and day are 0 when the source gives none."""
    if year is None:
        return None
    t = (date or "").lower()
    m = re.search(rf"\b({MONTH_PAT})[a-z]*\.?", t)
    if not m:
        return year * 10000
    d = re.search(rf"(\d{{1,2}})(?:[–-]\d{{1,2}})?\s+(?:{MONTH_PAT})|(?:{MONTH_PAT})[a-z]*\.?\s+(\d{{1,2}})\b", t)
    return year * 10000 + MONTHS[m.group(1)] * 100 + (int(d.group(1) or d.group(2)) if d else 0)


def add(**kw):
    base = dict(
        doc_id=None, author=None, author_confidence=None, role=None, register=None, work=None,
        edition=None, date=None, year=None, scribe=None, bom_book=None, bom_chapter_1830=None,
        bom_narrator=None, bom_plates=None, dictation_rank=None, chunk_group=None, order=0,
        mask_kjv=True, mask_bom=True, source_path=None, notes=None, text="",
        source_id=None, source_type="single_author",
    )
    base.update(kw)
    base["source_id"] = base["source_id"] or base["doc_id"]
    if base["source_path"] and Path(base["source_path"]).is_absolute():
        base["source_path"] = str(Path(base["source_path"]).relative_to(ROOT))
    base["date_key"] = date_key(base["date"], base["year"])
    assert base["doc_id"] not in SEEN_IDS, f"duplicate doc_id {base['doc_id']}"
    SEEN_IDS.add(base["doc_id"])
    base["text"] = normalize(base["text"])
    if len(base["text"].split()) < 20:
        return
    DOCS.append(base)


# ----------------------------------------------------------------------------------------------
# text utilities
# ----------------------------------------------------------------------------------------------
JUNK_PAT = re.compile(
    r"(forgotten ?books|oahspe, vol\. \d of \d|digitized by|google|internet archive|archive\.org|librar(y|ies)|"
    r"brigham young|university of|preservat|thomson park|cranberry township|latterdaytruth|"
    r"www\.|http|copyright|all rights reserved|\bisbn\b|printed by|scanned)", re.I)


def normalize(t: str) -> str:
    t = unicodedata.normalize("NFC", t or "")
    t = t.replace("ſ", "s").replace("­", "").replace("\xa0", " ")
    t = re.sub(r"[“”„]", '"', t)
    t = re.sub(r"[‘’‚]", "'", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def is_junk_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 0.5 * len(s.replace(" ", "")):
        return True  # mostly digits/punctuation (page numbers, OCR garbage)
    if JUNK_PAT.search(s):
        return True
    upper = sum(c.isupper() for c in letters)
    if len(s) < 70 and letters and upper / len(letters) > 0.7:
        return True  # running heads, chapter headings, title lines
    return False


def clean_ocr(text: str) -> str:
    lines = [l for l in text.split("\n") if not is_junk_line(l)]
    t = "\n".join(lines)
    t = re.sub(r"(\w)[-¬]\s*\n\s*(\w)", r"\1\2", t)    # de-hyphenate across line breaks
    t = re.sub(r"(\w)- (\w)", r"\1\2", t)            # djvu "walk- ing" artifacts
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)            # join wrapped lines; blank line = paragraph
    t = t.replace("<fe", "&")
    return normalize(t)


def lines_between(path: Path, start: int | None = None, end: int | None = None,
                  start_pat: str | None = None, end_pat: str | None = None, start_occ: int = 1) -> str:
    lines = path.read_text(errors="ignore").split("\n")
    s, e = (start or 1) - 1, (end or len(lines))
    if start_pat:
        hits = [i for i, l in enumerate(lines) if re.search(start_pat, l)]
        s = hits[start_occ - 1]
    if end_pat:
        hits = [i for i, l in enumerate(lines) if re.search(end_pat, l) and i > s]
        e = hits[0]
    return "\n".join(lines[s:e])


def gutenberg_body(path: Path, start: str | None = None, end: str | None = None) -> str:
    """The text inside Gutenberg's wrapper; `start`/`end` (line patterns) trim the edition's own front and back
    matter (title pages, others' prefaces, indexes, appendices, transcriber's notes)."""
    t = path.read_text(errors="ignore")
    t = t.split("*** START OF", 1)[1].split("\n", 1)[1]
    t = t.split("*** END OF", 1)[0]
    if start:
        t = t[re.search(start, t, re.M).start():]
    if end:
        t = t[:re.search(end, t, re.M).start()]
    return t


def cut(text: str, patterns: list[str], label: str) -> str:
    """Remove passages someone else wrote (each pattern must match exactly once)."""
    for p in patterns:
        text, n = re.subn(p, " ", text, flags=re.S | re.M)
        assert n == 1, f"cut {p[:40]!r} matched {n} times in {label}"
    return text


def ia_meta(path: Path) -> dict:
    try:
        return json.loads(path.read_text())["metadata"]
    except Exception:
        return {}


# ----------------------------------------------------------------------------------------------
# 1. Book of Mormon, 1830 first edition (target)
# ----------------------------------------------------------------------------------------------
NARRATOR = {"1 Nephi": "Nephi", "2 Nephi": "Nephi", "Jacob": "Jacob", "Enos": "Enos", "Jarom": "Jarom",
            "Omni": "Omni (several)", "Words of Mormon": "Mormon", "Mosiah": "Mormon (abridging)",
            "Alma": "Mormon (abridging)", "Helaman": "Mormon (abridging)", "3 Nephi": "Mormon (abridging)",
            "4 Nephi": "Mormon (abridging)", "Mormon": "Mormon", "Ether": "Moroni (abridging)", "Moroni": "Moroni"}
# Consensus dictation order: Mosiah..Moroni first (Apr-Jun 1829), then the small plates (1 Nephi-Words of Mormon).
DICTATION_ORDER = ["Mosiah", "Alma", "Helaman", "3 Nephi", "4 Nephi", "Mormon", "Ether", "Moroni",
                   "1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni", "Words of Mormon"]
SMALL_PLATES = {"1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni"}


def book_of_mormon():
    """The 1830 first edition, one document per chapter (the target)."""
    bom_dir = RAW / "bom_1830_wikisource"
    for row in json.loads((bom_dir / "manifest.json").read_text()):
        book = row["book"]
        if book not in NARRATOR:
            continue  # preface (Smith's voice) and witness statements excluded
        txt = (bom_dir / row["file"]).read_text()
        txt = re.sub(r"^\s*CHAPTER [IVXLC]+\.?\s*$", "", txt, flags=re.M)
        add(doc_id=f"bom1830_{row['file'].split('/')[-1][:-4]}", author="Book of Mormon (unknown)",
            author_confidence="target", role="target", register="revealed_scripture",
            work=f"BoM {book}", edition="1830 Palmyra (Wikisource)", date="1829", year=1829,
            bom_book=book, bom_chapter_1830=row["chapter_1830"], bom_narrator=NARRATOR[book],
            bom_plates="small" if book in SMALL_PLATES else ("Words of Mormon" if book == "Words of Mormon" else "large"),
            dictation_rank=DICTATION_ORDER.index(book), chunk_group=f"bom::{book}",
            order=row["chapter_1830"], mask_bom=False, source_path=str(bom_dir / row["file"]), text=txt)


# ----------------------------------------------------------------------------------------------
# 2. KJV
# ----------------------------------------------------------------------------------------------
KJV_GROUPS = {
    "Pentateuch": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
    "Isaiah": ["Isaiah"], "Malachi": ["Malachi"],
    "Psalms & wisdom": ["Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon"],
    "Gospels & Acts": ["Matthew", "Mark", "Luke", "John", "Acts"],
}


def kjv():
    """The King James Bible, one document per book."""
    kjv_books: dict[str, str] = {}
    for fn in ["old-testament.json", "new-testament.json"]:
        d = json.loads((RAW / "lds_scriptures_json" / fn).read_text())
        for b in d["books"]:
            kjv_books[b["book"]] = "\n\n".join(" ".join(v["text"] for v in c["verses"]) for c in b["chapters"])
    ot_names = [b["book"] for b in json.loads((RAW / "lds_scriptures_json" / "old-testament.json").read_text())["books"]]
    for i, (name, txt) in enumerate(kjv_books.items()):
        g = next((k for k, v in KJV_GROUPS.items() if name in v), None)
        if g is None:
            g = "OT history & prophets (other)" if name in ot_names else "NT epistles & Revelation"
        add(doc_id=f"kjv_{name.replace(' ', '_')}", author="KJV", author_confidence="control", role="control",
            register="scripture_kjv", work=f"KJV {g}", edition="KJV (1769 text, LDS 2013 JSON)", date="1611/1769",
            year=1769, chunk_group=f"kjv::{g}", order=i, mask_kjv=False, mask_bom=False, source_type="mixed_collection",
            source_path=str(RAW / "lds_scriptures_json"), text=txt)


# ----------------------------------------------------------------------------------------------
# 3. Joseph Smith: Joseph Smith Papers transcriptions, split by hand
# ----------------------------------------------------------------------------------------------


def jsp_segments(text_dir: Path, uri: str):
    meta = json.loads((text_dir / f"{uri}.meta.json").read_text())
    segs = []
    for line in (text_dir / f"{uri}.pages.jsonl").read_text().splitlines():
        p = json.loads(line)
        for s in p["segments"]:
            segs.append((s["scribe"], bool(s["js_hand"]), s["text"]))
    return meta, segs


def jsp_year(meta) -> int | None:
    m = re.search(r"(18\d\d)", meta.get("date", "") or meta.get("title", ""))
    return int(m.group(1)) if m else None


# Smith's class is what he composed alone: the holograph (H) and sole-composition (S) tiers of
# pipeline/smith_tiers.tsv, which rests on each document's Joseph Smith Papers introduction. Joint (J) and
# other-composer (O) documents, and the Martin Harris letter (in Rigdon's hand; the Papers are silent on who composed
# it), keep their text under SMITH_SHARED: never Smith's class.
C_SMITH, SMITH_SHARED = "Joseph Smith", "Joseph Smith (joint or by others)"
NOT_SMITH = {"letter-to-martin-harris-22-february-1831"}
CUT = {  # passages inside an S or H document that someone else composed
    "letter-to-hyrum-smith-3-4-march-1831": r"My dearly beloved bretheren after.*?your Brother forever\s*Oliver",  # copy of Cowdery's letter
    "letter-to-edward-partridge-and-others-30-march-1834": r"P\.S\. To bro\. William.*",                       # Cowdery and Phelps
    "letter-to-emma-smith-4-june-1834": r"N\.B\. The enclosed bill.*",                                           # F. G. Williams
}


def smith_doc(uri, meta, segs, tier, own_hand_only, k, edition_dir):
    """One Smith document; `tier` is its row in pipeline/smith_tiers.tsv (H, S, J, O or MIXED)."""
    title = meta["title"]
    reg = "letter" if title.startswith("Letter") else ("history_memoir" if re.match(r"(History|Journal)", title) else "other_document")
    segs = [(scribe, js, t) for scribe, js, t in segs if not scribe.startswith("Signatures")]
    words = sum(len(t.split()) for _, _, t in segs) or 1
    own = sum(len(t.split()) for scribe, js, t in segs if js or scribe.startswith("Joseph Smith")) / words
    tier = "H" if own_hand_only else tier
    in_class = tier in ("H", "S") and uri not in NOT_SMITH
    if own_hand_only:
        segs = [(scribe, js, t) for scribe, js, t in segs if js]
    text = "\n\n".join(t for _, _, t in segs)
    if uri in CUT:
        text, n = re.subn(CUT[uri], " ", text, flags=re.S)
        assert n == 1, f"cut not found in {uri}"
    conf = {"H": "holograph", "S": "sole_composition"}.get(tier, "joint_or_other") if in_class else "joint_or_other"
    hands = sorted({scribe for scribe, _, _ in segs})
    # One document per source, in manuscript order. (Grouping the passages by hand would break up the text.)
    add(doc_id=f"jsp_{uri}", author=C_SMITH if in_class else SMITH_SHARED, author_confidence=conf,
        role="candidate" if in_class else "control", register=reg, work=f"Smith {reg}", edition="JSP transcription",
        date=meta.get("date"), year=jsp_year(meta), scribe="; ".join(hands), chunk_group=f"smith::{reg}", order=k,
        source_path=str(edition_dir / f"{uri}.pages.jsonl"),
        notes=f"{title} | tier {tier} | {own:.0%} of words in Smith's own hand", text=text)


FORMULAIC = re.compile(r"promissory|pay-order|receipt|egyptian|warrant|agreement")


def smith_writings():
    """Smith's letters, histories and other documents (Joseph Smith Papers)."""
    smith_tier = {r[0]: r[5] for r in csv.reader((ROOT / "pipeline" / "smith_tiers.tsv").open(), delimiter="\t")
                  if r[0] != "uri"}
    sm_dir = RAW / "jsp_joseph_smith_early_writings" / "text"
    for k, mf in enumerate(sorted(sm_dir.glob("*.meta.json"))):
        uri = mf.name[: -len(".meta.json")]
        meta, segs = jsp_segments(sm_dir, uri)
        # Journal 1832-34 mixes JS's hand with entries by Rigdon, Cowdery, Pratt and others: only his own hand is used
        smith_doc(uri, meta, segs, smith_tier[uri], own_hand_only=smith_tier[uri] == "MIXED", k=k,
                  edition_dir=sm_dir)

    # 1835-44: passages in Smith's own hand in documents he composed (data/raw/jsp_joseph_smith_later_writings).
    # Left out: pay orders, notes of hand, receipts, warrants and agreements (formulaic), the Egyptian Alphabet (a
    # character list), and documents with fewer than 50 words in his hand, among them the 1839 Liberty jail letters
    # (dictated; co-signed by Hyrum Smith, Lyman Wight, Caleb Baldwin and Alexander McRae).
    later_dir = RAW / "jsp_joseph_smith_later_writings" / "text"
    for k, r in enumerate(csv.DictReader((later_dir.parent / "composition_notes.tsv").open(), delimiter="\t")):
        uri = r["uri"]
        meta, segs = jsp_segments(later_dir, uri)
        if r["composition"] != "own" or FORMULAIC.search(uri) or sum(len(t.split()) for _, js, t in segs if js) < 50:
            continue
        smith_doc(uri, meta, segs, "H", own_hand_only=True, k=1000 + k, edition_dir=later_dir)


# Revelation Book 1 (manuscript, mostly John Whitmer's hand), one document per revelation. The Book of
# Commandments (1833) prints many of the same revelations: those rows are `role="twin"`, share the manuscript's
# source_id and are never used. A printed chapter with no manuscript stands in for it (below).
ITEM = re.compile(r"^(Chapter \d+ • )?((?:Revelation|Account of John|Articles and Covenants|Explanation of Scripture"
                  r"|Vision|Answers to Questions), [^\n]*)$", re.M)
# Lines that end an item without starting one: documents not by Smith, and the volumes' back matter
BOUNDARY = re.compile(r"^((Articles of the Church of Christ|Testimony|Minutes), [^\n]*|Index|Hymn: [^\n]*)$", re.M)
JOINT = ("[D&C 20]", "[D&C 76]")   # issued jointly with Cowdery / Rigdon


def jsp_items(text: str, printed: bool) -> list[tuple[str, str]]:
    """(title, body) for each revelation, in order.

    A body ends at the next title or boundary line. "<title>, continued" is joined to its first part.
    A title that appears again is a later copy and is dropped. In the printed volume only the printed
    chapters count: later handwritten additions to that copy have no "Chapter N" prefix.
    """
    cuts = sorted([(m.start(), m.end(), m.group(2), bool(m.group(1))) for m in ITEM.finditer(text)]
                  + [(m.start(), m.end(), None, False) for m in BOUNDARY.finditer(text)])
    ends = [c[0] for c in cuts[1:]] + [len(text)]
    items: dict[str, str] = {}
    for (_, e, title, chapter), end in zip(cuts, ends):
        if title is None or (printed and not chapter):
            continue
        if title.endswith(", continued"):
            items[title.removesuffix(", continued")] += "\n\n" + text[e:end]
        elif title not in items:
            items[title] = text[e:end]
    return list(items.items())


DC_LATE = [108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 124, 125, 126, 132, 137]
DC_YEAR = {108: 1835, 109: 1836, 110: 1836, 111: 1836, 112: 1837, 113: 1838, 114: 1838, 115: 1838, 116: 1838,
           117: 1838, 118: 1838, 119: 1838, 120: 1838, 124: 1841, 125: 1841, 126: 1841, 132: 1843, 137: 1836}


def smith_revelations():
    """Smith's revelations (manuscript books, 1833 printing, later D&C) and the Pearl of Great Price."""
    rb_dir = RAW / "jsp_revelation_book_1_and_book_of_commandments" / "text"
    for fn, role, conf, ed, group in [
        ("revelation-book-1", "candidate", "dictated_revelation", "JSP transcription of MS", "smith::revelation_book_1"),
        ("book-of-commandments-1833", "twin", "printed_revelation", "Book of Commandments 1833 (JSP)", "smith::boc_1833"),
    ]:
        for k, (title, body) in enumerate(jsp_items((rb_dir / f"{fn}.txt").read_text(), printed=role == "twin")):
            slug = re.sub(r"[^a-z0-9]+", "_", title.split(" [")[0].lower()).strip("_")
            add(doc_id=f"{fn}__{slug}", source_id=f"smith_{slug}", author="Joseph Smith", author_confidence=conf,
                role=role, register="revealed_scripture", work="Smith revelations (1828-31)", edition=ed,
                date=title, year=int(m.group(0)) if (m := re.search(r"18\d\d", title)) else None,
                scribe="John Whitmer (mostly)" if role == "candidate" else "printed", chunk_group=group, order=k,
                source_type="attributed" if title.endswith(JOINT) else "single_author",
                source_path=str(rb_dir / f"{fn}.txt"), notes=title, text=body)

    # Smith revelations not in Revelation Book 1:
    #  * Revelation Book 2 (manuscript): revelations and visions whose source is not already present
    #  * Book of Commandments chapters with no manuscript in Revelation Book 1 become ordinary documents
    #  * revelations of 1835-43 found only in the modern edition. Letters (D&C 85, 121-123, 127-128),
    #    minutes (102), clerks' notes of instructions (129-131), and texts not by Smith (134-136, 138) are left out.
    have = {d["source_id"] for d in DOCS if d["work"] == "Smith revelations (1828-31)" and d["role"] == "candidate"}
    rb2 = RAW / "jsp_revelation_book_2_and_doctrine_and_covenants" / "items"
    rb2_items: dict[str, list] = {}
    for row in csv.DictReader((rb2 / "revelation-book-2.items.tsv").open(), delimiter="\t"):
        title = re.sub(r"^Heading to ", "", row["jsp_title"]).replace(", continued", "")
        if not re.match(r"(Revelation|Vision|Explanation of Scripture), ", title):
            continue
        slug = re.sub(r"[^a-z0-9]+", "_", title.split(" [")[0].lower()).strip("_")
        rb2_items.setdefault(slug, []).append((title, row))
    for k, (slug, parts) in enumerate(rb2_items.items()):
        if f"smith_{slug}" in have:
            continue
        title = parts[0][0]
        text = "\n\n".join((rb2 / row["file"].removeprefix("items/")).read_text() for _, row in parts)
        add(doc_id=f"revelation-book-2__{slug}", source_id=f"smith_{slug}", author="Joseph Smith",
            author_confidence="dictated_revelation", role="candidate", register="revealed_scripture",
            work="Smith revelations (1828-31)", edition="JSP transcription of Revelation Book 2", date=title,
            year=int(m.group(0)) if (m := re.search(r"18\d\d", title)) else None, scribe="Frederick G. Williams (mostly)",
            chunk_group="smith::revelation_book_2", order=k, source_path=str(rb2), notes=title,
            source_type="attributed" if title.endswith(JOINT) else "single_author", text=text)
        have.add(f"smith_{slug}")
    for d in DOCS:
        if d["role"] == "twin" and d["source_id"] not in have:
            d.update(role="candidate", author_confidence="printed_revelation_only", chunk_group="smith::boc_only")
    dc = {int(s["section"]): s for s in json.loads((RAW / "lds_scriptures_json" / "doctrine-and-covenants.json").read_text())["sections"]}
    for n in DC_LATE:
        add(doc_id=f"dc_{n}", source_id=f"smith_dc_{n}", author="Joseph Smith", author_confidence="dictated_modern_edition",
            role="candidate", register="revealed_scripture", work="Smith revelations (1835-43, modern edition)",
            edition="LDS 2013 text", date=str(DC_YEAR[n]), year=DC_YEAR[n], chunk_group="smith::dc_late", order=n,
            source_path=str(RAW / "lds_scriptures_json/doctrine-and-covenants.json"),
            text=" ".join(v["text"] for v in dc[n]["verses"]))

    # Pearl of Great Price (modern edition): Book of Moses, Book of Abraham, JS-History
    pgp = json.loads((RAW / "lds_scriptures_json" / "pearl-of-great-price.json").read_text())
    for b in pgp["books"]:
        name = b["book"]
        if name.startswith("Moses"):
            reg, yr, w = "revealed_scripture", 1830, "Smith Book of Moses (JST, 1830-31)"
        elif name.startswith("Abraham"):
            reg, yr, w = "revealed_scripture", 1835, "Smith Book of Abraham (1835-42)"
        elif "History" in name:
            reg, yr, w = "history_memoir", 1838, "Smith History 1838 (JS-H)"
        else:
            continue
        joint = "History" in name          # JS-H: from the 1838 manuscript JS, Rigdon and Robinson created (tier J)
        add(doc_id=f"pgp_{b['lds_slug']}", author=SMITH_SHARED if joint else "Joseph Smith",
            author_confidence="joint_or_other" if joint else "dictated_modern_edition", role="control" if joint else "candidate", register=reg, work=w, edition="LDS 2013 text", date=str(yr), year=yr,
            chunk_group=f"smith::{w}", source_path=str(RAW / "lds_scriptures_json/pearl-of-great-price.json"),
            text="\n\n".join(" ".join(v["text"] for v in c["verses"]) for c in b["chapters"]))


# ----------------------------------------------------------------------------------------------
# 4. Sidney Rigdon (Broadhurst transcriptions)
# ----------------------------------------------------------------------------------------------
RIG_REG = {"millennium": "sermon_essay", "gospel": "sermon_essay", "articles_letters": "sermon_essay",
           "oration_1838": "oration_political", "appeal_1840": "oration_political", "memorial_1844": "oration_political"}
# The 1840 Appeal prints documents by others inside Rigdon's narrative; they are cut, his lead-ins kept. Its
# appendix (appeal_1840_02: the collectively signed 1838 memorial to the Missouri legislature and Amasa Lyman's
# affidavit) is left out whole.
APPEAL_CUT = [
    r"STATE OF MISSOURI, \}.*?(?=After the election, threatenings)",       # election affidavits (Brown, Nelsons, Daleys)
    r'"I Adam Black, a justice.*?ADAM BLACK, J\. P\."',                    # Adam Black's certificate
    r"State of Missouri\.\}.*?(?=But the case, having undergone)",          # Joseph Smith's affidavit
    r"Head Quarters of the Militia,.*?To S\. D\. LUCAS\.",                  # Boggs's order to Lucas
    r"The following is a short history of my travels.*?DAVID LEWIS\.",     # Haun's Mill: Youngs' and Lewis's testimonies
]


def sidney_rigdon():
    """Rigdon's prose, his revelations and letters of 1856-76, and the Lectures on Faith."""
    rd = RAW / "sidney_rigdon_broadhurst"
    for k, d in enumerate(json.loads((rd / "documents.json").read_text())):
        if d["series"] not in RIG_REG or d["doc_id"] == "appeal_1840_02":
            continue  # appeal_1863 (nominally by others, disputed), the co-signed 1834 circular and the Appeal's appendix excluded
        text = (rd / "text" / f"{d['doc_id']}.txt").read_text()
        if d["doc_id"] == "appeal_1840_01":
            text = cut(text, APPEAL_CUT, d["doc_id"])
        add(doc_id=f"rigdon_{d['doc_id']}", source_id=f"rigdon_{d['series'] if d['series'] == 'appeal_1840' else d['doc_id']}",  # the Appeal is one pamphlet
            source_type="attributed" if d["series"] in ("millennium", "gospel") else "single_author",   # unsigned series
            author="Sidney Rigdon", author_confidence="attributed_print",
            role="candidate", register=RIG_REG[d["series"]], work=f"Rigdon {d['series']}",
            edition="Broadhurst transcription of periodical/pamphlet", date=(d.get("masthead") or "")[:60],
            year=int(m.group(0)) if (m := re.search(r"18\d\d", (d.get("masthead") or "") + " " + d["doc_id"])) else None,
            chunk_group=f"rigdon::{d['series']}", order=k, source_path=str(rd / "text" / f"{d['doc_id']}.txt"),
            notes=d.get("attribution_note"), text=text)


    # More signed Rigdon prose, 1831-46 and one 1873 letter (Broadhurst). Left out: a letter signed
    # jointly with Joseph and Hyrum Smith, and a hymn (verse).
    ra = RAW / "sidney_rigdon_broadhurst_additional"
    for k, d in enumerate(json.loads((ra / "documents.json").read_text())):
        if d["joint_signature"] or d["doc_id"] == "pittsburgh_ma_07":
            continue
        yr = int(m.group(0)) if (m := re.search(r"18\d\d", (d.get("masthead") or "") + " " + d["doc_id"])) else 1846
        add(doc_id=f"rigdon_{d['doc_id']}", author="Sidney Rigdon", author_confidence="signed_print", role="candidate",
            register="letter" if d["doc_id"] == "letter_woodward_1873" else "sermon_essay",
            work=f"Rigdon {d['series']}", edition="Broadhurst transcription", date=(d.get("masthead") or "")[:60], year=yr,
            chunk_group=f"rigdon::{d['series']}", order=k, source_path=str(ra / "text" / f"{d['doc_id']}.txt"),
            notes="abridged by the transcriber (ellipses)" if d["has_ellipsis_excerpts"] else None,
            text=(ra / "text" / f"{d['doc_id']}.txt").read_text())

    # Rigdon's revelations and letters of 1856-76, transcribed from Stephen Post's fair copies (Church History
    # Library MS 1304; prepare/rigdon_revelations.py). Phebe Rigdon's parts and others' text are left out.
    # A part is scripture-style if it has 10 or more archaic markers (thee, unto, saith ...) per 1000 words.
    rr = pl.read_parquet(PREPARED / "rigdon_revelations.parquet").filter(
        pl.col("author").is_in(["sidney", "joint", "unsigned"]))
    for r in rr.iter_rows(named=True):
        add(doc_id=f"rigdon_post_{r['item_id']}_{r['part']}", source_id=f"rigdon_post_{r['item_id']}",
            author="Sidney Rigdon", author_confidence="copyist_fair_copy", role="candidate",
            register="revealed_scripture" if r["scripture_markers_per_1000"] >= 10 else "letter",
            work="Rigdon revelations and letters (1856-76)", edition="Stephen Post's fair copy, transcribed 2026",
            date=r["date"], year=r["year"], scribe="Stephen Post", chunk_group="rigdon::post_books",
            order=int(r["item_id"][1:]) + (0 if r["book"] == "A" else 1000),
            source_type="single_author" if r["author"] == "sidney" and not r["via_newton"] else "attributed",
            source_path="data/prepared/rigdon_revelations.parquet", notes=r["heading"], text=r["text"])

    lec = RAW / "jsp_lectures_on_faith_1835" / "text" / "doctrine-and-covenants-1835.txt"
    add(doc_id="lectures_on_faith_1835", author="Lectures on Faith (mixed, Rigdon-dominant)",
        author_confidence="mixed", role="mixed", register="sermon_essay", work="Lectures on Faith (1835)",
        edition="1835 D&C (JSP)", date="1835", year=1835, chunk_group="lectures_on_faith", source_path=str(lec),
        source_type="mixed_collection",
        text=lines_between(lec, start_pat=r"^Lecture 1$"))      # the D&C title page and the presidents' preface left out


# ----------------------------------------------------------------------------------------------
# 5. Oliver Cowdery
# ----------------------------------------------------------------------------------------------
COWDERY_CUT = {"statement_1836_v2n03": [r'^"This is to make known.*?Egyptian Mummies\."']}   # Michael Chandler's certificate


def oliver_cowdery():
    """Cowdery's periodical writings and his letters (Joseph Smith Papers)."""
    cd = RAW / "oliver_cowdery_periodical_writings"
    for k, d in enumerate(json.loads((cd / "documents.json").read_text())):
        reg = "history_memoir" if d["doc_id"].startswith("letter_") else "sermon_essay"
        text = cut((cd / "text" / f"{d['doc_id']}.txt").read_text(), COWDERY_CUT.get(d["doc_id"], []), d["doc_id"])
        add(doc_id=f"cowdery_{d['doc_id']}", author="Oliver Cowdery", author_confidence="signed_print",
            role="candidate", register=reg, work=f"Cowdery {'Letters I-VIII (history)' if reg == 'history_memoir' else 'editorials'}",
            edition="centerplace.org transcription of M&A / EMS", date=d.get("date"),
            year=int(m.group(0)) if (m := re.search(r"18\d\d", d.get("date") or "")) else None,
            chunk_group=f"cowdery::{reg}", order=k, source_path=str(cd / "text" / f"{d['doc_id']}.txt"),
            notes=d.get("desc"), text=text)
    cl = RAW / "jsp_oliver_cowdery_letters" / "text"
    for k, mf in enumerate(sorted(cl.glob("*.meta.json"))):
        uri = mf.name[: -len(".meta.json")]
        meta, segs = jsp_segments(cl, uri)
        hands = {s for s, _, _ in segs}
        conf = "holograph" if hands == {"Oliver Cowdery"} else "copy_by_other"
        add(doc_id=f"jsp_{uri}", author="Oliver Cowdery", author_confidence=conf, role="candidate", register="letter",
            work="Cowdery letters (JSP)", edition="JSP transcription", date=meta.get("date"), year=jsp_year(meta),
            scribe=", ".join(sorted(hands)), chunk_group=f"cowdery::letter::{conf}", order=k,
            source_path=str(cl / f"{uri}.pages.jsonl"), notes=meta["title"], text="\n\n".join(t for _, _, t in segs))


# ----------------------------------------------------------------------------------------------
# 6. Solomon Spalding
# ----------------------------------------------------------------------------------------------


def solomon_spalding():
    """Spalding's Manuscript Story."""
    sp = RAW / "spalding_manuscript_story" / "manuscriptfoundo00spau.djvu.txt"
    add(doc_id="spalding_manuscript_story", author="Solomon Spalding", author_confidence="autograph_ms_transcribed",
        role="candidate", register="novel", work="Spalding Manuscript Story", edition="RLDS verbatim ed., Lamoni 1885 (OCR)",
        date="c.1812", year=1812, chunk_group="spalding", source_path=str(sp),
        # Two copyist's notes: the first (after p. 132) is mid-story, so the narrative resumes after it; the second ends it
        text=clean_ocr(lines_between(sp, start_pat=r"^INTRODUCTION\.", end_pat=r"Note\s+of\s+Copyist") + "\n"
                       + lines_between(sp, start_pat=r"^Hambolan,\s+King\s+of\s+Chiauga",
                                       end_pat=r"Note\s+of\s+Copyist.*other\s+side")))


# ----------------------------------------------------------------------------------------------
# 7. Parley P. Pratt (Gutenberg)
# ----------------------------------------------------------------------------------------------


# Each text runs from Pratt's first words to his last. Left out: Mormon Texts Project credits, title pages and
# contents, the Key's frontispiece verse and errata; in the Autobiography, the son's preface, John Taylor's "To the
# Public" and poem, the appendix on Pratt's death (with others' accounts and a family genealogy), the transcriber's
# note, and the editor's footnotes. `year` is first publication; `edition` is the printing the text reproduces.
def parley_pratt():
    """Pratt's three books (Gutenberg)."""
    for fn, w, reg, yr, ed, start, end in [
        ("pg35554.txt", "Pratt Voice of Warning", "sermon_essay", 1837, "11th ed., Salt Lake City 1881 (revised from 1837)",
         r"^PREFACE\s*$", None),
        ("pg35470.txt", "Pratt Key to the Science of Theology", "sermon_essay", 1855, "Liverpool 1855 (Gutenberg)",
         r"^PREFACE\.\s*$", r"^ERRATA\."),
        ("pg44896.txt", "Pratt Autobiography", "history_memoir", 1874,
         "Chicago 1888 printing of the 1874 posthumous ed. (P. P. Pratt Jr.)", r"^CHAPTER I\.\s*$", r"^A RESPONSE TO P\. P\. PRATT"),
    ]:
        p = RAW / "pratt_parley" / fn
        text = re.sub(r"^\[Footnote\][^\n]*(?:\n[^\n]+)*", " ", gutenberg_body(p, start, end), flags=re.M)
        add(doc_id=f"pratt_{fn[:-4]}", author="Parley P. Pratt", author_confidence="signed_print", role="candidate",
            register=reg, work=w, edition=ed, date=str(yr), year=yr, chunk_group=f"pratt::{w}", source_path=str(p),
            text=text)


# ----------------------------------------------------------------------------------------------
# 8. Impostors and controls
# ----------------------------------------------------------------------------------------------


def ocr_doc(doc_id, author, reg, work, ed, yr, path, conf="single_author_print", role="impostor", notes=None,
            source_type="single_author", cuts=(), drop_brackets=False, **lb):
    text = cut(clean_ocr(lines_between(path, **lb)), list(cuts), doc_id)
    if drop_brackets:                                    # editors' supplied words and cross-references
        text = re.sub(r"\[[^\]]*\]", " ", text)
    add(doc_id=doc_id, author=author, author_confidence=conf, role=role, register=reg, work=work, edition=ed,
        source_type=source_type,
        date=str(yr), year=yr, chunk_group=f"{doc_id}", source_path=str(path), notes=notes, text=text)


def controls():
    """Biblical-style texts by others, and the other controls."""
    ocr_doc("hunt_late_war", "Gilbert J. Hunt", "pseudo_biblical_history", "Hunt The Late War", "New York 1816 (OCR)", 1816,
            RAW / "late_war_hunt_1816/latewarbetween_00hunt.djvu.txt", start=493, end=10898)
    ocr_doc("napoleon_first_book", "'Eliakim the Scribe' (pseud.)", "pseudo_biblical_history", "The First Book of Napoleon",
            "London 1809 (OCR)", 1809, RAW / "kjv_pastiche_other/firstbooknapole00gruagoog.djvu.txt", start=539,
            end_pat=r"Priated by John Moir")
    for vol, fn, st in [(1, "bim_eighteenth-century_the-american-revolution_snowden-richard_1793_1.djvu.txt", 385),
                        (2, "bim_eighteenth-century_the-american-revolution_snowden-richard_1794_2.djvu.txt", 429)]:  # after the contents
        add(doc_id=f"snowden_vol{vol}", author="Richard Snowden", author_confidence="single_author_print", role="impostor",
            register="pseudo_biblical_history", work="Snowden American Revolution", edition=f"vol. {vol}, 179{2 + vol} (OCR)",
            date=str(1792 + vol), year=1792 + vol, chunk_group="snowden", order=vol, source_id="snowden_american_revolution",
            source_path=str(RAW / "kjv_pastiche_other" / fn), text=clean_ocr(lines_between(RAW / "kjv_pastiche_other" / fn, start=st)))
    ocr_doc("ethan_smith_view_of_hebrews", "Ethan Smith", "treatise", "Ethan Smith View of the Hebrews", "Poultney 1823 (OCR)",
            1823, RAW / "view_of_hebrews_ethan_smith/viewofhebrewsexh00smitrich.djvu.txt", start=165, end=7736, source_type="composite",
            notes="contains long quotations from other authors (Adair, Boudinot, Humboldt...) that masking cannot remove")
    ocr_doc("oahspe", "John Ballou Newbrough", "revealed_scripture", "Oahspe", "1882 text, Forgotten Books vol. 1 of 7 (OCR)",
            1882, RAW / "kjv_register_controls/oahspe0001john.djvu.txt", start=396,
            end=13350)                       # stops before the OCR of the back cover and the reprint publisher's advertising
    # Part I only, from the Proclamation: the publishers' advertisement and contents, their notes and errata, and Part II
    # (testimonies signed by others) are left out, as are the words the publishers supplied in [brackets].
    ocr_doc("shaker_holy_roll", "Philemon Stewart (Shaker)", "revealed_scripture", "Shaker Holy Sacred and Divine Roll",
            "Canterbury NH 1843 (OCR)", 1843, RAW / "kjv_register_controls/holysacreddivine00stew.djvu.txt",
            start_pat=r"^A\s+PROCLAMATION\s*$", end_pat=r"^NOTICE\s+TO\s+ALL\s+WHO\s+MAY\s+READ", drop_brackets=True,
            notes="Part I only; publishers' notes and bracketed supply words removed")
    ocr_doc("whitmer_address", "David Whitmer", "sermon_essay", "Whitmer Address to All Believers", "Richmond MO 1887 (OCR)",
            1887, RAW / "whitmer_address_1887/addresstoallbeli00whit.clean.txt", start_pat=r"^PART FIRST", end_pat=r"^Date Due",
            cuts=[r'"We, the undersigned citizens.*?(?=Besides other false statements)'])   # Richmond citizens; Conservator
    ocr_doc("lucy_mack_smith", "Lucy Mack Smith", "history_memoir", "Lucy Mack Smith Biographical Sketches",
            "Liverpool 1853 (OCR)", 1853, RAW / "lucy_mack_smith_1853/BiographicalSketchesOfJosephSmithTheProphet.clean.txt",
            start_pat=r"^ORSON PRATT\.", end_pat=r"^APPENDIX\s*$", conf="dictated_edited", source_type="composite",
            notes="dictated to the Corays, edited by Orson Pratt; contains inserted documents; "
                  "Pratt's preface and the appendix (Don C. Smith's journal and letters, elegies) left out")
    ocr_doc("campbell_delusions", "Alexander Campbell", "sermon_essay", "Campbell Delusions", "Boston 1832 (OCR)", 1831,
            RAW / "campbell_delusions_1832/delusionsanalysi00camp.clean.txt", start_pat=r"^DELUSIONS\.")
    ocr_doc("campbell_christian_baptist_v1", "Campbell-edited periodicals", "sermon_essay", "Campbell Christian Baptist",
            "vol. 1 (1823-24), 1955 reprint (OCR)", 1823, RAW / "campbell_christian_baptist_v1/cbv-1-sipdf.clean.txt",
            start=41, end_pat=r"^INDEX TO VOLUME I", conf="periodical_mostly_editor", source_type="mixed_collection",
            notes="edited periodical; includes correspondents")
    ocr_doc("campbell_millennial_harbinger_1830", "Campbell-edited periodicals", "sermon_essay", "Campbell Millennial Harbinger",
            "vol. 1 (1830) (OCR)", 1830, RAW / "campbell_millennial_harbinger_1830/millennialharbinger1830.clean.txt",
            start=27, end_pat=r"^INDEX TO VOL\. I\.", conf="periodical_mostly_editor", source_type="mixed_collection",
            notes="edited periodical; includes correspondents and reprints")

    # The gospel only: the title page, Eva S. Dowling's introduction, the contents and subject index, and the
    # transcriber's notes are left out.
    aq = RAW / "kjv_register_controls/pg44073_aquarian_gospel.txt"
    add(doc_id="aquarian_gospel", author="Levi H. Dowling", author_confidence="single_author_print", role="impostor",
        register="revealed_scripture", work="Dowling Aquarian Gospel", edition="London and Los Angeles 1911 printing (Gutenberg)",
        date="1908", year=1908, chunk_group="aquarian_gospel", source_path=str(aq),
        text=gutenberg_body(aq, r"^SECTION I\.\s*$", r"^\[Illustration\]\s*$"))

    st = RAW / "kjv_register_controls/strang_law_1851_strangite_org.html"
    t = st.read_text(errors="ignore")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S)
    t = re.sub(r"<br\s*/?>|</p>|</h\d>|</div>|</li>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    lines = [l.strip() for l in t.split("\n")]
    s = lines.index("CHAPTER 1")       # the witnesses' testimony, the contents and the chapter-source notes left out
    e = max(i for i, l in enumerate(lines) if l.startswith("Grand Total"))
    body = [l for l in lines[s:e] if not re.match(r"^(\(\d+ (chapters|sections).*\)|Return to Table|of Contents)$", l)]
    body = re.sub(r"\(\d+, \d+\)", "", "\n".join(body))
    add(doc_id="strang_book_of_the_law_1851", author="James J. Strang", author_confidence="single_author_print",
        role="impostor", register="revealed_scripture", work="Strang Book of the Law of the Lord", edition="1851 (strangite.org)",
        date="1851", year=1851, chunk_group="strang", source_path=str(st),
        notes="strangite.org forbids re-publication of its electronic text; private analysis only",
        text=re.sub(r"(?<!\n)\n(?!\n)", " ", body))


# Federalist Papers (known-answer control)
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman(s):
    n = 0
    for a, b in zip(s, s[1:] + " "):
        n += -ROMAN[a] if ROMAN.get(b, 0) > ROMAN[a] else ROMAN[a]
    return n


FED_AUTH = {"HAMILTON": "Hamilton", "MADISON": "Madison", "JAY": "Jay",
            "HAMILTON OR MADISON": "Federalist disputed (Hamilton or Madison)",
            "HAMILTON AND MADISON": "Federalist joint (Hamilton and Madison)"}


def federalist():
    """The Federalist Papers, one document per paper."""
    fed = gutenberg_body(RAW / "gutenberg/pg18.txt")
    seen = set()
    for part in fed.split("THE FEDERALIST.")[1:]:
        m = re.match(r"\s*No\. ([IVXLC]+)\.", part)
        am = re.search(r"^(HAMILTON OR MADISON|HAMILTON AND MADISON|HAMILTON|MADISON|JAY)\s*$", part, re.M)
        if not m or not am:
            continue
        num = roman(m.group(1))
        if num in seen:
            continue
        seen.add(num)
        a = FED_AUTH[am.group(1)]
        body = part[am.end():]
        body = re.sub(r"^\s*To the People of the State of New York:?", "", body.strip()).rsplit("PUBLIUS", 1)[0]
        add(doc_id=f"federalist_{num:02d}", author=a, author_confidence="known_answer",
            role="control_disputed" if "disputed" in a else ("control_joint" if "joint" in a else "control"),
            register="political", work=f"Federalist ({a})", edition="Gutenberg #18", date="1787-88", year=1788,
            chunk_group=f"federalist::{a}", order=num, mask_bom=False, source_path=str(RAW / "gutenberg/pg18.txt"),
            text=re.sub(r"(?<!\n)\n(?!\n)", " ", body))


# ----------------------------------------------------------------------------------------------
# 8b. Two-register study: authors with both scripture-style text and plain prose.
#     Texts cleaned by prepare/two_register/clean_<author>.py into data/prepared/two_register/.
#     Strang's scripture side is the 1851 Book of the Law, added above.
# ----------------------------------------------------------------------------------------------
TR = PREPARED / "two_register"
TRANSFER = {   # folder: (author, scripture year, prose year, source_type, files left out)
    "white_richard_grant": ("Richard Grant White", 1863, 1876, "single_author", []),
    "strang": ("James J. Strang", 1851, 1854, "single_author", ["prose__diamond_epistles"]),   # badly garbled OCR
    "thompson_charles_b": ("Charles B. Thompson", 1857, 1841, "single_author", ["scripture__proclamations"]),
    "ilive": ("Jacob Ilive", 1751, 1738, "attributed", []),                    # Jasher: an acknowledged forgery
    "memminger": ("Christopher G. Memminger", 1830, 1851, "attributed",        # attribution probable (Capers 1893)
                  ["prose__bank_argument_1843", "prose__college_orations_1817_1819"]),   # legal genre; juvenilia
}
LONG_S_LEFT = {"fo": "so", "faid": "said"}    # long-s misreadings the cleaning rule could not repair (Ilive prose)


def two_register():
    """Both sides of each two-register author, cleaned in prepare/two_register."""
    for folder, (name, s_year, p_year, stype, skip) in TRANSFER.items():
        for k, f in enumerate(sorted((TR / folder).glob("*.txt"))):
            side, work = f.stem.split("__", 1)
            if f.stem in skip:
                continue
            text = f.read_text()
            if folder == "ilive" and side == "prose":
                text = re.sub(r"\b(fo|faid)\b", lambda m: LONG_S_LEFT[m.group(1)], text)
            add(doc_id=f"transfer_{folder}__{f.stem}", author=name, author_confidence="transfer_study", role="transfer",
                register="revealed_scripture" if side == "scripture" else "prose", work=f"{name}: {work}",
                edition="cleaned OCR (data/prepared/two_register)", date=None, year=s_year if side == "scripture" else p_year,
                chunk_group=f"transfer::{folder}::{side}", order=k, source_type=stype, source_path=str(f), text=text)


# ----------------------------------------------------------------------------------------------
# 9. Quotation masking (runs of 8-grams >= MIN_RUN tokens): KJV and Book of Mormon text in other texts, and any
#    passage two sources share, removed from the later source
# ----------------------------------------------------------------------------------------------
N, MIN_RUN, MAX_GAP = 8, 15, 3
TOK = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def toks(text):
    return [(m.start(), m.end(), m.group(0).lower()) for m in TOK.finditer(text)]


def ngram_set(texts):
    s = set()
    for t in texts:
        w = [x[2] for x in toks(t)]
        s.update(hash(tuple(w[i:i + N])) for i in range(len(w) - N + 1))
    return s


def find_runs(tk, ref):
    cov = [False] * len(tk)
    w = [x[2] for x in tk]
    for i in range(len(w) - N + 1):
        if hash(tuple(w[i:i + N])) in ref:
            for j in range(i, i + N):
                cov[j] = True
    runs, i = [], 0
    while i < len(cov):
        if cov[i]:
            j = i
            while j + 1 < len(cov) and (cov[j + 1] or any(cov[j + 1:j + 2 + MAX_GAP])):
                j += 1
            while not cov[j]:
                j -= 1
            if j - i + 1 >= MIN_RUN:
                runs.append((i, j))
            i = j + 1
        else:
            i += 1
    return runs


SCRIPTURE = {"revealed_scripture", "scripture_kjv"}


def yields_to(d, other) -> bool:
    """True if document d loses a passage it shares with a source dated `other`."""
    (k, scr), (k2, scr2) = (d["date_key"], d["register"] in SCRIPTURE), other
    if k is not None and k2 is not None and k != k2:
        return k2 < k
    return not (scr and not scr2)


def shared_ref(d, doc_grams, owners) -> set:
    """The n-grams d shares with another source that d yields to."""
    return {g for g in doc_grams[id(d)] if g in owners
            and any(sid != d["source_id"] and yields_to(d, o) for sid, o in owners[g].items())}


def mask_quotations(docs: list[dict]) -> list[dict]:
    """Add text_masked and the masking counts to every document; return the Book of Mormon's KJV quotations as
    documents of their own."""
    print("building n-gram references ...")
    kjv_ref = ngram_set([d["text"] for d in docs if d["author"] == "KJV"])
    bom_ref = ngram_set([d["text"] for d in docs if d["role"] == "target"])

    # Passages two sources share. A source loses a passage it shares with an earlier source. On the same date (or a
    # missing one) both lose it, except that scripture keeps a passage shared with a non-scripture text (a letter
    # quoting a revelation of the same day). The target is never masked this way; texts quoting it are (bom_ref).
    doc_grams = {id(d): ngram_set([d["text"]]) for d in docs}
    first, owners = {}, {}
    for d in docs:
        for g in doc_grams[id(d)]:
            f = first.setdefault(g, d["source_id"])
            if f != d["source_id"]:
                owners[g] = None                                           # seen in two or more sources
    for d in docs:
        info = (d["date_key"], d["register"] in SCRIPTURE)
        for g in doc_grams[id(d)]:
            if g in owners:
                owners[g] = owners[g] or {}
                owners[g][d["source_id"]] = info
    del first

    quote_docs = []
    for d in docs:
        text = d["text"]
        tk = toks(text)
        spans = []
        if d["mask_kjv"]:
            spans += [("kjv", tk[i][0], tk[j][1], j - i + 1) for i, j in find_runs(tk, kjv_ref)]
        if d["mask_bom"]:
            spans += [("bom", tk[i][0], tk[j][1], j - i + 1) for i, j in find_runs(tk, bom_ref)]
        if d["role"] != "target":
            spans += [("shared", tk[i][0], tk[j][1], j - i + 1) for i, j in find_runs(tk, shared_ref(d, doc_grams, owners))]
        spans.sort(key=lambda x: x[1])
        out, last, kjv_n, bom_n, shared_n, removed = [], 0, 0, 0, 0, []
        for kind, a, b, n in spans:
            if b <= last:
                continue
            a = max(a, last)                                               # overlapping spans: remove the union
            out.append(text[last:a])
            out.append("\n\n")
            if kind == "kjv":
                removed.append(text[a:b])
            last = b
            kjv_n += n if kind == "kjv" else 0
            bom_n += n if kind == "bom" else 0
            shared_n += n if kind == "shared" else 0
        out.append(text[last:])
        d["text_masked"] = normalize("".join(out))
        d["n_tokens"] = len(tk)
        d["kjv_masked_tokens"] = kjv_n
        d["bom_masked_tokens"] = bom_n
        d["shared_masked_tokens"] = shared_n
        d["masked_frac"] = round((kjv_n + bom_n + shared_n) / max(len(tk), 1), 4)
        if d["role"] == "target" and removed:
            quote_docs.append(dict(d, doc_id=d["doc_id"] + "__kjv_quotes", source_id=d["doc_id"] + "__kjv_quotes",
                                   author="KJV (quoted in BoM)",
                                   author_confidence="positive_control", role="positive_control",
                                   register="scripture_kjv", work="BoM KJV quotations (Isaiah etc.)",
                                   chunk_group="bom_kjv_quotations", text="\n\n".join(removed),
                                   text_masked=normalize("\n\n".join(removed)), notes="spans masked out of the BoM"))
    return quote_docs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for load in [book_of_mormon, kjv, smith_writings, smith_revelations, sidney_rigdon, oliver_cowdery,
                 solomon_spalding, parley_pratt, controls, federalist, two_register]:
        load()
    DOCS.extend(mask_quotations(DOCS))
    for d in DOCS:
        d["words"] = len(d["text_masked"].split())

    df = pl.DataFrame(DOCS, infer_schema_length=None).drop("mask_kjv", "mask_bom")
    df.write_parquet(OUT / "documents.parquet")
    summary = (df.group_by("author", "role").agg(pl.len().alias("docs"), pl.col("words").sum(),
                                                 pl.col("kjv_masked_tokens").sum(), pl.col("bom_masked_tokens").sum(),
                                                 pl.col("shared_masked_tokens").sum())
               .sort("role", "words", descending=[False, True]))
    with pl.Config(tbl_rows=60, tbl_width_chars=160, fmt_str_lengths=50):
        print(summary)
    print("documents:", df.height, "words:", df["words"].sum())


if __name__ == "__main__":
    main()
