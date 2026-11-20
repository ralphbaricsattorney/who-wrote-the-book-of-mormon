# Charles B. Thompson ("Baneemy"): cleaning record

Script: `prepare/two_register/clean_thompson_charles_b.py`
(run `~/miniconda3/envs/sr-theory/bin/python -I prepare/two_register/clean_thompson_charles_b.py [scripture|prose] [--report]`).
`--report` prints every cut and every detected quotation, with raw line numbers. All line numbers below are 1-based lines of the raw files, which are not modified.

| Output file | Side | Words |
|---|---|---|
| `scripture__laws_covenants.txt` | scripture | 21,418 |
| `scripture__proclamations.txt` | scripture (optional, see below) | 6,638 |
| `prose__evidences.txt` | prose | 32,249 |

**Words per side:** scripture 21,418 (revelations and laws only), or 28,056 if the proclamations are added. Prose 32,249.

Word counts are whitespace tokens of the output files.

---

## 1. `scripture__laws_covenants.txt`

**Source:** `data/raw/two_register_authors/thompson_charles_b/scripture/lawscovenantsofi00thom.djvu.txt`. This is *The Laws and Covenants of Israel … also Ephraim and Baneemy's Proclamations*, Preparation, Iowa, 1857 (IA `lawscovenantsofi00thom`). It is uncorrected OCR.

**Lines kept:** 2216–8271. This is Part Second ("Law and Covenants"), chapters V–XXX, plus the appendix revelation (12 March 1857, §743–745). The manifest range was 298–8201, which also covers Part First. Part First is written to its own file (§2). I extended the range past 8201 so that it takes in the appendix revelation.

**Contents kept:** the text of the numbered sections:
- the creed ("Faith of Israel", ch. V);
- the Blessing of Jacob (ch. VI), minus the Genesis verses;
- Thompson's first-person "Prophetic Vision" of 1 Sept 1845 (ch. VII);
- the two Constitutional Codes (ch. VIII);
- Thompson's two petitions and the answers to them (ch. IX);
- the revelations "by the voice of Baneemy", 1848–1857 (ch. X–XXVI, XXX and the appendix), including the Ten Covenants (forms of oath, ch. XIX);
- the vision of the clairvoyant and rapping spirits, with the treasury law that follows it (ch. XXVIII–XXIX).

**Removed:**
- The Erratum and an editorial note on the word "law" (2178–2203), and both Errata pages (8159–8201). The part title and all chapter headings and titles, such as "Revelation.", "How to Know the Chosen.", "Constitutional Codes", "Code First", the "Title 1.— Of Faith" headings, "Part One.—The Positive", "First Petition" and "ANSWER.".
- The editorial headnotes in the form "The word of the Lord came unto Chas. B. Thompson, by the voice of Baneemy, on the … day of …, saying:" (one per revelation), and the longer superscriptions of ch. XVII and XVIII.
- The headings of the Ten Covenants ("To be taken and subscribed under the administration of …").
- Signatures, places and dates, such as "(Signed,) CHAS. B. THOMPSON. St. Louis, Mo., June, 1852". Also the attestation of the cholera revelation: "Attested, and communicated to the President … by C. B. THOMPSON, Agent …" (4462–4475).
- Ch. XXVII (7037–7091): the Noachide commandments, which are traditional rabbinic material and not Thompson's, and the bare numbered list of the seven ordinances.
- Two quotations of Genesis set into the Blessing of Jacob: §201–205 (Gen 32:24–29, 168 words) and §213 (Gen 32:30). The blessing itself (§206–212) is Thompson's and is kept.
- Section numbers. There were 505 of them, as "§ 359." and its OCR forms ("6 212.", "$804.", "0 609.", "NG 208."), removed by pattern. One numbered section is one output paragraph.
- 137 running heads ("Ch. 18 LAW AND COVENANTS. 115") and 32 lines of OCR debris. Marginal specks at line ends are trimmed. Two damaged page feet were removed: 8240–8243 and the last lines of the appendix revelation (8272–8282).

**Not documents by others:** no minutes or documents by another hand are printed inside Part Second. The testimonies of the three Chief Pastoral Apostles and of the Twelve Apostles of Ephraim, which are signed by others, are in the front matter (lines 108–245) and are excluded with it.

**Words:** 26,474 raw tokens in lines 2178–8282; 2,039 removed by the explicit cuts; 21,418 out.

**OCR quality: fair, poor in patches.** 96.8% of word tokens of the output are known words, against 99.1% for the 1841 prose. Most pages read cleanly. Some pages have a damaged or cropped outer margin, and there the line ends are lost or garbled. Examples are ch. V §182–197 ("w hoi is | ove Gods", "empowsegs zee mind to shay Dione"), parts of ch. IX and XIII, and ch. XXX §702–704 ("CONGREGATION OVALS PRESBYTERY OF"). This damage was left in, because the protocol forbids correcting OCR. About 14 OCR-mangled section numbers survive (e.g. "9 5738.", "65/5."). Five samples of 200 words, taken at 10/30/50/70/90% through the file, were read. All five are Thompson's revelation or vision text, with no running heads or headnotes; the 90% sample falls on one of the damaged pages.

