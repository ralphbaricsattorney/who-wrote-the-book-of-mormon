"""Clean the two-register texts of Jacob Ilive (1705-1763).

Follows prepare/two_register/CLEANING_PROTOCOL.md.

Scripture side: The Book of Jasher (Ilive's forgery, first printed 1751). Base text is the
1829 Bristol reprint scan (bookofjasherwith00iliv), which is far more legible than the 1751
scan. The 1751 scan is used only as a witness: verses of the 1829 text that have no
counterpart in the 1751 printing are treated as additions of the 1829 editor and removed.

Prose side: five eighteenth-century long-s scans (bim_eighteenth-century_*), each
cleaned by line ranges plus pattern rules (running heads, page numbers, signatures,
catchwords, footnotes, marginal references, long quotations, OCR debris).

Long s: in the bim scans the long s is mostly encoded as the character U+017F, which is
mapped to "s" (counted separately). Then the protocol's conservative f->s repair is
applied to EVERY output file, both sides alike.

Run:  python prepare/two_register/clean_ilive.py
Raw files are read only, never modified.
"""
from __future__ import annotations

import difflib
import itertools
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vocabulary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "two_register_authors" / "ilive"
OUT = ROOT / "data" / "prepared" / "two_register" / "ilive"

DEBUG = "--debug" in sys.argv
DEBUG_DIR = Path(sys.argv[sys.argv.index("--debug") + 1]) if DEBUG else None

WORD_RE = re.compile(r"[A-Za-z]+")

# --------------------------------------------------------------------------------------
# Reference vocabulary and long-s repair
# --------------------------------------------------------------------------------------


VOCAB = vocabulary.words()


def longs_candidate(word: str) -> str | None:
    """Return the f->s repaired form of `word` if the protocol allows it, else None."""
    lw = word.lower()
    if "f" not in lw or lw in VOCAB:
        return None
    pos = [i for i, ch in enumerate(lw) if ch == "f"]
    if len(pos) > 4:
        return None
    best, best_n = None, 0
    for k in range(1, len(pos) + 1):
        for combo in itertools.combinations(pos, k):
            cand = list(lw)
            for i in combo:
                cand[i] = "s"
            cand_s = "".join(cand)
            n = VOCAB.get(cand_s, 0)
            if n > best_n:
                best, best_n = combo, n
    if best is None:
        return None
    out = list(word)
    for i in best:
        out[i] = "S" if word[i] == "F" else "s"
    return "".join(out)


def longs_repair(text: str) -> tuple[str, Counter]:
    repairs: Counter = Counter()

    def sub(m: re.Match) -> str:
        w = m.group(0)
        r = longs_candidate(w)
        if r is None:
            return w
        repairs[(w.lower(), r.lower())] += 1
        return r

    return WORD_RE.sub(sub, text), repairs


def known(word: str) -> bool:
    lw = word.lower()
    if lw in VOCAB:
        return True
    r = longs_candidate(lw)
    return r is not None


# --------------------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------------------

CHAR_MAP = {
    "ſ": "s",  # long s
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "ﬅ": "st", "ﬆ": "st",
    "«": '"', "»": '"', "„": '"', "“": '"', "”": '"',
    "‘": "'", "’": "'", "⸗": "-", "­": "-",
    "æ": "ae", "œ": "oe", "Æ": "Ae", "Œ": "Oe",
}


def normalize_chars(s: str) -> str:
    for a, b in CHAR_MAP.items():
        if a in s:
            s = s.replace(a, b)
    return s


def read_raw(rel: str) -> list[str]:
    """Raw file as a list of lines; index 0 is a dummy so that lines are 1-based."""
    text = (RAW / rel).read_text(encoding="utf-8")
    return [""] + text.split("\n")


def letters_share(s: str) -> float:
    s = s.strip()
    if not s:
        return 1.0
    return sum(ch.isalpha() for ch in s) / len(s)


def known_share(s: str) -> tuple[float, int]:
    words = [w for w in WORD_RE.findall(s)]
    if not words:
        return 0.0, 0
    return sum(known(w) for w in words) / len(words), len(words)


PARA = object()  # explicit paragraph break marker in line streams

SENT_END = re.compile(r"""[.!?:]["')\]]*$""")


def join_lines(stream: list, blank_breaks: bool = True) -> list[str]:
    """Join wrapped lines into paragraphs; mend words hyphenated across line ends.

    `stream` holds strings (lines; '' = blank line in the scan) and PARA markers.
    A new paragraph starts at a PARA marker, or at a blank line that follows a line ending
    in sentence punctuation.
    """
    paras: list[str] = []
    cur = ""
    blank = False
    for item in stream:
        if item is PARA:
            if cur:
                paras.append(cur)
            cur, blank = "", False
            continue
        s = item.strip()
        if not s:
            blank = True
            continue
        if not cur:
            cur = s
        elif re.search(r"[A-Za-z][-—=]$", cur) and re.match(r"[a-z]", s):
            head, tail = cur[:-1], s
            if cur.endswith("-") or cur.endswith("="):
                cur = head + tail
            else:  # em dash at line end: join only if it makes a known word
                lw = re.search(r"([A-Za-z]+)$", head).group(1) + re.match(r"[a-z]+", tail).group(0)
                cur = head + tail if known(lw) else cur + " " + s
        elif blank and blank_breaks and SENT_END.search(cur):
            paras.append(cur)
            cur = s
        else:
            cur = cur + " " + s
        blank = False
    if cur:
        paras.append(cur)
    return paras


