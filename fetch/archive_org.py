"""Download Internet Archive OCR texts.

For each item: data/raw/<dir>/<id>.metadata.json (https://archive.org/metadata/<id>) and
data/raw/<dir>/<id>.djvu.txt (the item's first *_djvu.txt file). Items marked `clean` also get
<id>.clean.txt: line-end hyphens repaired and wrapped lines joined, nothing else changed.

Run:  python fetch/archive_org.py
"""
from __future__ import annotations

import json
import re
import urllib.parse

from common import RAW, download

TR = "two_register_authors"
ITEMS = [  # (directory under data/raw, archive.org identifier, make .clean.txt)
    ("spalding_manuscript_story", "manuscriptfoundo00spau", False),
    ("late_war_hunt_1816", "latewarbetween_00hunt", False),
    ("view_of_hebrews_ethan_smith", "viewofhebrewsexh00smitrich", False),
    ("kjv_pastiche_other", "firstbooknapole00gruagoog", False),
    ("kjv_pastiche_other", "bim_eighteenth-century_the-american-revolution_snowden-richard_1793_1", False),
    ("kjv_pastiche_other", "bim_eighteenth-century_the-american-revolution_snowden-richard_1794_2", False),
    ("kjv_register_controls", "oahspe0001john", False),
    ("kjv_register_controls", "holysacreddivine00stew", False),
    ("whitmer_address_1887", "addresstoallbeli00whit", True),
    ("lucy_mack_smith_1853", "BiographicalSketchesOfJosephSmithTheProphet", True),
    ("campbell_delusions_1832", "delusionsanalysi00camp", True),
    ("campbell_christian_baptist_v1", "cbv-1-sipdf", True),
    ("campbell_millennial_harbinger_1830", "millennialharbinger1830", True),
    (f"{TR}/strang/prose", "ancientmodernm1885stra", False),
    (f"{TR}/strang/prose", "diary00stra", False),
    (f"{TR}/strang/prose", "propheticcontr1878stra", False),
    (f"{TR}/strang/prose", "diamondbeinglawo02stra", False),
    (f"{TR}/white_richard_grant/scripture", "newgospelofpeac00whit", False),
    (f"{TR}/white_richard_grant/prose", "wordsandthieruses00whitrich", False),
    (f"{TR}/white_richard_grant/prose", "englandwithoutwi01whit", False),
    (f"{TR}/thompson_charles_b/scripture", "lawscovenantsofi00thom", False),
    (f"{TR}/thompson_charles_b/prose", "evidencesinproof00thom_0", False),
    (f"{TR}/ilive/scripture", "bookofjasherwith00iliv", False),
    (f"{TR}/ilive/scripture", "bim_eighteenth-century_the-book-of-jasher_ilive-jacob_1751", False),
    (f"{TR}/ilive/prose", "bim_eighteenth-century_the-oration-spoke-at-joy_ilive-jacob_1733", False),
    (f"{TR}/ilive/prose", "bim_eighteenth-century_the-oration-spoke-at-tri_ilive-jacob_1738", False),
    (f"{TR}/ilive/prose", "bim_eighteenth-century_the-speech-of-mr-jacob-_ilive-jacob_1750", False),
    (f"{TR}/ilive/prose", "bim_eighteenth-century_reasons-offered-for-the-_ilive-jacob_1757", False),
    (f"{TR}/ilive/prose", "bim_eighteenth-century_the-laymans-vindication_ilive-jacob_1730", False),
    (f"{TR}/memminger/scripture", "bookofnullificat00char", False),
    (f"{TR}/memminger/prose", "addressofhoncgme00memm", False),
    (f"{TR}/memminger/prose", "lecturedelivered00memm", False),
    (f"{TR}/memminger/prose", "cu31924032767505", False),
]


def clean_ocr(src, dst) -> int:
    t = src.read_text(encoding="utf-8", errors="replace").replace("\r", "")
    t = re.sub(r"(\w)[-­]\s*\n\s*(\w)", r"\1\2", t)        # de-hyphenate across line breaks
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)                        # join wrapped lines; blank line = paragraph
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    dst.write_text(t.strip() + "\n")
    return len(t.split())


def fetch_item(dest: str, ident: str, clean: bool) -> None:
    d = RAW / dest
    meta = json.loads(download(f"https://archive.org/metadata/{ident}", d / f"{ident}.metadata.json", delay=2))
    ocr = next(f["name"] for f in meta["files"] if f["name"].endswith("_djvu.txt"))
    txt = d / f"{ident}.djvu.txt"
    download(f"https://archive.org/download/{ident}/{urllib.parse.quote(ocr)}", txt, delay=2)
    if clean:
        print(f"  {ident}.clean.txt", clean_ocr(txt, d / f"{ident}.clean.txt"), "words")


if __name__ == "__main__":
    for item in ITEMS:
        print(item[1])
        fetch_item(*item)
