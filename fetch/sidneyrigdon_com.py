"""Fetch Sidney Rigdon texts transcribed by Dale R. Broadhurst on sidneyrigdon.com.

data/raw/sidney_rigdon_broadhurst/: periodical series, pamphlets and memorials, one text per bordered
  transcription box (article or installment).
data/raw/sidney_rigdon_broadhurst_additional/: further signed items (Pittsburgh Messenger and Advocate
  1844-46, newspaper letters 1831-44, an 1873 letter). Each box is one newspaper issue, split at <hr>; a
  segment is kept if it ends with Rigdon's signature or opens with a "BY S. RIGDON" byline, and four items are
  cut by hand-specified start and end patterns (SLICES).
Each directory gets html/ (pages as served), text/<doc_id>.txt and documents.json; the second also
all_segments.jsonl (every segment, kept or not).

Run:  python fetch/sidneyrigdon_com.py
"""
from __future__ import annotations

import json
import re

from lxml import html as LH

from common import RAW, download

B = "http://www.sidneyrigdon.com/"

# ---- first set: (page, series id, top-level table indexes to keep (None = every bordered box), attribution note)
PAGES = [
    ("RigWrit/RigWrit3.htm", "millennium", None,
     "'Millennium' series nos. I-XIV, EMS Dec 1833-Aug 1834 & M&A Nov 1834-May 1835; unsigned/'Communicated'; attributed to Rigdon by Broadhurst and most scholars"),
    ("RigWrit/RigWrit3b.htm", "gospel", None,
     "'The Gospel' series, EMS Apr 1833 & Sep 1834, M&A Nov 1834-Jun 1835; unsigned; attributed to Rigdon by Broadhurst"),
    ("RigWrit/RigWrit3d.htm", "articles_letters", None,
     "Signed or editorially attributed Rigdon articles/letters in EMS, M&A (1834-37) and Elders' Journal (1837-38)"),
    ("RigWrit/RigWrit2.htm", "dear_brethren_1834", None,
     "Circular 'Dear Brethren', Kirtland 10 May 1834, signed jointly by Sidney Rigdon and Oliver Cowdery (MIXED AUTHORSHIP)"),
    ("rigd1838.htm", "oration_1838", [2],
     "Oration delivered 4 July 1838 at Far West (printed pamphlet, Far West: Journal Office, 1838); Rigdon"),
    ("1840RigA.htm", "appeal_1840", [3, 4],
     "An Appeal to the American People (Cincinnati, 1840); written by Rigdon per Broadhurst and the 1839 conference commission; second part is the appended Memorial to the Missouri Legislature (Dec 1838; multiple signers)"),
    ("RigWrit/Rigd1844.htm", "memorial_1844", [1],
     "Rigdon's Memorial to the Pennsylvania Legislature, Times and Seasons 5 (1 Feb 1844)"),
    ("books/Appl1863.htm", "appeal_1863", [2, 3, 4, 5],
     "An Appeal to the Latter-day Saints (Philadelphia, 1863), NOMINALLY by J. H. Newton, W. Richards, W. Stanley; Broadhurst argues 'probably entirely by Rigdon' (DISPUTED; late)"),
]
MAST = re.compile(r"^\s*Vol\.?\s*[IVX]+\.?.{0,80}?No\.\s*\d+\.?\s*", re.S)
PAGEMARK = re.compile(r"\[\s*(?:p\.\s*)?\d+\s*\]|^\s*\(\s*\d+\s*\)\s*", re.M)


def text_of(tb):
    """Plain text of a transcription box, with its masthead line split off and page markers removed."""
    for br in tb.xpath(".//br"):
        br.tail = "\n" + (br.tail or "")
    for p in tb.xpath(".//p|.//blockquote|.//div|.//center"):
        p.tail = "\n" + (p.tail or "")
    for img in tb.xpath(".//img"):
        img.drop_tree()
    t = tb.text_content().replace(" ", " ").replace("\r", "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    mast = MAST.match(t)
    masthead = mast.group(0).strip() if mast else None
    if mast:
        t = t[mast.end():]
    t = PAGEMARK.sub(" ", t)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r" *\n *", "\n", t).strip(), masthead


