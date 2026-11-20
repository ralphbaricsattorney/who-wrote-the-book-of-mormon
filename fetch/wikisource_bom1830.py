"""Fetch the Book of Mormon, first edition (Palmyra, 1830), from English Wikisource, one file per 1830 chapter.

Uses the MediaWiki API (action=parse) on the pages "Book of Mormon (1830)/<book>/Chapter N".
Writes data/raw/bom_1830_wikisource/html/<NN>_<Book>_chMM.html (rendered page), txt/<same>.txt (plain text,
page-number markers removed) and manifest.json (file, book, 1830 chapter, Wikisource page, words).

Run:  python fetch/wikisource_bom1830.py
"""
import html as H
import json
import re

from common import RAW, request

API = "https://en.wikisource.org/w/api.php"
OUT = RAW / "bom_1830_wikisource"
BOOKS = ["Preface", "1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni", "Words of Mormon", "Mosiah", "Alma",
         "Helaman", "3 Nephi", "4 Nephi", "Mormon", "Ether", "Moroni", "Three Witnesses", "Eight Witnesses"]


def api(**params):
    r = request("GET", API, delay=2.5, tries=8, params={**params, "format": "json", "formatversion": 2})
    r.raise_for_status()
    return r.json()["parse"]


def to_text(h):
    h = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S)
    h = re.sub(r'<span[^>]*class="[^"]*pagenum[^"]*"[^>]*>.*?</span>', ' ', h, flags=re.S)  # page number markers
    h = re.sub(r'<div[^>]*class="[^"]*(wst-header|ws-noexport|licenseContainer)[^"]*".*?</div>', '', h, flags=re.S)
    h = re.sub(r'<br\s*/?>', '\n', h)
    h = re.sub(r'</p>|</div>|</h\d>', '\n\n', h)
    t = H.unescape(re.sub(r'<[^>]+>', '', h))
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n\n', t)
    return t.strip()


def main():
    (OUT / "html").mkdir(parents=True, exist_ok=True)
    (OUT / "txt").mkdir(exist_ok=True)
    manifest = []
    for bi, b in enumerate(BOOKS, 1):
        page = f"Book of Mormon (1830)/{b}"
        links = [l["title"] for l in api(action="parse", page=page, prop="links")["links"]
                 if l["title"].startswith(page + "/Chapter")]
        links.sort(key=lambda s: int(re.search(r'(\d+)$', s).group(1)))
        for t in links or [page]:
            ch = re.search(r'Chapter (\d+)$', t)
            ch = int(ch.group(1)) if ch else 0
            stem = f"{bi:02d}_{b.replace(' ', '_')}_ch{ch:02d}"
            txt_path = OUT / "txt" / f"{stem}.txt"
            if txt_path.exists():
                txt = txt_path.read_text()
            else:
                p = api(action="parse", page=t, prop="text")["text"]
                (OUT / "html" / f"{stem}.html").write_text(p)
                txt = to_text(p)
                txt_path.write_text(txt)
                print(stem, len(txt.split()), flush=True)
            manifest.append({"file": f"txt/{stem}.txt", "book": b, "chapter_1830": ch, "wikisource_page": t,
                             "words": len(txt.split())})
    json.dump(manifest, open(OUT / "manifest.json", "w"), indent=1)


if __name__ == "__main__":
    main()
