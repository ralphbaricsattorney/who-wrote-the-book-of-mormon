"""Assemble the page transcriptions of Rigdon's revelations (Stephen Post papers) into attributed items.

Input:  data/raw/rigdon_revelations_transcription/{A,B}_NNN.txt   (one file per page image; prepare/rigdon_protocol.md)
Output: data/prepared/rigdon_revelations.parquet  one row per item part, with attribution

An item is the text under one `## heading:` line. A heading-less run at the start of a volume belongs to no
item. Within an item the text is cut at every `## signed:` line, and each part is attributed to its signer:
    sidney   signed by Sidney Rigdon alone (including "Sidney Rigdon per Phebe Rigdon", his words in her hand)
    joint    signed by both Sidney and Phebe
    phebe    signed by Phebe alone, or introduced by the copyist's note "P.S. by Phebe"
    other    signed by anyone else (Stephen Post, Joseph Smith, Sylvester Smith, ...)
    unsigned no signature, or signed in the name of "Phineas", an angelic voice in these revelations
"Attest ..." lines are witnesses and do not divide the text.
A trailing part after the last signature takes the item's last signer. Whole items that are not Rigdon
material (minutes, a patriarchal blessing, a certificate, an angel's message to Evva Adams, an extract from a
printed paper) are kept with author "other".

Clean-up applied to the text (structure lines are never part of it):
  * words split across a page turn are rejoined ("opera-" + "-ative", "citi" + "zens")
  * the copyist's omission marks ("x x x") are removed
  * "[?]" marks are removed, keeping the word; "[illegible]" is removed
The loose sheets (L_NNN) are not assembled: they are used only to check Post's copying.

Run: python prepare/rigdon_revelations.py
"""
import re
from pathlib import Path

import polars as pl

import vocabulary

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "rigdon_revelations_transcription"
OUT = ROOT / "data" / "prepared"
OUT.mkdir(parents=True, exist_ok=True)

NOT_RIGDON = re.compile(r"Patriarchal blessing|Minutes of a conference|Nauvoo|Angel of the Lord's communication"
                        r"|^Extract$|Messenger & Advocate Extra|Book of revelations Through the Holy Ghost", re.I)
SCRIPTURE_MARKERS = re.compile(r"\b(thee|thou|thy|thine|ye|hath|doth|unto|saith|verily|behold|lo|yea|shalt|wilt"
                               r"|i the lord|thus saith)\b", re.I)

# vocabulary for rejoining words split across pages without a hyphen
vocab = set(vocabulary.tokens())


def signer(line: str) -> str:
    s = line.lower()
    if "phineas" in s:                    # an angelic voice in Rigdon's revelations: his text, signed in its name
        return "unsigned"
    sidney = bool(re.search(r"sidney|\bs\.? ?rigdon|\bs\.r\.|from s rigdon", s))
    phebe = bool(re.search(r"phebe|\bp\.? rigdon", s))
    if "per. phebe" in s or "per phebe" in s:
        return "sidney"
    if sidney and phebe:
        return "joint"
    return "sidney" if sidney else "phebe" if phebe else "other"


def page_lines(book: str):
    """Every line of every text page of one volume, in page order, tagged with its page."""
    for f in sorted(SRC.glob(f"{book}_*.txt")):
        text = f.read_text()
        if not re.search(r"^# status:\s*text", text, re.M):
            continue
        lines = [l for l in text.splitlines() if not l.startswith("# ")]
        yield f.stem, [l for l in lines if l.strip()]


