# Strang: cleaning record (prose side)

Script: `prepare/two_register/clean_strang.py`. Run it with `~/miniconda3/envs/sr-theory/bin/python`.
It also writes `removed_lines.tsv` (every removed raw line with its reason) and `stats.json`.
The scripture side, the *Book of the Law of the Lord*, is already in the corpus and was not touched.

## Outputs

| file | words |
|---|---|
| `prose__michilimackinac.txt` | 31,810 |
| `prose__diary_1831_36.txt` | 17,009 |
| `prose__prophetic_controversy.txt` | 17,808 |
| `prose__diamond_epistles.txt` | 4,565 (poor OCR, use with caution) |

Prose side total: **71,192 words**. Excluding the Diamond file, the total is 66,627. Words are whitespace tokens.

**Common rules for all four files**
- Removal is by explicit raw-line ranges plus rules for page furniture.
- Lines where fewer than half the tokens are words are dropped as OCR debris.
- Runs of spaces are collapsed.
- Wrapped lines are joined, and line-end hyphens are rejoined when the joined word is in the corpus vocabulary or a half is not a word. A spaced stray dash between two whole words is dropped.
- A blank line counts as a paragraph break only after sentence-final punctuation.
- Spelling is never corrected.
- No long-s problem arises in any of these files: they are 19th- and 20th-century printings.