STRAY = re.compile(r"[|\\{}■•►©®™°#$%<>_~^@]+")


def tidy(par: str) -> str:
    par = STRAY.sub(" ", par)
    par = re.sub(r"\s+([,;:.?!])", r"\1", par)
    toks = []
    for t in par.split():
        if not re.search(r"[A-Za-z0-9]", t) and t not in {"&", "-", "—", "--"}:
            continue  # lone punctuation debris
        toks.append(t)
    par = " ".join(toks)
    par = re.sub(r"\s+([,;:.?!])", r"\1", par)
    par = re.sub(r"([,;:])(?=[A-Za-z])", r"\1 ", par)
    return par.strip()


def wc(text: str) -> int:
    return len(text.split())


# --------------------------------------------------------------------------------------
# Book of Jasher (1829 reprint, checked against the 1751 printing)
# --------------------------------------------------------------------------------------

JSLUG = "scripture__book_of_jasher"
JASHER_1829 = "scripture/bookofjasherwith00iliv.djvu.txt"
JASHER_1751 = "scripture/bim_eighteenth-century_the-book-of-jasher_ilive-jacob_1751.djvu.txt"
JASHER_START = 758   # "CHAP. I."
JASHER_END_RE = re.compile(r"THE\s+END\s+OF\s+THE\s+BOOK\s+OF\s+JASHER")

CHAP_RE = re.compile(r"^\s*CHAP[.,]?\s+[IVXLivxlnmT]+[.,]?\s*$")
JASHER_HEAD_RE = re.compile(r"J\s*A\s*S\s*H\s*E\s*[RH]\b")
CHAP_HEAD_RE = re.compile(r"^\s*Chap[.,;]?\s+[ivxlcnmIVXL.,\s]+", re.I)
GLOSS_RE = re.compile(
    r"^\W*(?:[a-z]{0,2})?(?:Heb|Hcb|Hcl>|Hei|Hdi|Hd\)|Hfi|Heh|Hfb|Hrb|Hel|Ileb|lleb|Ueb|llcb|Ilcb|Ildt|IM|"
    r"ffei|Hfb|//\S*|i/\S*|\.//\S*|Ihb|IJeb|Hed|Hcl|lie\^)[.,\-]|^\W*Or[.,]$|//",
)
AM_RE = re.compile(r"^\W*A\.?\s*M\.?\W*$")
YEAR_RE = re.compile(r"^\W*\d{1,4}\W*$")
VERSE_START_RE = re.compile(r"^\s*[\]I\|l1]?\s*(\d{1,2})\s+(?=\S)")

# Verse 1 of each chapter starts with a large initial that the OCR garbles. The repaired
# opening words are taken from the surviving letters and from the 1751 printing.
DROPCAP_FIX = [
    (re.compile(r"^A\^+\s+Lamech"), "And Lamech"),
    (re.compile(r"^p\^Ti\s+the children"), "Now the children"),
    (re.compile(r"^J!\^lSiT>\s+it came"), "And it came"),
    (re.compile(r"^A\^+\s+\^\"\s+those days"), "And in those days"),
    (re.compile(r"^A\^+\s+'\^\^hen"), "And when"),
    (re.compile(r"^A\^D\s"), "And "),
    (re.compile(r"^\|?\^ND\s"), "And "),
    (re.compile(r"^A[-.]?\^+\s+\^+\s+Lord"), "And the Lord"),
    (re.compile(r"^[\]\\|^l]?\S{0,3}[O0][WV]\s"), "Now "),
    (re.compile(r"^\\\^li\s"), "Now "),
    (re.compile(r"^A[-.']*\S*\s+\S+\s+(?:\S+\s+)?(?:\S+\s+)?(?=on the morrow|after|about|when the days|to pass)"),
     "And it came to pass "),
    (re.compile(r"^A[-.']*\^\S*\s+\S+\s+came to pass"), "And it came to pass"),
]


def jasher_dropcap(s: str) -> str:
    s2 = re.sub(r"^[\^\s]+(?=A)", "", " ".join(s.split()))
    for rx, rep in DROPCAP_FIX:
        if rx.search(s2):
            out = rx.sub(rep, s2, count=1)
            out = re.sub(r"\bto pass to pass\b", "to pass", out)
            return out
    return s2


TOKEN_LEAD = re.compile(r"^[\-\"'`^*°•■►«»„“”‘’\[\]|]+(?=[A-Za-z])")


MID_GLOSS_RE = re.compile(r"^\W*(?:Heb|Hcb|Ileb|lleb|Hei|Hdi|Hd|Hti|Htb|Hfi|Ueb|Ub|Ildt|Hrb|llrb|Heh|Hfb|Hed|Hel|Hcl|Ihb)[.,]+\W*$")


