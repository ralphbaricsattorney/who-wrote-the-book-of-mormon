# Sidney Rigdon — texts transcribed by Dale R. Broadhurst (sidneyrigdon.com)

- **Source:** http://www.sidneyrigdon.com/RigWrit1.htm ("The Collected Writings of Sidney Rigdon", index) and the pages below. Fetched 2026-11-12 with a generic browser User-Agent, 1.2 s between requests. sidneyrigdon.com has no robots.txt (404).
- **Script:** `scripts/fetch_rigdon_broadhurst.py` (one text file per bordered transcription box = one article / installment).
- **Author:** Sidney Rigdon (1793–1876), *as attributed by Broadhurst*. See per-series attribution notes below — several series are unsigned in the original periodicals.
- **Autograph vs scribe:** all items are **printed texts** (newspapers/pamphlets), so compositor/editor intervention is possible; none are manuscripts.
- **Total:** 47 documents, ~150,500 words (core 1833–1838 Kirtland/Far West material ≈ 94,000 words: Millennium + Gospel + Articles/Letters + 1838 Oration + Dear Brethren).

## Raw files
`html/` — raw pages exactly as served: RigWrit1.htm (index), RigWrit_RigWrit3.htm (Millennium), RigWrit_RigWrit3b.htm (Gospel), RigWrit_RigWrit3d.htm (Articles & Letters 1834–38), RigWrit_RigWrit2.htm (Dear Brethren 1834), rigd1838.htm (4 July 1838 Oration), 1840RigA.htm (1840 Appeal), RigWrit_Rigd1844.htm (1844 Memorial + T&S "History of Joseph Smith", the latter NOT extracted), books_Appl1863.htm (1863 Appeal). `documents.json` gives, per text, the source page, table index, masthead line, opening words and word count.

## Series and attribution
| series | date | attribution / caveat |
|---|---|---|
| millennium_01–14 | EMS Dec 1833–Aug 1834; M&A Nov 1834–May 1835 | "Millenium" nos. I–XIV, unsigned ("Communicated"); conventionally attributed to Rigdon. |
| gospel_01–09 | EMS Apr 1833 (Independence), EMS Sep 1834, M&A Nov 1834–Jun 1835 | "The Gospel"; unsigned; attribution per Broadhurst. gospel_01 (Independence, Apr 1833) is the least secure (Phelps was editor there). |
| articles_letters_01–15 | EMS Apr 1834 – Elders' Journal Aug 1838 | Mostly signed "Sidney Rigdon"/"S. Rigdon" (letters to O. Barr, to J. Whitmer, "Saints and the World", "Persecution" etc.). _13 = Elders' Journal prospectus (signed Rigdon in M&A 3:11); _14 letter to Don C. Smith 1837; _15 "To the Saints Abroad" (Elders' Journal 1838; editorial, attribution per Broadhurst). |
| dear_brethren_1834_01 | 10 May 1834 circular | **Joint** signature Rigdon & Oliver Cowdery — mixed authorship. |
| oration_1838_01 | 4 Jul 1838, Far West pamphlet | Rigdon's Fourth of July oration (the "Salt Sermon" of June 1838 is not extant). Title-page box omitted. |
| appeal_1840_01 | *An Appeal to the American People* (Cincinnati, 1840) | Written by Rigdon on commission of the Nov 1839 Quincy conference (conference resolution box omitted). |
| appeal_1840_02 | 1840 Appeal, appendix | Memorial to the Missouri Legislature (Dec 1838) — collectively signed; Rigdon's sole authorship uncertain. |
| memorial_1844_01 | Times and Seasons 5 (1 Feb 1844) | Rigdon's Memorial to the Pennsylvania Legislature. |
| appeal_1863_01–04 | *An Appeal to the Latter-day Saints* (Philadelphia, 1863) | **Nominally by J. H. Newton, W. Richards, W. Stanley**; Broadhurst argues "probably entirely by Rigdon". Disputed and very late — use only as a flagged/late sample. |

## Cleaning
Plain text = the transcription box's text with images removed, masthead line ("Vol. II. Kirtland, Ohio, December, 1833. No. 15.") stripped (kept in documents.json) and page markers like "[p. 117]" / "(5)" removed. Original line breaks (Broadhurst's typographic lines) are kept; hyphen/space artifacts are not otherwise normalised. Headlines and "{Continued from our last.}" notes remain at the top of each file. Scripture quotations (heavy in Millennium/Gospel) are **not** removed — consider masking KJV quotations before stylometry.

