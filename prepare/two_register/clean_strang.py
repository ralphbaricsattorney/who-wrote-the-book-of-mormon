"""Clean James J. Strang's plain-prose texts for the two-register study (prose side only).

Raw files (data/raw/two_register_authors/strang/prose/, Internet Archive OCR):
  ancientmodernm1885stra.djvu.txt   Ancient and Modern Michilimackinac (1854), 1885 St. Ignace reprint
  diary00stra.djvu.txt              Diary 1831-36, ed. Mark A. Strang (1961)
  propheticcontr1878stra.djvu.txt   The Prophetic Controversy: letter to Mrs Corey (1854), 1878 reprint
  diamondbeinglawo02stra.djvu.txt   The Diamond (Voree, 1848): only Strang's two signed epistles

Not used: afk0709.0001.001.umich.edu.djvu.txt (a worse scan of the 1854 printing of
Michilimackinac; same text as the 1885 reprint apart from one clause), ancientmodernmic00stra
(another 1854 scan), and secondary_quaife_1930 (used for nothing). The scripture-style Book of the
Law of the Lord is already in the project corpus and is not touched.

Removal is by explicit line ranges (front matter, footnotes, documents and quotations by others,
editorial matter, headings) and by rules for page furniture and OCR debris, following
prepare/two_register/CLEANING_PROTOCOL.md. Wrapped lines are joined and line-end
hyphenation repaired. No spelling is corrected.

Run:  python prepare/two_register/clean_strang.py
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vocabulary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAWDIR = ROOT / "data/raw/two_register_authors/strang/prose"
OUT = ROOT / "data/prepared/two_register/strang"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
WORD_RX = re.compile(r"[a-z]+(?:'[a-z]+)?")


def load_vocab() -> set[str]:
    return set(vocabulary.tokens())


def core(tok: str) -> str:
    return re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", tok)


def valid_token(tok: str, vocab: set[str], edge: bool) -> bool:
    c = re.sub(r"['’]s$", "", core(tok))
    if c.isdigit():
        return True
    if not c.isalpha():
        return False
    if c.lower() in vocab or re.fullmatch(r"[A-Z][a-z]+", c):
        return True
    return edge  # hyphenation fragment at a line edge


def garble_share(text: str, vocab: set[str]) -> float:
    toks = [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]
    if not toks:
        return 0.0
    ok = sum(valid_token(t, vocab, i == 0 or (i == len(toks) - 1 and t.endswith("-")))
             for i, t in enumerate(toks))
    return ok / len(toks)


TERMINAL_RX = re.compile(r"""[.!?:]["'”’)\]]*\s*$""")
HYPHEN_END_RX = re.compile(r"(\S*?[A-Za-z])\s?-\s*$")


def join_lines(prev: str, nxt: str, vocab: set[str]) -> str:
    nxt = nxt.strip()
    first = nxt.split()[0] if nxt.split() else ""
    m = HYPHEN_END_RX.search(prev)
    if m and not prev.rstrip().endswith("--"):
        a = core(m.group(1).split()[-1])
        b = core(first)
        head = prev[: m.start(1)] + m.group(1)
        if first[:1].islower():
            spaced = bool(re.search(r"\s[-—]\s*$", prev))
            if a.lower() in vocab and b.lower() in vocab:
                if spaced:  # a stray dash between two whole words
                    return head + " " + nxt
                if (a + b).lower() in vocab or a[:1].isupper():
                    return head + nxt
                return head + "-" + nxt
            return head + nxt
        return head + "-" + nxt
    return prev.rstrip() + " " + nxt


def apply_ops(text: str, ops, n: int) -> str:
    for op in ops:
        kind = op[0]
        if kind == "set":
            text = op[1]
            continue
        m = re.search(op[1], text)
        if not m:
            raise SystemExit(f"line {n}: pattern {op[1]!r} not found in {text!r}")
        if kind == "sub":
            text = re.sub(op[1], op[2], text, count=1)
        elif kind == "cut_from":
            text = text[: m.start()].rstrip()
        elif kind == "keep_after":
            text = text[m.end():].strip()
        else:
            raise ValueError(kind)
    return text