def jasher_clean_tokens(s: str) -> str:
    # marginal glosses caught inside a text line: 'Caleb, the Ub. regard, son of'
    toks = s.split()
    keep = []
    k = 0
    while k < len(toks):
        t = toks[k]
        if MID_GLOSS_RE.match(t) or "//" in t or re.search(r"[a-z]\.[a-z]{3,}", t):
            k += 1
            n = 0
            while k < len(toks) and n < 2 and (re.search(r"[.,;]$", toks[k]) or not known(re.sub(r"[^A-Za-z]", "", toks[k]) or "x")) \
                    and not re.match(r"^[A-Z]", toks[k]):
                last = toks[k]
                k += 1
                n += 1
                if re.search(r"[.,;]$", last):
                    break
            continue
        # OCR debris token: several non-alphanumeric characters inside it
        core = t.strip(".,;:!?'\"()")
        if len(re.findall(r"[^A-Za-z0-9'\-]", core)) >= 2:
            k += 1
            continue
        keep.append(t)
        k += 1
    s = " ".join(keep)
    out = []
    for t in s.split():
        t = TOKEN_LEAD.sub("", t)
        if re.fullmatch(r"[\"'`^*°•■►\[\]|]+", t):
            continue  # stand-alone reference mark
        if t in {"H", "fT", "IT", "1[", "*[", "[^", "^", "^["}:
            continue  # paragraph mark
        t = re.sub(r"^[a-z][-']?(?=[A-Z][a-z])", "", t)  # reference letter fused to a name
        out.append(t)
    return " ".join(out)


def is_gloss_token(t: str) -> bool:
    """First token of a marginal gloss line ('Heb.', OCR 'Ileb.', 'i/ef.', 'Or,')."""
    t0 = re.sub(r"^[\"'`^*\u00b0\u2022\u25a0\u25ba\u00ab\u00bb\u201e\u201c\u201d\u2018\u2019]+", "", t)
    if GLOSS_RE.search(t0):
        return True
    if re.fullmatch(r"[A-Za-z/\\<>\u00ab\u00bb(){}^|'\-7]{1,6}[.,^]", t0):
        letters = re.sub("[^a-z]", "", t0.lower())
        return letters in {"heb", "or", "im", "hed"} or "/" in t0 or not known(letters)
    return False


def strip_gloss_segment(seg: str) -> str:
    """Remove a marginal Hebrew gloss ('Heb. the feeder.') at the start or end of a segment."""
    toks = seg.split()
    for i, t in enumerate(toks):
        if GLOSS_RE.search(t):
            if i == 0:
                # gloss at start: drop up to the first token ending in '.' (max 5 tokens)
                j = 1
                while j < len(toks) and j < 6:
                    j += 1
                    if toks[j - 1].endswith("."):
                        break
                return " ".join(toks[j:])
            return " ".join(toks[:i])  # gloss at end of the line
    return seg


