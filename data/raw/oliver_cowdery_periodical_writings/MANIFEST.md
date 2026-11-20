# Oliver Cowdery — signed periodical writings, 1834–1837 (derived corpus)

- **Derived from:** `../messenger_and_advocate_centerplace/` and `../evening_and_morning_star_centerplace/` (centerplace.org transcriptions; see those manifests for raw HTML and cleaning). Built 2026-11-12 by `scripts/build_cowdery_and_ocr.py`.
- **Author:** Oliver Cowdery (1806–1850). **Printed texts** (Cowdery was editor/printer of both papers in this period), not manuscripts.
- **Total:** 17 documents, ~35,800 words. The core is the eight historical letters to W. W. Phelps ("Letters I–VIII", M&A Oct 1834–Oct 1835, ~22,200 words), the earliest narrative history of the church and the Book of Mormon translation.

## Selection method
- Letters I–VIII were located by hand in the cleaned issue texts and cut by **verified line ranges** (recorded in documents.json). In the centerplace transcription Letters III, V, VI carry no signature line; they are identified by their series headings ("LETTER III." etc., "To W. W. Phelps, Esq.").
- Other items are articles that end in an explicit right-aligned signature "OLIVER COWDERY." / "O. COWDERY" in the transcription; their *start* boundary comes from the heuristic segmenter (cut at the previous centered heading or signature), so a few lines of an adjacent unsigned item could be included — spot-check before use.
- **Excluded:** the many unsigned editorials ("-Editor.") written while Cowdery edited M&A (Oct 1834–May 1835 and Mar 1836–Jan 1837) because editorial authorship is not certain (J. Whitmer, W. W. Phelps, W. A. Cowdery also edited/wrote), council minutes he co-signed as clerk, and the joint Rigdon–Cowdery circular of May 1834 (in `../sidney_rigdon_broadhurst/`).

## Caveats
- **Joseph Smith involvement:** Letter I is introduced by a note from JS, and JS is said to have assisted with the history letters; treat the series as Cowdery-dominant but possibly JS-informed. W. W. Phelps's reply letters are interleaved in the same issues and are excluded.
- centerplace inserted bracketed modern spellings after misspellings ("opponants [opponents]"); these were removed, keeping the original spelling. Long KJV quotations are present (esp. Letters IV–VI).
- Letter II ends "...I shall proceed.-Editor." (as printed).

## Documents
| file | issue, date | description | words |
|---|---|---|---|
| text/letter_01.txt | v1n01, Oct 1834 | Letter I to W. W. Phelps (Norton, Ohio, 7 Sep 1834), signed O. Cowdery | 1772 |
| text/letter_02.txt | v1n02, Nov 1834 | Letter II to W. W. Phelps; closes '-Editor.' | 3073 |
| text/letter_03.txt | v1n03, Dec 1834 | Letter III to W. W. Phelps (unsigned in transcription) | 1273 |
| text/letter_04.txt | v1n05, Feb 1835 | Letter IV to W. W. Phelps, signed Oliver Cowdery, 27 Feb 1835 | 2058 |
| text/letter_05.txt | v1n06, Mar 1835 | Letter V to W. W. Phelps (unsigned in transcription) | 2104 |
| text/letter_06.txt | v1n07, Apr 1835 | Letter VI to W. W. Phelps (unsigned in transcription) | 3325 |
| text/letter_07.txt | v1n10, Jul 1835 | Letter VII to W. W. Phelps, signed Oliver Cowdery | 3503 |
| text/letter_08.txt | v2n01, Oct 1835 | Letter VIII to W. W. Phelps, signed Oliver Cowdery | 5107 |
| text/editorial_address_1834.txt | v1n01, Oct 1834 | Opening 'Address' of M&A, signed OLIVER COWDERY | 1149 |
| text/travel_letter_pontiac_1834.txt | v1n01, Oct 1834 | Travel letter from Pontiac, M.T., 20 Oct 1834, signed OLIVER COWDERY | 3176 |
| text/editorial_to_patrons_1835.txt | v1n08, May 1835 | 'To the Patrons', signed OLIVER COWDERY | 1250 |
| text/statement_1836_v2n03.txt | v2n03, Dec 1835 | Signed statement, Oliver Cowdery | 1007 |
| text/editorial_v3n01_a.txt | v3n01, Oct 1836 | Editorial, signed O. COWDERY | 772 |
| text/editorial_v3n01_b.txt | v3n01, Oct 1836 | Article, signed O. COWDERY | 1835 |
| text/valedictory_1837.txt | v3n11, Aug 1837 | Valedictory, signed OLIVER COWDERY | 858 |
| text/ems_letter_to_wa_cowdery_1834.txt | EMS v2n16_10, Jan 1834 | EMS 2:16, letter 'Dear Brother' to W. A. Cowdery (Kirtland, 23 Jan 1834 heading), signed OLIVER COWDERY | 789 |
| text/ems_address_to_patrons_1834.txt | EMS v2n24_01, Sep 1834 | EMS 2:24, closing 'Address to the Patrons of The Evening and the Morning Star', signed O. COWDERY | 2764 |

## Also from JSP (manuscript) — see `../jsp_oliver_cowdery_letters/`
Cowdery's 1829–1835 letters to JS as transcribed by the Joseph Smith Papers (several survive only as later copies by other scribes).