## 2. `scripture__proclamations.txt`

**Source:** the same file. **Lines kept:** 352–2171, which is Part First: ch. I, Ephraim's Proclamation (Jan. 1857); ch. II, Baneemy's 1st Proclamation (1848); ch. III, Baneemy's 2nd Proclamation "to all the Kings of the World" (1849); and ch. IV, the Chief Teacher's Proclamation (1850).

**Why a separate file:** these are Thompson's own words, but they are proclamations, not revelations. They are in an oratorical, scripture-tinged register that mixes long Bible paraphrase (Isaiah 28, 62; Micah 5) with plain exposition. The brief was to keep "the revelations' text" for the scripture side. I kept these chapters apart so that they can be added to the scripture side, or left out, deliberately.

**Removed:**
- Part and chapter headings, superscriptions and salutations ("Dear Brethren:—"), signatures with places and dates, Baneemy's 1849 attestation, and a bracketed citation of the D&C and *Times and Seasons* (763–766).
- §1–5 (316–351): Jeremiah 31:10–20, quoted verbatim.
- §35–37 (808–832): Revelation 12:14–16, quoted. Thompson's parenthetical glosses inside it go with it.
- §45 (902–925): the quotation from the Epistle of the Twelve of 23 Dec 1847, which is by another writer.
- §65 (1084–1090): Isaiah 28:15, quoted.
- Section numbers (160), running heads (42) and debris lines (9).

Unmarked KJV paraphrase woven into Thompson's sentences (§52–55, §66–69 and others) is kept, for the later KJV-masking step.

**Words:** 8,329 raw; 811 removed by cuts; 6,638 out.

**OCR quality: fair.** 97.3% of tokens are known words. Ch. III has a cropped margin over roughly §87–96 ("tha ave unto Abraham, Isaac ani on enitors"). Five 200-word samples were read: all are Thompson's proclamation text, with no headings or signatures.

## 3. `prose__evidences.txt`

**Source:** `data/raw/two_register_authors/thompson_charles_b/prose/evidencesinproof00thom_0.djvu.txt`. This is *Evidences in Proof of the Book of Mormon*, Batavia, N.Y., 1841 (IA `evidencesinproof00thom_0`).

**Lines kept:**
- 130–223: the Preface. It is by Thompson, who writes in the third person as "the writer".
- 244–9013: Part 1 (the evidences), Part 2 ("Objections answered and refuted") and the prose of the Appendix, "A Proclamation and Warning to the Gentiles who inhabit America".
- 9407–9462: Thompson's own introduction to Appendix No. 3, "American Antiquities".

**Excluded ranges:**
- 1–129: library stamp, title page and copyright entry (403 raw words).
- 224–243: debris and half-title.
- 9014–9404: verse, 1,438 words. This is the poem that closes the Proclamation and the two Acrostics, with their scripture-reference footnotes. It is Thompson's own, but it is verse.
- 9463–10022: the description of the ruins of Copan and of other cities, "copied from the Albany Weekly Journal" (Stephens). It is another writer's text (3,293 words), and Thompson's few footnotes go with it.
- 10023–10037: Errata.

### Page furniture

209 running heads were removed ("EVIDENCES IN PROOF OF THE", "BOOK OF MORMON.", "OBJECTIONS ANSWERED / AND REFUTED.", "A PROCLAMATION / AND WARNING.", "PART SECOND"), with their OCR variants. Also removed: 201 page-number and speck lines, and 16 debris lines. Words broken across a line end (by "¬" or "-") are rejoined. Paragraphs are rebuilt from short final lines. Bare parenthetical references of the form "(See Luke, 21st chapt. 24th verse.)" are dropped, and so are fragments of fewer than 3 words left between two removed quotations.

### Quotations

The book is largely a chain of quotations: Bible, Book of Mormon, Apocrypha, the Book of Enoch, and antiquarian and polemical writers. The rule applied: **any quoted passage longer than 20 words** (about 2.5 printed lines) is removed. Short inline quotations are kept, and so is Thompson's own argument, including scripture phrases he works into his own sentences. Quotations were found in three ways:

1. **Marked quotations.** A parser pairs each opening double quotation mark with the next closing mark. This includes the OCR forms of the marks: “ as "4 ‘" or "6 ‘", and ” as "77", "??", "/*" or "*7". 86 marked quotations of more than 20 words were removed (8,467 words). A bare "(" read as '("' is not treated as an opening mark.
2. **Quotations whose closing mark the OCR lost.** From the opening mark, the quotation is followed forward for as long as it matches verbatim scripture, stopping before the next opening mark. The scripture reference is the KJV Old and New Testaments, the Book of Mormon, the D&C and the PGP, from `data/raw/lds_scriptures_json`. A match is a word 5-gram, and up to 12 non-matching tokens are bridged for OCR damage and glosses. 33 such quotations were removed (7,405 words), mostly long Book of Mormon extracts in the Appendix.
3. **Unmarked verbatim scripture.** A run of at least 60 words matching scripture, or at least 30 words next to a stray quotation mark, was treated as a quotation whose marks were lost. 8 runs were removed (854 words): Isaiah 11, the Book of Ether's account of the great city, Isaiah 29:11–14, and 2 Nephi 28 in the Proclamation.