def jasher_1829_lines(log: list) -> tuple[list, list[list[str]]]:
    """Return (line stream for joining, verses as lists of lines) for the 1829 text."""
    raw = read_raw(JASHER_1829)
    end = next(i for i in range(JASHER_START, len(raw)) if JASHER_END_RE.search(raw[i]))
    log.append((JSLUG, JASHER_START, "body range", f"lines {JASHER_START}-{end - 1} of {JASHER_1829}"))
    lines = raw[JASHER_START:end]
    base = JASHER_START

    def squeeze(t: str) -> str:
        return " ".join(t.split())

    # pass 1a: running heads. Left pages: '<topic> ; JASHER. <topic>'; right pages:
    # 'Chap. iii. <topic>'. Topic halves printed on their own lines are short isolated
    # lines within 4 lines of the 'JASHER' / 'Chap.' line.
    drop: dict[int, str] = {}
    chap_tail = re.compile(r"\bCh\S{0,3}[.,]?\s+[ivxlcnmIVX]+[.,]\s*$")
    for i, ln in enumerate(lines):
        s = squeeze(ln)
        if JASHER_HEAD_RE.search(s) or (CHAP_HEAD_RE.match(s) and not CHAP_RE.match(s)) or chap_tail.search(s):
            drop[i] = "running head"
            for d in (-4, -3, -2, -1, 1, 2, 3, 4):
                j = i + d
                if not (0 <= j < len(lines)) or j in drop:
                    continue
                t = squeeze(lines[j])
                if not t or len(t) > 48 or VERSE_START_RE.match(t) or is_gloss_token(t.split()[0]):
                    continue
                if AM_RE.match(t) or YEAR_RE.match(t):
                    continue
                prev_blank = j == 0 or not lines[j - 1].strip()
                next_blank = j + 1 >= len(lines) or not lines[j + 1].strip()
                isolated = prev_blank and next_blank
                if isolated and (abs(d) <= 2 or re.match(r"^\W*(?:[A-Z]|and\b)", t)):
                    drop[j] = "running head"
                elif abs(d) == 1 and len(t) <= 40 and re.search(r"[.;]\W*$", t):
                    drop[j] = "running head"
    # topic heads whose 'JASHER' / 'Chap.' partner was lost: an isolated short line that is
    # directly followed by the 'A. M.' date that heads the margin of every page
    for i, ln in enumerate(lines):
        t = squeeze(ln)
        if i in drop or not t or len(t) > 45 or VERSE_START_RE.match(t) or not re.match(r"^\W*[A-Z]", t):
            continue
        if (i > 0 and lines[i - 1].strip()) or (i + 1 < len(lines) and lines[i + 1].strip()):
            continue
        nxt = next((squeeze(lines[k]) for k in range(i + 1, min(i + 4, len(lines))) if lines[k].strip()), "")
        if re.match(r"^A\.\s?M\.?", nxt):
            drop[i] = "running head"
    # pass 1b: marginal blocks (Hebrew glosses 'Heb. the feeder', 'A. M.' dates): blocks of
    # short lines in which at least one line opens with a gloss marker or is a date; and
    # short gloss fragments split off by the OCR right after such a block.
    blocks = []
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        j = i
        while j < len(lines) and lines[j].strip():
            j += 1
        blocks.append((i, j))
        i = j
    prev_marg_end = -10
    for i, j in blocks:
        blk = [squeeze(lines[x]) for x in range(i, j)]
        short = all(len(t) <= 24 for t in blk) and not any(VERSE_START_RE.match(t) and len(t) > 12 for t in blk)
        if not short:
            continue
        has_marg = any(is_gloss_token(t.split()[0]) or AM_RE.match(t) or YEAR_RE.match(t) for t in blk)
        follows = (i - prev_marg_end) <= 3 and len(blk) <= 3 and not any(VERSE_START_RE.match(t) for t in blk)
        if has_marg or follows:
            for x in range(i, j):
                drop.setdefault(x, "marginal gloss / date")
            prev_marg_end = j

    stream: list = []
    verses: list[list[str]] = []
    cur_verse: list[str] = []
    mode = "text"
    for i, ln in enumerate(lines):
        lno = base + i
        s = ln.strip()
        if not s:
            stream.append("")
            continue
        if CHAP_RE.match(s):
            mode = "summary"
            summary_lines = 0
            log.append((JSLUG, lno, "chapter heading", squeeze(s)))
            if cur_verse:
                verses.append(cur_verse)
                cur_verse = []
            stream.append(PARA)
            continue
        if i in drop and mode != "summary":
            log.append((JSLUG, lno, drop[i], squeeze(s)))
            continue
        if mode == "summary":
            # the editor-style chapter summary runs until verse 1, whose first word is a
            # large initial (garbled by the OCR) or in capitals
            s_ = re.sub(r"^\s*(?:\d[\d\-.,']{2,}\s+|A\.?\s?M\.?\s+)+", "", s)
            m = re.match(r"^\s*(?:[1I\]|l]\s+)?(\S+)", s_)
            first = m.group(1) if m else ""
            is_v1 = bool(re.search(r"[\^\\\]|!]", first) or re.fullmatch(r"[A-Z]{2,}", first)
                         or re.match(r"^A[-.'\^](?!\s?M\b)", first) or re.fullmatch(r"\S{0,3}[O0]W", first))
            if AM_RE.match(s_) or YEAR_RE.match(s_):
                is_v1 = False
            elif not is_v1 and re.match(r"^\s*[\]|\\^]", s_) and not re.search(r"\d", s_[:6]):
                is_v1 = True
            if is_v1:
                s = s_
                m = re.match(r"^\s*(?:[1I\]|l]\s+)?(\S+)", s)
            summary_lines += 1
            if summary_lines == 20:
                log.append((JSLUG, lno, "WARNING: " + "chapter summary longer than 20 lines", squeeze(s)))
            if not is_v1:
                log.append((JSLUG, lno, "chapter summary", squeeze(s)))
                continue
            mode = "text"
            if m:
                s = s[m.start(1):]
            s = jasher_dropcap(s)
            s = re.sub(r"^([A-Z])([A-Z]+)\b", lambda mm: mm.group(1) + mm.group(2).lower(), s)
            if cur_verse:
                verses.append(cur_verse)
            cur_verse = []
            stream.append(PARA)
        elif AM_RE.match(s) or YEAR_RE.match(s) or len(squeeze(s)) <= 2:
            log.append((JSLUG, lno, "margin date / page no. / signature", squeeze(s)))
            continue
        # split off marginal-column material separated by wide gaps
        segs = [g for g in re.split(r"\s{4,}", s) if g.strip()]
        kept = []
        for g in segs:
            g0 = squeeze(g)
            if AM_RE.match(g0) or YEAR_RE.match(g0):
                log.append((JSLUG, lno, "margin date", g0))
                continue
            g1 = strip_gloss_segment(g0)
            if g1 != g0:
                log.append((JSLUG, lno, "marginal gloss", g0))
            if g1.strip():
                kept.append(g1)
        s = " ".join(kept)
        s = re.sub(r"^\s*A\.\s?M\.\s+", "", s)
        s = re.sub(r"^\s*\d{4}\.\s+", "", s)
        s = re.sub(r"\s+\d{4}\.?\s*$", "", s)
        s = re.sub(r"\s+A\.\s?M\.\s*$", "", s)
        if not s.strip():
            continue
        vm = VERSE_START_RE.match(s)
        if vm:
            s = s[vm.end():]
            if cur_verse:
                verses.append(cur_verse)
            cur_verse = []
            stream.append(PARA)
        s = jasher_clean_tokens(s)
        if not s:
            continue
        if letters_share(s) < 0.5:
            log.append((JSLUG, lno, "OCR debris", s))
            continue
        stream.append(s)
        cur_verse.append(s)
    if cur_verse:
        verses.append(cur_verse)
    return stream, verses


