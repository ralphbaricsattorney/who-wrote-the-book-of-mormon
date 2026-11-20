# Jacob Ilive (1705–1763): cleaning record

Produced by `prepare/two_register/clean_ilive.py` (run with `~/miniconda3/envs/sr-theory/bin/python`),
following `data/prepared/two_register/CLEANING_PROTOCOL.md`. All cleaning is done by line ranges and
pattern rules in the script. Audit files written alongside:
`removed_lines.tsv` (every removed raw line with its reason), `removed_quotations.tsv` (every long
quotation removed), `stats.json` (counts below, the long-s repairs, and per-reason word totals).

Word counts are whitespace tokens. "Raw" = tokens in the kept raw line range(s) before cleaning.

| Output | Side | Raw words | Clean words |
|---|---|---|---|
| `scripture__book_of_jasher.txt` | scripture | 29,631 | **22,879** |
| `prose__laymans_vindication_1730.txt` | prose | 98,248 | **85,096** |
| `prose__oration_joyners_hall_1733.txt` | prose | 27,027 | **12,521** |
| `prose__oration_trinity_hall_1738.txt` | prose | 12,013 | **10,079** |
| `prose__speech_master_printers_1750.txt` | prose | 689 | **642** |
| `prose__reasons_house_of_correction_1757.txt` | prose | 22,323 | **17,805** |
| **Scripture side** | | | **22,879** |
| **Prose side** | | | **126,143** |

## Long s (applied identically to every output file)

1. In the five `bim_eighteenth-century_*` prose scans the long s is mostly encoded as the character
   `ſ` (U+017F). It is mapped to `s` before anything else: 1733 oration 3,195 characters; 1738 oration
   1,724; 1750 speech 73; 1757 Reasons 2,202; 1730 Layman's Vindication 12,720.
2. Then the protocol's conservative f→s repair runs on every output, scripture and prose alike:
   a word containing `f` is changed only if it is not in the reference list (words occurring ≥3 times
   in `prepare/vocabulary.parquet` `text_norm`) and an f→s variant is. Words changed:
   Jasher 1 (the 1829 scan has no long s; the single change is `afs→ass`), 1733 oration 21, 1738
   oration 118, 1750 speech 2, 1757 Reasons 40, 1730 Vindication 249. **Total 431 words.**

30 most frequent repairs, all files: chrift→christ (33), fays→says (18), fay→say (14), fon→son (14),
fin→sin (10), fince→since (9), teftament→testament (8), falvation→salvation (7), defign→design (6),
fave→save (6), defire→desire (5), fome→some (5), ascenfion→ascension (5), fouls→souls (5),
fick→sick (5), alfo→also (4), raifing→raising (4), deftroy→destroy (4), eftablish→establish (4),
mofes→moses (4), fuch→such (3), leaft→least (3), chriftianity→christianity (3), againft→against (3),
muft→must (3), perfon→person (3), thefe→these (3), defired→desired (3), reafons→reasons (2),
priefts→priests (2). Per-file lists are in `stats.json` (`top_repairs`).

**Known limit of the rule.** f-forms that are themselves in the reference list are not repaired, so a
few long-s errors remain in the prose (counts in the cleaned files): `fo` for *so* (1730: 30, 1757: 19,
1738: 12, 1733: 1), `faid` for *said* (1730: 22), `fame` for *same* (1730: 25, 1733: 4, 1738: 4),
`foul` for *soul* (1738: 8, 1730: 3), `fee` for *see* (1757: 11). These are small next to the
correct forms but `so` and `said` are function words.

---

## Scripture side: `scripture__book_of_jasher.txt`

**Source.** `ilive/scripture/bookofjasherwith00iliv.djvu.txt` (1829 Bristol reprint), lines 758–8539
(`CHAP. I.` to the line before `THE END OF THE BOOK OF JASHER`). The 1751 first printing
(`bim_eighteenth-century_the-book-of-jasher_ilive-jacob_1751.djvu.txt`) is complete but its OCR is very
poor (two-column pages with marginal glosses interleaved, and garbled where the page is crowded), so the
1829 scan, which is far more legible, is the base text. The 1751 scan is used as a witness (below).