def ranges(spec: str) -> list[tuple[int, int]]:
    out = []
    for part in spec.split():
        a, _, b = part.partition("-")
        out.append((int(a), int(b or a)))
    return out


def clean_work(w: dict, vocab: set[str]):
    raw = (RAWDIR / w["file"]).read_text(encoding="utf-8", errors="replace").split("\n")
    L = {i + 1: s for i, s in enumerate(raw)}
    a, b = w["body"]
    drop: dict[int, str] = {}
    for spec, why in w["remove"]:
        for s, e in ranges(spec):
            for n in range(s, e + 1):
                if L[n].strip() and n not in drop:
                    drop[n] = why
    furn = w.get("furniture")
    if furn:
        for n in range(a, b + 1):
            if n not in drop and L[n].strip():
                r = furn(n, L)
                if r:
                    drop[n] = r
    removed = []
    seq: list[str | None] = []
    garbled = 0
    for n in range(a, b + 1):
        t = L[n]
        if n in drop:
            removed.append((n, drop[n], t))
            seq.append(None)
            continue
        if not t.strip():
            seq.append(None)
            continue
        t = re.sub(r"[ \t]+", " ", t)  # the OCR doubles most word spaces
        if n in w.get("edits", {}):
            t = apply_ops(t, w["edits"][n], n)
        if w.get("line_fix"):
            t = w["line_fix"](n, t)
        if not t.strip():
            seq.append(None)
            continue
        if len(t.split()) >= 4 and garble_share(t, vocab) < w.get("garble_min", 0.5):
            removed.append((n, "ocr_garble: under half the tokens are words", t))
            garbled += 1
            seq.append(None)
            continue
        seq.append(t.strip())
    paras, cur, gap = [], "", False
    for t in seq:
        if t is None:
            gap = True
            continue
        if not cur:
            cur = t
        elif gap and TERMINAL_RX.search(cur):
            paras.append(cur)
            cur = t
        else:
            cur = join_lines(cur, t, vocab)
        gap = False
    if cur:
        paras.append(cur)
    paras = [re.sub(r"\s{2,}", " ", p).strip() for p in paras]
    text = "\n\n".join(paras) + "\n"
    stats = {
        "source": str((RAWDIR / w["file"]).relative_to(ROOT)),
        "body_lines": [a, b],
        "words_raw_body": sum(len(L[n].split()) for n in range(a, b + 1)),
        "words_out": len(text.split()),
        "paragraphs": len(paras),
        "garbled_lines_dropped": garbled,
        "removed_words_by_reason": dict(collections.Counter(
            {k: v for k, v in _sum_words(removed).items()})),
    }
    return text, removed, stats


def _sum_words(removed):
    c = collections.Counter()
    for _, why, t in removed:
        c[why.split(":")[0]] += len(t.split())
    return c


# ---------------------------------------------------------------------------
# 1. Ancient and Modern Michilimackinac (1885 reprint)
# ---------------------------------------------------------------------------
MICH_HEAD_RX = re.compile(r"^\W{0,3}M\S{3,20}(\s+\S{2,10})?\s+A[NX]\S{0,3}\s+T\S{1,4}\s+\S{4,12}\s*/?\s*$", re.I)


def mich_furniture(n, L):
    s = L[n].strip()
    if MICH_HEAD_RX.match(s):
        return "furniture: running head"
    if len(s.replace(" ", "")) <= 4 and any(MICH_HEAD_RX.match(L[k].strip()) for k in range(n - 3, n + 4) if k in L):
        return "furniture: page number / library stamp"
    return None


def mich_fix(n, t):
    # isolated margin characters at the line end (column bleed): | j < * •
    return re.sub(r"\s+[|j<*•]\s*$", "", t)


