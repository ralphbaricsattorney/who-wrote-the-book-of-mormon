# Richard Grant White: cleaning record

Script: `prepare/two_register/clean_white_richard_grant.py` (run with `~/miniconda3/envs/sr-theory/bin/python`).
Raw folder: `data/raw/two_register_authors/white_richard_grant/`. Line numbers below are 1-based lines of the raw `.djvu.txt` files.
Word counts are whitespace tokens. "Before" is all tokens in the kept line range, so it includes running heads, notes, etc.

| Output file | Side | Words before | Words after |
|---|---|---:|---:|
| `scripture__new_gospel_of_peace.txt` | scripture | 79,145 | **60,397** |
| `prose__words_and_their_uses.txt` | prose | 127,913 | **108,345** |
| `prose__england_without_and_within.txt` | prose | 193,346 | **177,080** |
| **Scripture side total** | | | **60,397** |
| **Prose side total** | | | **285,425** |

Audit files in this folder, all written by the script:
- `removed_lines.tsv`: every raw line dropped, with the rule that dropped it (rows marked `*_KEPT` are kept text logged for checking).
- `removed_quotations.tsv`: every quoted span cut out of running prose, with the 160 characters before it.
- `wtu_line_end_joins.tsv`: every word rejoined across a line end in *Words and Their Uses*, where the OCR had lost the hyphen.
- `stats.json`: the counts used here.

## How the rules work (all three files)
The texts are split into pages at running heads, and the pages into blocks at blank lines. All three books set notes, chapter summaries, block quotations and footnotes in smaller type. In the OCR, smaller type shows up as longer lines: the body runs about 42–48 characters a line in the *Gospel*, 46–54 in *Words*, and 46–56 in *England*, while small type runs 52–60, 58–66 (with footnotes about 80) and 64–76 respectively. A block whose median line length passes the threshold for that work is removed. The thresholds are 49, 56 and 58. Other rules:
- Once a footnote starts, the rest of that page is a footnote zone. A footnote's continuation on the next page is caught by its line length; a short tail is caught by its position.
- Running heads, bare page numbers, signature marks, `CHAPTER` lines and short all-capital headings are dropped.
- Displayed verse is dropped. This covers a block of short lines that mostly begin with a capital, and a run of two or more such lines inside a paragraph.
- Blocks are rejoined into paragraphs across page breaks and stray marks. A paragraph continues when the next block starts in lower case or the previous block ends without closing punctuation.
- Lines are joined. A word hyphenated at a line end is joined without the hyphen if the joined form is a known word, or if either half is not a word. If both halves are words and the joined form is not, the hyphen is kept (`fiddle-maker`, `well-known`).
- Footnote reference marks (`*`, `^`, `†`) are removed.
- Spelling is not corrected or modernised. **Long s:** these are 1860s–1880s printings, with no long s. A check for `fuch/himfelf/faid/firft/fome/alfo` found 0 in every output, so no long-s repair was run and no words were changed.

## scripture__new_gospel_of_peace.txt
**Source.** *The New Gospel of Peace, according to St. Benjamin*, Books I–IV (1863–66), collected edition, American News Company, 1866. File: `scripture/newgospelofpeac00whit.djvu.txt` (IA `newgospelofpeac00whit`, Indiana State Library / Lincoln Financial Foundation copy).

**Choice of scan.** There are two scans of the same 1866 edition. The manifest's `newgospelpeace00white` is the LoC copy. I aligned the two line by line. Both are complete: 9,558 of about 10,750 non-blank lines are identical, and neither has a gap longer than 8 lines. On the lines where they differ, the Indiana scan has more dictionary words (6,688 against 6,530) and fewer non-words (1,107 against 1,271). Examples: it reads `Land`/`spoil`/`by`/`public` where the LoC scan has `Lmid`/`sfoil`/`bj`/`pubhc`. So the Indiana scan was used. Its line numbers differ from the manifest's (the body starts at 889, not 891).

**Range kept.** From the first `CHAPTER I.` of Book I (line 889) to the line before `END OF THE FOURTH BOOK.` (line 13228).
- Removed inside that range: **Note A** (lines 3494–3748) and **Note B** (lines 6511–6698). These are end-of-book notes that reprint newspaper reports, speeches and court affidavits.
- Removed after it: **Note C** (lines 13235–end), which reprints *World* editorials.
- Removed before it: the front matter, lines 1–888. This is the title page, the dedication, and the Publisher's Advertisement. The Advertisement includes the "U. Donough Outis" letter (White in persona, plain prose), press notices, and White's signed letter of 30 July 1866.