**Sources not used**
- `afk0709.0001.001.umich.edu.djvu.txt` is a worse scan of the 1854 first printing of *Michilimackinac*.
  - I compared it word by word with the 1885 reprint. It contains no Strang prose beyond one clause (afk 5585–5587, on Garden Island's harbor).
  - Including it would duplicate the work.
  - Its end matter is errata plus "Notices of the Press" by others, all from 1853.
- `ancientmodernmic00stra` is a third scan of the same work.
- `secondary_quaife_1930` was not used for any text.

## 1. `prose__michilimackinac.txt`

**Source.** `ancientmodernm1885stra.djvu.txt`, *Ancient and Modern Michilimackinac* (1854), in the 1885 St. Ignace reprint. It is laid out in two columns.

**Kept.** Raw lines 54–5917, from "The name of the Island of Michilimacki-nac…" to "…its growth must be as rapid as it is long delayed."

**Correction to the recorded bounds.** Line 5882, "SUPPLEMENT.", is only the 1885 running head of the page on which the Supplement begins. Strang's text, the Pine River section and the CONCLUSION, runs on to 5917. The Supplement by others starts at 5920 ("The foregoing was published in pamphlet form in 1854…") and is excluded.

**Words.** 33,314 in the raw range, 31,810 after cleaning.

**What was removed**
- Lines 1–53: the 1885 title pages.
- 64 section-heading lines, such as "NAME." and "WINTER OF 1851-2." (187 words). Lines 4880–4881, OCR "THE MORMONS the TERVERSION OF REGAL AUTHORITY.", look like a heading but are small capitals inside a sentence, so they were kept.
- Lines 230–253 (123 words): Charlevoix's opinion of the Jesuit Relations, a block quotation. The lead-in fragment on line 229 was trimmed.
- Lines 5113–5301 (113 words): the islands table, which is only names and figures and is OCR debris.
- Page furniture (231 words): 47 running heads ("MICHILIMACKINAC AND THE MORMONS." in many garbled forms), page numbers and "UPB" stamps.
- Margin bleed: single characters at line starts and ends, such as "j", "|" and "I". The leading ones were removed only at listed lines, because a leading "I" is often the real pronoun.
- One garbled line.

**Repaired**
- Line 1739, OCR "•y-", was set to "ty.". It is the end of "socie-ty."
- "Com •" was rejoined.

**Content.** There are no letters, affidavits or newspaper extracts by others in the body; resolutions and charges are paraphrased. The book is Strang's own third-person narrative ("Mr. Strang"). The 1854 errata are already worked into the 1885 text, and I found no 1885 interpolations.

**OCR.** Fair; the manifest's dict_share is 0.946. I read five 200-word samples, at words 3.1k, 9.4k, 15.8k, 22.2k and 28.5k. All were running text with no furniture or editorial matter.
- There are about one to three character errors per ten lines: "thecount}^ f)f Emmet", "custod3%", "witnes5.;es", "w'aked" for "waked".
- Some words are split by spaces: "Wis cousin", "im provement".
- No long stretches are garbled.

## 2. `prose__diary_1831_36.txt`

**Source.** `diary00stra.djvu.txt`, *The Diary of James J. Strang*, deciphered and annotated by Mark A. Strang (Michigan State University Press, 1961).

**Licence.** The manifest flags this edition as possibly still in copyright. Quaife's 1930 public-domain transcription exists, but I did not use it.

**Kept.** Raw lines 2187–5237, from "[May] 29th. To day I read seven hours in [V]olney's…" to "OLD BOOK FAREWELL."
- The editor's title and year heading (2183, 2186) are excluded.
- So are everything before them: the foreword by R. B. Nye, the editor's preface and introduction, and facsimiles.
- So is everything after 5237: the last footnote and the annotated bibliography from 5286.
- The recorded end of 5285 overshot by about 48 lines of editor's text.

**Words.** 21,189 in the raw range, 17,009 after cleaning.

**What was removed**
- 38 blocks of editor's footnotes, holding 43 notes (3,200 words). These sit at the foot of each page, and some continue across pages. They are listed in the script.
- 43 editor's footnote markers glued to words ("mankind.®", "consent.24", "Mills)?®"), stripped by line number.
- Page numbers "[N]", and a photostat plate with its caption (2887–2952).
- Strang's 23 page-top name-and-date lines ("JAMES J. STRANG JAN. 9TH 1833"). These are not prose and often split sentences.
- Editor's year headings and bracketed titles ("[TWENTIETH BIRTHDAY]", "[LA FAYETTE]"), bracketed years inside dates ("[1834]"), the gloss "[Racine, Wisconsin]", and a gap marker.
- Date-only lines and short captions ("OLD TIMES.", "HANOVER").
- Verse (103 words of Strang's own): satirical couplets, and the free-verse ending of the La Fayette eulogy. The eulogy's prose part is kept.
- A list of books with prices.
- Verse by others (294 words):
  - Byron's *Childe Harold* IV.124;
  - Byron's *Manfred* I.i, which the editor took to be Strang's;
  - two quoted poems, on Time and on Spring.

**Kept with change.** The editor's square-bracket restorations of Strang's words, such as "[V]olney" and "do[zen]", keep their words with the brackets removed. There are about 200 bracket pairs in the range, counting those removed with footnotes. The OCR had read the restored "l" in "shal[l]" as "1"; this was set right.

**Kept as is.** Dates that open entries ("Jan. 3d. This morning…") are Strang's own and were kept. So are his archaic spellings ("allmost", "writen", "schollars").

**Check.** Searching the output for "Strang" returns nothing, which confirms no third-person editor's prose survives.

**OCR.** Good: a clean modern typeset edition. I read five 200-word samples, at words 1.6k, 5k, 8.4k, 11.8k and 15.2k. All were Strang's first-person diary with no editorial matter. OCR errors in the kept text are rare.

## 3. `prose__prophetic_controversy.txt`

**Source.** `propheticcontr1878stra.djvu.txt`, *The Prophetic Controversy*, Strang's letter to Mrs Corey dated Saint James, 26 Sept. 1854, in the 1878 reprint.

**Kept.** Raw lines 12–5170, from "[Dear Sister —] Your good sister, Mrs. Derby…" to "…especially with the love of the truth."
- The title, dateline and salutation (1–11) are excluded.
- So are the signature (5172–5174) and the OCR junk and errata slip after it.

**Correction to the recorded bounds.** The recorded range of 6–1585 was wrong. Line 1585 is the signature of Strang's 1846 note to Hyde and Taylor, quoted inside a footnote. The letter continues to page 49 of 49, so the whole letter is used.

**Words.** 28,788 in the raw range, 17,808 after cleaning.

**What was removed**
- **Footnotes and furniture (9,235 words).**
  - All reprint footnotes were removed. They run at the foot of each page, and the OCR interleaves them with the text as separate blocks, often continued across pages. Their line ranges are listed in the script.
  - Some notes carry "— Ed." or are dated "Now (1855)". One duplicates an editorial note in *The Diamond*. Most quote documents by others: George Miller's letter, the Twelve's epistle, the Winter Quarters minutes, the Joseph Smith "letter of appointment", the angel's ordination revelation, a Brigham Young sermon, the Dunn and Taylor letters, and the Hyde/Taylor reply.
  - Running heads ("PROPHETIC CONTROVERSY." and variants) and page numbers.
- **Block quotations and documents (1,168 words).**
  - Doctrine and Covenants extracts (145–246, 3854–3868).
  - The certificate of the four witnesses to the Voree plates (4726–4765).
  - The Southport Telegraph extract (4795–4826).
  - Orson Hyde's squib from the Millennial Star (4932–4949).
- **Footnote markers and margin marks.** Footnote markers in the text ("*", and daggers read as "f", "t", "J", "§") and margin bars ("|", "j", "!") were stripped at listed lines.
- **Kept.** Short scripture citations and quotations of a few lines inside Strang's argument were kept.

**Known residue.** On a few pages the OCR read two columns side by side, at 786–792, 1898–1900, 2733–2783, 3301–3329, 3504, 3927–3973 and 4613–4660. In these places every word is Strang's, but the line order alternates between the two halves. Bag-of-words features are unaffected; n-grams across those lines are not reliable. The script does not reorder them.

**OCR.** Good; about 97% of kept tokens are valid. I read five 200-word samples, at words 1.7k, 5.2k, 8.8k, 12.4k and 15.9k. All were Strang's argumentative letter with no footnote matter. Errors are scattered: "w"ords", "l)e", "Avillfully", "2^r€senti".

## 4. `prose__diamond_epistles.txt`

**Source.** `diamondbeinglawo02stra.djvu.txt`, *The Diamond* (Voree, 1848).

**What was kept.** Only Strang's own signed plain prose: parts of two epistles, between raw lines 496 and 1071.
- **Pastoral letter** (signed Voree, 25 Dec. 1845):
  - Lines 496–574 keep the argument on succession, with the Doctrine and Covenants quotation at 575–587 removed.
  - Lines 589–714 keep the rest of the argument and the exhortation.
- **"The True Shepherd to the Saints Emigrating from Great Britain"** (signed Voree, 1848): lines 777–1071 are kept, with these removals:
  - the shredded lines 875–886;
  - the Doctrine and Covenants quotations at 931–933, 939–942 and 1019–1039;
  - margin bleed at line starts.

**What was excluded**
- Title and front matter.
- Chapter I, Doctrine and Covenants extracts (scripture).
- Chapter II, the "letter of appointment" attributed to Joseph Smith.
- Chapter III, the ordination revelation.
- The unsigned editorial notes (303–377, 1080–1107). These are probably Strang's, but that is not certain.
- The pastoral letter's opening (460–494), which is written in Pauline epistolary idiom ("I wist ye are not ignorant", "Suffer me", "I beseech you").
- Its closing prophetic warnings (716–753), in biblical cadence ("The cloud which surrounds by day shall bewilder…", "Causeless the curse…"), which are scripture-style.
- The Hebrews-style opening sentence of the second epistle (766–774).
- Page numbers.

**Words.** 5,767 in the raw range, 4,565 after cleaning.

**OCR.** Poor and uneven; 92% of the remaining tokens look like clean words. I read five samples.
- All were Strang's argument.
- Lines 510–523, 616–632 and 834–872 are heavily corrupted, for example "'J he Twelve are a trnvelinu and noi a lociil .•^r 'general high council".
- Facing-page bleed leaves junk at some line ends (998–1017).
- Raising the garble threshold only fragmented the text without removing the noise, so the standard threshold was kept.
- **Recommendation:** treat this file as optional. Use it only if a few thousand extra words matter more than the noise.