Quotations from writers other than scripture whose marks are garbled were found by reviewing every unclosed quotation that the parser reports. They are removed by explicit line cuts in the script (12 cuts, 4,948 raw words):
- 2 Esdras 13 (407–418);
- Elias Boudinot, twice (1236–1254, 1264–1275);
- Isaiah 45:8 and Deuteronomy 33:16, each with interleaved glosses (1381–1389, 1583–1591);
- Josiah Priest, *American Antiquities* (3841–3859);
- the circular of the Jews of Jerusalem from the *Morning Herald*, with the editor's note and the Bethdin certificate (4389–4639);
- a long extract from the Book of Enoch (4870–4988);
- E. D. Howe, *Mormonism Unvailed* (6441–6462);
- the *Quincy Whig* article with John Haven's letter and A. Badlam's certificate (6593–6711);
- Parley P. Pratt's testimony, copied from his pamphlet (6867–7056);
- a quoted poem in the Proclamation (8811–8828).

The other non-scripture quotations had intact marks and were removed by rule 1. These include:
- Boudinot and Col. James Smith on Indian traditions;
- Priest's descriptions of the Newark, Circleville and Lookout Mountain works;
- the Enoch title page and first extract;
- the Testimonies of the Three and of the Eight Witnesses;
- 2 Kings on the captivities;
- Howe's witnesses.

**Share of the book removed as quotation.** After page furniture was removed, the body in the kept ranges was about 54,100 words. Of these, 21,674 (**about 40%**) were removed as quotation: 4,948 by explicit cuts and 16,726 by rule. About 8,500 of the quotation words came out of the Appendix Proclamation, which is mostly Book of Mormon extracts; only about 2,400 words of Thompson's own Appendix prose survive. If the Copan description is counted (3,293 words, copied from a newspaper), quotation of others is about 25,000 words, or **about 42%** of the 1841 book's text after the title page. On top of this there are the 1,438 words of verse.

**Words:** 56,016 raw tokens in the kept ranges; 49,126 tokens left after furniture and the explicit cuts; 32,249 out.

### Doubtful points (prose)

- **Woven scripture is kept.** 32 runs (1,394 words, about 4% of the output) match scripture verbatim for 30–59 words with no quotation mark nearby. Reading them shows that they are Thompson's indirect speech or paraphrase inside his own sentences, e.g. "But Joshua the son of Nun, took it and smote the king thereof …" or "he says, that they send embassadors by the sea, even in vessels of bulrushes …". Following the protocol, they are left for the KJV-masking step. The heavily scriptural exposition of the Appendix Proclamation (2 Nephi 28 and Micah 5 turned into "you") is treated the same way, except for one 146-word verbatim run.
- **Boundaries can be off by a few words.** Where a closing mark was lost and the end of the quotation does not match the reference text (OCR damage, or the 1830/1837 Book of Mormon text differing from the modern text used for matching), a removal can stop a few words early or late. Examples are "of the house of Israel, the" at 1731 and "And again," at 531. A handful of quotation tails survive, such as the end of Isaiah 29:4 at 1400.
- **Quoted objections are kept.** Objections that Thompson puts in single quotation marks, e.g. 'if God had a new revelation to give to man, he would not have chosen …', are short and stated by Thompson himself, so they stay. Two longer double-quoted objections were removed by the 20-word rule (6192–6196, 29 words).
- **Some passages may not be Thompson's.** 6426–6588 (on D. P. Hurlburt and the Spalding story) uses "our society" and "Brother Smith". It reads as Thompson's own, but it may have been borrowed without marks from a church publication; I could not verify this.
- **Citation formulas remain** where they are part of a sentence ("Isaiah 11th Chapt. 11th and 12th verses:"). They raise the frequency of "chapt", "verse" and ordinal numbers. A few bare lead-ins remain as short paragraphs ("Again, page 523, 2d edition:").

**OCR quality: good.** 99.1% of word tokens of the output are known words. The manifest's dict_share is 0.977. Errors are scattered single letters ("saitli", "1" for "I", "w7e") and a few garbled lines, the worst being 7166–7170. Five samples of 200 words, at 8/27/46/65/84%, were read. All are Thompson's running argument, with no running heads, page numbers or block quotations. The 84% sample shows his paraphrase of Howe's claims, with short inline quotations of 15 words or fewer.

## Long s

Both books are American printings (1841, 1857) set without the long s. The script's check (see the protocol) finds 0 candidate tokens in the prose file, and 4 in the two scripture files: "confe", "yf", "gf" and "fouls", which are OCR noise and not long-s errors. **No long-s repair was applied (0 words changed)**, so there is no list of repairs.