**Removed.**
- Everything outside the range: the 1829 title page, editor's Advertisement, Preliminary Dissertation,
  Alcuin's pilgrimage narrative and "Various Readings" (lines 1–757), and the Notes and Testimonies after
  the end of the book (presented as by others).
- Chapter headings (37) and the chapter summaries printed under them (263 lines, 1,437 words).
- Running heads (`<topic> ; JASHER. <topic>`, `Chap. iii. <topic>`) and their topic halves on
  neighbouring lines (723 words); page numbers and signature letters.
- The marginal column: Hebrew glosses (`Heb. the feeder`, OCR `Ileb.`, `i/ef.`, `Hdi.` …), `A. M.` years
  and other margin dates (about 830 words), including glosses caught inside a text line.
- Verse numbers, pilcrows (OCR `51`, `5[`, `H`, `f`), and the superscript reference marks before glossed
  words (`'Jehovah`, `''Eden`, `^Gentiles`). The OCR-garbled large initial of each chapter's verse 1
  is restored from the surviving letters (`A^^ ''' came to pass` → `And it came to pass`, `]^0W` → `Now`).
- **Additions made by the 1829 editor (45 verses, 1,219 words).** Every 1829 verse was scored by the share of
  its word trigrams found anywhere in the 1751 scan. Genuine verses have a median score of 0.82. Two runs of
  verses score near zero, and both are King James text that the 1829 edition inserted:
  (1) chap. III, the binding of Isaac (Gen. 22:3–19, 17 verses). The 1751 chapter has Sarah talk Abraham
  out of the sacrifice, and its summary numbers his death at verse 22, not 39.
  (2) chap. XI, Pharaoh pursuing Israel into the sea, the drowning and the Song of Moses
  (Exod. 14:23–15:21, 28 verses). In the 1751 text Pharaoh turns back into Egypt (1751 vv. 14–17).
  Both runs are removed; they are in `removed_lines.tsv` as "1829 addition".

**Paragraphs.** One verse per paragraph.

