# Memminger: cleaning record

Christopher Gustavus Memminger (1803–1888), Charleston lawyer and legislator, later Confederate Secretary of the Treasury.

The outputs are produced by `prepare/two_register/clean_memminger.py`; rerun it with `~/miniconda3/envs/sr-theory/bin/python -I prepare/two_register/clean_memminger.py --report`. All inputs are uncorrected Internet Archive OCR. Line numbers are 1-based lines of the raw `*.djvu.txt` files. Word counts are whitespace tokens: "before" counts every token inside the kept line range or ranges, and "after" counts the output file.

## Summary

| Output | Date | Source | Before | After | OCR |
|---|---|---|---|---|---|
| `scripture__book_of_nullification.txt` | 1830 | IA `bookofnullificat00char` | 15,372 | **14,779** | fair–good |
| `prose__virginia_address_1860.txt` | 1860 | IA `addressofhoncgme00memm` | 16,216 | **11,686** | good |
| `prose__augusta_lecture_1851.txt` | 1851 | IA `lecturedelivered00memm` (new) | 9,267 | **8,505** | fair |
| `prose__cooperation_address_1851.txt` | 1851 | Capers 1893, IA `cu31924032767505` (new) | 9,320 | **7,640** | good |
| `prose__bank_letters_1850.txt` | 1850 | Capers 1893 | 6,033 | **5,336** | good |
| `prose__bank_argument_1843.txt` | 1843 | Capers 1893 (from the 1844 printed report) | 10,353 | **10,116** | good (legal genre) |
| `prose__bible_oration_1842.txt` | 1842 | Capers 1893, appendix | 8,813 | **7,783** | good |
| `prose__college_orations_1817_1819.txt` | 1817–19 | Capers 1893, appendix | 12,630 | **11,408** | good |

- **Scripture side:** 14,779 words.
- **Prose side:** 62,474 words in all.
  - The original 1860 address alone is 11,686 words. That is below the manifest's ~16k because the resolutions, letters and speeches by others that it reads into the record have been removed.
  - Prose within 13 years of 1830: college orations 1817–19, Bible oration 1842 and bank argument 1843, 29,307 words together. Without the legal argument it is 19,191 words.
  - Prose from 1850–51: 21,481 words.
  - Prose from 1860: 11,686 words.

New raw files are described in `data/raw/two_register_authors/memminger/ADDITIONS.md`.

The OCR indicator is the share of tokens found in the corpus vocabulary (`normalized.parquet`, words with 3 or more occurrences). The values are 0.959–0.980. Each judgement below also rests on reading samples.

**Long s:** these are 19th-century imprints with no long s. The check found one candidate in all files ("fickle" → "sickle", a false positive), so no repair was applied.

## Attribution of *The Book of Nullification*

**Verdict: probable.** The pamphlet is signed only "A Spectator of the Past". No contemporary (1830–33) document naming Memminger was found. The attribution comes from one 19th-century witness close to Memminger, and the reference works follow it.

Evidence:

1. **Henry D. Capers, *The Life and Times of C. G. Memminger* (Richmond, 1893), p. 107.** Raw file `prose/cu31924032767505.djvu.txt` lines 5246–5258; https://archive.org/details/cu31924032767505.
   - Capers writes that a satire "written in biblical style … entitled the Book of Nullification" appeared, and that "for some time the author was not discovered, but before the election he was found to be Mr. Memminger."
   - He reprints the whole text in his appendix (pp. 569 ff.; raw lines ~28207–29100) "as a specimen of my honored friend's wit".
   - Capers knew Memminger personally. He was Chief Clerk of the Confederate Treasury under him (Capers p. ~320, raw line 15726), and he wrote with the family's help: the college papers were lent by Memminger's son.
   - He was writing 60 years after the event, five years after Memminger's death, and he cites no source for the discovery.
2. **Library catalogue records.**
   - East Carolina University's record for the Gale *Sabin Americana* reproduction of the Huntington Library copy enters it under "Memminger, C. G. (Christopher Gustavus), 1803-1888". Its note reads: "Attributed to Memminger by the Dictionary of American Biography and the National Union Catalog." Sabin nos. 6357 and 56313. https://librarycatalog.ecu.edu/catalog/2421920
   - Open Library carries the same note from a Miami University (Ohio) MARC record of the Research Publications microfiche (Selected Americana from Sabin, 8479). https://openlibrary.org/works/OL1116825W
   - The NUC and DAB attributions are therefore the cataloguing authority. They could not be read directly here.