MICH_LEAD = {n: [("sub", r"^[ji{|,.1I] +", "")] for n in
             [85, 96, 97, 98, 1110, 1654, 4226, 4227, 4228, 4230, 4232, 4234, 4235, 4236, 4237, 4238,
              4239, 4240, 4241, 4242, 4243, 4244, 4245, 5402]}
MICH_EDITS = {
    **MICH_LEAD,
    229: [("cut_from", r"Of\s*$")],                 # lead-in to the Charlevoix quotation
    1041: [("sub", r"Com\s+•\s*$", "Com-")],
    1739: [("set", "ty.")],                          # OCR '•y-' = end of 'socie-ty.'
    2160: [("sub", r"\s+1\s*$", "")],
    2514: [("sub", r"\s+'\s*$", "")],
    3199: [("sub", r"pro\s*$", "pro-")],
    4876: [("sub", r";\*", ";")],
}
MICH_HEADINGS = ("161 213 285 305 411 495 576 627 851 933 1199 1307 1350 1528 1583 1668 1811 1908 2053 "
                 "2178 2371 2461 2549 3150 3224 3327 3399 3836 4080 4186 4228 4262 4439 4689 5104 5303 "
                 "5465 5578 5598 5608 5647 5654 5664 5699 5705 5716 5724 5732 5738 5777 5799 5831 5907 "
                 "2870-2871 2926-2927 3564-3565 4710-4711 4840-4841")
MICH = {
    "slug": "prose__michilimackinac",
    "file": "ancientmodernm1885stra.djvu.txt",
    "body": (54, 5917),
    "remove": [
        ("54", "heading: section heading (NAME.)"),
        (MICH_HEADINGS, "heading: section heading"),
        ("230-253", "quotation: Charlevoix on the Jesuit Relations (block quotation)"),
        ("5113-5301", "table: islands of Emmet County (names and figures, OCR debris)"),
        ("5882 5885", "furniture: 1885 running head 'SUPPLEMENT.' and page number"),
    ],
    "edits": MICH_EDITS,
    "furniture": mich_furniture,
    "line_fix": mich_fix,
}
# The heading at 4228 carries a junk prefix; it is removed as a heading, so drop its lead edit.
MICH_EDITS.pop(4228)

# ---------------------------------------------------------------------------
# 2. Diary 1831-36 (ed. Mark A. Strang, 1961)
# ---------------------------------------------------------------------------
DIARY_FOOTNOTES = ("2199-2225 2275-2279 2325-2329 2378-2383 2432-2435 2529-2533 2578-2584 2621-2634 "
                   "2727-2733 2978-3003 3021-3057 3097-3109 3195-3204 3246-3252 3343-3345 3431-3439 "
                   "3572-3580 3719-3724 3861-3865 3900-3914 3953-3967 4011-4015 4203-4207 4352-4363 "
                   "4461-4465 4507-4510 4552-4555 4593-4604 4643-4652 4702-4709 4841 4857-4859 4905-4911 "
                   "4946-4957 5001-5007 5037-5056 5240-5243 5249-5280")
DIARY_SIGS = ("2240 2294 2344 2411 2470 2767 2822 3284 3420 3477 3501 3538 3702 3747 4059 4140 4333 4450 "
              "4585 4770 4885 4979 5210")
