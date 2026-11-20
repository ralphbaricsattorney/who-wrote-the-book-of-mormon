# Alexander Campbell (ed.), *The Millennial Harbinger*, vol. 1 (Bethany, Va., 1830)

- **Source:** https://archive.org/details/millennialharbinger1830 ("The Millennial Harbinger (1830)").
- **Fetched:** 2026-11-12 from archive.org (metadata API + `_djvu.txt` OCR download) via `scripts/ia_get.sh` (or direct curl for items whose OCR filename contains spaces). Generic client.
- **Cleaning:** `*.clean.txt` made by `scripts/build_cowdery_and_ocr.py`: de-hyphenation across line breaks and joining of wrapped lines only. OCR errors, running heads, page numbers and library stamps are NOT removed. Raw OCR kept as `*.djvu.txt`.
- **Files:** `millennialharbinger1830.djvu.txt` (~385,000 words), `.clean.txt` (~382,000 words), `.metadata.json`.
- **Caveats:** periodical edited by Campbell with substantial contributions from others (correspondents, Walter Scott, reprints) and long scripture quotations; also includes Campbell's "Extra" numbers. Campbell's "Delusions" analysis of the Book of Mormon appeared in vol. 2 (1831) — see `../campbell_delusions_1832/` instead. Only this one volume downloaded (scope: "one or two volumes is enough").