def join_page_turns(pages):
    """Rejoin a word split across two pages; yields (page, line) pairs."""
    pages = [(p, list(ls)) for p, ls in pages]
    for (p1, l1), (p2, l2) in zip(pages, pages[1:]):
        body1 = [i for i, l in enumerate(l1) if not l.startswith("##")]
        body2 = [i for i, l in enumerate(l2) if not l.startswith("##")]
        if not body1 or not body2:
            continue
        a, b = l1[body1[-1]], l2[body2[0]]
        last, first = a.split()[-1], b.split()[0]
        joined = last.rstrip("-") + first.lstrip("-")
        word = re.sub(r"[^a-z]", "", joined.lower())
        if last.endswith("-") or first.startswith("-") or (
                word in vocab and re.sub(r"[^a-z]", "", last.lower()) not in vocab):
            l1[body1[-1]] = a[: len(a) - len(last)] + joined
            l2[body2[0]] = b[len(first):].lstrip()
    for p, ls in pages:
        for l in ls:
            yield p, l


def clean(text: str) -> str:
    text = re.sub(r"\[illegible\]", " ", text)
    text = text.replace("[?]", "")
    text = re.sub(r"(?<![a-z])x(?: x){2,}(?![a-z])", " ", text)          # the copyist's omission marks
    return re.sub(r"[ \t]+", " ", text).strip()


rows = []
for book in ("A", "B"):
    item, n = None, 0
    for page, line in join_page_turns(page_lines(book)):
        if line.startswith("## heading:"):
            n += 1
            heading = line.split(":", 1)[1].strip()
            item = dict(book=book, n=n, heading=heading, date=None, pages=[page], parts=[[]], signers=[],
                        not_rigdon=bool(NOT_RIGDON.search(heading)), phebe_next=False, notes=[])
            rows.append(item)
            continue
        if item is None:
            continue
        if page not in item["pages"]:
            item["pages"].append(page)
        if line.startswith("## date:") and item["date"] is None:
            item["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("## note:"):
            note = line.split(":", 1)[1].strip()
            item["notes"].append(note)
            if re.search(r"P\.S\. by Phebe", note):
                item["parts"].append([])
                item["signers"].append(None)          # placeholder: the part before is closed unsigned
                item["phebe_next"] = True
        elif line.startswith("## signed:") and "attest" in line.lower():
            item["notes"].append(line)        # a witness's attestation, not an author's signature
        elif line.startswith("## signed:"):
            item["signers"].append("phebe" if item["phebe_next"] else signer(line))
            item["phebe_next"] = False
            item["parts"].append([])
        elif not line.startswith("##"):
            item["parts"][-1].append(line)

records = []
for it in rows:
    signers = [s for s in it["signers"] if s is not None]
    last = signers[-1] if signers else None
    parts = []
    for i, lines in enumerate(it["parts"]):
        who = it["signers"][i] if i < len(it["signers"]) else last
        if who is None:
            who = last
        if it["not_rigdon"]:
            who = "other"
        text = clean("\n".join(lines))
        if text:
            parts.append((who or "unsigned", text))
    year = re.search(r"18\d\d", (it["date"] or "") + " " + it["heading"])
    item_id = f"{it['book']}{it['n']:03d}"
    sec = re.search(r"Sec(?:tion)?\.?\s*(\d+)", it["heading"])
    for k, (who, text) in enumerate(parts):
        words = len(text.split())
        records.append(dict(
            item_id=item_id, part=k, book=it["book"], section=int(sec.group(1)) if sec else None,
            heading=it["heading"], date=it["date"], year=int(year.group(0)) if year else None,
            pages=", ".join(it["pages"]), author=who, words=words,
            scripture_markers_per_1000=round(1000 * len(SCRIPTURE_MARKERS.findall(text)) / max(words, 1), 1),
            via_newton=any("Newton" in x for x in it["notes"]), text=text))

items = pl.DataFrame(records)
# Fill a missing year from the nearest dated item before it in the same volume (the books run in date order)
items = items.with_columns(pl.col("year").forward_fill().over("book"))
items.write_parquet(OUT / "rigdon_revelations.parquet")

with pl.Config(tbl_rows=20, tbl_width_chars=150):
    print(items.group_by("author").agg(pl.len().alias("parts"), pl.col("words").sum()).sort("words", descending=True))
print("items:", items["item_id"].n_unique(), "| parts:", items.height, "| years:", items["year"].min(), "-", items["year"].max())
