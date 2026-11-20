#!/usr/bin/env python
"""Clean the two-register texts of Richard Grant White.

Follows prepare/two_register/CLEANING_PROTOCOL.md.

Inputs (never modified), under data/raw/two_register_authors/white_richard_grant/:
  scripture/newgospelofpeac00whit.djvu.txt   The New Gospel of Peace, 1866 collected ed.
                                             (Indiana State Library scan; chosen over the LoC
                                             scan newgospelpeace00white, see CLEANING.md)
  prose/wordsandthieruses00whitrich.djvu.txt Words and Their Uses (revised ed.)
  prose/englandwithoutwi01whit.djvu.txt      England Without and Within

Outputs, under data/prepared/two_register/white_richard_grant/:
  scripture__new_gospel_of_peace.txt
  prose__words_and_their_uses.txt
  prose__england_without_and_within.txt
  removed_lines.tsv        (every raw line dropped, with the rule that dropped it)
  removed_quotations.tsv   (log of quoted spans cut out of running text, for checking)
  wtu_line_end_joins.tsv   (words rejoined across line ends where the OCR lost the hyphen)
  stats.json               (counts used in CLEANING.md)
  CLEANING.md is written by hand from these logs and from reading samples.

Method, per work:
  1. Keep the body line range (located by regex; the found line numbers are asserted).
  2. Split into pages at running heads, and pages into blocks at blank lines.
  3. Classify blocks. The printed books set notes, chapter summaries, block quotations and
     footnotes in smaller type, which the OCR shows as longer lines; a block whose median
     line length is above a per-work threshold is removed. Footnote zones (from a footnote
     start to the page foot) are removed whole. Headings, running heads, page numbers,
     signature marks and displayed verse are removed.
  4. Join the remaining blocks into paragraphs (blocks continuing across a page or a stray
     mark are rejoined), join hyphenated and wrapped lines, strip verse numbers (scripture).
  5. Prose: remove quoted passages longer than the limit for the work (see QUOTE_RULES).

Run:  python prepare/two_register/clean_white_richard_grant.py
"""
from __future__ import annotations

import collections
import json
import re
import statistics
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vocabulary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/two_register_authors/white_richard_grant"
OUT = ROOT / "data/prepared/two_register/white_richard_grant"

WORD_RE = re.compile(r"[A-Za-z]+")


# ----------------------------------------------------------------------------------------
# generic helpers
# ----------------------------------------------------------------------------------------
def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").split("\n")