3. **Modern reference works.**
   - William L. Barney, "Memminger, Christopher Gustavus", *American National Biography* (2000). It is quoted at House Divided (Dickinson College): https://hd.housedivided.dickinson.edu/node/20297
   - Aaron W. Marrs, "Memminger, Christopher Gustavus", *South Carolina Encyclopedia* (2016): https://www.scencyclopedia.org/sce/entries/memminger-christopher-gustavus/. Its bibliography lists Capers.
   - Both give the attribution without qualification.
4. **The scan itself.**
   - The Internet Archive / Duke University record (`bookofnullificat00char`, https://archive.org/details/bookofnullificat00char) names no author.
   - The title page reads "By a Spectator of the Past. Charleston—1830". In the OCR this is "^HARLESTON—lSSO^", which matches the catalogues' 1830.
   - The closing verse (ch. X v. 66) says the scribe's "name is not great, for it is not found in the Book". That fits a young, little-known Union-party lawyer, but it does not identify him.

Doubts:

- **The date does not agree across sources.**
  - The imprint and the catalogues say 1830.
  - ANB and the *South Carolina Encyclopedia* say 1832.
  - Capers puts the pamphlet "early in the year following" the Union party's 4 July 1831 celebration and "before the election for delegates", which is 1832.
  - So Capers's chronology does not match the imprint. His account is a late recollection, not a documented discovery.
- **No independent contemporary confirmation was found.** That would be a newspaper of 1830–32 naming Memminger, or a letter. The Library of Congress catalogue and the Huntington record could not be reached (bot blocks and rate limits).
- **Nothing points to another author.** No rival attribution was found, and the satire's Union-party standpoint matches Memminger's known politics in 1830–32.

## Per file

### `scripture__book_of_nullification.txt`

- **Source:** `scripture/bookofnullificat00char.djvu.txt`. *The Book of Nullification. By a Spectator of the Past*, Charleston, 1830, 31 pp. Duke University copy.
- **Kept:** lines 48–1943, which run from "CHAPTER I." to the end of ch. X v. 66. The manifest's 1940 cut off the last three lines of v. 66.
- **Removed:**
  - **Front matter (lines 1–47):** the IA/Duke title leaf ("Perkins Library, Duke University") and the title page.
  - **The author's own 9-line prose note** ("The style in which the Jewish history is written in the Scriptures … A Spectator of the Past", ~85 words). It is plain prose, not the scripture register, and too short to use, so it was left out.
  - **Chapter headings (9).**
  - **Verse numbers (364).** The OCR variants of the numbers are handled ("4S.", "2Q.", "1 9.", "2.3.", "J2.", "3o.", "•1.").
  - **Page numbers and stray OCR letters (21 lines).** This includes one garbled line-end fragment, "i-jOUl." (= "soul.", line 953).
  - **After 1943:** a library stamp.
- **Repairs:**
  - Line-end hyphens rejoined. Some of these the OCR read as "^" or "=", as in "pro^ / duceth" and "vexa= / lion".
  - Wrapped lines joined, with one paragraph per verse. One paragraph (ch. I, after v. 34, "Then, O Robert! the people…") has no verse number in the print and is kept inside the preceding verse.
  - Nothing else was corrected.
- **Content note:** the speeches inside the satire put real phrases of the nullifiers in quotation marks ("not to be borne", "ought to be resisted at any AND EVERY HAZARD", "One of the People"). These are short and part of the author's sentences, so they are kept.
- **OCR: fair to good** (vocabulary share 0.968).
  - Body text in roman type reads well.
  - Italic and small-capital words are often garbled: "jyullijic'dion^", "J^ord", "captkuivS", "Cotivtrdio7i".
  - The vocative "O" is read as "0", and the apostrophe and quote marks are noisy ("<'0", "'^").
  - About one damaged token per 40–60 words.
- **Samples read:** five 200-word passages, at 5%, 25%, 45%, 65% and 85% (ch. I–II, IV, VI, VIII, X). All are verse text in the author's register with no page furniture.

### `prose__virginia_address_1860.txt`

- **Source:** `prose/addressofhoncgme00memm.djvu.txt`. *Address of the Hon. C. G. Memminger, special commissioner from the State of South Carolina, before the assembled authorities of the State of Virginia, January 19, 1860* (Richmond, 1860; Virginia Doc. No. LVIII).
- **Kept:** lines 121–1884, from "When the Athenian orator…" to "…our southern country."
- **Removed before 121:**
  - Virginia's letter and resolution requesting the text.
  - Memminger's covering letter (formulaic, ~90 words).
  - IA boilerplate, the heading and the salutation.
- **Removed inside the range** (399 lines). These are documents and speeches by others that the address reads into the record:
  - the S.C. resolutions of 1859 (158–188);
  - Virginia's 1833 resolutions (300–331);
  - the letters of B. W. Leigh and James Hamilton jr (345–375);
  - the S.C. convention resolutions of 1833 (388–402);
  - Virginia's 1851 resolutions (428–466);
  - Art. 6 of the Ordinance of 1787 (700–711);
  - Jefferson to John Holmes, 1820 (824–851);
  - Calhoun's 1838 speech (876–955);
  - the London *Times* report of the Brougham/Aberdeen debate (1032–1095);
  - Virginia's 1847 resolutions (1181–1221);
  - Clayton's account of the 1848 committee (1237–1273);
  - Virginia's 1849 resolutions (1291–1314);
  - the 1850 D.C. act (1337–1343);
  - the preamble of the Constitution (1485–1493);
  - Bryant's verse "The Antiquity of Freedom" (1857–1870).
- **Also removed:**
  - 26 running heads ("Doc. No. 58. 7").
  - 5 signature marks and debris lines.
  - Six marginal marks at line ends (lines 404, 405, 411, 412, 426, 713).
- **Kept:**
  - Short quotations woven into his sentences ("the Philistines be upon thee, O Samson"; "In the sweat of thy face…").
  - His own numbered lists.
- **OCR: good** (0.977). There are few errors, mostly digits: "1S52", "17S7".
- **Samples read:** five, at 5–85%. All are Memminger's running argument; the seams where quotations were removed read cleanly ("I respectfully ask leave to have them read :" ¶ "Three distinct objects…").

### `prose__augusta_lecture_1851.txt`

- **Source:** `prose/lecturedelivered00memm.djvu.txt`. *Lecture delivered before the Young Men's Library Association, of Augusta, April 10th, 1851. Showing African slavery to be consistent with the moral and physical progress of a nation* (Augusta, 1851). Library of Congress copy.
- **Kept:** lines 136–1185.
- **Removed:**
  - **Before 136:** LC shelf marks, two title pages and the caption "On the Institution of Slavery".
  - **After 1185:** LC stamps.
  - **Inside the range:**
    - the author's footnote quoting Bigelow's *Jamaica in 1850* (944–963);
    - the definition of slavery quoted from "a profound thinker of our day" (103 words; his introducing sentence is kept);
    - God's message to Eli from 1 Samuel 3 (95 words);
    - 34 lines of page numbers and scanned page-border ornaments;
    - marginal letters and bars at line starts and ends, which the scan picked up from the gutter ("j of the master", "I began. j"). Line 246's marginal "I" was removed by an explicit fix.
- **Kept:** short Bible phrases inside his sentences. A later step masks King James Bible runs.
- **OCR: fair** (0.970).
  - Pages 4–5 are poor ("Seeins: Iiow suecessfully tlie people of ICno^land").
  - Elsewhere "g" is often read as "^" ("itnao^ination", "Cona^resses").
  - The rest is readable.
- **Samples read:** five, at 5–85%. All are author's text; no ornaments or page numbers remain.

### `prose__cooperation_address_1851.txt`

- **Source:** Capers (1893) pp. 204–222, raw `prose/cu31924032767505.djvu.txt`. This is Memminger's speech moving the Co-operation party's nominations for the Southern Congress, Charleston, September 1851. Capers reprints it from the copy the party printed.
- **Kept:** lines 9930–10873, from "Fellow Citizens, — I rise…" to "…that declaration will be maintained."
- **Removed:**
  - the 1848 report and resolutions (9990–10019);
  - the 1849 Senate and House reports and resolutions (10031–10124);
  - the preamble of the 1850 act (10153–10161);
  - the act's 7-line statement of purpose (76 words);
  - House Journal extracts (10250–10254, and the p. 221 extract, 46 words);
  - his footnote with the 1850 resolutions (10274–10292);
  - 16 Capers running heads ("Secession Movement of 1851. 209", "Life and Times of C. G. Memminger").
- **Kept:** short quoted phrases from the reports (2–3 lines) that his sentences analyse.
- **OCR: good** (0.979). Cornell's scan of clean 1893 type.
- **Samples read:** five. All are the speech.

### `prose__bank_letters_1850.txt`

- **Source:** Capers pp. 160–174. It contains two letters, separated by a paragraph break in the output:
  - (a) lines 7800–8023: "To the People of South Carolina", *Charleston Mercury*, 8 March 1850, a reply to F. H. Elmore, president of the Bank of the State;
  - (b) lines 8179–8585: "To the People of St. Philip's and St. Michael's Parishes", the summing-up of his 1850 series against the bank's recharter.
- **Removed:**
  - Capers's framing.
  - The first letter's heading and both signatures.
  - The letters of Judge Wardlaw and T. W. Glover printed between the two (8024–8178).
  - A footnote listing committee members (7927–7930).
  - A Richland member's 1841 resolution (7949–7964).
  - Five quotations of Elmore's and Wardlaw's words, 32–103 words each, 343 words in all. These leave seams such as "Speaking of me, he says : Answer. — Truth and integrity never fly."
  - 11 running heads.
- **OCR: good** (0.980).
- **Samples read:** five. All are Memminger's argument. Letter (a) is polemical and close to its opponent's text; letter (b) is a numbered recapitulation.

### `prose__bank_argument_1843.txt`

- **Source:** Capers pp. 136–155, lines 6575–7576. Memminger's argument for the State in *State v. Bank of South Carolina*, Court of Errors, Columbia, May 1843. Capers reprints it from the report printed by order of the legislature in 1844.
- **Removed:**
  - 19 running heads.
  - One page signature.
  - Line 6953 "512." was kept by an explicit rule, because it ends a citation and is not a page number.
- **Cautions:**
  - The first paragraph is the reporter's indirect speech ("Mr. Memminger, on behalf of the State, opened the argument by stating that … they must premise…"). The rest is direct argument in the first person plural.
  - Case citations ("Com. Dig. Franchises, G. 3", "9 Cranch, 43") are kept, since they are the author's text. They depress the vocabulary share (0.959) and give the file a legal register.
  - Use it as a separate genre, or leave it out.
- **OCR: good.**
- **Samples read:** five. All are argument with citations.

### `prose__bible_oration_1842.txt`

- **Source:** Capers, Appendix pp. 532–548, lines 26293–27106. "An Oration on the Bible" (running head "Sacred and Profane History"), delivered before the Euphradian and Clariosophic Societies, South Carolina College, December 1842.
- **Removed:**
  - title and caption;
  - Isaiah 13, 44 and 45 read as a block (26604–26640);
  - Deuteronomy 28–29 (26904–26926);
  - Pope's *Essay on Man*, 8 lines (26997–27004);
  - two hymn lines (27085–27087);
  - "Tell it out among the heathen…" (Ps. 96, 38 words);
  - the closing hymn stanza (27107–27111);
  - a footnote asterisk with no printed note;
  - 15 running heads.
- **Kept:** shorter scriptural phrases inside his sentences. Expect the King James Bible masking step to catch some more.
- **OCR: good** (0.976).
- **Samples read:** five. All are the oration. It is historical and religious oratory, the nearest dated plain prose to 1830 after 1830 itself.

### `prose__college_orations_1817_1819.txt`

- **Source:** Capers, Appendix pp. 490–515, "College Essays and Orations", lines 24121–25358. The six pieces are:
  - "Love of Country" (sophomore essay, age 14);
  - "The Art of Printing" (Clariosophic Society, 1818);
  - "Immortality of the Soul" (1819);
  - "Influence of Popular Opinion" (senior exhibition, 22 April 1819);
  - "Eulogy on President Maxey" (1819);
  - "Influence of Fiction upon the Human Mind" (commencement, 6 December 1819).
- **Removed:**
  - titles and captions;
  - the Latin salutatory of the 1819 commencement (25087–25194);
  - two short verse quotations (24240–24241, 24929–24932);
  - 21 running heads, including one lower-case "appendix: 507" (24966).
- **Cautions:**
  - These are juvenilia and school exercises in a florid, declamatory style.
  - Capers printed them from family manuscripts 75 years later, and he may have edited them.
  - Treat them as the author's earliest prose, not as typical of his mature plain style.
- **OCR: good** (0.968).
- **Samples read:** five. All are the essays.

## Anything doubtful

- **Attribution of the scripture side:** probable, not secure (see above).
- **Transmission of the Capers texts:**
  - Five prose files come from Capers's 1893 reprint, not from the original imprints.
  - The texts read as faithful, and the 1850 letters and 1851 speech cite their printed sources.
  - Spelling and punctuation may have been regularised by the 1893 printer.
- **Genre and register mismatch:** the prose side mixes oratory (1842, 1851, 1860), a lecture (1851), newspaper polemic (1850), a legal argument (1843) and student declamation (1817–19).
- **Choice of prose subset:** a scripture-versus-prose comparison closest in date and genre would use the 1842 oration and the 1850–51 pieces, with the 1860 address as the manifest's original pair.
