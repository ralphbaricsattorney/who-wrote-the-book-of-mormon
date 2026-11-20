# Memminger: additional prose downloaded 2026-11-16

The existing MANIFEST.md is unchanged. These files were added to bring the plain-prose side above 20,000 words and closer in date to the 1830 *Book of Nullification*. They were fetched the same way as `scripts/ia_get.sh` fetches files: the Internet Archive metadata JSON and the `_djvu.txt` OCR file, saved as served (uncorrected OCR, nothing edited).

| File (in `prose/`) | Item | Date | Source | Rights | Words (raw) |
|---|---|---|---|---|---|
| `lecturedelivered00memm.djvu.txt` (+ `.metadata.json`) | C. G. Memminger, *Lecture delivered before the Young Men's Library Association, of Augusta, April 10th, 1851. Showing African slavery to be consistent with the moral and physical progress of a nation* (Augusta, Ga.: W. S. Jones, 1851), 25 pp. | 1851 | https://archive.org/details/lecturedelivered00memm (Library of Congress copy) | IA: NOT_IN_COPYRIGHT (1851) | 9,445 |
| `cu31924032767505.djvu.txt` (+ `.metadata.json`) | Henry D. Capers, *The Life and Times of C. G. Memminger* (Richmond: Everett Waddey, 1893), 604 pp. | 1893 | https://archive.org/details/cu31924032767505 (Cornell copy) | US public domain (1893); Cornell: "no known copyright restrictions" | 269,171 |

**What is usable from Capers.** The biography is by Capers, not by Memminger. Only the passages Capers reprints as Memminger's own texts are used (line ranges are in `scripts/two_register/clean_memminger.py`):

- lines 6575–7576: Memminger's argument for the State in *State v. Bank of South Carolina*, Court of Errors, Columbia, May 1843, which Capers takes from the 1844 printed report. This is a legal argument with case citations, and its first paragraph is the reporter's indirect speech.
- lines 7800–8022: Memminger's signed letter "To the People of South Carolina", *Charleston Mercury*, 8 March 1850.
- lines 8180–8585: Memminger's signed letter "To the People of St. Philip's and St. Michael's Parishes", 1850, which sums up his newspaper series against rechartering the Bank of the State.
- lines 9930–10873: Memminger's speech at the Co-operation meeting in Charleston, September 1851. Capers reprints it from the party's printed copy.
- lines 24121–25358 (Appendix pp. 490–515, "College Essays and Orations"): six student pieces from South Carolina College, c. 1817–1819, written at ages 14–16. Capers prints them from manuscripts lent by Memminger's son Edward. The Latin salutatory of December 1819 (lines 25087–25194) is excluded.
- lines 26293–27106 (Appendix pp. 532–548): "An Oration on the Bible", delivered before the Euphradian and Clariosophic Societies, South Carolina College, December 1842.

Not used from Capers:

- the speech "To afford aid to the Blue Ridge Railroad" (S.C. House, 1858; lines 25360–26286), which is the author's own text but is later than the other pieces and not needed;
- Governor McDuffie's message, which is not by Memminger;
- the Confederate Treasury letters and reports.

Capers also reprints *The Book of Nullification* in his appendix (around raw lines 28207–29100). That copy is a second witness to the scripture text, and he states the attribution on p. 107 (raw lines 5246–5258). Neither part is used as prose.

**Looked for but not downloaded.**

- No plain prose by Memminger from 1830–1840 itself was found as full text. For those years Capers gives only resolutions, a one-sentence toast (4 July 1831) and narrative. The nearest dated texts on either side of 1830 are the college orations (1817–19) and the 1842 and 1843 pieces above.
- *Mr. Memminger's opinion and reply upon the question of forfeiture of bank charters by reason of suspensions of specie payments* (Charleston: A. E. Miller, 1841) has page images at HathiTrust (https://catalog.hathitrust.org/Record/009782749). HathiTrust's text download sits behind a bot check, so it could not be fetched here. It would be the earliest substantial prose; it is a legal argument close in content to the 1843 text.
- *The mission of South Carolina to Virginia* (IA `missionofsouthca01memm`, `…02memm`) is another printing of the 1860 address, so it was not taken.
- The Confederate Treasury reports (1861–64) are official documents and were not taken.
