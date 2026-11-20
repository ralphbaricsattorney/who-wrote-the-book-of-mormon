"""Fetch page images of Sidney Rigdon's revelations, 1856-76, in the Stephen Post papers (Church History Library,
MS 1304, box 3, folders 11-13). These images were transcribed for the study; no transcription is published.

The catalog (catalog.churchofjesuschrist.org) serves JSON:
  POST /api/catalog/search  every record under call number MS 1304 (20 per page)
  POST /api/catalog/record  a folder's first 25 image ids ("flid") and a nextPage pointer
  POST /api/catalog/child   the next 25 image ids
  GET  /api/delivery/<image id>  full-resolution JPEG
Writes data/raw/sidney_rigdon_revelations_post_papers_chl/raw/catalog/*.json (responses as served),
raw/images/<folder>/<original file name>.jpg and images_manifest.csv. Resumable; 1.5 s between requests.

Run:  python fetch/chl_post_papers.py
"""
from __future__ import annotations

import csv
import json
import os

from common import RAW, request

B = "https://catalog.churchofjesuschrist.org"
OUT = RAW / "sidney_rigdon_revelations_post_papers_chl"
DELAY = 1.5
FOLDERS = [  # (local name, digital-object record id, call number, title)
    ("b0003_f0011_revelations_loose", "12c41b2a-4c06-4753-94a6-53db5788a099", "MS 1304/b0003/f0011", "Revelations (loose sheets)"),
    ("b0003_f0012_revelations_book_A_1863-1873", "c85ca354-3148-4aee-a72b-191eaf1bb8d4", "MS 1304/b0003/f0012", "Revelations, Book A, 1863-1873"),
    ("b0003_f0013_revelations_book_B_1873-1876", "85e2c056-f2ff-42cc-94fd-3e400064024e", "MS 1304/b0003/f0013", "Revelations, Book B, 1873-1876"),
]


def post(path, body, cache):
    if cache.exists():
        return json.loads(cache.read_bytes())
    r = request("POST", B + path, DELAY, json=body, headers={"Accept": "application/json"})
    r.raise_for_status()
    cache.write_bytes(r.content)
    return r.json()


def fetch_image(url, fn):
    for _ in range(4):
        r = request("GET", url, DELAY)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            part = fn.with_name(fn.name + ".part")
            part.write_bytes(r.content)
            part.replace(fn)
            return
        print("  HTTP", r.status_code, url)
    raise RuntimeError(f"giving up on {url}")


def main():
    cat = OUT / "raw" / "catalog"
    cat.mkdir(parents=True, exist_ok=True)
    page = 1
    while True:
        d = post("/api/catalog/search",
                 {"terms": [{"field": "callNumber", "operator": "QUERY_CONTAINS", "value": "MS 1304", "logical": "AND"}],
                  "facets": [], "sort": [{"field": "componentPath", "direction": "ASC"}], "page": page, "limit": 20},
                 cat / ("search_p%02d.json" % page))
        if d.get("last") or page >= d.get("totalPages", 1):
            break
        page += 1
    rows = []
    for name, rid, dcid, title in FOLDERS:
        d = post("/api/catalog/record", {"ids": [rid], "forcePublic": False, "paginate": False, "getChildren": True, "verbose": True},
                 cat / f"{name}.record.json")
        rel = d["results"]["result"][0]["relation"]
        fl, nxt = list(rel.get("flid", [])), rel.get("nextPage")
        while nxt:
            c = post("/api/catalog/child", {"parentId": nxt["parentId"], "offset": nxt["offset"]},
                     cat / ("%s.children_%04d.json" % (name, int(nxt["offset"]))))
            fl += c["page"].get("flid", [])
            nxt = c["page"].get("nextPage")
        print(name, len(fl), "images", flush=True)
        idir = OUT / "raw" / "images" / name
        idir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(fl, 1):
            fn = idir / f["title"].replace(" ", "_").replace(".JPG", ".jpg")
            url = B + "/api/delivery/" + f["id"]
            if not fn.exists():
                fetch_image(url, fn)
            rows.append({"folder": name, "dcid": dcid, "folder_title": title, "seq": i, "source_name": f["title"],
                         "image_id": f["id"], "image_url": url,
                         "viewer_url": "%s/assets/%s/0/%d" % (B, rid, i - 1),
                         "local_file": os.path.relpath(fn, OUT), "bytes": fn.stat().st_size})
    with open(OUT / "images_manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("done", len(rows), "images")


if __name__ == "__main__":
    main()