DIARY_MARKERS = {  # editor's footnote markers glued to words (OCR of superscripts)
    2314: (r"training\*", "training"), 2336: (r"life>", "life"), 2403: (r"school\.’", "school."),
    2522: (r"mankind\.®", "mankind."), 2525: (r"brother®", "brother"), 2543: (r"Smith\?", "Smith"),
    2549: (r"sister!!", "sister!"), 2593: (r"Religion’\?", "Religion"), 2598: (r"them\.1\*", "them."),
    2687: (r"Crawford\.\"4", "Crawford."), 2970: (r"benefit\.!®", "benefit."), 3072: (r"Crown\.'®", "Crown."),
    3309: (r"games\?®", "games"), 3405: (r"stitutional\.49", "stitutional."), 3426: (r"predict\?", "predict"),
    3543: (r"consent\.24", "consent."), 3558: (r"Hayne,\?\*", "Hayne,"), 3682: (r"quiting\?®", "quiting"),
    3836: (r"Nature,24", "Nature,"), 3887: (r"disappeared”", "disappeared"), 3896: (r"light\.2°", "light."),
    3935: (r"necessary\.\?\*", "necessary."), 3949: (r"school\?®", "school"), 4000: (r"Mills\)\?®", "Mills)"),
    4176: (r"temperance®\*®", "temperance"), 4324: (r"mind\.34", "mind."), 4344: (r"last\.®\?", "last."),
    4430: (r"W\[h\]Jigs\*®", "W[h]igs"), 4472: (r"afternoon\.\*\*", "afternoon."),
    4517: (r"survive\.\*®", "survive."), 4574: (r"\]®®", "]"), 4624: (r"David’s®”", "David’s"),
    4640: (r"covered ;\?8", "covered ;"), 4839: (r"to\?", "to"), 4901: (r"Smith\.\*°", "Smith."),
    4940: (r"nineteen\*!", "nineteen"), 5237: (r"^bOLOLD BOOK FAREWELL\.\*", "OLD BOOK FAREWELL."),
}
DIARY_EDITS = {n: [("sub", rx, rep)] for n, (rx, rep) in DIARY_MARKERS.items()}
DIARY_EDITS[5219] = [("cut_from", r"\[Racine")]
DIARY_EDITS[5230] = [("sub", r"shal\[1\]", "shal[l]")]  # OCR read the restored 'l' as '1'
DIARY_EDITS[5220] = [("keep_after", r"^consin\]")]


def diary_fix(n, t):
    t = re.sub(r"\s*\[1[78]\d\d\??\]", "", t)  # editor's bracketed years
    t = t.replace("[", "").replace("]", "")      # editor's restorations: keep the words, drop brackets
    return t


DIARY = {
    "slug": "prose__diary_1831_36",
    "file": "diary00stra.djvu.txt",
    "body": (2187, 5237),
    "remove": [
        (DIARY_FOOTNOTES, "footnote: editor's footnotes (Mark A. Strang, 1961)"),
        ("2887-2952", "furniture: photostat plate of a diary page and editor's caption"),
        (DIARY_SIGS, "furniture: Strang's page-top name-and-date lines (not prose)"),
        ("2455 5144", "heading: editor's year heading"),
        ("3825 3920 4121 4243 4792", "heading: editor's bracketed titles"),
        ("3938", "editorial: gap marker"),
        ("2394-2395 2959 3941 4663 5147", "heading: date-only lines"),
        ("2651 2719 2857", "heading: short captions"),
        ("2358-2361 4269-4287", "verse: Strang's own verse (not prose)"),
        ("2372-2375", "list: list of books with prices"),
        ("4666-4681", "quotation: Byron, Childe Harold IV.124"),
        ("4799-4807", "quotation: verse on Time (another writer, in quotation marks)"),
        ("4844-4856 4865-4866", "quotation: poem on Spring (another writer, in quotation marks)"),
        ("4987-4998 5013-5016", "quotation: Byron, Manfred I.i"),
    ],
    "edits": DIARY_EDITS,
    "furniture": lambda n, L: "furniture: page number" if re.fullmatch(r"\s*\[\d{1,2}\]\s*", L[n]) else None,
    "line_fix": diary_fix,
}