## Documents
| file | masthead (periodical issue) | opening | words |
|---|---|---|---|
| text/millennium_01.txt | Vol. II. Kirtland, Ohio, December, 1833. No. 15. | Communicated for The Evening and the Morning Star, Millenium | 1093 |
| text/millennium_02.txt | Vol. II. Kirtland, Ohio, January, 1834. No. 16. | Communicated for The Evening and the Morning Star, MILLENIUM | 1785 |
| text/millennium_03.txt | Vol. II. Kirtland, Ohio, February, 1834. No. 17. | MILLENIUM. No. III. As all writers on the Millenium, up to t | 2013 |
| text/millennium_04.txt | Vol. II. Kirtland, Ohio, April, 1834. No. 19. | {For the Star.} Millenium. No. IV. THE Millenium is that imp | 4396 |
| text/millennium_05.txt | Vol. II. Kirtland, Ohio, May, 1834. No. 20. | {For the Star.} Millenium. No. V. IN the 24 chapter of Isaia | 3130 |
| text/millennium_06.txt | Vol. II. Kirtland, Ohio, June, 1834. No. 21. | Millenium. No. VI. {Continued from our last.} What proves th | 3072 |
| text/millennium_07.txt | Vol. II. Kirtland, Ohio, July, 1834. No. 22. | Millenium. No. VII. {Continued from our last.} Isaiah says i | 3760 |
| text/millennium_08.txt | Vol. II. Kirtland, Ohio, August, 1834. No. 23. | Millenium. No. VIII. {Continued from our last.} Having seen  | 3393 |
| text/millennium_09.txt | Vol. I. Kirtland, Ohio, November, 1834. No. 2. | M I L L E N I U M. No. IX. {Continued from the Star, No. 23. | 2615 |
| text/millennium_10.txt | Vol. I. Kirtland, Ohio, December, 1834. No. 3. | MILLENIUM. No. X. Continued from page 19. The apostasy of th | 1169 |
| text/millennium_11.txt | Vol. I. Kirtland, Ohio, January, 1835. No. 4. | MILLENIUM. No. XI. Continued from page 40. Having ascertaine | 1312 |
| text/millennium_12.txt | Vol. I. Kirtland, Ohio, February, 1835. No. 5. | MILLENIUM. No. XII. Continued from page 54. In the 144 Ps. w | 1279 |
| text/millennium_13.txt | Vol. I. Kirtland, Ohio, March, 1835. No. 6. | MILLENIUM. No. XIII. Continued from page 68. The sacred writ | 2239 |
| text/millennium_14.txt | Vol. I. Kirtland, Ohio, May, 1835. No. 8. | MILLENIUM. No. XIV. Continued from page 87. Every thing said | 1316 |
| text/gospel_01.txt | Vol. I. Independence, Missouri, April, 1833. No. 11. | THE GOSPEL. BY a reference to the last number of the Star, i | 6816 |
| text/gospel_02.txt | Vol. II. Kirtland, Ohio, September, 1834. No. 24. | THE GOSPEL, No. I. What ever difference may exist in the wor | 3204 |
| text/gospel_03.txt | Vol. I. Kirtland, Ohio, November, 1834. No. 2. | THE GOSPEL. No. II. (Continued from the last No. of the Star | 676 |
| text/gospel_04.txt | Vol. I. Kirtland, Ohio, December, 1834. No. 3. | THE GOSPEL. No. III. (Continued from page 21.) Mark gives th | 1167 |
| text/gospel_05.txt | Vol. I. Kirtland, Ohio, January, 1835. No. 4. | THE GOSPEL. No. IV. (Continued from page 39.) There never ou | 1228 |
| text/gospel_06.txt | Vol. I. Kirtland, Ohio, February, 1835. No. 5. | THE GOSPEL. No. V. (Continued from page 56.) There is one th | 3085 |
| text/gospel_07.txt | Vol. I. Kirtland, Ohio, March, 1835. No. 6. | THE GOSPEL. No. VI. (Continued from page 74.) Inasmuch then, | 1650 |
| text/gospel_08.txt | Vol. I. Kirtland, Ohio, May, 1835. No. 8. | THE GOSPEL. No. VII. (Continued from page 89.) There is noth | 1395 |
| text/gospel_09.txt | Vol. I. Kirtland, Ohio, June, 1835. No. 9. | THE GOSPEL. No. VIII. (Continued from page 120.) From reflec | 1402 |
| text/articles_letters_01.txt | Vol. II. Kirtland, Ohio, April, 1834. No. 19. | TO THE PUBLIC. I feel myself called upon to notice the condu | 514 |
| text/articles_letters_02.txt | Vol. I. Kirtland, Ohio, September, 1835. No. 12. | THE ANCIENT ORDER OF THINGS. The ancient order of things has | 2337 |
| text/articles_letters_03.txt | Vol. II. Kirtland, Ohio, November, 1835. No. 2. | ORDER OF THE NEW TESTAMENT CHURCH. No. I. Brother J. Whitmer | 1868 |
| text/articles_letters_04.txt | Vol. II. Kirtland, Ohio, January, 1836. No. 4. | For the Messenger and Advocate. BROTHER WHITMER: -- A short  | 3682 |
| text/articles_letters_05.txt | Vol. II. Kirtland, Ohio, February, 1836. No. 5. | Kirtland, November 15, 1835. Elder O. Barr, Dear Sir: -- A l | 3635 |
| text/articles_letters_06.txt | Vol. II. Kirtland, Ohio, March, 1836. No. 6. | Kirtland, March, 1836. Mr. O. Barr, Sir: -- Yours of Februar | 783 |
| text/articles_letters_07.txt | Vol. II. Kirtland, Ohio, April, 1836. No. 7. | For the Messenger and Advocate. Br. O. Cowdery. Sir: -- It a | 1908 |
| text/articles_letters_08.txt | Vol. II. Kirtland, Ohio, June, 1836. No. 9. | Kirtland, June, 1836. Mr. O. Barr: Sir -- I have received yo | 3222 |
| text/articles_letters_09.txt | Vol. III. Kirtland, Ohio, November, 1836. No. 2. | THE LATTER DAY GLORY. The subject of the latter day glory, h | 2626 |
| text/articles_letters_10.txt | Vol. III. Kirtland, Ohio, December, 1836. No. 3. | THE SAINTS AND THE WORLD. The opinions entertained by the wo | 5242 |
| text/articles_letters_11.txt | Vol. III. Kirtland, Ohio, January, 1837. No. 4. | PERSECUTION. The spirit of persecution has prevailed in ever | 2712 |
| text/articles_letters_12.txt | Vol. III. Kirtland, Ohio, March, 1837. No. 6. | PERSECUTION. Persecution has been the lot of the righteous s | 1936 |
| text/articles_letters_13.txt | Vol. III. Kirtland, Ohio, August, 1837. No. 11. | PROSPECTUS. For a new paper, to be published at Kirtland, Ge | 1771 |
| text/articles_letters_14.txt | Vol I. Kirtland, Ohio, October, 1837. No. 1. | Tere Haute, Ia. Oct. 13th, 1837. Brother Don C. Smith, Havin | 1021 |
| text/articles_letters_15.txt | Vol I. Far West, Mo., August, 1838. No. 4. | TO THE SAINTS ABROAD. In order that the object for which the | 1033 |
| text/dear_brethren_1834_01.txt | - | DEAR BRETHREN, -- IT becomes our duty to address you on the  | 1592 |
| text/oration_1838_01.txt | - | ORATION. ___________ Friends and Fellow Citizens: By your re | 5499 |
| text/appeal_1840_01.txt | - | AN APPEAL TO THE AMERICAN PEOPLE. _______________________ Th | 26070 |
| text/appeal_1840_02.txt | - | A P P E N D I X COPY OF A MEMORIAL TO THE LEGISLATURE OF MIS | 4507 |
| text/memorial_1844_01.txt | Vol. V. City of Nauvoo, Ill. February 1, 1844. No. 3. | TO THE HONORABLE, THE SENATE AND HOUSE OF REPRESENTATIVES OF | 4856 |
| text/appeal_1863_01.txt | - | [ iii ] AUTHORS' PREFACE. We have been induced to send forth | 447 |
| text/appeal_1863_02.txt | - | OUR APPEAL. __________ In presenting our appeal to our forme | 10091 |
| text/appeal_1863_03.txt | - | 40 SECTION VI. We commence this division of our appeal by tr | 5120 |
| text/appeal_1863_04.txt | - | 57 that the Lord has authorized us to believe, a question is | 4865 |

## Not obtained / known gaps
- **Pre-1830 (Baptist/Campbellite-era) Rigdon writings:** none located as transcribed primary text. Broadhurst's index has only a third-party *report* of a June 1830 Rigdon sermon (Millennial Harbinger) — not Rigdon's own words, not downloaded. No 1820s Rigdon sermon/letter text was found on sidneyrigdon.com or via web search.
- "To the Public" letters (Dec 1831/Jan 1832, Ohio newspapers), Quincy Whig letters (May 1839), Sangamo Journal (1842), 1844 Conference talk (T&S, reported by clerks and mixed with Broadhurst commentary), and the Pittsburgh *Messenger and Advocate* 1844–46 pages were **not** extracted (embedded in multi-article newspaper compilation pages or mixed with commentary).
- "Rise and Progress of the Church of Christ" (EMS 1833–35, "probably" Rigdon) and "Faith of the Church of Christ" (M&A 1834–36, "mostly" Rigdon) are not separated here; their raw text is in `../messenger_and_advocate_centerplace/` and `../evening_and_morning_star_centerplace/`.
- **Lectures on Faith** are in `../jsp_lectures_on_faith_1835/` (from the 1835 D&C on JSP), not here.