def ngrams(tokens: list[str], n: int) -> set:
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def norm_tokens(text: str) -> list[str]:
    text = normalize_chars(text)
    toks = [w.lower() for w in WORD_RE.findall(text)]
    out = []
    for w in toks:
        r = longs_candidate(w)
        out.append(r if r else w)
    return out


def jasher_1751_witness() -> tuple[set, set]:
    raw = (RAW / JASHER_1751).read_text(encoding="utf-8")
    # the 1751 scan: body from 'CHAP. I.' to the start of the Notes
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == "CHAP. I.")
    end = next(i for i, l in enumerate(lines) if l.startswith("Netes relative to Chap. I."))
    toks = norm_tokens("\n".join(lines[start:end]))
    return ngrams(toks, 2), ngrams(toks, 3)


def jasher_insertions(verses: list[list[str]]) -> tuple[set[int], list[float]]:
    """Verses of the 1829 text that have no counterpart in the 1751 printing.

    Score = share of the verse's word trigrams found anywhere in the 1751 scan (after the
    same long-s normalisation). Genuine verses score ~0.8 (median); verses added by the 1829
    editor score near 0. A run of >= 4 consecutive verses all scoring < 0.35 (verses under
    6 words are neutral) is treated as an 1829 addition.
    """
    _, tri51 = jasher_1751_witness()
    scores = []
    for v in verses:
        toks = norm_tokens(" ".join(v))
        g = ngrams(toks, 3)
        scores.append(len(g & tri51) / len(g) if len(toks) >= 6 and g else None)
    removed: set[int] = set()
    i = 0
    while i < len(verses):
        if scores[i] is None or scores[i] >= 0.35:
            i += 1
            continue
        j = i
        while j < len(verses) and (scores[j] is None or scores[j] < 0.35):
            j += 1
        scored = [scores[k] for k in range(i, j) if scores[k] is not None]
        if len(scored) >= 4 and statistics.mean(scored) < 0.25:
            removed.update(range(i, j))
        i = j
    return removed, scores


# --------------------------------------------------------------------------------------
# Prose: bim eighteenth-century scans
# --------------------------------------------------------------------------------------

PAGE_NO_RE = re.compile(r"^\W*(?:[\[\(]?\s*[0-9ivxlcIlVXLC]{1,4}\s*[\]\)\}]?|[\[\(]\s*\S{1,4}\s*[\]\)\}])\W*$")
SIG_RE = re.compile(r"^\W*[A-Z][a-z]?\s*\d{0,3}\W*$")
SIG_PREFIX_RE = re.compile(r"^\s*(?:[A-Z]{1,2}|[A-Z][a-z]|\d?[a-z])\s?\d{1,3}\s+(?=\S)")
NOTE_REF_RE = re.compile(r"\(\s?[A-Za-z0-9*+%]{0,2}\s?\)")  # in-text footnote reference '(a)'
NOTE_RE = re.compile(r"^\s*[\(\[{]\s*[^\s\)\]]{0,2}\s*[\)\]}]\s*[\"'A-Z\d]")
QUOTE_TOKENS = {'"', "'", '""', "''", '"\'', '<<', '<', '&', 'ce', 'cc', 'c', 'te', 'e', '*', '*"', '%',
                '4', '66', '6', 'ec', 'Ce', '"*', '*\'', '„', '+'}
MARGIN_TAIL_RE = re.compile(
    r"\s+(?:PA\s?R\s?T|C\s?H\s?A\s?[Pp]\.?|S\s?[Ee]\s?[Cc]\s?[Tr]\.?|INTRO-?|DUCT\.?|[IVXL]{2,5}\.?|[IVXL]\.)\s*[?,.]?\s*$"
)
MARGIN_HEAD_RE = re.compile(r"^\s*(?:PA\s?R\s?T|C\s?H\s?A\s?P\.?|S\s?E\s?C\s?T\.?|INTRO-?)\s+(?=[a-z])")
MARGIN_ONLY_RE = re.compile(
    r"^\W*(?:PA\s?R\s?T|C\s?H\s?A\s?[Pp]|S\s?[Ee]\s?[Cc]\s?[Tr]|INTRO-?|DUCT|[IVXL]{1,5})\W*[IVXL]{0,5}\W*$"
)
# marginal scripture reference standing alone on a line, e.g. 'Pal. xix.1.', 'Matth. iv,'
MARGIN_REF_RE = re.compile(r"^\W*(?:\d\s*)?[A-Z]?[a-z]{1,6}\.?\s*[ivxlcIVXLC]{1,6}[.,]?\s*[\d.,\-\s]*$")