**OCR quality: good** (98.7% of word tokens are in the reference list; this share is not comparable with the manifest's system-dictionary `dict_share`). From reading
samples: clean running KJV-style narrative; occasional character errors (`Hel)rews`, `ISIoses`,
`Aloses`, `iight`), a few marginal years left inside the text (`2624,`), and rare fragments of
running heads or glosses.

**Doubtful.**
- The 1829 text is a revised edition, not a straight reprint. Apart from the two insertions, the editor
  changed wording in places. In chap. I the 1751 printing has "Cain conceived, and bare Enoch" and
  "Seth conceived, and bare Enos", where 1829 has "Cain begat Enoch" and "Seth begat Enos". Edits of this
  size cannot be told apart from 1751 OCR noise, so they remain. The 1751 verses the 1829 editor cut
  (chap. XI vv. 14–17, about 60 words) are missing. If exact 1751 wording matters, the 1751 scan
  (or ECCO-TCP) would have to be used instead.

---

## Prose side

Rules common to the five bim scans: running heads (fuzzy match to the file's head titles); page numbers
(including `[ 34 ]`); signature marks (`B 2`); catchwords (a lone word at the page foot repeated at the
head of the next page); footnotes (from a note marker `(a)`, or from a block of the longer small-type lines,
to the next page break); marginal references and `PART`/`CHAP.`/`SECT.` margin tokens; OCR debris
(lines under 50% letters, or with fewer than 40% reference-list words); in-text note references `(a)`.
Long quotations are runs of 4 or more lines that each open with a quotation mark (18th-century style;
OCR `«`, `"`, `&`, `ce`, `*` …) and that total 30 or more words. Shorter quotations inside Ilive's own
sentences are kept, with the line-start quote marks stripped (the later KJV masking step handles scripture).

### `prose__laymans_vindication_1730.txt`
**Source.** `prose/bim_eighteenth-century_the-laymans-vindication_ilive-jacob_1730.djvu.txt`, lines
66–495 (dedication to George II and Preface) and 560–22000 (Introduction, Part I chaps. I–IX, Part II
"Plain Answer" to Collins's *Discourse of the Grounds and Reasons*, to the conclusion).
**Removed.** Title page; Contents and Errata (496–559); Index (22001–end); running heads (1,518 words);
page numbers, signatures, catchwords; marginal notes (188); footnotes (1,467); 67 long quotations,
almost all scripture (3,289 words); OCR debris (2,213).
**OCR quality: fair to poor** (96.0% reference-list words). Running text is readable, but many pages
have show-through from the reverse side, which puts junk words inside lines (`KK" BW wu CTY`), and
small-capital paragraph openings are garbled (`Tux`, `Taz` = *The*). Italic *J* is often read as *F*
(`Ferusalem`).
**Doubtful.** Part II quotes Collins's book in italics, without quotation marks, so short quotations
of Collins remain inside Ilive's sentences. Some marginal references remain stuck to line ends
(`Ver. 11.`, `C n a y`).

### `prose__oration_joyners_hall_1733.txt`
**Source.** `prose/bim_eighteenth-century_the-oration-spoke-at-joy_ilive-jacob_1733.djvu.txt`, lines
59–4440 (dedication to the Lord Mayor, Preface, the Oration, the account of his mother, to "Amen").
**Removed.** Title page; running heads; page furniture; **footnotes, 12,800 words**. The book is printed
"with large Notes", and about half of it is notes (by Ilive himself, but mostly quotation and citation).
They are removed as the protocol requires, which is why the clean text is less than half the raw
count. Also removed: 4 long quotations (256 words, including his mother's will in the Preface) and OCR debris.
**OCR quality: good to fair** (97.6%). Clean text with a few garbled small capitals and running-head
remnants.

### `prose__oration_trinity_hall_1738.txt`
**Source.** `prose/bim_eighteenth-century_the-oration-spoke-at-tri_ilive-jacob_1738.djvu.txt`, lines
173–2504 (from the text 1 Cor. xv. 50 to "for evermore").
**Removed.** Title page and the dedication's list of jurors (before 173); "Books written by the same
Author" advertisement (after 2504); running heads, page furniture; 11 long quotations (628 words,
mostly quotations of Dr Felton's *Discourses*, which the oration answers, and scripture); OCR debris.
**OCR quality: fair** (97.4%). This scan reads many long s as `f`: 118 repaired, but `fo` and `foul`
remain (see the limit above). A few unmarked short footnotes (`*` notes) remain inline.

### `prose__speech_master_printers_1750.txt`
**Source.** `prose/bim_eighteenth-century_the-speech-of-mr-jacob-_ilive-jacob_1750.djvu.txt`, lines
74–259 (from "GENTLEMEN" to "nor ever WILL").
**Removed.** Title page; the footnotes "* STEWARD." and "* William Caslon, Esq;" (lines 94–97, 149);
page numbers, catchwords. Very short (642 words). **OCR quality: fair** (garbled small capitals:
`Dors`, `WuxV`).

### `prose__reasons_house_of_correction_1757.txt`
**Source.** `prose/bim_eighteenth-century_reasons-offered-for-the-_ilive-jacob_1757.djvu.txt`, lines
305–4600 (dedication to the Middlesex magistrates, Introduction, Sections I–XIII, Proposals and closing
Queries).
**Removed.** Title page and the folded prison plan (OCR debris, before 305); three account tables
(lines 2599–2642, 2662–2695, 3974–4004; 505 words); footnotes, identified by marker or by their longer
small-type lines (1,327 words, including the itemised list of alms given to prisoners); page numbers,
signatures; OCR debris (1,672 words, mostly plan and show-through).
**OCR quality: fair** (93.9%; the lowest). It is a narrative of prison life with names and trade words
not in the reference list (Locker, Turnkey, Hemp), so the share is lower than the readability would suggest.
**Doubtful.** A few lines of main text next to footnotes were lost where the page break was not
detected (for example raw line 2270).

---

## Checks done

At least five 200-word passages spread through every output were read (the 1750 speech whole), after
the final run. All are Ilive's running text. Page furniture and editorial matter are gone except for
the stray residues noted above (marginal years or glosses in Jasher; marginal references and
show-through junk in the 1730 Vindication). The removal logs were reviewed: the "OCR debris" lines over
30 characters are junk, the footnote spans start and stop at page boundaries, and the removed quotations
are scripture or quotations of other writers.