# ---------------------------------------------------------------------------
# 3. The Prophetic Controversy (1854; 1878 reprint)
# ---------------------------------------------------------------------------
PC_REMOVE = (
    "45-47 88-96 318-321 336-374 388-424 427-430 441-486 497-544 547-550 558-611 619-663 666 673-722 "
    "733-778 780-783 795-882 884-887 903-939 954-994 997-1000 1021-1052 1073-1110 1113-1116 1159-1167 "
    "1219-1222 1313-1319 1322-1325 1361-1374 1425-1428 1527-1530 1557-1585 1608-1649 1679-1703 1714-1770 "
    "1809-1824 1831-1895 1903-2024 2031-2089 2099-2159 2174-2224 2262-2285 2327-2338 2371-2396 2495-2501 "
    "2536-2558 2577-2624 2661-2677 2727-2730 2783 2786-2789 2882-2887 2929-2933 2984-2987 3091-3094 3192-3195 "
    "3295-3298 3350-3377 3386-3437 3463-3501 3603-3606 3653-3655 3688-3718 3813-3822 3921-3924 3976-3979 "
    "4080-4083 4183-4186 4269-4296 4339-4349 4402-4405 4505-4508 4607-4610 4662-4668 4770-4773 4872-4875 "
    "4975-4978 5082-5085")
PC_MARKERS = {
    27: r"(?<=\.)\*", 333: r"\s+\*\s*$", 438: r"(?<=\.)\*", 730: r"(?<=\.)\*", 1308: r"(?<=”)\*",
    1554: r"(?<=\.)\*", 1606: r"(?<=\.)\*", 1676: r"\s+f\s*$", 1710: r"\s+f(?= It)", 1806: r"\s+J\s*$",
    2093: r"(?<=\.)\*", 2235: r"\s+t\s*$", 2247: r"(?<=,)\*", 2295: r"(?<=xlvi\.)t", 2313: r"\s+J(?= Had)",
    2317: r"(?<=,)\*", 2342: r"\s+f\s*$", 2354: r"\s+J(?= He)", 2360: r"\s+§", 2410: r"(?<=\.)\*",
    2514: r"(?<=\.)\*", 2744: r"(?<=\.)\*", 2880: r"(?<=\.)\* —", 3329: r"(?<=\))\*", 3651: r"(?<=\")\^",
    3733: r"(?<=Elder)\*", 3796: r"(?<=14,)\*", 4263: r"(?<=’)\*",
}
PC_EDITS = {n: [("sub", rx, "")] for n, rx in PC_MARKERS.items()}
PC_EDITS[12] = [("sub", r"^Dear\s+Sister\s+—\s*", "")]
PC_EDITS[3853] = [("cut_from", r"“I\s*$")]
PC_EDITS[3259] = [("sub", r"\s+I\s*$", "")]       # 'whom I I' (margin I)
PC_EDITS[3253] = [("sub", r"\s+Ij\s*$", "")]
for n in (2523, 2524, 2526, 2527, 2528, 2529, 2531, 3335, 3341):
    PC_EDITS[n] = [("sub", r"^[iIj|]\s+", "")]
PC_MARGIN = ranges("2520-2533 3247-3263 3333-3343 4258-4266 4822-4866")


def pc_fix(n, t):
    t = re.sub(r"\s+[|!?^\\][^\sA-Za-z]*[ij]?\s*$", "", t)   # margin bars and marks
    t = re.sub(r"\s+\|[ij]?\s*$", "", t)
    if any(s <= n <= e for s, e in PC_MARGIN):
        t = re.sub(r"\s+(?:[ij;:'1]|;\*|\|i)\s*$", "", t)
        t = re.sub(r"(-)\s+\S{1,2}\s*$", r"\1", t)
    return t


PC_HEAD_RX = re.compile(r"^P[A-Za-z]{2,6}\s+CONT[A-Za-z]{4,8}[.,]?\s*$")


