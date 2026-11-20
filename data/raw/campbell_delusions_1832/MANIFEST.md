# Alexander Campbell, *Delusions. An Analysis of the Book of Mormon* (Boston: Benjamin H. Greene, 1832)

- **Source:** https://archive.org/details/delusionsanalysi00camp (University of Illinois copy).
- **Fetched:** 2026-11-12 from archive.org (metadata API + `_djvu.txt` OCR download) via `scripts/ia_get.sh` (or direct curl for items whose OCR filename contains spaces). Generic client.
- **Cleaning:** `*.clean.txt` made by `scripts/build_cowdery_and_ocr.py`: de-hyphenation across line breaks and joining of wrapped lines only. OCR errors, running heads, page numbers and library stamps are NOT removed. Raw OCR kept as `*.djvu.txt`.
- **Files:** `delusionsanalysi00camp.djvu.txt` (~10,100 words), `.clean.txt` (~9,950 words), `.metadata.json`.
- **Caveats:** Boston reprint of Campbell's Millennial Harbinger article of 7 Feb 1831, with a preface/notes by **Joshua V. Himes** (not Campbell) — strip before attributing. Contains many quotations from the Book of Mormon. Useful as a Campbell sample on the same subject matter, and as a contemporary religious "impostor".
