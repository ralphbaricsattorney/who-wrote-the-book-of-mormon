"""Fetch Joseph Smith Papers (josephsmithpapers.org) transcriptions.

The site is a Next.js app. Each document page's data is served as JSON at
  https://www.josephsmithpapers.org/_next/data/<buildId>/paper-summary/<uri>/<page>.json
with the buildId read from the home page. One connection, 1.2 s between requests. Resumable: pages
already on disk are not fetched again.

For each document URI, in data/raw/<dir>/:
  raw/<uri>/pNNNN.json            page JSON without site chrome (intro and source notes on p0001 only)
  text/<uri>.txt                  reading text (clearText), all hands, no page labels
  text/<uri>.pages.jsonl          per page: page, label, page_scribes, segments [{scribe, js_hand, text}]
  text/<uri>.by_scribe/<hand>.txt text per hand (documents with more than one hand or any of Smith's hand)
  text/<uri>.meta.json            title, date, handwriting statement, source note, word counts
Multi-item documents (Revelation Book 2) are also cut at JSP's item markers into
  items/<uri>/<seq>_<title>.txt and items/<uri>.items.jsonl / .items.tsv

Run:  python fetch/jsp.py [dir ...]        (default: every directory in JOBS)
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import time

from lxml import html as LH

from common import HERE, RAW, request

BASE = "https://www.josephsmithpapers.org"
LISTS = HERE / "jsp"


def uris(name: str) -> list[str]:
    return [u.strip() for u in (LISTS / name).read_text().splitlines() if u.strip()]


JOBS = [  # (directory under data/raw, document URIs, page range or None, split into items)
    ("jsp_joseph_smith_early_writings", uris("uris_smith_early.txt"), None, False),
    ("jsp_oliver_cowdery_letters", uris("uris_cowdery.txt"), None, False),
    ("jsp_joseph_smith_later_writings", uris("uris_smith_later.txt"), None, False),
    ("jsp_revelation_book_1_and_book_of_commandments", ["revelation-book-1", "book-of-commandments-1833"], None, False),
    ("jsp_revelation_book_2_and_doctrine_and_covenants", ["revelation-book-2"], None, True),
    ("jsp_lectures_on_faith_1835", ["doctrine-and-covenants-1835"], (9, 82), False),   # the Lectures only
]
# Hand-written composition judgments (from the JSP introductions) that 01_build_corpus.py reads
EXTRA = {"jsp_joseph_smith_later_writings": ["composition_notes.tsv"]}

_BID = None


def build_id(refresh=False):
    global _BID
    if _BID and not refresh:
        return _BID
    r = request("GET", BASE + "/")
    _BID = re.search(r'"buildId":"([^"]+)"', r.text).group(1)
    return _BID


def get_page(uri, page):
    for _ in range(4):
        r = request("GET", f"{BASE}/_next/data/{build_id()}/paper-summary/{uri}/{page}.json",
                    headers={"Accept": "application/json,text/html;q=0.9"})
        if r.status_code == 404:          # the site was redeployed: new buildId
            build_id(refresh=True)
            continue
        if r.status_code != 200:
            print("  HTTP", r.status_code, uri, page, file=sys.stderr)
            time.sleep(10)
            continue
        pp = r.json().get("pageProps", {})
        if pp.get("summary"):
            return pp
        time.sleep(5)
    return None


def trim(pp, first):
    keep = {k: v for k, v in pp.items() if k not in ("metaStrings", "layoutStrings", "env")}
    s = dict(keep.get("summary") or {})
    if not first:  # these repeat on every page
        for k in ("historicalIntro", "sourceNotes"):
            s.pop(k, None)
    keep["summary"] = s
    return keep


SCRIBE_BEGINS = re.compile(r"(?:^|;)\s*([^;]+?)\s+(?:handwriting\s+)?begins\b", re.S)
ALIASES = {"JS": "Joseph Smith Jr.", "Joseph Smith": "Joseph Smith Jr."}


def ws(t):
    return re.sub(r"\s+", " ", t)


def norm_scribe(name):
    name = ws(name).strip()
    if re.match(r"(?i)^scribe \d+$", name):
        name = "Scribe " + name.split()[1]
    return ALIASES.get(name, name)


def extract(clear_html, start_scribe):
    """Segments [{scribe, js_hand, text}] of a page's clearText, and the hand in force at its end.

    A segment's hand is Smith's where JSP marks `josephswriting`, else the hand named by the latest
    "new scribe" note, else the page's single listed scribe carried forward.
    """
    if not clear_html or not clear_html.strip():
        return [], start_scribe
    root = LH.fromstring(clear_html)
    segs = []
    state = {"scribe": start_scribe}

    def emit(text, js):
        if not text:
            return
        sc = "Joseph Smith Jr." if js else state["scribe"]
        if segs and segs[-1][0] == sc and segs[-1][1] == js:
            segs[-1][2].append(text)
        else:
            segs.append([sc, js, [text]])

    def emit_tail(el, js):
        if el.tail:
            emit(el.tail, js)

    def walk(el, js):
        cls = el.get("class") or ""
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag == "aside":
            a = el.find("a")
            acls = (a.get("class") or "") if a is not None else ""
            if "new-scribe-note" in acls:
                note = " ".join(el.xpath(".//div[contains(@class,'popup-content')]//text()"))
                m = [x for x in SCRIBE_BEGINS.finditer(ws(note)) if " ends" not in x.group(1)]
                if m:
                    state["scribe"] = norm_scribe(m[0].group(1))
                elif "signature" in note.lower():
                    state["scribe"] = "Signatures (individual)"
                elif "ends" in note:
                    state["scribe"] = "UNKNOWN(after: %s)" % ws(note).strip()[:60]
                emit_tail(el, js)
                return
            if a is not None and "reference" in acls and "editorial" not in acls:
                walk(a, js)  # keep linked text, drop popup content
            emit_tail(el, js)
            return
        if "popup-content" in cls or "editorial-comment" in cls or "note-data" in cls:
            emit_tail(el, js)
            return
        if tag in ("script", "style", "head", "img", "input"):
            emit_tail(el, js)
            return
        js2 = js or ("josephswriting" in cls.split())
        if tag in ("div", "p", "br"):
            emit("\n", js2) if tag != "br" else emit(" ", js2)
        if el.text:
            emit(el.text, js2)
        for ch in el:
            walk(ch, js2)
        if tag in ("div", "p"):
            emit("\n", js2)
        emit_tail(el, js)

    body = root.find(".//body")
    walk(body if body is not None else root, False)
    out = []
    for sc, js, parts in segs:
        t = "".join(parts)
        t = re.sub(r"[ \t ​]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        t = re.sub(r"\n{2,}", "\n", t)
        if t.strip():
            out.append({"scribe": sc, "js_hand": js, "text": t})
    return out, state["scribe"]


def source_note_text(s1):
    t = (s1.get("sourceNotes") or {}).get("text")
    if not t:
        return None
    root = LH.fromstring(t)
    for el in root.xpath("//div[contains(@class,'popup-content')]"):
        el.drop_tree()
    return re.sub(r"\s+", " ", root.text_content()).strip()[:3000]


PAGELABEL = re.compile(r"\s*\[p\. \[?[^\]\[]{0,12}\]?\]|\[\]")


def strip_labels(t):
    """Remove page labels such as '[p. 73]' or '[p. [ii]]' and empty '[]'."""
    return re.sub(r"[ \t]{2,}", " ", PAGELABEL.sub("", t))


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "unknown"


def load_or_fetch(path, uri, page, first):
    if os.path.exists(path):
        return json.load(open(path))
    pp = get_page(uri, page)
    if not pp:
        return None
    d = trim(pp, first)
    json.dump(d, open(path, "w"), ensure_ascii=False)
    return d


def fetch_doc(outdir, uri, page_range=None):
    rawdir = os.path.join(outdir, "raw", uri)
    txtdir = os.path.join(outdir, "text")
    os.makedirs(rawdir, exist_ok=True)
    os.makedirs(txtdir, exist_ok=True)
    first = load_or_fetch(os.path.join(rawdir, "p0001.json"), uri, 1, True)
    if not first:
        print("FAILED", uri)
        return
    gallery = first.get("gallery") or []
    pages = [g["page"] for g in gallery] or ["1"]
    if page_range:
        a, b = page_range
        pages = [p for p in pages if a <= int(p) <= b]
    labels = {g["page"]: g.get("label") for g in gallery}
    recs = []
    scribe = None
    for p in pages:
        d = load_or_fetch(os.path.join(rawdir, "p%04d.json" % int(p)), uri, p, False)
        if not d:
            print("  page failed", uri, p)
            recs.append({"page": p, "error": True})
            continue
        s = d["summary"]
        psc = [norm_scribe(x.get("name")) for x in (s.get("scribes") or []) if x.get("name")]
        if len(psc) == 1:
            scribe = psc[0]
        elif scribe is None and psc:
            scribe = psc[0] + " (first-listed of: %s)" % "; ".join(psc)
        segs, scribe = extract(s.get("clearText") or "", scribe or "UNATTRIBUTED")
        recs.append({"page": p, "label": labels.get(p), "page_scribes": psc, "segments": segs})
    with open(os.path.join(txtdir, uri + ".pages.jsonl"), "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    allsegs = [sg for r in recs for sg in r.get("segments", [])]
    full = re.sub(r"\n{2,}", "\n", strip_labels("".join(sg["text"] for sg in allsegs))).strip() + "\n"
    open(os.path.join(txtdir, uri + ".txt"), "w").write(full)
    by = {}
    for sg in allsegs:
        by.setdefault(sg["scribe"], []).append(sg["text"])
    counts = {k: len(strip_labels("".join(v)).split()) for k, v in by.items()}
    if len(by) > 1 or any(sg["js_hand"] for sg in allsegs):
        bd = os.path.join(txtdir, uri + ".by_scribe")
        os.makedirs(bd, exist_ok=True)
        for k, v in by.items():
            text = re.sub(r"\n{2,}", "\n", strip_labels("".join(v))).strip() + "\n"
            open(os.path.join(bd, safe(k) + ".txt"), "w").write(text)
    s1 = first["summary"]
    meta = {
        "uri": uri, "url": f"{BASE}/paper-summary/{uri}/1",
        "title": s1.get("cleanEditorialTitle") or s1.get("editorialTitle"),
        "date": s1.get("date"), "handwriting": s1.get("handwriting"),
        "classification": s1.get("classification"), "numberOfPages": s1.get("numberOfPages"),
        "pages_fetched": len([r for r in recs if not r.get("error")]),
        "pages_failed": [r["page"] for r in recs if r.get("error")],
        "word_count": len(full.split()), "words_by_scribe": counts,
        "js_hand_words": sum(len(sg["text"].split()) for sg in allsegs if sg["js_hand"]),
        "source_note": source_note_text(s1),
        "fetched": time.strftime("%Y-%m-%d"),
    }
    json.dump(meta, open(os.path.join(txtdir, uri + ".meta.json"), "w"), ensure_ascii=False, indent=1)
    print("DONE", uri, meta["word_count"], "words", flush=True)


DIV = re.compile(r'<div class="[^"]*journal-entry-divider[^"]*">\s*<a name="([^"]+)">(.*?)</a>\s*</div>', re.S)
CANON = re.compile(r"\[(D&C [^\]]+|Moses [^\]]+|Abraham [^\]]+|[^\]]*\d[^\]]*)\]")


def slug(t):
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")[:70]


def split_doc(docdir, uri):
    """Cut a fetched document into its items at JSP's item dividers; hands are attributed as in fetch_doc."""
    pages = sorted(f for f in os.listdir(os.path.join(docdir, "raw", uri)) if re.fullmatch(r"p\d{4}\.json", f))
    pages = [os.path.join(docdir, "raw", uri, f) for f in pages]
    first = json.load(open(pages[0]))
    toc = {t["linkID"]: t for t in (first.get("tableOfContents") or [])}
    items = [{"link": None, "title": "(text before first item marker)", "segs": [], "start": None, "end": None}]
    scribe = None
    for pf in pages:
        s = json.load(open(pf))["summary"]
        pno = int(os.path.basename(pf)[1:5])
        psc = [norm_scribe(x.get("name")) for x in (s.get("scribes") or []) if x.get("name")]
        if len(psc) == 1:
            scribe = psc[0]
        elif scribe is None and psc:
            scribe = psc[0]
        c = s.get("clearText") or ""
        c = re.sub(r"^\s*<html><head></head><body>|</body></html>\s*$", "", c)
        pos, chunks = 0, []
        for m in DIV.finditer(c):
            chunks.append((None, c[pos:m.start()]))
            chunks.append((m.group(1), re.sub(r"<[^>]+>", "", m.group(2))))
            pos = m.end()
        chunks.append((None, c[pos:]))
        for link, body in chunks:
            if link is not None:
                t = toc.get(link, {})
                items.append({"link": link, "title": html.unescape(t.get("pageTitle") or body).strip(),
                              "date": t.get("date"), "segs": [], "start": pno, "end": pno})
                continue
            if not body.strip():
                continue
            segs, scribe = extract("<html><body>" + body + "</body></html>", scribe or "UNATTRIBUTED")
            if segs:
                it = items[-1]
                it["segs"] += segs
                it["end"] = pno
                if it["start"] is None:
                    it["start"] = pno
    outdir = os.path.join(docdir, "items", uri)
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for k, it in enumerate(items):
        text = re.sub(r"\n{2,}", "\n", strip_labels("".join(x["text"] for x in it["segs"]))).strip()
        if not text:
            continue
        by = {}
        for x in it["segs"]:
            by[x["scribe"]] = by.get(x["scribe"], 0) + len(strip_labels(x["text"]).split())
        m = CANON.search(it["title"])
        fn = "%03d_%s.txt" % (k, slug(it["title"]))
        open(os.path.join(outdir, fn), "w").write(text + "\n")
        rows.append({"seq": k, "file": "items/%s/%s" % (uri, fn), "jsp_title": it["title"], "jsp_date": it.get("date"),
                     "canon_ref": m.group(1) if m else None, "first_page": it["start"], "last_page": it["end"],
                     "words": len(text.split()), "words_by_scribe": by,
                     "js_hand_words": sum(len(x["text"].split()) for x in it["segs"] if x["js_hand"])})
    with open(os.path.join(docdir, "items", uri + ".items.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(docdir, "items", uri + ".items.tsv"), "w") as f:
        f.write("seq\tjsp_date\tjsp_title\tcanon_ref\tpages\twords\tmain_scribe\tfile\n")
        for r in rows:
            ms = max(r["words_by_scribe"], key=r["words_by_scribe"].get) if r["words_by_scribe"] else ""
            f.write("%d\t%s\t%s\t%s\t%s-%s\t%d\t%s\t%s\n" % (r["seq"], r["jsp_date"] or "", r["jsp_title"], r["canon_ref"] or "",
                                                         r["first_page"], r["last_page"], r["words"], ms, r["file"]))
    print(uri, len(rows), "items")


if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for name, docs, page_range, split in JOBS:
        if wanted and name not in wanted:
            continue
        outdir = str(RAW / name)
        for uri in docs:
            fetch_doc(outdir, uri, page_range)
            if split:
                split_doc(outdir, uri)
        for f in EXTRA.get(name, []):
            shutil.copy(LISTS / f, RAW / name / f)
