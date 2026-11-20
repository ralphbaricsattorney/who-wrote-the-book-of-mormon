# Sidney Rigdon — additional SIGNED items from Dale R. Broadhurst's transcriptions (1831–1873)

Supplements `../sidney_rigdon_broadhurst/` (which is unchanged). Nothing here duplicates that folder.

- **Source:** sidneyrigdon.com pages listed below (Broadhurst's typed transcriptions of newspapers). Fetched 2026-11-15, generic browser User-Agent, 1.2 s between requests; the site has no robots.txt.
- **Script:** `scripts/fetch_rigdon_broadhurst_more.py`. Each bordered box on a page is one newspaper issue; articles inside are separated by `<hr>`. A segment is kept only if it ends with Rigdon's printed signature or opens with a "BY S. RIGDON" byline. Four items were cut by hand-specified start/end patterns (see `SLICES` in the script) because the signature is followed by other matter.
- **Licence:** originals are public domain (1831–1873). Transcriptions and notes are Broadhurst's; private research use.
- **Total:** 29 documents, 41,475 words. Signed solely by Rigdon: 28 documents, 41,105 words.

## Files
- `html/` — the 11 pages exactly as served.
- `text/<doc_id>.txt` — one item each; Broadhurst's line breaks kept, mastheads and his "Notes:" removed.
- `documents.json` — per item: source page and anchor, masthead, how it is signed, joint-signature flag, excerpt flag, opening and closing words, word count.
- `all_segments.jsonl` — every segment of every issue box fetched, signed or not, for auditing what was left out.

## Documents
| doc_id | source | words | notes |
|---|---|---|---|
| ohio_star_1831_01 | Ohio Star (Ravenna), 15 Dec 1831 | 251 | two short notices to Ezra Booth and Simonds Ryder, both signed |
| ohio_star_1832_01 | Ohio Star, 12 Jan 1832 (dated Hiram, 6 Jan) | 556 | letter on Ryder. **Earliest Rigdon prose in the corpus.** |
| quincy_whig_1839_letter_may17_JOINT | Quincy Whig, 25 May 1839 | 370 | **JOINT**: signed Rigdon, Joseph Smith Jr., Hyrum Smith. Exclude from single-author sets. |
| quincy_whig_1839_01 | Quincy Whig, 8 Jun 1839 (Commerce, 27 May) | 1,583 | Rigdon's reply to the Spalding-authorship claim |
| sangamo_journal_1842_letter_aug27 | Sangamo Journal, 16 Sep 1842 (reprinting the Wasp) | 230 | letter about Nancy Rigdon |
| sangamo_journal_1842_01 | Sangamo Journal, 23 Sep 1842 | 136 | sworn certificate; legal boilerplate, in the third person |
| peoples_organ_1844_01 | People's Organ (St. Louis), 17 Sep 1844 | 994 | letter to the editor |
| pittsburgh_ma_01 … _20, pittsburgh_ma_1845-02-15_the_mormons | *Messenger and Advocate* (Pittsburgh), 15 Oct 1844 – Sep 1846 | 36,836 (21 items) | Rigdon edited the paper. Signed editorials, letters (to J. Gregg, to James M. Greig), "Sermon … to the Saints of the Last Days" nos. 1–2, "The Plan of Salvation", "An Essay on Life and Death", "Tour East", the 1846 "Proclamation to the Kings…" (4,099 words), and one hymn (`_07`, verse, 311 words). |
| letter_woodward_1873 | MS letter, Friendship NY, 25 May 1873 (NYPL) | 519 | holograph, aged 80; transcription is full of bracketed illegible gaps. Low quality; closest in date to the revelations. |

## Caveats
- **Broadhurst excerpts.** The Pittsburgh pages are "Excerpted M. & A. Articles": he sometimes abridges with "…" or "* * * *". Ten Pittsburgh items contain such ellipses (`has_ellipsis_excerpts` in `documents.json`), so those are not complete articles. Full-issue scans are linked from the pages as PDFs (`http://www.sidneyrigdon.com/RigWrit/M&A/pdfs/MA-1-01.pdf` …) and were not downloaded.
- `pittsburgh_ma_02` and `_04` are parts 1 and 2 of one letter series; `_09`, `_11`, `_13` are a serial sermon; `_15`, `_16` likewise.
- Unsigned editorials in the Pittsburgh paper are probably Rigdon's too but were not extracted (several signed pieces by others — Winchester, McLellin, "An Observer" — sit beside them). They are recoverable from `all_segments.jsonl` and `html/`.
- Typos in Broadhurst's typing are kept ("surprsing", "he eastern").
- Heavy scripture and D&C quotation in the 1844–45 succession pieces; mask before stylometry.

## Looked at and left out
- Painesville Republican, 14 Feb 1839: a newspaper's paraphrase/quotation of a Rigdon letter from Liberty Jail, unsigned (raw page saved in `html/`).
- Minutes of the April 1845 Pittsburgh conference (signed by Rigdon as president, written by the secretaries).
- April 1844 conference discourse (`RigWrit/1844Conf.htm`): clerks' reports, not Rigdon's composition.
- Nauvoo *Wasp* (`dbroadhu/LDS/wasp2.htm`), the 1838 Senate document, and the EMS April 1834 "To the Public" (already in the first folder as articles_letters_01) — not extracted.
- The 1846–47 continuation of the *Messenger and Advocate* (Greencastle) is not transcribed on the site.