def fetch_main():
    out = RAW / "sidney_rigdon_broadhurst"
    (out / "text").mkdir(parents=True, exist_ok=True)
    docs = []
    for page, sid, keep, note in PAGES:
        root = LH.fromstring(download(B + page, out / "html" / page.replace("/", "_")))
        tops = [tb for tb in root.iter("table") if not tb.xpath("ancestor::table")]
        k = 0
        for i, tb in enumerate(tops):
            bg = (tb.get("bgcolor") or "").upper()
            if keep is not None and i not in keep:
                continue
            if keep is None and (tb.get("border") in (None, "0") or bg == "#FFFFFF"):
                continue
            t, masthead = text_of(tb)
            if len(t.split()) < 30:
                continue
            k += 1
            did = "%s_%02d" % (sid, k)
            (out / "text" / f"{did}.txt").write_text(t + "\n")
            docs.append({"doc_id": did, "series": sid, "source_page": B + page, "table_index": i,
                         "masthead": masthead, "opening": " ".join(t.split()[:20]),
                         "words": len(t.split()), "attribution_note": note})
    json.dump(docs, open(out / "documents.json", "w"), indent=1, ensure_ascii=False)
    print("sidney_rigdon_broadhurst", len(docs), "documents")


# ---- second set: (url, series id, anchors of the issue boxes (None = every box on the page), note)
MORE_PAGES = [
    (B + "RigWrit/M&A/MA-1844.htm", "pittsburgh_ma", None, "Messenger and Advocate of the Church of Christ (Pittsburgh), Oct-Dec 1844; Broadhurst excerpts"),
    (B + "RigWrit/M&A/MA-1845a.htm", "pittsburgh_ma", None, "Messenger and Advocate (Pittsburgh), Jan-Jun 1845; Broadhurst excerpts"),
    (B + "RigWrit/M&A/MA-1845b.htm", "pittsburgh_ma", None, "Messenger and Advocate (Pittsburgh), Jul-Dec 1845; Broadhurst excerpts"),
    (B + "RigWrit/M&A/MA-1846.htm", "pittsburgh_ma", None, "Messenger and Advocate (Pittsburgh), 1846; Broadhurst excerpts"),
    (B + "dbroadhu/OH/miscohio.htm", "ohio_star_1831", ["121531"], "Ohio Star (Ravenna), 15 Dec 1831"),
    (B + "dbroadhu/OH/miscoh02.htm", "ohio_star_1832", ["011232"], "Ohio Star (Ravenna), 12 Jan 1832"),
    (B + "dbroadhu/OH/painerep.htm", "painesville_republican_1839", ["021439"], "Painesville Republican, 14 Feb 1839 (quoted extract of a Rigdon letter from Liberty Jail)"),
    (B + "dbroadhu/IL/whig1839.htm", "quincy_whig_1839", ["0525", "rigdon"], "Quincy Whig, 25 May and 8 Jun 1839"),
    (B + "dbroadhu/IL/sang1842.htm", "sangamo_journal_1842", ["0916", "0923"], "Sangamo Journal (Springfield), 16 and 23 Sep 1842"),
    (B + "dbroadhu/MO/miscstl3.htm", "peoples_organ_1844", ["091744"], "People's Organ (St. Louis), 17 Sep 1844"),
    (B + "1869Moor.htm", "letter_woodward_1873", ["1873letter"], "Letter to Charles L. Woodward, Friendship NY, 25 May 1873 (NYPL); Broadhurst's line-by-line transcription with many illegible gaps"),
]
SIG = r"S(?:IDNEY|idney|\.) ?R(?:IGDON|igdon)"
# Items the <hr> split cannot isolate: (series, page substring, anchor, start regex, end regex (both inclusive),
# doc id, joint signature?, note)
SLICES = [
    ("pittsburgh_ma", "MA-1845a", None, r"THE MORMONS\.\s+It is surprsing", r"share in her ruin\.\s+SIDNEY RIGDON\.",
     "pittsburgh_ma_1845-02-15_the_mormons", False, "Messenger and Advocate (Pittsburgh) 1:8, 15 Feb 1845, 'The Mormons', signed"),
    ("sangamo_journal_1842", "sang1842", "0916", r"NAUVOO, Aug\. 27th, 1842\.", r"justice to Miss Rigdon\.\s+S\. R\.",
     "sangamo_journal_1842_letter_aug27", False, "Letter to the editor of the Wasp, Nauvoo 27 Aug 1842, as reprinted in the Sangamo Journal 16 Sep 1842"),
    ("quincy_whig_1839", "whig1839", "0525", r"Commerce, May 17, 1839\.", r"SIDNEY RIGDON,\s+JOSEPH SMITH, JR\.\s+HIRAM SMITH\.",
     "quincy_whig_1839_letter_may17_JOINT", True, "Letter to the editors, Commerce 17 May 1839, Quincy Whig 25 May 1839; signed by Rigdon, Joseph Smith and Hyrum Smith (JOINT)"),
    ("letter_woodward_1873", "1869Moor", "1873letter", r"Friendship May 25 1873", r"Respectfully\s+SIDNEY RIGDON",
     "letter_woodward_1873", False, "Manuscript letter to C. L. Woodward, 25 May 1873 (NYPL); Broadhurst transcription with bracketed illegible gaps"),
]
MAST2 = re.compile(r"^\s*[A-Z][^\n]*\n\s*Whole No\.\s*\d+\.\s*")      # 'Pittsburgh, December, 1845.\n\nWhole No. 26.'
MAST3 = re.compile(r"^.{0,300}?\[(?:Whole|Vol\.)[^\n]*\n", re.S)        # newspaper mastheads ending '[Whole 102.' / '[Vol. 2 - No. 4.'
SKIP_AUTO = {("quincy_whig_1839", "0525")}                               # replaced by a hand slice
SEP = "\n@@HR@@\n"