def norm(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def n_words(text: str) -> int:
    return len(text.split())


def find_line(lines: list[str], pattern: str, start: int = 0, end: int | None = None) -> int:
    """Return the 1-based number of the first line matching pattern in [start, end)."""
    rx = re.compile(pattern)
    for i in range(start, len(lines) if end is None else end):
        if rx.search(lines[i]):
            return i + 1
    raise ValueError(f"pattern not found: {pattern}")


def letters(s: str) -> str:
    return "".join(ch for ch in s if ch.isalpha())


def upper_ratio(s: str) -> float:
    lt = letters(s)
    return sum(ch.isupper() for ch in lt) / len(lt) if lt else 0.0


NUMLIKE = r"[\dIlOoSi\*\]\[\(\)\^\-\.,]{1,6}"


def is_junk(line: str) -> bool:
    """Signature marks, stray marks and lines that are mostly non-letters."""
    if not line:
        return False
    lt = letters(line)
    if len(lt) <= 1 and len(line) <= 8:
        return True
    if len(line) >= 4 and len(lt) / len(line) < 0.45:
        return True
    if re.fullmatch(r"[a-zA-Z]{1,2}\d*[\^\*\.,]?", line) and line not in ("I", "a", "A", "O"):
        return True
    return False


def median_len(block: list[tuple[int, str]]) -> float:
    lines = block[:-1] if len(block) > 2 else block
    return statistics.median(len(t) for _, t in lines)


def split_blocks(numbered: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    blocks, cur = [], []
    for ln, t in numbered:
        if not t:
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append((ln, t))
    if cur:
        blocks.append(cur)
    return blocks


# ----------------------------------------------------------------------------------------
# vocabulary (for joining words broken at line ends)
# ----------------------------------------------------------------------------------------
class Vocab:
    """Word and bigram counts from the corpus (text_norm, words occurring >= 3 times),
    plus words seen in the interior of lines (not at either end) in White's raw files."""

    def __init__(self, raw_files: list[Path]):
        self.corpus = collections.Counter(vocabulary.words())
        self.bigram = vocabulary.pairs()
        inner: collections.Counter = collections.Counter()
        for f in raw_files:
            for line in read_lines(f):
                toks = norm(line).split()
                for tok in toks[1:-1]:
                    if re.fullmatch(r"[\"'(\[]*[A-Za-z]+[\"'.,;:!?)\]]*", tok):
                        inner[WORD_RE.search(tok).group(0).lower()] += 1
        self.inner = collections.Counter({w: c for w, c in inner.items() if c >= 2})
        self.system = vocabulary.dictionary()   # used only for joining line-broken words

    def count(self, w: str) -> int:
        w = w.lower()
        return self.corpus.get(w, 0) + self.inner.get(w, 0)

    def known(self, w: str) -> bool:
        return self.count(w) > 0 or w.lower() in self.system


# ----------------------------------------------------------------------------------------
# joining lines into paragraph text
# ----------------------------------------------------------------------------------------
class Joiner:
    def __init__(self, vocab: Vocab, join_unhyphenated: bool):
        self.v = vocab
        self.join_unhyphenated = join_unhyphenated
        self.stats = collections.Counter()
        self.joined_pairs = collections.Counter()

    def join(self, lines: list[str]) -> str:
        out = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not out:
                out = line
                continue
            out = self._join2(out, line)
        return out

    def _join2(self, left: str, right: str) -> str:
        # the OCR sometimes reads a line-end hyphen as "*" or a stray mark
        left = re.sub(r"(?<=[A-Za-z])[*\u2022\u25a0~]\s*$", "-", left)
        m_l = re.search(r"([A-Za-z]+)(-)\s*$", left)
        m_r = re.match(r"([\"'(]*)([A-Za-z]+)", right)
        if m_l and m_r:
            a, b = m_l.group(1), m_r.group(2)
            if b[0].islower():
                if self.v.known(a + b) or not (self.v.known(a) and self.v.known(b)):
                    self.stats["hyphen_joined"] += 1
                    return left[: m_l.start(2)] + right
                self.stats["hyphen_kept"] += 1
                return left[: m_l.end(2)] + right
        if self.join_unhyphenated:
            m_l2 = re.search(r"(?<![A-Za-z'])([A-Za-z]+)\s*$", left)
            m_r2 = re.match(r"([A-Za-z]+)(?![A-Za-z'])", right)
            if m_l2 and m_r2 and m_r2.group(1)[0].islower():
                a, b = m_l2.group(1), m_r2.group(1)
                ab = a + b
                ka, kb, kab = self.v.known(a), self.v.known(b), self.v.known(ab)
                join = False
                if kab and not (ka and kb):
                    join = True
                elif not ka and not kb and len(a) >= 2 and len(b) >= 2:
                    join = True         # two unknown fragments: a word split at the line end
                elif kab and ka and kb and len(a) >= 2 and len(b) >= 2:
                    # both halves are words ("in deed", "with in"): join only when the
                    # joined word is attested (5+) and commoner than the two-word sequence
                    join = self.v.count(ab) > self.v.bigram.get((a.lower(), b.lower()), 0) \
                        and self.v.count(ab) >= 5
                if join:
                    self.stats["unhyphenated_joined"] += 1
                    self.joined_pairs[f"{a} {b}"] += 1
                    return left[: m_l2.start(1)] + ab + right[m_r2.end(1):]
        return left + " " + right


def tidy(text: str) -> str:
    text = text.replace("­", "")
    text = re.sub(r"[\^†‡]", "", text)          # footnote reference marks
    text = re.sub(r"(?<=\S) \*(?=\s|$)", "", text)          # " *" footnote marks
    text = re.sub(r"(?<=[\w.,;:!?\"')\]])\*+(?=\s|$)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ----------------------------------------------------------------------------------------
# quotation removal (prose)
# ----------------------------------------------------------------------------------------
SENT_END = re.compile(r"(\S*)[.!?][\"')\]]*\s+[\"'(]*[A-Z]")
ABBREV = {"mr", "mrs", "dr", "st", "rev", "messrs", "gen", "capt", "col", "prof", "hon", "esq",
          "jr", "sr", "vol", "p", "pp", "ch", "chap", "no", "viz", "etc", "ed", "cf", "ibid", "i.e",
          "e.g", "a.d", "b.c", "lib", "fol", "sect", "anglice", "angl"}


def n_sentences(span: str) -> int:
    n = 1
    for m in SENT_END.finditer(span):
        tok = m.group(1).strip("\"'([").lower()
        if tok in ABBREV or re.fullmatch(r"[a-z]|[ivxlc]+", tok):
            continue
        n += 1
    return n


def remove_quotes(paragraphs: list[str], max_words: int, max_sentences: int, work: str,
                  log: list[list], only_prefixes: tuple[str, ...] | None = None,
                  drop_quoted_paragraphs: bool = False) -> list[str]:
    """Remove "..." spans that are longer than allowed. Quote marks in the OCR are
    normalised first ('' ,, “ ” *' -> "). A span is only taken when the opening mark is
    preceded by start/space/punctuation and the closing mark is followed by
    end/space/punctuation; spans over 400 words are assumed to be unmatched marks and
    left alone. An attribution that follows the span (' — Source, p. 9.') is cut with it."""
    out = []
    for p in paragraphs:
        p = re.sub(r"''|,,|[“”]|\*'|'\*", '"', p)
        p = re.sub(r'"\s+"', '" "', p)
        if drop_quoted_paragraphs and p.startswith('"') and p.count('"') % 2 == 0:
            # a paragraph made (almost) wholly of quoted matter: a displayed quotation
            idx = [m.start() for m in re.finditer('"', p)]
            inside = sum(idx[j + 1] - idx[j] for j in range(0, len(idx), 2))
            if inside / len(p) >= 0.8 and (n_words(p) > max_words
                                            or n_sentences(p) > max_sentences):
                log.append([work, n_words(p), n_sentences(p), "[paragraph] " + p[:150], ""])
                continue
        pieces = []
        pos = 0
        i = 0
        quote_idx = [m.start() for m in re.finditer('"', p)]
        if len(quote_idx) % 2:
            # an odd number of marks: pairing is unreliable, so nothing is cut here
            quote_idx = []
        k = 0
        while k + 1 < len(quote_idx):
            s, e = quote_idx[k], quote_idx[k + 1]
            pre = p[s - 1] if s > 0 else " "
            post = p[e + 1] if e + 1 < len(p) else " "
            opening_ok = pre in " (—-:[" or s == 0
            closing_ok = post in " .,;:!?)—-]" or e + 1 == len(p)
            span = p[s + 1:e]
            if not (opening_ok and closing_ok):
                k += 1
                continue
            nw = n_words(span)
            nsent = n_sentences(span)
            if nw <= 400 and (nw > max_words or nsent > max_sentences) \
                    and (only_prefixes is None
                         or any(span.strip().startswith(x) for x in only_prefixes)):
                end = e + 1
                m = re.match(r"\s*[.,;:]?\s*—\s*[^.]{0,80}?(?:\d+|[A-Z][^.]{0,40})\.(?=\s|$)",
                             p[end:])
                if m and n_words(m.group(0)) <= 14:
                    end += m.end()
                pieces.append(p[pos:s])
                pieces.append(" ")
                log.append([work, nw, nsent, p[s:end][:160], p[max(0, s - 160):s]])
                pos = end
                k += 2
                continue
            k += 2
        pieces.append(p[pos:])
        q = "".join(pieces)
        q = re.sub(r"\s+([.,;:])", r"\1", q)
        q = re.sub(r"\s+", " ", q).strip()
        if letters(q) and n_words(q) >= 3:
            out.append(q)
        i += 1
    return out


# ----------------------------------------------------------------------------------------
# page / block classification shared by the prose works
# ----------------------------------------------------------------------------------------
def is_running_head(line: str, head_words: tuple[str, ...]) -> bool:
    if n_words(line) > 10:
        return False
    if re.fullmatch(NUMLIKE + r"(\s" + NUMLIKE + r")?", line):
        return True                                            # bare page number
    up = upper_ratio(line)
    has_num = bool(re.match(r"^" + NUMLIKE + r"\s", line) or re.search(r"\s" + NUMLIKE + r"$", line))
    if up >= 0.7 and has_num:
        return True
    low = line.lower()
    if any(h in low for h in head_words) and up >= 0.6:
        return True
    return False


def is_heading_line(line: str) -> bool:
    """CHAPTER lines and short all-capital lines (chapter titles, garbled running heads)."""
    if re.match(r"^CHAPTER\b", line):
        return True
    if n_words(line) <= 12 and upper_ratio(line) >= 0.75 and len(letters(line)) >= 3:
        return True
    return False


def is_verse_block(block: list[tuple[int, str]]) -> bool:
    """Displayed verse: several short lines, most beginning with a capital."""
    if len(block) < 2:
        return False
    texts = [t for _, t in block]
    caps = sum(1 for t in texts if re.match(r"^[\"'(]*[A-Z]", t)) / len(texts)
    med = statistics.median(len(t) for t in texts)
    # prose wraps mid-sentence, so its lines rarely all begin with a capital
    return (caps >= 0.75 and med < 40) or (len(texts) >= 3 and caps >= 0.9 and med < 48)


def drop_verse_runs(block: list[tuple[int, str]], max_len: int, log: list[list],
                    work: str) -> list[tuple[int, str]]:
    """Inside a body-type block, a run of two or more short lines that each begin with a
    capital is quoted verse set into the paragraph; prose lines run the full measure."""
    short = [len(t) < max_len and bool(re.match(r"^[\"'(\u2018\u201c]*[A-Z]", t)) for _, t in block]
    keep = [True] * len(block)
    i = 0
    while i < len(block):
        if short[i]:
            j = i
            while j < len(block) and short[j]:
                j += 1
            if j - i >= 2:
                for k in range(i, j):
                    keep[k] = False
                    log.append([work, block[k][0], "verse_in_paragraph", block[k][1]])
            i = j
        else:
            i += 1
    return [x for x, k in zip(block, keep) if k]


FOOTNOTE_START = re.compile(r"^(\*|t\s|\d\s+[A-Z\"]|[†‡]|1\s|I\s+[A-Z][a-z])")


def prose_paragraphs(lines: list[str], first: int, last: int, small_type: float, verse_max: int,
                     head_words: tuple[str, ...], joiner: Joiner, log: list[list],
                     work: str, drop_ranges: list[tuple[int, int]] = ()) -> list[str]:
    """Return paragraph strings for lines first..last (1-based, inclusive)."""
    numbered = []
    for ln in range(first, last + 1):
        if any(a <= ln <= b for a, b in drop_ranges):
            log.append([work, ln, "drop_range", norm(lines[ln - 1])])
            numbered.append((ln, ""))
            continue
        numbered.append((ln, norm(lines[ln - 1])))
    # pages
    pages: list[list[tuple[int, str]]] = [[]]
    for ln, t in numbered:
        if t and is_running_head(t, head_words):
            log.append([work, ln, "running_head", t])
            pages.append([])
            continue
        if t and is_junk(t):
            log.append([work, ln, "junk", t])
            pages[-1].append((ln, ""))
            continue
        pages[-1].append((ln, t))

    kept_blocks: list[tuple[list[tuple[int, str]], bool]] = []
    forced_break = False
    for page in pages:
        blocks = split_blocks(page)
        in_notes = False
        for bi, b in enumerate(blocks):
            # strip heading lines at block edges; text after a heading starts a paragraph
            while b and is_heading_line(b[0][1]):
                log.append([work, b[0][0], "heading", b[0][1]])
                b = b[1:]
                forced_break = True
            if not b:
                continue
            ml = median_len(b)
            first_text = b[0][1]
            if in_notes:
                if len(b) >= 3 and ml < small_type:
                    log.append([work, b[0][0], "body_after_note_KEPT", first_text])
                else:
                    for ln, t in b:
                        log.append([work, ln, "footnote_zone", t])
                    continue
            if ml >= small_type or (len(b) == 1 and len(first_text) >= small_type + 2):
                kind = "small_type"
                if FOOTNOTE_START.match(first_text):
                    kind = "footnote"
                    in_notes = True
                for ln, t in b:
                    log.append([work, ln, kind, t])
                continue
            if is_verse_block(b):
                for ln, t in b:
                    log.append([work, ln, "verse", t])
                continue
            b = drop_verse_runs(b, verse_max, log, work)
            if not b:
                continue
            kept_blocks.append((b, forced_break))
            forced_break = False

    # blocks -> paragraphs (rejoin continuations)
    paras: list[list[str]] = []
    for b, forced in kept_blocks:
        texts = [t for _, t in b]
        starts_lower = bool(re.match(r"^[\"'(]*[a-z]", texts[0]))
        prev_open = bool(paras) and not re.search(r"[.!?:][\s\"')\]]*$", paras[-1][-1])
        if paras and not forced and (starts_lower or prev_open):
            paras[-1].extend(texts)
        else:
            paras.append(texts)
    return [tidy(joiner.join(p)) for p in paras]


# ----------------------------------------------------------------------------------------
# The New Gospel of Peace
# ----------------------------------------------------------------------------------------
VER_RE = re.compile(r"^(V|F|Y|\\)\s?[eo]\s?[rf]s?[\.,:]?\s*[\dIl\$]")
VERSE_NUM_RE = re.compile(
    r"^(?:\d{1,2}(?:\s[\doIl])?|[IilJr]|[Il1i]{2}|[Il1][\do]|[\do][Il1]|lo|io|S|\$\$)\s?[\.,]\s+(?=\S)")
SCRIPTURE_SMALL = 49


def scripture_head(line: str) -> bool:
    if re.search(r"G[O0]SP[EI][LE]\s+OF\s+PE", line) and len(line) <= 48:
        return True
    if re.fullmatch(r"\(?[xvilcXVILC\d]{1,6}\)?", line):
        return True
    return False


SCRIPTURE_HEADINGS = re.compile(
    r"^(BOOK\b|B\s?O\s?O\s?K\b|CHAPTER\b|\[Published|NEW\s+GOSPEL\s+OF\s+PEACE|ACCORDING\s+TO|"
    r"The\s+New\s+Gospel\s+of\s+Peace\.?$|END\s+OF\s+THE|\d+\s*\(\d+\)$|\(\d+\)$)")


def clean_scripture(vocab: Vocab, log: list[list], stats: dict) -> list[str]:
    path = RAW / "scripture/newgospelofpeac00whit.djvu.txt"
    lines = read_lines(path)
    book1 = find_line(lines, r"^BOOK\s+I\s*$")
    first = find_line(lines, r"^CHAPTER\s+I\.", book1)
    last = find_line(lines, r"END\s+OF\s+THE\s+FOURTH\s+BOOK") - 1
    # Notes A and B: from "END OF THE FIRST/SECOND BOOK" to the next book's half-title.
    e1 = find_line(lines, r"END\s+OF\s+THE\s+FIRST\s+BOOK")
    b2 = find_line(lines, r"^The\s+New\s+Gospel\s+of\s+Peace\.", e1) - 1
    e2 = find_line(lines, r"END\s+OF\s+THE\s+SECOND\s+BOOK")
    b3 = find_line(lines, r"^The\s+New\s+Gospel\s+of\s+Peace\.", e2) - 1
    assert (first, last, e1, e2) == (889, 13228, 3494, 6511), (first, last, e1, e2)
    drop = [(e1, b2), (e2, b3)]
    stats["scripture_ranges"] = {"first": first, "last": last, "notes_dropped": drop}
    raw_words = sum(n_words(lines[i - 1]) for i in range(first, last + 1))
    stats["scripture_raw_words"] = raw_words
    work = "scripture"

    numbered = []
    for ln in range(first, last + 1):
        t = norm(lines[ln - 1])
        if any(a <= ln <= b for a, b in drop):
            log.append([work, ln, "end_note", t])
            t = ""
        numbered.append((ln, t))

    pages: list[list[tuple[int, str]]] = [[]]
    for ln, t in numbered:
        if t and scripture_head(t):
            log.append([work, ln, "running_head", t])
            pages.append([])
            continue
        if t and SCRIPTURE_HEADINGS.match(t):
            log.append([work, ln, "heading", t])
            numbered_t = ""
            pages[-1].append((ln, numbered_t))
            continue
        if t and is_junk(t):
            log.append([work, ln, "junk", t])
            pages[-1].append((ln, ""))
            continue
        pages[-1].append((ln, t))

    kept: list[list[tuple[int, str]]] = []
    after_chapter = set()
    chapter_lines = {ln for ln, t in numbered if re.match(r"^CHAPTER\b", t)}
    for page in pages:
        blocks = split_blocks(page)
        # chapter summaries: the first block after a CHAPTER heading, set in small type
        cls = []
        for b in blocks:
            ml = median_len(b)
            first_text = b[0][1]
            prev_heading = any(c < b[0][0] and b[0][0] - c <= 4 for c in chapter_lines)
            if prev_heading and (ml >= SCRIPTURE_SMALL - 2 or re.match(r"^[\dIir]\.?\s", first_text)):
                cls.append("summary")
            elif VER_RE.match(first_text):
                cls.append("note")
            elif ml >= SCRIPTURE_SMALL or (len(b) == 1 and len(first_text) >= SCRIPTURE_SMALL + 1):
                cls.append("note")
            else:
                cls.append("body")
        # footnote zone: from the first note block to the page foot
        if "note" in cls:
            z = cls.index("note")
            for j in range(z + 1, len(cls)):
                if cls[j] == "body":
                    # body type and either verse-numbered or 3+ lines: body text that the
                    # OCR placed after the notes, or a page whose running head was missed
                    if (VERSE_NUM_RE.match(blocks[j][0][1]) and len(blocks[j]) >= 2) \
                            or (len(blocks[j]) >= 3 and not is_verse_block(blocks[j])):
                        log.append([work, blocks[j][0][0], "body_after_note_KEPT", blocks[j][0][1]])
                        continue
                    cls[j] = "note_tail"
            # a short unnumbered block just before the zone, not first on the page,
            # is the tail end of a note continued from the previous page
            j = z - 1
            while j >= 1 and cls[j] == "body" and not VERSE_NUM_RE.match(blocks[j][0][1]) \
                    and (len(blocks[j]) <= 2 or is_verse_block(blocks[j])):
                cls[j] = "note_tail_before"
                j -= 1
        for b, c in zip(blocks, cls):
            if c == "body":
                kept.append(b)
            else:
                for ln, t in b:
                    log.append([work, ln, c, t])

    # paragraphs: each verse is a block; unnumbered blocks continue the previous verse
    paras: list[list[str]] = []
    n_stripped = 0
    for b in kept:
        texts = [t for _, t in b]
        m = VERSE_NUM_RE.match(texts[0])
        if m:
            texts[0] = texts[0][m.end():]
            n_stripped += 1
            paras.append(texts)
        elif paras and (re.match(r"^[\"'(]*[a-z]", texts[0])
                        or not re.search(r"[.!?:][\"')\]]*\s*$", paras[-1][-1])):
            paras[-1].extend(texts)
        else:
            paras.append(texts)
    # verse numbers left at the start of a line inside a block (verses not separated by a
    # blank line in the OCR): split there
    joiner = Joiner(vocab, join_unhyphenated=False)
    out = []
    for p in paras:
        cur: list[str] = []
        for t in p:
            m = re.match(r"^(\d{1,2})\.\s+(?=[A-Z])", t)
            if m and cur:
                out.append(cur)
                cur = [t[m.end():]]
                n_stripped += 1
            else:
                cur.append(t)
        out.append(cur)
    stats["scripture_verse_numbers_stripped"] = n_stripped
    text = [tidy(joiner.join(p)) for p in out]
    stats["scripture_join"] = dict(joiner.stats)
    return [t for t in text if t]


# ----------------------------------------------------------------------------------------
# Words and Their Uses
# ----------------------------------------------------------------------------------------
def clean_wtu(vocab: Vocab, log: list[list], stats: dict) -> list[str]:
    path = RAW / "prose/wordsandthieruses00whitrich.djvu.txt"
    lines = read_lines(path)
    contents = find_line(lines, r"^CONTENTS\.")
    first = find_line(lines, r"^CHAPTER\s+I\.\s*$", contents + 80)
    last = find_line(lines, r"^APPENDIX\.\s*$", first) - 1
    assert (first, last) == (688, 17623), (first, last)
    stats["wtu_range"] = [first, last]
    stats["wtu_raw_words"] = sum(n_words(lines[i - 1]) for i in range(first, last + 1))
    joiner = Joiner(vocab, join_unhyphenated=True)
    paras = prose_paragraphs(lines, first, last, small_type=56, verse_max=38,
                             head_words=("words and their", "misused words", "conclusion",
                                         "britisms", "briticisms", "introduction", "style",
                                         "dictionaries", "grammar", "tongue", "being done"),
                             joiner=joiner, log=log, work="wtu")
    stats["wtu_join"] = dict(joiner.stats)
    with open(OUT / "wtu_line_end_joins.tsv", "w", encoding="utf-8") as fh:
        fh.write("pair_joined\tcount\n")
        for pair, c in joiner.joined_pairs.most_common():
            fh.write(f"{pair}\t{c}\n")
    stats["wtu_words_before_quote_removal"] = sum(n_words(p) for p in paras)
    return paras


# ----------------------------------------------------------------------------------------
# England Without and Within
# ----------------------------------------------------------------------------------------
ENGLAND_QUOTES_BY_OTHERS = (
    "might have been annoying had not a homely English stranger",   # Frances Power Cobbe
    "The hounds were now very little behind",                        # Fielding, Joseph Andrews
    "of being at school with Bardolph",                              # Thackeray
    "Your Molly has never been false",                               # song, Wapping Old Stairs
    "My duty to my neighbor is",                                     # Church Catechism
)


def clean_england(vocab: Vocab, log: list[list], stats: dict) -> list[str]:
    path = RAW / "prose/englandwithoutwi01whit.djvu.txt"
    lines = read_lines(path)
    toc_end = find_line(lines, r"^ENGLAND,\s+WITHOUT\s+AND\s+WITHIN\.\s*$")
    first = find_line(lines, r"^CHAPTER\s+I\.", toc_end)
    last = find_line(lines, r"^THE\s+E\w+D\s*$", first) - 1
    assert (first, last) == (441, 23997), (first, last)
    stats["england_range"] = [first, last]
    stats["england_raw_words"] = sum(n_words(lines[i - 1]) for i in range(first, last + 1))
    joiner = Joiner(vocab, join_unhyphenated=False)
    paras = prose_paragraphs(lines, first, last, small_type=58, verse_max=40,
                             head_words=("england, without", "without and within"),
                             joiner=joiner, log=log, work="england")
    stats["england_join"] = dict(joiner.stats)
    stats["england_words_before_quote_removal"] = sum(n_words(p) for p in paras)
    return paras


# ----------------------------------------------------------------------------------------
def write(name: str, paras: list[str]) -> int:
    path = OUT / name
    path.write_text("\n\n".join(paras) + "\n", encoding="utf-8")
    return sum(n_words(p) for p in paras)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_files = [RAW / "scripture/newgospelofpeac00whit.djvu.txt",
                 RAW / "prose/wordsandthieruses00whitrich.djvu.txt",
                 RAW / "prose/englandwithoutwi01whit.djvu.txt"]
    vocab = Vocab(raw_files)
    log: list[list] = []
    qlog: list[list] = []
    stats: dict = {}

    scripture = clean_scripture(vocab, log, stats)
    wtu = clean_wtu(vocab, log, stats)
    # Words and Their Uses: remove quoted examples longer than one sentence (or 40 words)
    wtu = remove_quotes(wtu, max_words=40, max_sentences=1, work="wtu", log=qlog,
                        drop_quoted_paragraphs=True)
    england = clean_england(vocab, log, stats)
    # England: of the in-text quotations longer than a few lines (> 60 words), most are
    # White's own letters home or conversations he reports (his writing: kept). Those
    # by other writers were identified by reading every candidate and are cut here.
    england = remove_quotes(england, max_words=60, max_sentences=99, work="england", log=qlog,
                            only_prefixes=ENGLAND_QUOTES_BY_OTHERS)

    stats["words"] = {
        "scripture__new_gospel_of_peace.txt": write("scripture__new_gospel_of_peace.txt", scripture),
        "prose__words_and_their_uses.txt": write("prose__words_and_their_uses.txt", wtu),
        "prose__england_without_and_within.txt": write("prose__england_without_and_within.txt", england),
    }
    stats["quotes_removed"] = {
        w: {"spans": sum(1 for r in qlog if r[0] == w), "words": sum(r[1] for r in qlog if r[0] == w)}
        for w in ("wtu", "england")}
    removed = collections.Counter()
    for work, ln, kind, t in log:
        if not kind.endswith("_KEPT"):          # *_KEPT rows are kept text, logged for audit
            removed[f"{work}:{kind}"] += n_words(t)
    stats["removed_words_by_rule"] = dict(sorted(removed.items()))
    # long-s check: count of typical long-s misreadings in the outputs
    allt = " ".join(scripture + wtu + england).lower()
    stats["long_s_check"] = {w: len(re.findall(rf"\b{w}\b", allt))
                             for w in ("fuch", "himfelf", "faid", "firft", "fome", "alfo")}

    with open(OUT / "removed_quotations.tsv", "w", encoding="utf-8") as fh:
        fh.write("work\twords\tsentences\tspan_start\tpreceding_text\n")
        for r in qlog:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    with open(OUT / "removed_lines.tsv", "w", encoding="utf-8") as fh:
        fh.write("work\tline\trule\ttext\n")
        for r in log:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    json.dump(stats["words"], sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
