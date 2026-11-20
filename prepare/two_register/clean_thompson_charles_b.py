#!/usr/bin/env python3
"""Clean the two-register texts of Charles B. Thompson ("Baneemy") for the stylometry study.

Follows prepare/two_register/CLEANING_PROTOCOL.md.

Inputs (never modified):
  data/raw/two_register_authors/thompson_charles_b/scripture/lawscovenantsofi00thom.djvu.txt
      The Laws and Covenants of Israel ... also Ephraim and Baneemy's Proclamations (Preparation, Iowa, 1857)
  data/raw/two_register_authors/thompson_charles_b/prose/evidencesinproof00thom_0.djvu.txt
      Evidences in Proof of the Book of Mormon (Batavia, N.Y., 1841)
  data/raw/lds_scriptures_json/*.json  (KJV, Book of Mormon, D&C, PGP: reference text used only to detect
      quotations in the 1841 book)
  prepare/vocabulary.parquet  (corpus vocabulary, used for the long-s check and OCR-debris tests)

Outputs (data/prepared/two_register/thompson_charles_b/):
  scripture__laws_covenants.txt    Part Second of the 1857 book: the revelations, the Faith of Israel, the
                                   Blessing of Jacob, the 1845 vision, the codes and petitions (ch. V-XXX
                                   plus the appendix revelation)
  scripture__proclamations.txt     Part First of the 1857 book: Ephraim's and Baneemy's proclamations (ch. I-IV),
                                   Thompson's own words in an oratorical prophetic register (kept apart so that
                                   it can be used or left out)
  prose__evidences.txt             Evidences in Proof of the Book of Mormon, with block quotations removed
  CLEANING.md is written by hand from the statistics this script prints (run with --report).

Run:  python prepare/two_register/clean_thompson_charles_b.py [--report]
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import vocabulary  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
RAW = os.path.join(ROOT, 'data', 'raw', 'two_register_authors', 'thompson_charles_b')
SCRIPTURE_RAW = os.path.join(RAW, 'scripture', 'lawscovenantsofi00thom.djvu.txt')
PROSE_RAW = os.path.join(RAW, 'prose', 'evidencesinproof00thom_0.djvu.txt')
REF_JSON = os.path.join(ROOT, 'data', 'raw', 'lds_scriptures_json')
OUT = os.path.join(ROOT, 'data', 'prepared', 'two_register', 'thompson_charles_b')

REPORT = '--report' in sys.argv
QUOTE_MIN_WORDS = 20      # a quoted passage longer than this (about 2.5 printed lines) is removed
SCRIPTURE_NGRAM = 5       # n-gram length used to find verbatim scripture
SCRIPTURE_GAP = 5         # OCR errors: gaps of up to this many tokens inside a match are bridged
UNMARKED_MIN_WORDS = 30   # an unmarked verbatim scripture run this long next to a stray quotation mark is a quotation
UNMARKED_LONG_WORDS = 60  # an unmarked verbatim scripture run this long is a quotation even with no mark nearby


def log(*a):
    if REPORT:
        print(*a)


def load_lines(path):
    with open(path, encoding='utf-8') as fh:
        return [None] + fh.read().split('\n')   # 1-based


def load_vocab():
    return set(vocabulary.words())


VOCAB = load_vocab()


def wc(text):
    return len(text.split())


# ---------------------------------------------------------------------------------------------------------
# Generic line handling
# ---------------------------------------------------------------------------------------------------------

def letter_share(s):
    s2 = re.sub(r'\s', '', s)
    if not s2:
        return 0.0
    return sum(ch.isalpha() for ch in s2) / len(s2)


def is_debris(s):
    """OCR debris: a line that is mostly non-letters, or a very short line with no real word in it."""
    t = s.strip()
    if not t:
        return True
    if letter_share(t) < 0.5:
        return True
    words = re.findall(r"[A-Za-z]+", t)
    real = [w for w in words if len(w) > 1 and w.lower() in VOCAB]
    if len(words) <= 3 and not real:
        return True
    return False


def apply_cuts(lines, cuts):
    """cuts: list of (start_line, start_text_or_None, end_line, end_text_or_None, reason).
    Removes text from the first occurrence of start_text in start_line (whole line if None) through the end
    of the first occurrence of end_text in end_line (whole line if None).  Returns a dict line->text."""
    keep = {i: lines[i] for i in range(1, len(lines))}
    removed = []
    for (a, sa, b, sb, why) in cuts:
        gone = []
        for i in range(a, b + 1):
            t = keep.get(i)
            if t is None:
                continue
            lo, hi = 0, len(t)
            if i == a and sa is not None:
                k = t.find(sa)
                assert k >= 0, (a, sa, t)
                lo = k
            if i == b and sb is not None:
                k = t.find(sb, lo if i == a else 0)
                assert k >= 0, (b, sb, t)
                hi = k + len(sb)
            gone.append(t[lo:hi])
            rest = (t[:lo] + ' ' + t[hi:]).strip() if (lo > 0 or hi < len(t)) else ''
            keep[i] = rest if rest else None
        removed.append((a, b, why, ' '.join(gone)))
    return keep, removed


def join_lines(items, para_break):
    """items: list of (line_no, text).  Joins wrapped lines and end-of-line hyphenation; para_break(prev, cur)
    says whether a paragraph ends after prev.  Returns text with paragraphs separated by blank lines."""
    paras, cur = [], ''
    prev = None
    for ln, t in items:
        t = re.sub(r'\s+', ' ', t).strip()
        if not t:
            continue
        if prev is not None and para_break(prev, (ln, t)):
            paras.append(cur)
            cur = ''
        if not cur:
            cur = t
        elif re.search(r'[A-Za-z][¬\-]$', cur) and not cur.endswith('--'):
            cur = cur[:-1] + t
        else:
            cur = cur + ' ' + t
        prev = (ln, t)
    if cur:
        paras.append(cur)
    out = []
    for p in paras:
        p = p.replace('¬', '')
        p = re.sub(r'\s+([,;:.!?])', r'\1', p)
        p = re.sub(r'\s{2,}', ' ', p).strip()
        if p:
            out.append(p)
    return '\n\n'.join(out) + '\n'


# ---------------------------------------------------------------------------------------------------------
# Scripture side: The Laws and Covenants of Israel (1857)
# ---------------------------------------------------------------------------------------------------------

# Running heads such as "Ch. 30 LAW AND COVENANTS. 183", "16 PROCLAMATIONS, Oh. ™", "194 APPENDIX."
RUNHEAD_1857 = re.compile(
    r'(L\s*a\s*w\s*a?\s*n\s*d\s*c\s*o\s*v|L?aw\s+a\w[dp]\.?\s+c\w?o\w*|LAW\s+AND|PROCLAMATIO|^\W*\d*\s*APPENDIX\W*$)',
    re.I)

# Section marks "§ 359." and their OCR variants ("6 212.", "$804.", "0 609.", "9 377.", "ae S 5.", "O1.")
SECTION_MARK = re.compile(
    r'^[\W_]*(?:[A-Za-z]{1,3}\s+)?(?:[§$¢S69O0]\s?[\'"“‘.,-]?\s?\d{1,3}\s?[.,:;]{0,2}|\d{3,4}\s?[.,:;]{0,2}|\d{1,2}\s?[.,])'
    r'\s?(?=[A-Za-z“‘"\'(_*])')
SECTION_MARK_MID = re.compile(r'(?:(?<=\s)|^)(?:[§$]\s?\d{1,3}\s?[.,]?|(?:[A-Z]{1,2}\s)?\d{3}\.)\s(?=[A-Z“‘])')

# Part First (proclamations, ch. I-IV), lines 298-2177.  Each tuple: start, start-text, end, end-text, reason.
PROCLAMATION_RANGE = (298, 2177)
PROCLAMATION_CUTS = [
    (298, None, 315, None, 'part title, chapter I heading, superscription of Ephraim\'s proclamation'),
    (316, None, 351, 'Jer. xxxi.', '§1-5: Jeremiah 31:10-20 quoted verbatim (block quotation)'),
    (717, 'th |', 717, None, 'OCR debris'),
    (721, None, 744, None, 'signature "(Signed,) EPHRAIM, First-born of the Restitution of Israel", running head, '
                          'chapter II heading, superscription and salutation of Baneemy\'s 1st proclamation'),
    (763, '[See', 766, '426.]', 'bracketed citation of D&C and Times and Seasons'),
    (808, None, 832, 'mouth.”', '§35-37: Revelation 12:14-16 quoted (block quotation; Thompson\'s glosses in '
                                'parentheses inside it go with it)'),
    (902, None, 925, None, '§45: quotation from the Epistle of the Twelve, 23 Dec 1847 (another writer)'),
    (1084, '“‘we', 1090, 'ourselves.”', '§65: Isaiah 28:15 quoted (block quotation)'),
    (1241, None, 1268, None, 'place and date, chapter III heading, superscription and salutation of the 2nd proclamation'),
    (1861, None, 1883, None, 'signature, attestation, place and date, chapter IV heading, superscription and '
                            'salutation of the Chief Teacher\'s proclamation'),
    (2172, None, 2177, None, 'signature, office and date'),
]

# Part Second (law and covenants, ch. V-XXX, appendix revelation): lines 2178-8282.
LAWS_RANGE = (2178, 8282)
LAWS_CUTS = [
    (2178, None, 2215, None, 'erratum, editorial note on the word "law", part title, chapter V heading'),
    (2398, None, 2403, None, 'chapter VI heading'),
    (2404, None, 2446, None, '§201-205: Genesis 32:24-29 quoted (block quotation; the blessing that follows is Thompson\'s)'),
    (2519, '* end', 2532, None, '§213: Genesis 32:30 quoted; chapter VII heading'),
    (2704, None, 2707, None, 'OCR debris'),
    (3251, None, 3270, None, 'signature, place and date of the vision; chapter VIII heading, code title, title heading'),
    (3277, None, 3277, None, 'title heading'), (3288, None, 3288, None, 'title heading'),
    (3291, None, 3291, None, 'title heading'), (3295, None, 3295, None, 'title heading'),
    (3302, None, 3302, None, 'title heading'), (3309, None, 3309, None, 'title heading'),
    (3415, None, 3418, None, 'part and title headings'), (3428, None, 3428, None, 'title heading'),
    (3433, None, 3433, None, 'title heading'), (3438, None, 3441, None, 'part and title headings'),
    (3458, None, 3458, None, 'title heading'), (3480, None, 3480, None, 'title heading'),
    (3544, None, 3554, None, 'chapter IX heading and headnote to the petitions (OCR damaged), "First Petition"'),
    (3572, None, 3572, None, '"ANSWER." heading'),
    (3697, None, 3697, None, '"Second Petition" heading'), (3705, None, 3705, None, '"ANSWER." heading'),
    (3846, None, 3851, None, 'chapter X heading and headnote'),
    (3913, None, 3921, None, 'chapter XI heading and headnote'),
    (3922, None, 3922, '6.', 'section number'),
    (3963, None, 3973, None, 'chapter XII heading and headnote'),
    (4017, None, 4030, None, 'chapter XIII heading and headnote'),
    (4092, None, 4101, None, 'chapter XIV heading and headnote'),
    (4123, None, 4139, None, 'chapter XV heading and headnote'),
    (4164, None, 4171, None, 'chapter XVI heading and headnote'),
    (4223, None, 4233, None, 'chapter XVII heading and headnote'),
    (4462, None, 4475, None, 'signature, date, attestation by C. B. Thompson'),
    (4478, None, 4500, None, 'chapter XVIII heading and headnote'),
    (5359, None, 5371, None, 'chapter XIX heading and headnote'),
    (5520, None, 5524, None, 'heading of the First Covenant'),
    (5562, None, 5574, None, 'heading of the Second Covenant'),
    (5590, None, 5598, None, 'heading of the Third Covenant'),
    (5624, None, 5631, None, 'heading of the Fourth Covenant'),
    (5670, None, 5679, None, 'heading of the Fifth Covenant'),
    (5716, None, 5723, None, 'heading of the Sixth Covenant'),
    (5780, None, 5784, None, 'heading of the Seventh Covenant'),
    (5842, None, 5853, None, 'heading of the Eighth Covenant'),
    (5897, None, 5905, None, 'heading of the Ninth Covenant'),
    (5958, None, 5965, None, 'heading of the Tenth Covenant'),
    (6019, None, 6024, None, 'chapter XX heading and headnote'),
    (6279, None, 6284, None, 'chapter XXI heading and headnote'),
    (6472, None, 6480, None, 'chapter XXII heading and headnote'),
    (6506, None, 6517, None, 'chapter XXIII heading, title and headnote'),
    (6554, None, 6562, None, 'revelation heading, title and headnote'),
    (6611, None, 6624, None, 'chapter XXIV heading, title and headnote'),
    (6664, None, 6671, None, 'revelation heading, title and headnote'),
    (6725, None, 6730, None, 'chapter XXV heading and headnote'),
    (6909, None, 6915, None, 'chapter XXVI heading and headnote'),
    (7037, None, 7091, None, 'chapter XXVII: the Noachide commandments (traditional, not Thompson\'s) and the bare '
                            'list of the seven ordinances'),
    (7094, None, 7100, None, 'chapter XXVIII heading and title'),
    (7370, None, 7377, None, 'chapter XXX heading, title and headnote'),
    (8159, None, 8214, None, 'errata; appendix heading, title and headnote of the appendix revelation'),
    (8240, None, 8243, None, 'OCR debris'),
    (8272, None, 8282, None, 'end of appendix revelation: OCR fragments of a damaged page foot'),
]


def strip_trailing_noise(t):
    """Marginal OCR noise after the end of a sentence: 'blessed forever. gee Ss' -> 'blessed forever.'"""
    m = re.search(r'^(.*[.;:!?)”’])\s+((?:\S+\s*){1,3})$', t)
    if m and not re.search(r'[A-Za-z][¬-]$', t):
        tail = m.group(2).split()
        if all(len(re.sub(r'[^A-Za-z]', '', w)) <= 3 or re.sub(r'[^a-z]', '', w.lower()) not in VOCAB
               for w in tail) and not any(w.lower().strip('.,;:') in ('i', 'o', 'and', 'the', 'for', 'but', 'a')
                                          and len(tail) == 1 for w in tail):
            return m.group(1)
    return t


def clean_1857_lines(keep, a, b):
    """Apply line rules to the 1857 text: running heads, section marks, OCR debris."""
    items, stats = [], Counter()
    for i in range(a, b + 1):
        t = keep.get(i)
        if t is None or not t.strip():
            continue
        if RUNHEAD_1857.search(t) and len(t.split()) <= 7:
            stats['running heads'] += 1
            continue
        t2, n = SECTION_MARK.subn('', t, count=1)
        if n:
            stats['section numbers'] += 1
            t = t2
        t, n = SECTION_MARK_MID.subn(' ', t)
        stats['section numbers'] += n
        t, n = re.subn(r'(?<=[.;:,!?)]\s)(?:\S{1,3}\s)?\d{3,4}[.,]+\s(?=[A-Z])', '', t)
        stats['section numbers'] += n
        # leading and trailing OCR specks (marginal noise, stray rules) but not line-end hyphens
        t = re.sub(r'^[\s_\-~|.,\'"`»«*•<>\\/{}\[\]:;©®™]+(?=[A-Za-z“‘(])', '', t)
        t = re.sub(r'(?<=[A-Za-z.,;:!?)”’])\s+[^A-Za-z\s]{1,3}\s*$', '', t)
        t = re.sub(r'\s+[~|_•©]+\s*$', '', t)
        t = strip_trailing_noise(t)
        if is_debris(t):
            stats['debris lines'] += 1
            continue
        items.append((i, t))
    return items, stats


def para_break_1857(prev, cur):
    # paragraphs = numbered sections; a new section begins where the raw line carried a section mark
    return cur[0] in SECTION_START_LINES


SECTION_START_LINES = set()


def scripture_side():
    lines = load_lines(SCRIPTURE_RAW)
    SECTION_START_LINES.clear()
    for i in range(1, len(lines)):
        if SECTION_MARK.match(lines[i]) or re.match(r'^\W*[§$]', lines[i]):
            SECTION_START_LINES.add(i)
    results = []
    for name, (a, b), cuts, label in (
            ('scripture__laws_covenants.txt', LAWS_RANGE, LAWS_CUTS, 'Part Second: law, covenants and revelations'),
            ('scripture__proclamations.txt', PROCLAMATION_RANGE, PROCLAMATION_CUTS, 'Part First: proclamations')):
        raw_words = sum(wc(lines[i]) for i in range(a, b + 1))
        keep, removed = apply_cuts(lines, cuts)
        items, stats = clean_1857_lines(keep, a, b)
        text = join_lines(items, para_break_1857)
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as fh:
            fh.write(text)
        cut_words = sum(wc(r[3]) for r in removed)
        results.append((name, a, b, raw_words, cut_words, stats, wc(text)))
        print(f'{name}: lines {a}-{b}, raw words {raw_words}, removed by cuts {cut_words}, '
              f'{dict(stats)}, words out {wc(text)}')
        for r in removed:
            log(f'   cut {r[0]}-{r[1]} ({wc(r[3])} w) {r[2]}: {r[3][:110]!r}')
    return results


# ---------------------------------------------------------------------------------------------------------
# Prose side: Evidences in Proof of the Book of Mormon (1841)
# ---------------------------------------------------------------------------------------------------------

PROSE_RANGES = [
    (130, 223, 'Preface (by Thompson, "the writer")'),
    (244, 9013, 'Body: Part 1 (evidences), Part 2 (objections answered), Appendix prose proclamation'),
    (9407, 9462, 'Appendix No. 3: Thompson\'s introduction to the American antiquities'),
]
PROSE_EXCLUDED_NOTE = [
    (1, 129, 'Library stamp, title page, copyright notice'),
    (224, 243, 'OCR debris, half-title'),
    (9014, 9404, 'Verse: the closing poem of the Proclamation and the two Acrostics, with their scripture-reference footnotes'),
    (9463, 10022, 'Description of the ruins of Copan etc. "copied from the Albany Weekly Journal" (Stephens), with Thompson\'s footnotes'),
    (10023, 10037, 'Errata'),
]

RUNHEAD_1841 = re.compile(
    r'^\W*(\S{1,5}\s+)?('
    r'(MORE\s+)?EVIDENCES\s+I\S\s+\S{2,7}(\s+\S{2,4})?\s+OF(\s+T\S{0,4})?(\s+BOOK\s+OF)?'
    r'|MORMON\.?'
    r'|EVIDENCES\s+IN\s+PROOF'
    r'|OF\s+THE\s+BOOK\s+OF\s+MORMON,?\s*&c.*'
    r'|.?[RB]OOK\s+O[FP]\s+.?ORMO.{0,3}'
    r'|OBJECTION.{0,3}\s+ANSWERED'
    r'|AND\s+REFUTED.?'
    r'|A\s+PROCLAMATION.{0,3}'
    r'|AND\s+WA\S{3,7}'
    r'|AMERICAN(\s+ANTIQUITIES)?.?'
    r'|ANTIQUITIES.{0,2}'
    r'|PREFACE.?'
    r'|APPENDIX.{0,8}'
    r'|PART\s+SECOND.?'
    r')\W*(\d+)?\W*$', re.I)

# Quotations of other writers (and a few scripture passages with interleaved glosses) whose quotation marks
# the OCR lost or garbled, so that the automatic rule below cannot delimit them.  Found by reviewing every
# unclosed quotation the parser reports (run with --report).  Same format as the 1857 cuts.
PROSE_CUTS = [
    (407, '“They', 418, '*7', '2 Esdras 13:41-47 (Apocrypha), quotation'),
    (1236, '“Their', 1254, 'leges.', 'Elias Boudinot (A Star in the West), quotation'),
    (1264, '“Can', 1275, 'sign.', 'Elias Boudinot, quotation'),
    (1381, '4 ‘Drop', 1389, 'it.”J', 'Isaiah 45:8 quoted with Thompson\'s glosses interleaved'),
    (1583, '“For', 1591, "brethren.'5", 'Deuteronomy 33:16 quoted with a gloss'),
    (3841, '“Near', 3859, "defence/'", 'Josiah Priest, American Antiquities p. 165, quotation'),
    (4389, 'A  voice', 4639, "Barnett.' ?", 'Circular of the Jews of Jerusalem as printed in the Morning Herald, '
                                            'with the editor\'s note and the Bethdin certificate (other writers)'),
    (4870, '“We', 4988, 'truth  A', 'Book of Enoch (tr. Laurence), long extract'),
    (6441, '“a', 6462, 'co."', 'E. D. Howe, Mormonism Unvailed p. 287, quotation'),
    (6593, None, 6711, None, 'Quincy Whig article, with the letter of John Haven and the certificate of A. Badlam'),
    (6867, '“For', 7056, 'Pratt.', 'Parley P. Pratt, testimony copied from his pamphlet'),
    (8811, None, 8828, None, 'quoted poem ("Great spirit of our Fathers")'),
]


def norm_tok(w):
    w = w.lower().replace('¬', '')
    if w in ('1', 'l'):
        return 'i'
    return re.sub(r'[^a-z]', '', w)


def ref_ngrams(n):
    grams = set()
    for fn in ('old-testament.json', 'new-testament.json', 'book-of-mormon.json',
               'doctrine-and-covenants.json', 'pearl-of-great-price.json'):
        with open(os.path.join(REF_JSON, fn), encoding='utf-8') as fh:
            d = json.load(fh)
        for b in d['books'] if 'books' in d else []:
            for c in b['chapters']:
                toks = []
                for v in c['verses']:
                    toks += [norm_tok(w) for w in v['text'].split()]
                toks = [t for t in toks if t]
                for i in range(len(toks) - n + 1):
                    grams.add(tuple(toks[i:i + n]))
        if 'sections' in d:
            for s in d['sections']:
                toks = []
                for v in s['verses']:
                    toks += [norm_tok(w) for w in v['text'].split()]
                toks = [t for t in toks if t]
                for i in range(len(toks) - n + 1):
                    grams.add(tuple(toks[i:i + n]))
    return grams


OPEN_RE = re.compile(r'^[\[—\-]*(“|"|‘‘|\'\'|„)')   # '("' is the OCR of a bare parenthesis
CLOSE_RE = re.compile(r'(”|"|’’|\'\'|[.,;:!?](77|\?\?|\*7|/\*|/7|7\?|\?7|’7)|\?\?)[\W\d]*$')


def prose_lines(lines):
    """Body lines of the 1841 book after removing page furniture and debris: list of (line_no, text)."""
    items, stats = [], Counter()
    for a, b, _ in PROSE_RANGES:
        for i in range(a, b + 1):
            t = lines[i]
            if t is None or not t.strip():
                continue
            t = re.sub(r'\s+', ' ', t).strip()
            if RUNHEAD_1841.match(t):
                stats['running heads'] += 1
                continue
            if re.fullmatch(r'[\W\dIiltOo]{1,5}', t):
                stats['page numbers / specks'] += 1
                continue
            if is_debris(t):
                stats['debris lines'] += 1
                continue
            items.append((i, t))
    return items, stats


def tokenize(items):
    """Token stream over the kept lines; words split across a line end by a hyphen are joined."""
    toks, tline = [], []
    carry = None
    for ln, t in items:
        ws = t.split()
        if carry is not None and ws:
            ws[0] = carry + ws[0]
            carry = None
        if ws and re.search(r'[A-Za-z][¬\-]$', ws[-1]) and not ws[-1].endswith('--'):
            carry = ws.pop()[:-1]
        for w in ws:
            toks.append(w.replace('¬', ''))
            tline.append(ln)
    if carry:
        toks.append(carry)
        tline.append(items[-1][0])
    return toks, tline


def find_quote_spans(toks):
    """Spans [i, j] (inclusive) opened by a double quotation mark and closed by the next closing mark."""
    def is_open(k):
        w = toks[k]
        if OPEN_RE.match(w):
            return True
        if re.fullmatch(r'[46]{1,2}', w) and k + 1 < len(toks) and re.match(r"^[‘']", toks[k + 1]):
            return True
        return False

    def is_close(k, start):
        w = toks[k]
        if k == start:
            w = OPEN_RE.sub('', w, count=1)
            if not w:
                return False
        return bool(CLOSE_RE.search(w)) or w in ('”', '"')

    spans, anomalies = [], []
    k = 0
    n = len(toks)
    while k < n:
        if is_open(k):
            j = k
            found = None
            while j < n:
                if j > k + 1 and is_open(j) and toks[j] not in ('"',):
                    break
                if is_close(j, k):
                    found = j
                    break
                j += 1
            if found is None:
                anomalies.append((k, j - 1))
                k += 1
                continue
            spans.append((k, found))
            k = found + 1
        else:
            k += 1
    return spans, anomalies


def scripture_cover(toks):
    grams = ref_ngrams(SCRIPTURE_NGRAM)
    nt = [norm_tok(w) for w in toks]
    idx = [k for k, w in enumerate(nt) if w]
    cov = [False] * len(toks)
    for a in range(len(idx) - SCRIPTURE_NGRAM + 1):
        g = tuple(nt[idx[a + m]] for m in range(SCRIPTURE_NGRAM))
        if g in grams:
            for m in range(SCRIPTURE_NGRAM):
                cov[idx[a + m]] = True
    raw = list(cov)
    # bridge short gaps left by OCR errors and small variants
    last = None
    for k in range(len(cov)):
        if cov[k]:
            if last is not None and 1 < k - last <= SCRIPTURE_GAP + 1:
                for m in range(last + 1, k):
                    cov[m] = True
            last = k
    runs, k = [], 0
    while k < len(cov):
        if cov[k]:
            j = k
            while j + 1 < len(cov) and cov[j + 1]:
                j += 1
            runs.append((k, j))
            k = j + 1
        else:
            k += 1
    return cov, raw, runs


def extend_by_scripture(cov, i, limit, max_gap=12):
    """From an opening quotation mark at i, follow verbatim scripture forward (bridging gaps of up to max_gap
    tokens, e.g. glosses or OCR damage) but not beyond limit.  Returns the last covered index or None."""
    k = i
    while k <= min(i + 3, limit) and not cov[k]:
        k += 1
    if k > limit or not cov[k]:
        return None
    last, gap = k, 0
    while k <= limit:
        if cov[k]:
            last, gap = k, 0
        else:
            gap += 1
            if gap > max_gap:
                break
        k += 1
    return last


def para_break_1841(prev, cur, width):
    pl, pt = prev
    return len(pt) < 0.72 * width and bool(re.search(r'[.!?:”"\'’)\]—\-*/7]\W*$', pt))


def prose_side():
    lines = load_lines(PROSE_RAW)
    raw_words = sum(wc(lines[i]) for a, b, _ in PROSE_RANGES for i in range(a, b + 1) if lines[i])
    keep, manual = apply_cuts(lines, PROSE_CUTS)
    lines2 = [None] + [keep.get(i) for i in range(1, len(lines))]
    items, stats = prose_lines(lines2)
    toks, tline = tokenize(items)
    spans, anomalies = find_quote_spans(toks)
    cov, rawcov, runs = scripture_cover(toks)
    remove = [False] * len(toks)
    why = [None] * len(toks)
    decided = []
    for (i, j) in spans:
        n = j - i + 1
        if n > QUOTE_MIN_WORDS:
            decided.append((i, j, 'marked'))
    for (i, j) in anomalies:
        e = extend_by_scripture(rawcov, i, j)
        if e is not None and e - i + 1 > QUOTE_MIN_WORDS:
            decided.append((i, e, 'unclosed+scripture'))
        else:
            log(f'  UNRESOLVED {tline[i]}-{tline[j]} {" ".join(toks[i:i+12])}')
    for (i, j, kind) in decided:
        for k in range(i, j + 1):
            remove[k] = True
            why[k] = kind
    for (i, j) in runs:
        n = j - i + 1
        if n < UNMARKED_MIN_WORDS:
            continue
        free = [k for k in range(i, j + 1) if not remove[k]]
        if len(free) < UNMARKED_MIN_WORDS:
            continue
        if sum(rawcov[k] for k in free) / len(free) < 0.8:
            log(f'  KEEP[weak unmarked] {tline[free[0]]}-{tline[free[-1]]} n={len(free)} '
                f'{" ".join(toks[free[0]:free[0]+8])} ... {" ".join(toks[free[-1]-5:free[-1]+1])}')
            continue
        near_mark = any(OPEN_RE.match(toks[k]) for k in range(max(free[0] - 7, 0), free[0] + 1)) or \
            any(CLOSE_RE.search(toks[k]) for k in range(free[-1], min(free[-1] + 7, len(toks))))
        if len(free) < UNMARKED_LONG_WORDS and not near_mark:
            log(f'  KEEP[woven unmarked] {tline[free[0]]}-{tline[free[-1]]} n={len(free)} '
                f'{" ".join(toks[free[0]:free[0]+8])} ... {" ".join(toks[free[-1]-5:free[-1]+1])}')
            continue
        # extend back to an opening mark / forward to a closing mark close by
        a, b = free[0], free[-1]
        for k in range(a - 1, max(a - 7, -1), -1):
            if OPEN_RE.match(toks[k]):
                a = k
                break
        for k in range(b + 1, min(b + 7, len(toks))):
            if CLOSE_RE.search(toks[k]):
                b = k
                break
        decided.append((a, b, 'unmarked scripture'))
        for k in range(a, b + 1):
            if not remove[k]:
                remove[k] = True
                why[k] = 'unmarked scripture'
    decided.sort()
    if REPORT:
        for (i, j, kind) in decided:
            n = j - i + 1
            sc = sum(cov[i:j + 1]) / n
            log(f'  RM[{kind}] {tline[i]}-{tline[j]} n={n} scr={sc:.2f}  {" ".join(toks[i:i+8])} ... '
                f'{" ".join(toks[max(i, j-5):j+1])}')
    # rebuild kept lines from tokens (hyphen-joined words stay with the line where they started)
    by_line = {}
    for k, w in enumerate(toks):
        if not remove[k]:
            by_line.setdefault(tline[k], []).append(w)
    kept_items = []
    for ln, t in items:
        if ln in by_line:
            kept_items.append((ln, ' '.join(by_line[ln])))
        else:
            kept_items.append((ln, ''))
    width = sorted(len(t) for _, t in items)[len(items) // 2]
    # paragraph structure from the original line lengths; removed quotations leave a paragraph break
    orig = dict(items)
    paras, cur, prev_ln = [], [], None
    for ln, t in kept_items:
        if prev_ln is not None and para_break_1841((prev_ln, orig[prev_ln]), (ln, orig[ln]), width):
            if cur:
                paras.append(' '.join(cur))
            cur = []
        if t:
            cur.append(t)
        elif cur:
            paras.append(' '.join(cur))
            cur = []
        prev_ln = ln
    if cur:
        paras.append(' '.join(cur))
    out = []
    for p in paras:
        p = re.sub(r'\(\s*See\s[^()]{0,90}?\)', ' ', p)          # bare "(See ... chapt. ... verse.)" references
        p = re.sub(r'\s+([,;:.!?])', r'\1', p)
        p = re.sub(r'\s{2,}', ' ', p).strip()
        if len(p.split()) >= 3 and re.search(r'[A-Za-z]{2,}', p):   # shorter = tails of removed quotations
            out.append(p)
    text = '\n\n'.join(out) + '\n'
    with open(os.path.join(OUT, 'prose__evidences.txt'), 'w', encoding='utf-8') as fh:
        fh.write(text)
    body_tokens = len(toks)
    rm_tokens = sum(remove)
    manual_words = sum(wc(r[3]) for r in manual)
    kinds = Counter(why[k] for k in range(len(toks)) if remove[k])
    print(f'prose__evidences.txt: raw words in ranges {raw_words}; furniture {dict(stats)}; '
          f'manual quotation cuts {manual_words} words; tokens after furniture {body_tokens}; '
          f'auto-removed quotation tokens {rm_tokens} {dict(kinds)}; words out {wc(text)}')
    for r in manual:
        log(f'   cut {r[0]}-{r[1]} ({wc(r[3])} w) {r[2]}: {r[3][:100]!r}')
    return dict(raw=raw_words, manual=manual_words, auto=rm_tokens, kinds=kinds, out=wc(text),
                body=body_tokens + manual_words)


def long_s_check(name):
    """Protocol check for long-s misreadings ('fuch' for 'such'): count words that are not in the corpus
    vocabulary but become vocabulary words when an f is read as s.  No repair is applied when this is
    negligible (these are 1841 and 1857 American printings, set without the long s)."""
    words = re.findall(r"[a-z]+", open(os.path.join(OUT, name), encoding='utf-8').read().lower())
    hits = Counter()
    for w in words:
        if 'f' in w and w not in VOCAB:
            for k in [m.start() for m in re.finditer('f', w)]:
                if w[:k] + 's' + w[k + 1:] in VOCAB:
                    hits[w] += 1
                    break
    print(f'long-s check {name}: {sum(hits.values())} candidate tokens of {len(words)}: {hits.most_common(10)}')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not which or 'scripture' in which:
        scripture_side()
    if not which or 'prose' in which:
        prose_side()
        lines = load_lines(PROSE_RAW)
        for a, b, what in PROSE_EXCLUDED_NOTE:
            print(f'excluded 1841 lines {a}-{b} ({sum(wc(lines[i]) for i in range(a, b + 1))} raw words): {what}')
    for name in sorted(os.listdir(OUT)):
        if name.endswith('.txt'):
            long_s_check(name)