def box_text(tb):
    for hr in tb.xpath(".//hr"):
        hr.tail = SEP + (hr.tail or "")
    for br in tb.xpath(".//br"):
        br.tail = "\n" + (br.tail or "")
    for p in tb.xpath(".//p|.//blockquote|.//div|.//center|.//tr"):
        p.tail = "\n" + (p.tail or "")
    for img in tb.xpath(".//img"):
        img.drop_tree()
    t = tb.text_content().replace("\xa0", " ").replace("\r", "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def classify(seg):
    """(body without Broadhurst's notes, 'byline' | 'signature' | None, joint signature?, signed as president?)"""
    body = re.split(r"\n(?:Notes?:|Note 1:)", seg)[0].strip()
    tail, head = body[-260:], body[:400]
    by = re.search(r"\bBY\s+" + SIG, head)
    signed = bool(re.findall(SIG, tail)) and bool(re.search(SIG + r"[.,]?\s*(?:\n.{0,120}){0,4}$", tail))
    joint = bool(re.search(SIG + r"[.,]?\s*\n\s*(?:JOSEPH SMITH|HIRAM SMITH|HYRUM SMITH|OLIVER COWDERY)", tail)) or \
        bool(re.search(r"(?:JOSEPH SMITH|HYRUM SMITH)[^\n]*\n\s*" + SIG, tail))
    official = bool(re.search(SIG + r",?\s*\n\s*President\.", tail))
    return body, ("byline" if by else "signature" if signed else None), joint, official


def fetch_more():
    out = RAW / "sidney_rigdon_broadhurst_additional"
    (out / "text").mkdir(parents=True, exist_ok=True)
    docs, counter = [], {}
    allseg = open(out / "all_segments.jsonl", "w")
    for url, sid, anchors, note in MORE_PAGES:
        fn = re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("sidneyrigdon.com/")[1])
        root = LH.fromstring(download(url, out / "html" / fn))
        if anchors is None:
            boxes = [(None, tb) for tb in root.iter("table") if not tb.xpath("ancestor::table")
                     and tb.get("border") not in (None, "0")]
        else:
            boxes = []
            for a in anchors:
                el = root.xpath('//a[@name="%s"]' % a)
                tb = el[0].xpath("ancestor::table") or el[0].xpath("following::table[1]")
                boxes.append((a, tb[0]))
        for anc, tb in boxes:
            t = box_text(tb)
            segs = [x.strip() for x in t.split(SEP.strip())]
            masthead = " ".join(segs[0].split("\n")[:5])[:160] if segs else ""
            m = re.match(r"^\s*(?:Vol\.?\s*[IVX]+\.?.{0,90}?(?:Whole )?No\.\s*\d+\.?)", t, re.S)
            if m:
                masthead = " ".join(m.group(0).split())
            for sl in SLICES:
                if sl[0] != sid or sl[1] not in url or sl[2] != anc:
                    continue
                ms = re.search(sl[3], t)
                me = re.search(sl[4], t[ms.start():] if ms else "")
                if not (ms and me):
                    continue   # not in this issue box
                body = t[ms.start():ms.start() + me.end()].replace(SEP.strip(), "")
                if sid == "letter_woodward_1873":   # line-by-line manuscript transcription: rejoin lines
                    body = re.sub(r"\n+page \d+\n+", "\n", body)
                    body = re.sub(r"\n+-", "", body)
                    body = re.sub(r"\s*\n\s*", " ", body)
                body = re.sub(r"[ \t]+", " ", body).strip()
                (out / "text" / f"{sl[5]}.txt").write_text(body + "\n")
                docs.append({"doc_id": sl[5], "series": sid, "source_page": url + ("#" + anc if anc else ""),
                             "masthead": masthead, "segment_index": None, "signed_by": "signature (hand slice)",
                             "joint_signature": sl[6], "official_minutes_signature": False,
                             "has_ellipsis_excerpts": "..." in body, "opening": " ".join(body.split()[:20]),
                             "closing": " ".join(body.split()[-12:]), "words": len(body.split()), "source_note": sl[7]})
            for j, seg in enumerate(segs):
                if j == 0 and m:
                    seg = seg[m.end():].strip()
                if j == 0:
                    seg = MAST2.sub("", seg, 1)
                    if anchors is not None:
                        seg = MAST3.sub("", seg, 1)
                if (sid, anc) in SKIP_AUTO:
                    continue
                body, how, joint, official = classify(seg)
                nw = len(body.split())
                allseg.write(json.dumps({"page": url, "anchor": anc, "masthead": masthead, "segment": j, "words": nw,
                                         "signed": how, "joint": joint, "opening": " ".join(body.split()[:25]),
                                         "closing": " ".join(body.split()[-12:])}, ensure_ascii=False) + "\n")
                if not how or nw < 40:
                    continue
                counter[sid] = counter.get(sid, 0) + 1
                did = "%s_%02d" % (sid, counter[sid])
                body = re.sub(r"\[\s*(?:p\.\s*)?\d+\s*\]", " ", body)
                body = re.sub(r"[ \t]+", " ", body).strip()
                (out / "text" / f"{did}.txt").write_text(body + "\n")
                docs.append({"doc_id": did, "series": sid, "source_page": url + ("#" + anc if anc else ""),
                             "masthead": masthead, "segment_index": j, "signed_by": how,
                             "joint_signature": joint, "official_minutes_signature": official,
                             "has_ellipsis_excerpts": "..." in body, "opening": " ".join(body.split()[:20]),
                             "closing": " ".join(body.split()[-12:]), "words": len(body.split()), "source_note": note})
    allseg.close()
    json.dump(docs, open(out / "documents.json", "w"), indent=1, ensure_ascii=False)
    print("sidney_rigdon_broadhurst_additional", len(docs), "documents")


if __name__ == "__main__":
    fetch_main()
    fetch_more()