def pc_furniture(n, L):
    s = L[n].strip()
    if PC_HEAD_RX.match(s):
        return "furniture: running head"
    if (re.fullmatch(r"(\d{1,2}|\]\^2|:>S|SO|\?A|UPB.*|n)", s)
            and any(PC_HEAD_RX.match(L[k].strip()) for k in range(n - 4, n + 5) if k in L)):
        return "furniture: page number / stamp"
    if s.startswith("UPB"):
        return "furniture: library stamp"
    return None


PC = {
    "slug": "prose__prophetic_controversy",
    "file": "propheticcontr1878stra.djvu.txt",
    "body": (12, 5170),
    "remove": [
        (PC_REMOVE, "footnote_or_quotation: reprint footnotes (incl. documents and letters by others "
                    "quoted in them), block quotations of revelations and of other writers, page furniture"),
        ("145-246", "quotation: Doctrine and Covenants block quotations"),
        ("3854-3868", "quotation: Doctrine and Covenants (sec. i) quoted at length"),
        ("4726-4765", "document: certificate of the four witnesses"),
        ("4795-4826", "quotation: Southport Telegraph extract"),
        ("4932-4949", "quotation: Orson Hyde in the Millennial Star"),
    ],
    "edits": PC_EDITS,
    "furniture": pc_furniture,
    "line_fix": pc_fix,
}

# ---------------------------------------------------------------------------
# 4. The Diamond (1848): Strang's two signed epistles only
# ---------------------------------------------------------------------------
DIAMOND_EDITS = {
    574: [("cut_from", r"\"The most")],
    934: [("keep_after", r"xiv\.'p\.\s*2\.\)")],
    938: [("sub", r"^'\*\s*", "")],
    939: [("cut_from", r"\*'\s*I\s+have\s+sent")],
    943: [("keep_after", r"p\.\s*3\.\)")],
    947: [("sub", r"^C\s+", "")],
    1003: [("sub", r"God'\"'", "God")],
}


def diamond_fix(n, t):
    if 777 <= n <= 1071:
        t = re.sub(r"^[\s'\"*^•■\\|;:,.`-]+(?=[A-Za-z(])", "", t)  # bleed-through at the left margin
    return t


DIAMOND = {
    "slug": "prose__diamond_epistles",
    "file": "diamondbeinglawo02stra.djvu.txt",
    "body": (496, 1071),
    "remove": [
        ("505 561 614 667 721 832 996 1051", "furniture: page number"),
        ("507-508", "quotation: end of a Doctrine and Covenants quotation (garbled)"),
        ("575-587", "quotation: Doctrine and Covenants sec. iii quoted at length"),
        ("716-776", "excluded: prophetic warnings in biblical cadence (scripture-style), signature, "
                    "Chapter V heading and opening sentence modelled on Hebrews 1:1 (garbled)"),
        ("875-886", "ocr_garble: shredded lines"),
        ("931-933 940-942", "quotation: Doctrine and Covenants (secs. xiv, i)"),
        ("1019-1039", "quotation: Doctrine and Covenants sec. ciii and its lead-in"),
    ],
    "edits": DIAMOND_EDITS,
    "line_fix": diamond_fix,
}

WORKS = [MICH, DIARY, PC, DIAMOND]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    vocab = load_vocab()
    all_stats = {}
    with open(OUT / "removed_lines.tsv", "w", encoding="utf-8") as fh:
        fh.write("work\traw_line\treason\ttext\n")
        for w in WORKS:
            text, removed, stats = clean_work(w, vocab)
            (OUT / f"{w['slug']}.txt").write_text(text, encoding="utf-8")
            for n, why, t in removed:
                fh.write(f"{w['slug']}\t{n}\t{why}\t{t.strip()}\n")
            all_stats[f"{w['slug']}.txt"] = stats
    all_stats["total_words_prose"] = sum(v["words_out"] for k, v in all_stats.items() if k.endswith(".txt"))
    (OUT / "stats.json").write_text(json.dumps(all_stats, indent=2), encoding="utf-8")
    print(json.dumps(all_stats, indent=2))


if __name__ == "__main__":
    main()