def norm_head(s: str) -> str:
    s = re.sub(r"[^a-z ]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def is_head(s: str, heads: list[str]) -> bool:
    if len(s) > 60:
        return False
    n = norm_head(s)
    if len(n) < 4:
        return False
    for h in heads:
        if h in n and len(n) <= len(h) + 10:
            return True
        if difflib.SequenceMatcher(None, n, h).ratio() >= 0.8:
            return True
    return False


def first_token(s: str) -> str:
    t = s.split()
    return re.sub(r"[^A-Za-z]", "", t[0]).lower() if t else ""


def strip_quote_marker(s: str) -> tuple[str, bool]:
    st = s.lstrip()
    toks = st.split(None, 1)
    if not toks:
        return s, False
    t0 = toks[0]
    if t0 in QUOTE_TOKENS or re.fullmatch(r"[\"'*&%<>,.]+", t0):
        return (toks[1] if len(toks) > 1 else ""), True
    if t0[0] in "\"'" and len(t0) > 1 and t0[1].isalpha():
        return st[1:], True
    return s, False


def clean_bim(cfg: dict, log: list, qlog: list) -> tuple[str, dict]:
    raw = read_raw(cfg["file"])
    stats = {"long_s_chars": 0}
    lines: list[tuple[int, str]] = []
    stats["words_raw_range"] = sum(len(raw[i].split()) for a, b in cfg["ranges"] for i in range(a, min(b, len(raw) - 1) + 1))
    for a, b in cfg["ranges"]:
        b = min(b, len(raw) - 1)
        for i in range(a, b + 1):
            stats["long_s_chars"] += raw[i].count("ſ")
            lines.append((i, normalize_chars(raw[i]).rstrip()))
    drop_ranges = cfg.get("drop", [])
    heads = cfg.get("heads", [])
    note_len = cfg.get("note_len")

    # ---- pass 1: classify furniture / notes / debris line by line
    cls: list[str] = []  # 'text', 'blank', or reason for removal
    texts: list[str] = []
    note_mode = False
    note_lines = 0
    # block median lengths for long-line footnote detection
    block_len: dict[int, float] = {}
    note_end_len = cfg.get("note_end_len")
    if note_len or note_end_len:
        k = 0
        while k < len(lines):
            if not lines[k][1].strip():
                k += 1
                continue
            j = k
            while j < len(lines) and lines[j][1].strip():
                j += 1
            lens = [len(lines[x][1].strip()) for x in range(k, j)]
            if len(lens) >= 3:
                med = statistics.median(lens)
                for x in range(k, j):
                    block_len[x] = med
            k = j
    for idx, (lno, ln) in enumerate(lines):
        s = ln.strip()
        if any(a <= lno <= b for a, b, _ in drop_ranges):
            reason = next(r for a, b, r in drop_ranges if a <= lno <= b)
            cls.append(reason)
            texts.append(s)
            continue
        if not s:
            cls.append("blank")
            texts.append("")
            continue
        furniture = None
        if is_head(s, heads):
            furniture = "running head"
        elif PAGE_NO_RE.match(s):
            furniture = "page number"
        elif SIG_RE.match(s) and len(s) <= 6:
            furniture = "signature"
        if furniture:
            if note_mode:
                note_mode = False
            cls.append(furniture)
            texts.append(s)
            continue
        if note_mode and note_end_len and idx in block_len and block_len[idx] < note_end_len:
            note_mode = False  # a block of full-measure lines: main text has resumed
        if not note_mode:
            if NOTE_RE.match(s):
                note_mode, note_lines = True, 0
            elif note_len and block_len.get(idx, 0) >= note_len:
                note_mode, note_lines = True, 0
            elif (cfg.get("note_line_len") and len(s) >= cfg["note_line_len"]
                  and cfg["note_line_range"][0] <= lno <= cfg["note_line_range"][1]):
                note_mode, note_lines = True, 0  # small-type footnote line (full measure is shorter)
        if note_mode:
            note_lines += 1
            if note_lines == 80:
                log.append((cfg["slug"], lno, "WARNING: footnote mode ran 80 lines", s))
            cls.append("footnote")
            texts.append(s)
            continue
        # marginal material; stray rule/bar tokens at either end of the line
        s2 = re.sub(r"^(?:[|\\/_=~:;.,\-\u2014]+\s+)+", "", s)
        s2 = re.sub(r"(?:\s+[|\\/_=~:;.,\-\u2014]+)+$", "", s2)
        s2 = MARGIN_HEAD_RE.sub("", s2)
        s2 = MARGIN_TAIL_RE.sub("", s2) if cfg.get("margin_tail") else s2
        if MARGIN_ONLY_RE.match(s2) or (len(s2) <= 22 and MARGIN_REF_RE.match(s2)):
            cls.append("marginal note")
            texts.append(s)
            continue
        # signature + catchword ('B 2 up')
        if len(s2.split()) <= 3:
            s2 = SIG_PREFIX_RE.sub("", s2)
        # debris
        share, nwords = known_share(s2)
        if letters_share(s2) < 0.5 or (nwords >= 3 and share < 0.4) or (nwords < 3 and share == 0 and len(s2) < 12):
            cls.append("OCR debris")
            texts.append(s)
            continue
        cls.append("text")
        texts.append(s2)

    # ---- pass 2: catchwords (single word at page foot repeated at the head of the next page)
    for idx in range(len(lines)):
        if cls[idx] != "text":
            continue
        toks = texts[idx].split()
        if len(toks) != 1:
            continue
        w = first_token(toks[0])
        if not w:
            continue
        # next text line
        seen_break = False
        for j in range(idx + 1, min(idx + 120, len(lines))):
            if cls[j] in ("running head", "page number", "signature", "footnote"):
                seen_break = True
            if cls[j] == "text":
                if seen_break and first_token(texts[j]) and (
                        first_token(texts[j]) == w or first_token(texts[j]).startswith(w) or w.startswith(first_token(texts[j]))):
                    cls[idx] = "catchword"
                break

    # ---- pass 3: long quotations = runs of >= QMIN lines that each open with a quote mark
    qmin = cfg.get("quote_min", 4)
    text_idx = [i for i in range(len(lines)) if cls[i] == "text"]
    marked = {i: strip_quote_marker(texts[i])[1] for i in text_idx}
    run: list[int] = []

    def flush(run: list[int]):
        if len(run) >= qmin and sum(len(texts[i].split()) for i in run) >= cfg.get("quote_min_words", 30):
            first = run[0]
            pos = text_idx.index(first)
            qtext = " ".join(texts[i] for i in run)
            # the quotation opens on the line before the run: cut that line at its last quote mark
            if pos > 0:
                p = text_idx[pos - 1]
                t = texts[p]
                k = max(t.rfind('"'), t.rfind("“"))
                if k > 0:
                    qtext = t[k:] + " " + qtext
                    texts[p] = t[:k].rstrip()
            # the quotation closes inside its last line: keep what follows the closing mark
            last = run[-1]
            t = texts[last]
            k = t.rfind('"')
            tail = t[k + 1:].strip() if k >= 0 else ""
            for i in run:
                cls[i] = "long quotation"
            if len(tail.split()) >= 2:
                cls[last] = "text"
                texts[last] = tail
            qlog.append((cfg["slug"], lines[first][0], lines[last][0], len(qtext.split()), qtext[:160]))
        else:
            for i in run:
                texts[i] = strip_quote_marker(texts[i])[0]

    for i in text_idx:
        if marked[i]:
            run.append(i)
        else:
            flush(run)
            run = []
    flush(run)

    if DEBUG:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_DIR / f"{cfg['slug']}_lines.tsv", "w") as fh:
            for idx, (lno, ln) in enumerate(lines):
                fh.write(f"{lno}\t{cls[idx][:10]:10}\t{ln}\n")

    # ---- assemble
    stream: list = []
    for idx, (lno, _) in enumerate(lines):
        c = cls[idx]
        if c == "text":
            stream.append(texts[idx])
        elif c == "blank":
            stream.append("")
        else:
            log.append((cfg["slug"], lno, c, texts[idx] if texts[idx] else lines[idx][1]))
    paras = [tidy(NOTE_REF_RE.sub(" ", p)) for p in join_lines(stream)]
    paras = [p for p in paras if p and len(WORD_RE.findall(p)) >= 1]
    stats["removed_by_reason"] = Counter(c for c in cls if c not in ("text", "blank"))
    return "\n\n".join(paras), stats