**Removed (words):**
- White's mock-exegetical footnotes (`Ver. N. …`), in small type at the foot of the page: 9,240, plus 139 in note tails. These are White's own words but in plain prose; they are **not** added to the prose side.
- Notes A and B: 2,969.
- Chapter summaries such as "1. The Mystery. 2. War in the Land of Unculpsalm. 5. Phernandiwud. …": 2,253. These are numbered fragments in small type, not running prose.
- Running heads: 1,953.
- Headings (`BOOK`, `CHAPTER`, `[Published …]`, half-titles): 109.
- Junk lines: 27.
- Verse numbers at the start of each verse: 1,144 stripped. OCR variants such as `1 1 .`, `ii.` and `lo.` are handled.

Each verse is written as its own paragraph. The first verse of each chapter keeps its printed capitals (`THE mystery …`, `NOW after …`).

**OCR quality: fair-good.** The five 200-word samples read cleanly as running text. Errors are sparse, for example `Iangkies` for `langkies` (capital I read for l, systematic in this scan) and stray spaces before punctuation (`peace ;`). Share of tokens in the system word list (macOS `/usr/share/dict/words`, which has few inflected forms, so the figure is lower than the manifest's) is 0.889. The punning invented names lower it a lot: Phernandiwud, Unculpsalm, Kopur-hedds, Tshivulree.

**Doubtful.**
- A footnote can contain verse quotations ("Ye whyte gals buy dere scente", "Say, darkies, have you seen de massa"). These are removed by the note-tail rules. I checked every block those rules dropped or kept: 7 kept blocks, 18 dropped lines.
- One running head was misread (`THE NEW GOSPEE OF PEACE. 39`). The head pattern now tolerates this. All-capital lines in the range were checked by hand and none are missed.

## prose__words_and_their_uses.txt
**Source.** *Words and Their Uses, Past and Present*. File: `prose/wordsandthieruses00whitrich.djvu.txt` (IA `wordsandthieruses00whitrich`). IA dates it 1872. The title page reads "New edition revised and corrected … 1876", and the book has "Afterthoughts and Forewords to the present edition", so this is the **revised edition**, not the 1870 first edition.

**Range kept.** Chapter I to the end of the Conclusion: lines 688–17623, as in the manifest. Excluded:
- Before line 688: White's own front matter (Afterthoughts, the dedication to Lowell, the Preface), the contents, and the epigraphs (Ascham, Hobbes, Tooke, Coleridge).
- After line 17623: Appendix I ("How the Exception Proves the Rule"), which is White's but set in small type; Appendix II ("Controversy"), which includes others' letters; and the index.

**Removed (words):**
- Block quotations in small type: 9,749. These are mostly examples quoted from other writers and newspapers.
- Footnotes: 1,970 + 886 (footnote zones).
- Running heads: 1,813.
- Displayed verse: 819.
- Headings: 207.
- Junk: 74.
- **Quoted examples longer than one sentence (or over 40 words) inside running text**: 31 spans, 1,211 words, listed in `removed_quotations.tsv`.

How the in-text quotation rule works:
- OCR quote marks (`''`, `,,`, `*'`, curly quotes) are normalised to `"`.
- A span between a pair of marks is cut if it holds more than one sentence or more than 40 words. Abbreviations such as `Mr.` and `St.` do not count as sentence ends.
- A following attribution (`— Letters, IV. 41.`) is cut with the span.
- A paragraph made of 80% or more quoted matter is dropped whole if it is longer than one sentence.
- A paragraph with an **odd** number of quote marks is left alone, because the pairing is unreliable there. Of 14 long "spans" that a naive pairing would find in such paragraphs, every one was White's own text between two unrelated marks.
- Quotations of a single sentence are kept, per the instructions.

**Line-end joins.** This scan has lost nearly all line-end hyphens: only 258 lines end in `-`, against 3,037 in *England*. Broken words (`lan / guage`, `re / ceived`) were rejoined using these rules:
- Join when the joined form is a known word and one half is not, or when neither half is a word.
- When both halves are words, join only when the joined form occurs at least 5 times and more often than the two-word sequence. This keeps `in deed`, `a long`, `final e` and `in en` apart.

Known words are the corpus vocabulary (`prepare/vocabulary.parquet` `text_norm`, at least 3 occurrences), plus words seen mid-line in White's three raw files, plus the system word list. There were 1,464 joins (`wtu_line_end_joins.tsv`). From inspecting the list, a few false joins remain (for example `direct or` → `director`, `in form` → `inform`), and a few true breaks stay split (for example `trust worthy`, `home stead`).

**OCR quality: fair-good.** The seven samples read as White's argument, with occasional OCR errors (`sarie`, `bettef`, `cf`, `azuful`, `undisfcllowshipable`). Italic words are sometimes garbled (`iccd-ivatcr`). Dictionary share is 0.907.

**Doubtful.**
- Single-sentence quoted examples remain, as the instructions allow. Some keep their attribution (`— Chap. LXIX.`).
- Removing quotations leaves White's lead-ins hanging ("Mr. Marsh himself has this passage: — But here …").
- About 5% of characters in the prose are still inside quotation marks, mostly cited words and phrases.
- Some single-line examples that were set in small type are removed together with the block quotations.

## prose__england_without_and_within.txt
**Source.** *England Without and Within* (1881). File: `prose/englandwithoutwi01whit.djvu.txt` (IA `englandwithoutwi01whit`, Houghton Mifflin printing, IA date 1900), complete in one volume (chapters I–XXV).

**Range kept.** From `CHAPTER I.` (line 441) to the line before `THE END` (line 23997). Excluded: the title page and contents before line 441, and the bindery and deacidification notices after line 23997.

**Removed (words):**
- Footnotes (numbered `1`, set in small type): 4,542 + 1,330 (footnote zones).
- Running heads: 2,547.
- Block quotations in small type: 2,060.
- Displayed verse: 387.
- Headings: 161.
- Junk: 49.
- Long in-text quotations by other writers: 5 spans, 452 words. These are Frances Power Cobbe, Fielding's *Joseph Andrews*, Thackeray, the song "Wapping Old Stairs", and the Church Catechism.

The script found every in-text quotation over 60 words (in paragraphs with an even number of quote marks) and I read each one. Most are **White's own letters home**, which he quotes ("The view from Richmond Hill …", "At all these 'great houses' …"), or **conversations he reports** with English people. Both are his own writing and are **kept**, under the protocol's "dialogue the author wrote". Only the five by others are cut. They are named by their opening words in `ENGLAND_QUOTES_BY_OTHERS` in the script.

**OCR quality: fair-good.** The six samples read cleanly as White's travel narrative and essay, with scattered OCR errors: `Bhall`, `dutj`, `tare` for `rare`, `>elf-respect`, `ot"` for `of`, and `B` for `S` at word starts. Dictionary share is 0.905.

**Doubtful.**
- Some of White's own letters are printed in the small type the book uses for quotations, for example the "letter written home" about the parks and the Canterbury letter. Those were removed with the other small-type blocks: roughly 1,000–1,500 words of his prose lost, not mixed in.
- Reported dialogue (English speakers' words as White recalls them) is kept.

## Not used
- `prose/nationalhymnsho02whitgoog.djvu.txt` (*National Hymns*, 1861). White's essay is interleaved throughout with the competition hymns and anthems by others that it discusses, so it is not cleanly separable. The prose side is large without it, so it was left out.
- `scripture/newgospelpeace00white.djvu.txt`: the second scan of the same edition, with slightly worse OCR (see above).

## Checks done
For each output file, at least five 200-word passages spread evenly through it were read: 5 from the *Gospel*, 7 from *Words*, 6 from *England*. All were the author's running text. None contained page furniture, running heads, verse numbers or footnote matter.

Further checks:
- I searched the scripture output for footnote vocabulary ("Ver.", "the author", "this book", "Mr.", "manuscript", "commentator", digits). Only scripture-voice text came up.
- I searched all outputs for running-head strings ("WORDS AND THEIR USES", "WITHOUT AND WITHIN", "GOSPEL OF PEACE.", "CHAPTER [IVX]"). Only legitimate in-text uses came up.
- I checked the first and last paragraphs of each file against the book.
