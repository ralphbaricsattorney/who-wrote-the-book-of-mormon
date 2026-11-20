# Joseph Smith Papers — Revelation Book 2 (1831–1834 revelations) and the 1835 Doctrine and Covenants, split into individual revelations

Joseph Smith's dictated revelations after the period covered by `../jsp_revelation_book_1_and_book_of_commandments/`.

- **Source:** https://www.josephsmithpapers.org/paper-summary/revelation-book-2/1 and https://www.josephsmithpapers.org/paper-summary/doctrine-and-covenants-1835/1 (The Church Historian's Press). Same JSON endpoint and method as the Revelation Book 1 folder; see that MANIFEST for the general description of `raw/` and `text/` files and the scribe-attribution method.
- **Fetched:** 2026-11-15 with `scripts/jsp_fetch.py` (queue: `scripts/jsp_queue3.sh`), one connection, 1.2 s pause; all pages fetched (150/150 and 305/305).
- **Licence:** transcripts and annotation © Intellectual Reserve / Church Historian's Press; the underlying 1830s texts are public domain. Private research use; do not redistribute.

## Contents
| document | pages | words | what |
|---|---|---|---|
| `text/revelation-book-2.txt` | 150 | 37,318 | "Kirtland Revelation Book", manuscript copybook, ca. Feb 1832 – Nov 1834. Hands (reading text): Frederick G. Williams 26,427; Orson Hyde 7,009; Oliver Cowdery 1,973; **Joseph Smith 1,086** (D&C 72 parts A–B); Willard Richards 674 (1843 history notes at the back, not revelation); W. W. Phelps 135. |
| `text/doctrine-and-covenants-1835.txt` | 305 | 115,997 | First edition, Kirtland 1835, printed. Includes the seven Lectures on Faith (24,445 words; already in `../jsp_lectures_on_faith_1835/`), 103 numbered sections (83,920 words), index and contents. |

## Individual revelations (`items/`)
`scripts/jsp_split_items.py` cuts each document at JSP's own item markers and names each piece with JSP's editorial title, date and D&C reference.
- `items/revelation-book-2/` + `revelation-book-2.items.tsv/.jsonl`: 57 items, of which **55 are revelations or related texts** (35,898 words), dated June 1829 – 25 Nov 1834 (mostly Dec 1831 – Nov 1834). Per-item scribe word counts are in the `.jsonl`.
- `items/doctrine-and-covenants-1835/` + `.items.tsv/.jsonl`: 116 items: title page, preface, Lectures 1–7, **Sections 1–102 (103 items; section 66 is split a/b)**, general assembly minutes, index, contents. Each section row gives the 1835 section number, JSP title/date and the modern D&C number.
- Columns: `seq, jsp_date, jsp_title, canon_ref, pages, words, main_scribe, file`.

## Which modern D&C sections are not in Revelation Book 1 (`dc_section_coverage.tsv`)
`scripts/dc_coverage.py` checks every section of the modern D&C (`../lds_scriptures_json/doctrine-and-covenants.json`) against each JSP source two ways: the section number appears in the source's table of contents, and the share of the section's word 4-grams found in the source text.
- **In Revelation Book 1 (89 sections, 73,692 modern words):** 1, 3, 4, 7–10, 19–31, 33–84, 86–90, 93–99, 101, 103–105, 133.
- **Not (or only partly) in Revelation Book 1 (49 sections, 38,238 words):**
  - in the 1833 Book of Commandments (already on disk): 5, 6, 11, 12, 14, 15, 16, 18
  - in Revelation Book 2: 17, 32, 91, 92, 100, 102, 106, 107 (107 is partial in both books)
  - in the 1835 D&C: all of the above plus 13 (matched by text overlap only), 120 (text overlap only — check), 134
  - **only in the modern JSON (30 sections, 26,740 words):** 2, 85, 108–119, 121–132, 135–138. The 1844 D&C (not fetched) would give period text for 103, 105, 112, 119, 124, 127, 128 and 135.
- 102 and 107 are flagged "partial" for Revelation Book 1: listed in its contents but with little matching text.

## Caveats
- **Not everything in the D&C is Smith's dictation.** By the usual attributions: 102 is council minutes; 134 (1835 section 102) is attributed to Oliver Cowdery; 1835 section 101 "Marriage" likewise; 135 John Taylor; 136 Brigham Young; 138 Joseph F. Smith (1918); 121–123 and 127–128 are letters; 129–131 are notes of remarks by William Clayton and others; 109 is a prepared prayer with several contributors; 2, 13, 110 and 137 are extracts from histories or journals. These attributions are from general knowledge, not from files here — confirm against JSP before excluding or including.
- **The 1835 text was edited** (by Smith, Cowdery, Rigdon and Williams as a committee) and differs from the manuscript wording, sometimes substantially (e.g. D&C 20, 42, 107). For the earliest wording prefer Revelation Book 1/2.
- **"Wilford Woodruff" as scribe of the 1835 D&C is an artefact.** JSP's page metadata names Woodruff because the copy imaged is his, with his marginalia; the text is print. Ignore `by_scribe/` and `main_scribe` for this document.
- Revelation Book 2 reading text folds in later redactions, and keeps both readings where a word was corrected ("Jerad Jared", "Pordage Portage"); bracketed editorial expansions also remain. Use `expandedText` in the raw JSON for diplomatic work.
- Revelation Book 2 items overlap Revelation Book 1 (e.g. D&C 76, 84, 88). De-duplicate by `canon_ref` before counting words.
- Three D&C 98 pieces in Revelation Book 2 all carry the title "…continued" because of an inserted leaf; treat seq 33–35 as one revelation. Same for D&C 96 (seq 28–30).

## Not fetched
- **Doctrine and Covenants, 1844** (`doctrine-and-covenants-1844`, 455 pages): the site slowed to 20–90 s per page with timeouts, so I stopped. `scripts/jsp_queue3.sh` is resumable and will fetch it.
- Standalone JSP documents for the 1836–1844 revelations (D&C 108–132), which exist as separate items in JS's journals and letterbooks, were not collected.