# head phrases (normalised: lower case, letters only)
PROSE = [
    {
        "slug": "prose__oration_joyners_hall_1733",
        "file": "prose/bim_eighteenth-century_the-oration-spoke-at-joy_ilive-jacob_1733.djvu.txt",
        "title": "The Oration spoke at Joyners-Hall (1733)",
        "ranges": [(59, 4440)],
        "drop": [],
        "heads": ["the dedication", "the depicartion", "the preface", "preface", "the doctrine of the plurality",
                  "of worlds aserted", "of worlds asserted", "of worlds aerted", "of the fall of the angels",
                  "their rebellion expulsion c", "their rebellion expulfion c"],
        "note_len": 55,
        "note_end_len": 52,
    },
    {
        "slug": "prose__oration_trinity_hall_1738",
        "file": "prose/bim_eighteenth-century_the-oration-spoke-at-tri_ilive-jacob_1738.djvu.txt",
        "title": "The Oration spoke at Trinity-Hall (1738)",
        "ranges": [(173, 2504)],
        "drop": [],
        "heads": ["the doctrine of the", "resurrection stated", "resurrection fated", "resurrection ated",
                  "te doftrine of c"],
    },
    {
        "slug": "prose__speech_master_printers_1750",
        "file": "prose/bim_eighteenth-century_the-speech-of-mr-jacob-_ilive-jacob_1750.djvu.txt",
        "title": "The Speech of Mr. Jacob Ilive to his Brethren the Master-Printers (1750)",
        "ranges": [(74, 259)],
        "drop": [(94, 97, "signature + footnote"), (149, 149, "footnote")],
        "heads": [],
    },
    {
        "slug": "prose__reasons_house_of_correction_1757",
        "file": "prose/bim_eighteenth-century_reasons-offered-for-the-_ilive-jacob_1757.djvu.txt",
        "title": "Reasons offered for the Reformation of the House of Correction in Clerkenwell (1757)",
        "ranges": [(305, 4600)],
        "drop": [(2599, 2642, "account table"), (2662, 2695, "account table"), (3974, 4004, "account table")],
        "heads": [],
        "note_end_len": 60,
        "note_line_len": 64,
        "note_line_range": (305, 4440),
    },
    {
        "slug": "prose__laymans_vindication_1730",
        "file": "prose/bim_eighteenth-century_the-laymans-vindication_ilive-jacob_1730.djvu.txt",
        "title": "The Layman's Vindication of the Christian Religion (1730)",
        "ranges": [(66, 495), (560, 22000)],
        "drop": [],
        "heads": ["dedication", "preface", "concerning reason", "the validity of the writings",
                  "of the old testament", "the state of the jews", "and heathens", "the internal excellence",
                  "of the gospel", "the divinity of christ", "vindicated", "christian religion",
                  "general expectation", "of the messiah", "prophetic expectation of a revelation",
                  "miracles confirm the truth", "prophecies testify the truth", "christianity"],
        "margin_tail": True,
    },
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list = []
    qlog: list = []
    report: dict = {}
    all_repairs: dict[str, Counter] = {}

    # ---------------- scripture
    stream, verses = jasher_1829_lines(log)
    removed_v, scores = jasher_insertions(verses)
    jasher_paras = []
    ins_words = 0
    ins_runs = []
    for k, v in enumerate(verses):
        par = " ".join(join_lines(v, blank_breaks=False))
        # paragraph mark (pilcrow) at the head of a verse, read by the OCR as '51', '5[', 'f', 'H' ...
        par = re.sub(r"^(?:51|5\[|5F|5|f\"?|T|H|IT|fT|\^|\[\^|\*\[|\[)\s+(?=[A-Z])", "", par)
        par = re.sub(r"^H(?=And\b)", "", par)
        par = tidy(par)
        if not par:
            continue
        if k in removed_v:
            ins_words += wc(par)
            if not ins_runs or ins_runs[-1][1] != k - 1:
                ins_runs.append([k, k, par[:120]])
            else:
                ins_runs[-1][1] = k
            log.append((JSLUG, -1, "1829 addition (no counterpart in 1751)", par))
            continue
        jasher_paras.append(par)
    raw29 = read_raw(JASHER_1829)
    jend = next(i for i in range(JASHER_START, len(raw29)) if JASHER_END_RE.search(raw29[i]))
    stats = {"words_raw_range": sum(len(raw29[i].split()) for i in range(JASHER_START, jend)),
             "body_lines": f"{JASHER_START}-{jend - 1}",
             "verses": len(verses), "verses_removed_1829_additions": len(removed_v),
             "words_removed_1829_additions": ins_words, "addition_runs": ins_runs,
             "median_trigram_overlap_with_1751": statistics.median([s for s in scores if s is not None])}
    outputs = [("scripture__book_of_jasher", "The Book of Jasher (1751), text of the 1829 Bristol reprint",
                "\n\n".join(jasher_paras), stats)]

    # ---------------- prose
    for cfg in PROSE:
        text, st = clean_bim(cfg, log, qlog)
        outputs.append((cfg["slug"], cfg["title"], text, st))

    # ---------------- long-s repair on every output, both sides alike
    summary = {}
    for slug, title, text, st in outputs:
        before = wc(text)
        fixed, reps = longs_repair(text)
        all_repairs[slug] = reps
        (OUT / f"{slug}.txt").write_text(fixed.strip() + "\n", encoding="utf-8")
        st = dict(st)
        st["words"] = wc(fixed)
        st["longs_f_to_s_words"] = sum(reps.values())
        st["longs_f_to_s_types"] = len(reps)
        st["top_repairs"] = [f"{a}->{b} ({n})" for (a, b), n in reps.most_common(30)]
        if "removed_by_reason" in st:
            st["removed_by_reason"] = dict(st["removed_by_reason"])
        rw: Counter = Counter()
        for e in log:
            if e[0] == slug and not str(e[2]).startswith(("WARNING", "body")):
                rw[e[2]] += len(str(e[3]).split())
        st["removed_words_by_reason"] = dict(rw)
        st["removed_quotation_words"] = sum(q[3] for q in qlog if q[0] == slug)
        summary[slug] = {"title": title, **st}
        print(f"{slug}: {st['words']} words; long-s chars {st.get('long_s_chars', 0)}; f->s repairs {st['longs_f_to_s_words']}")

    # audit files
    with open(OUT / "removed_lines.tsv", "w", encoding="utf-8") as fh:
        fh.write("output\traw_line\treason\ttext\n")
        for e in log:
            fh.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in e) + "\n")
    with open(OUT / "removed_quotations.tsv", "w", encoding="utf-8") as fh:
        fh.write("output\tfirst_raw_line\tlast_raw_line\twords\tstart_of_text\n")
        for q in qlog:
            fh.write("\t".join(str(x).replace("\t", " ") for x in q) + "\n")
    rep_all: Counter = Counter()
    for r in all_repairs.values():
        rep_all.update(r)
    summary["_all_files_top_repairs"] = [f"{a}->{b} ({n})" for (a, b), n in rep_all.most_common(30)]
    summary["_side_words"] = {
        "scripture": sum(v["words"] for k, v in summary.items() if k.startswith("scripture__")),
        "prose": sum(v["words"] for k, v in summary.items() if k.startswith("prose__")),
    }
    (OUT / "stats.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(summary["_side_words"])


if __name__ == "__main__":
    main()
