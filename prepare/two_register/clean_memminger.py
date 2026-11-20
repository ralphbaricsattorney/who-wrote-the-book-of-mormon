#!/usr/bin/env python3
"""Clean the two-register texts of Christopher G. Memminger (1803-1888) for the stylometry study.

Follows prepare/two_register/CLEANING_PROTOCOL.md.

Inputs (never modified; all Internet Archive uncorrected OCR, *.djvu.txt):
  data/raw/two_register_authors/memminger/scripture/bookofnullificat00char.djvu.txt
      The Book of Nullification. By a Spectator of the Past. Charleston, 1830 (pseudonymous; attributed).
  data/raw/two_register_authors/memminger/prose/addressofhoncgme00memm.djvu.txt
      Address ... before the assembled authorities of the State of Virginia, 19 Jan 1860 (Richmond, 1860).
  data/raw/two_register_authors/memminger/prose/lecturedelivered00memm.djvu.txt
      Lecture delivered before the Young Men's Library Association of Augusta, April 10th, 1851 (Augusta, 1851).
  data/raw/two_register_authors/memminger/prose/cu31924032767505.djvu.txt      
      H. D. Capers, The Life and Times of C. G. Memminger (Richmond, 1893). Only passages that Capers reprints
      as Memminger's own signed or delivered texts are taken (see SOURCES below); Capers's narrative is not used.
  prepare/vocabulary.parquet  (corpus vocabulary: OCR indicator and long-s check only)

Outputs (data/prepared/two_register/memminger/):
  scripture__book_of_nullification.txt   ten chapters (364 verses), verse numbers and chapter headings removed
  prose__virginia_address_1860.txt       the 1860 address, quoted resolutions, letters, extracts removed
  prose__augusta_lecture_1851.txt        the 1851 lecture on slavery, footnote and long quotations removed
  prose__cooperation_address_1851.txt    Sept. 1851 Charleston Co-operation meeting speech (from Capers)
  prose__bank_letters_1850.txt           two signed newspaper letters on the Bank of the State, 1850 (from Capers)
  prose__bank_argument_1843.txt          argument for the State in State v. Bank of South Carolina, 1843
                                         (from Capers, who took it from the 1844 printed report; legal genre,
                                         case citations retained)
  prose__bible_oration_1842.txt          "An Oration on the Bible", South Carolina College societies, Dec. 1842
                                         (from Capers's appendix)
  prose__college_orations_1817_1819.txt  six student essays/orations, South Carolina College 1817-1819, written at
                                         ages 14-16 (from Capers's appendix; Latin salutatory excluded)
  CLEANING.md is written by hand from the statistics this script prints (run with --report).

Run:  python prepare/two_register/clean_memminger.py [--report] [--show-dropped]
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import vocabulary  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
RAW = os.path.join(ROOT, 'data', 'raw', 'two_register_authors', 'memminger')
OUT = os.path.join(ROOT, 'data', 'prepared', 'two_register', 'memminger')

REPORT = '--report' in sys.argv
SHOW_DROPPED = '--show-dropped' in sys.argv


def log(*a):
    if REPORT:
        print(*a)


def load_lines(rel):
    with open(os.path.join(RAW, rel), encoding='utf-8') as fh:
        return [None] + fh.read().split('\n')   # 1-based


def load_vocab():
    return set(vocabulary.words())


def wc(text):
    return len(text.split())


# ---------------------------------------------------------------------------------------------------------
# Line classification (page furniture and OCR debris)
# ---------------------------------------------------------------------------------------------------------
TRAIL = r"""[.,;:!?'"’”)\]—*-]*"""
WORDLIKE = re.compile(r"""^["'(\[‘“]*([a-z]{2,}|[A-Z][a-z]+|[A-Z]{3,})(-[a-z]+)*""" + TRAIL + "$")
JUNK_TOKEN = re.compile(r"""^["'*■•|^~\\{}<>«»©®¦]*[*■•|^~\\{}<>«»©®¦]["'*■•|^~\\{}<>«»©®¦]*$""")


def is_running_head(s):
    t = s.strip()
    if re.search(r'\bDo[ce]\.\s+No[.,]?\s', t):                       # 1860 address: "Doc. No. 58. 7"
        return True
    if re.search(r'L[I1]FE\s+(AND|ANP)\s+T', t) or re.search(r'TIMES\s+OF\s*\.?\s*C', t):   # Capers verso heads
        return True
    if re.match(r'^APPEN\w*\.?\s+\S{1,4}$', t):                         # Capers "APPENDIX. BOl" (page no. misread)
        return True
    toks = t.split()
    letters = [c for c in t if c.isalpha()]
    if 1 < len(toks) <= 8 and len(letters) >= 5:
        upper = sum(c.isupper() for c in letters) / len(letters)
        if upper >= 0.7 and (re.search(r'\d', toks[-1]) or re.search(r'\d', toks[0])):
            return True                                                 # Capers recto heads, "THE LAWYER. 137"
    return False


def is_debris(s):
    t = s.strip()
    if not t:
        return False
    toks = t.split()
    if not any(WORDLIKE.match(x) for x in toks):
        return True                                                     # page numbers, ornaments, stray letters
    nonspace = sum(not c.isspace() for c in t)
    alnum = sum(c.isalnum() for c in t)
    return alnum / nonspace < 0.6


# ---------------------------------------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------------------------------------
VERSE = re.compile(r"""^[\s•.*'"<;:■]*J?(\d{1,2}|\d[ .]{1,2}\d|\d[SOQIlo]|[SOQIl]\d)\s?[.,]{0,2}-?\s+(?=["'<(A-Z])""")
CHAPTER = re.compile(r'^\s*CHAPTER\s+[IVXLl]+', re.I)


def strip_margin(s):
    """Lecture scan: remove marginal letters/bars that OCR picked up at line starts and ends."""
    s = re.sub(r'^\s*[^\sAaIO\d"\'(]\s{2,}(?=\S)', '', s)               # "j  of the", "!    ranny"
    s = re.sub(r'^\s*[I|]\s{3,}(?=\S)', '', s)                         # "I    began."
    s = re.sub(r'\s{2,}[|!{}\[\]^\'1jit,;:]\s*$', '', s)               # "... preju-  1", "began.  j"
    return s


DROPPED = '<dropped>'   # marker left where a removed block was


def collect(lines, ranges, drop=(), fixes=None, margin=False, stats=None, keep=()):
    """Return list of (lineno, text) kept, with None marking a blank line."""
    dropset = set()
    for a, b in drop:
        dropset.update(range(a, b + 1))
    fixes = fixes or {}
    out = []
    for a, b in ranges:
        for i in range(a, b + 1):
            s = lines[i]
            if i in dropset:
                if s.strip():
                    stats['dropped_range'] += 1
                if out and out[-1][1] != DROPPED:
                    out.append((i, DROPPED))
                continue
            if i in fixes:
                old, new = fixes[i]
                assert re.search(old, s), (i, old, s)
                s = re.sub(old, new, s)
            if margin:
                s = strip_margin(s)
            if not s.strip():
                out.append((i, None))
                continue
            if is_running_head(s):
                stats['running_head'] += 1
                if SHOW_DROPPED:
                    print('  HEAD', i, s)
                continue
            if CHAPTER.match(s):
                stats['chapter_heading'] += 1
                continue
            if is_debris(s) and i not in keep:
                stats['debris'] += 1
                if SHOW_DROPPED:
                    print('  DEBRIS', i, s)
                continue
            out.append((i, s))
        out.append((b, DROPPED))           # separate texts taken from different ranges
    return out


def clean_tokens(s):
    toks = [t for t in s.split() if not JUNK_TOKEN.match(t)]
    return ' '.join(toks)


def join_lines(texts):
    """Join wrapped lines; rejoin words hyphenated across line ends."""
    buf = ''
    for s in texts:
        s = clean_tokens(s)
        if not s:
            continue
        if not buf:
            buf = s
        elif re.search(r'[A-Za-z][-^=]$', buf) and re.match(r'[a-z]', s):   # OCR reads some hyphens as ^ or =
            buf = buf[:-1] + s
        else:
            buf = buf + ' ' + s
    return buf


def paragraphs_prose(kept):
    """Blank line = paragraph break only if the text before it ends a sentence and the next line can begin one
    (page breaks in these scans fall mid-sentence and are also surrounded by blank lines)."""
    paras, cur, pending_break, after_drop = [], [], False, False
    for i, s in kept:
        if s is None or s == DROPPED:
            pending_break = True
            after_drop = after_drop or s == DROPPED
            continue
        if cur and pending_break:
            prev = clean_tokens(cur[-1])
            starts = re.match(r'[\s"\'“(]*[A-Z0-9]', s)
            if starts and (after_drop or re.search(r'[.?!:"\'”)]$', prev)):
                paras.append(join_lines(cur))
                cur = []
        cur.append(s)
        pending_break = after_drop = False
    if cur:
        paras.append(join_lines(cur))
    return paras


def paragraphs_verses(kept, stats):
    """Scripture: one paragraph per verse; verse numbers removed; blank lines ignored."""
    paras, cur = [], []
    for i, s in kept:
        if s is None or s == DROPPED:
            continue
        m = VERSE.match(s)
        if m:
            stats['verse_numbers'] += 1
            if cur:
                paras.append(join_lines(cur))
            cur = [s[m.end():]]
        else:
            cur.append(s)
    if cur:
        paras.append(join_lines(cur))
    return paras


def apply_cuts(paras, cuts, stats):
    out = []
    for p in paras:
        for name, rx in cuts:
            p2, n = re.subn(rx, ' ', p, flags=re.S)
            if n:
                stats['cut:' + name] += wc(p) - wc(p2)
                stats['cuts_applied'] += n
            p = p2
        p = re.sub(r'\s+', ' ', p).strip()
        if p:
            out.append(p)
    return out


# ---------------------------------------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------------------------------------
NULL = 'scripture/bookofnullificat00char.djvu.txt'
VA = 'prose/addressofhoncgme00memm.djvu.txt'
LECT = 'prose/lecturedelivered00memm.djvu.txt'
CAP = 'prose/cu31924032767505.djvu.txt'

SOURCES = [
    dict(
        out='scripture__book_of_nullification.txt', src=NULL, mode='verses',
        # 48 = "CHAPTER I."; 1943 = last line of ch. X v. 66 (the scribe's colophon, in register).
        # Excluded before 48: IA/Duke title leaf, title page, and the pseudonymous author's 9-line prose note
        # ("The style in which the Jewish history is written ...", signed A Spectator of the Past).
        ranges=[(48, 1943)],
    ),
    dict(
        out='prose__virginia_address_1860.txt', src=VA, mode='prose',
        # 121 = first sentence after the salutation; 1884 = last line ("... southern country.").
        # Excluded before 121: Virginia legislature's letter and resolution, Memminger's covering letter,
        # IA boilerplate, heading and salutation.  After 1884: debris.
        ranges=[(121, 1884)],
        drop=[(158, 188),    # South Carolina resolutions read into the record
              (300, 331),    # Virginia resolutions of 1833
              (345, 375),    # extracts of letters by B. W. Leigh and James Hamilton jr, with captions
              (388, 402),    # S.C. convention resolutions of 1833
              (428, 466),    # Virginia resolutions of 1851
              (700, 711),    # Art. 6 of the Ordinance of 1787
              (824, 851),    # Jefferson to John Holmes, 22 April 1820
              (876, 955),    # Calhoun's 1838 Senate speech
              (1032, 1095),  # London Times report of Lords debate (Brougham, Aberdeen)
              (1181, 1221),  # Virginia resolutions of 1847, with caption
              (1237, 1273),  # Clayton's account of the 1848 committee
              (1291, 1314),  # Virginia resolutions of 1849, with caption
              (1337, 1343),  # D.C. slave-trade act of 1850
              (1485, 1493),  # preamble of the Constitution
              (1857, 1870)], # Bryant, "The Antiquity of Freedom" (verse)
        fixes={404: (r'\s+\\\s*$', ' '), 405: (r'\s+J\s*$', ' '), 411: (r'\s+!\s*$', ' '),
               412: (r'\s+~\*\s*$', ' '), 426: (r'\s+l\s*$', ' '), 713: (r'that f\s*$', 'that ')},
               # marginal marks picked up by OCR at line ends
    ),
    dict(
        out='prose__augusta_lecture_1851.txt', src=LECT, mode='prose', margin=True,
        # 136 = first sentence; 1185 = last sentence.  Before 136: LC shelf marks, two title pages, caption
        # "ON THE INSTITUTION OF SLAVERY".  After 1185: LC stamps.
        ranges=[(136, 1185)],
        drop=[(944, 963)],   # author's footnote quoting Bigelow, "Jamaica in 1850"
        fixes={246: (r'^I\s+of', 'of')},   # marginal "I" (the scan's binding edge), not the pronoun
        cuts=[('quote_profound_thinker', r'It is " ?the obligation to labor.*?work upon different principles\."'),
              ('quote_1sam3_eli', r'"Behold,! will do a thing in Israel.*?nor offering forever\."'),
              ('footnote_marker', r'(?<=barbarism\.)\*')],
    ),
    dict(
        out='prose__cooperation_address_1851.txt', src=CAP, mode='prose',
        # Capers pp. 204-222: speech at the Co-operation meeting, Charleston, Sept. 1851.
        ranges=[(9930, 10873)],
        drop=[(9990, 10019),   # 1848 report and resolutions (Joint Committee on Federal Relations)
              (10031, 10124),  # 1849 Senate and House reports and resolutions
              (10153, 10161),  # preamble of the 1850 act
              (10250, 10254),  # House Journal extract
              (10274, 10292)], # footnote (with 1850 resolutions)
        cuts=[('quote_act_1850', r'" ?for the purpose, in the first place, of tak.*?shall suffer no detriment\."'),
              ('quote_journal_p221', r'"Mr\. Harrison moved to reduce.*?etc\.')],
    ),
    dict(
        out='prose__bank_letters_1850.txt', src=CAP, mode='prose',
        # Capers pp. 160-174.  (a) "To the People of South Carolina", Charleston Mercury 8 Mar 1850;
        # (b) summing-up letter "To the People of St. Philip's and St. Michael's Parishes", 1850.
        # Excluded: Capers's framing, Judge Wardlaw's and T. W. Glover's letters (8028-8171), salutations
        # and signatures.
        ranges=[(7800, 8023), (8179, 8585)],
        drop=[(7927, 7930),    # footnote listing committee members
              (7949, 7964)],   # resolution of a member from Richland, 1841
        cuts=[('quote_elmore_1', r'" ?The journals show that he offered the resolution.*?Where will he fly to now \? ?"'),
              ('quote_wardlaw', r'" ?You had no agency in procuring.*?to investigate the bank\."'),
              ('quote_elmore_2', r'" ?On the next day Mr\. Memminger assembled.*?state my views on the bill\."'),
              ('quote_elmore_3', r'" ?The chairman said the committee desired.*?measures it proposed\."'),
              ('quote_elmore_4', r'" ?that this measure taken up in the Committee.*?regarding the bank\.\'\'')],
    ),
    dict(
        out='prose__bank_argument_1843.txt', src=CAP, mode='prose',
        # Capers pp. 136-152: Memminger's argument for the State before the Court of Errors (Columbia, May 1843),
        # as printed in the 1844 report.  The first paragraph is the reporter's indirect speech
        # ("Mr. Memminger ... opened the argument by stating that ..."); the rest is direct argument.
        ranges=[(6575, 7576)],
        keep={6953},         # "512." ends a citation begun on the previous line, not a page number
    ),
    dict(
        out='prose__college_orations_1817_1819.txt', src=CAP, mode='prose',
        # Capers, Appendix pp. 490-515, "College Essays and Orations", from manuscripts lent by Memminger's son:
        # "Love of Country" (c. 1817, sophomore essay), "The Art of Printing" (1818), "Immortality of the Soul"
        # (1819), "Influence of Popular Opinion" (22 Apr 1819), "Eulogy on President Maxey" (1819),
        # "Influence of Fiction upon the Human Mind" (commencement, 6 Dec 1819).  Written at ages 14-16.
        ranges=[(24121, 25358)],
        drop=[(24240, 24241),  # two lines of verse (Shakespeare) inside a sentence
              (24271, 24274),  # title and caption: The Art of Printing
              (24493, 24496),  # title and caption: Immortality of the Soul
              (24647, 24650),  # title and caption: Influence of Popular Opinion
              (24798, 24801),  # title and caption: Eulogy on President Maxey
              (24929, 24932),  # four lines of verse
              (24966, 24966),  # running head "appendix: 507" (lower-case OCR)
              (25084, 25196)], # title, caption and the Latin salutatory of the 1819 commencement
    ),
    dict(
        out='prose__bible_oration_1842.txt', src=CAP, mode='prose',
        # Capers, Appendix pp. 532-548: "An Oration on the Bible" (running head "Sacred and Profane History"),
        # delivered before the Euphradian and Clariosophic Societies, South Carolina College, December 1842.
        ranges=[(26293, 27106)],   # 27107-27111: closing hymn stanza, excluded
        drop=[(26604, 26640),  # Isaiah 13, 44, 45 (KJV) read as a block
              (26904, 26926),  # Deuteronomy 28-29 (KJV) block
              (26997, 27004),  # Pope, Essay on Man, eight lines of verse
              (27085, 27087)], # two lines of a hymn
        cuts=[('quote_ps96', r'"Tell it out among the heathen.*?righteously\."'),
              ('footnote_marker', r'(?<=balance\.)\*')],   # marker without a printed note
    ),
]


def build(src, vocab):
    lines = load_lines(src['src'])
    stats = Counter()
    raw_words = sum(wc(lines[i]) for a, b in src['ranges'] for i in range(a, b + 1))
    kept = collect(lines, src['ranges'], src.get('drop', ()), src.get('fixes'), src.get('margin', False), stats,
                   src.get('keep', ()))
    if src['mode'] == 'verses':
        paras = paragraphs_verses(kept, stats)
    else:
        paras = paragraphs_prose(kept)
    paras = apply_cuts(paras, src.get('cuts', ()), stats)
    text = '\n\n'.join(paras) + '\n'
    # indicators
    toks = re.findall(r"[a-z]+", text.lower())
    in_vocab = sum(t in vocab for t in toks) / max(1, len(toks)) if vocab else float('nan')
    longs = Counter()
    if vocab:
        for t in toks:
            if 'f' in t and t not in vocab:
                for k in range(len(t)):
                    if t[k] == 'f':
                        cand = t[:k] + 's' + t[k + 1:]
                        if cand in vocab:
                            longs[(t, cand)] += 1
                            break
    return text, dict(raw_words=raw_words, words=wc(text), paras=len(paras), vocab_share=in_vocab,
                      longs_candidates=sum(longs.values()), longs_top=longs.most_common(10), stats=stats)


def main():
    os.makedirs(OUT, exist_ok=True)
    vocab = load_vocab()
    totals = Counter()
    for src in SOURCES:
        text, info = build(src, vocab)
        with open(os.path.join(OUT, src['out']), 'w', encoding='utf-8') as fh:
            fh.write(text)
        side = src['out'].split('__')[0]
        totals[side] += info['words']
        print(f"{src['out']}: {info['words']} words ({info['raw_words']} raw in range), "
              f"{info['paras']} paragraphs, vocab share {info['vocab_share']:.3f}")
        log('   ', dict(info['stats']))
        log('    long-s candidates:', info['longs_candidates'], info['longs_top'])
    for side, n in totals.items():
        print(f'TOTAL {side}: {n} words')


if __name__ == '__main__':
    main()
