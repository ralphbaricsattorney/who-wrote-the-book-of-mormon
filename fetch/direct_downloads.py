"""Download single files saved exactly as served: Project Gutenberg texts, the LDS scriptures JSON,
the Jockers, Witten and Criddle (2008) word-frequency matrix, and the strangite.org Book of the Law.

Run:  python fetch/direct_downloads.py
"""
from common import RAW, download

GUTENBERG = "https://www.gutenberg.org/cache/epub/{0}/pg{0}.txt"
SCRIPTURES = "https://raw.githubusercontent.com/bcbooks/scriptures-json/HEAD/{}"
FILES = [  # (url, path under data/raw)
    (GUTENBERG.format(18), "gutenberg/pg18.txt"),
    (GUTENBERG.format(35554), "pratt_parley/pg35554.txt"),
    (GUTENBERG.format(35470), "pratt_parley/pg35470.txt"),
    (GUTENBERG.format(44896), "pratt_parley/pg44896.txt"),
    (GUTENBERG.format(44073), "kjv_register_controls/pg44073_aquarian_gospel.txt"),
    ("http://www.strangite.org/Law.htm", "kjv_register_controls/strang_law_1851_strangite_org.html"),
    *[(SCRIPTURES.format(f), f"lds_scriptures_json/{f}") for f in
      ["README.md", "old-testament.json", "new-testament.json", "book-of-mormon.json",
       "doctrine-and-covenants.json", "pearl-of-great-price.json"]],
    ("https://stacks.stanford.edu/file/druid:rs276tc2764/dataMatrix.txt",
     "jockers_witten_criddle_2008_supplement/dataMatrix.txt"),
]

if __name__ == "__main__":
    for url, path in FILES:
        print(url)
        download(url, RAW / path, delay=2)
