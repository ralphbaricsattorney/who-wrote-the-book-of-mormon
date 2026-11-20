# Cleaning protocol: two-register authors

Goal: for each author, plain text of the author's own words in each register, with everything else removed,
produced by a script so the cleaning can be rerun and checked.

## Inputs
Raw files in `data/raw/two_register_authors/<author>/{scripture,prose}/`. Read
`data/raw/two_register_authors/MANIFEST.md` and `body_bounds_counts.tsv` first: they record where each
body starts and ends and the known problems. Never modify anything under `data/raw/`.

## Outputs
- `scripts/two_register/clean_<author>.py`: a script that reads the raw files and writes the outputs below.
  Python standard library, plus polars if needed. Run it with `~/miniconda3/envs/sr-theory/bin/python`.
  Cleaning is done by line ranges and pattern rules in the script, never by hand-editing output files.
- `data/prepared/two_register/<author>/<side>__<work>.txt`: one file per work, where `<side>` is
  `scripture` or `prose` and `<work>` is a short slug. Plain UTF-8 text, paragraphs separated by a blank line.
- `data/prepared/two_register/<author>/CLEANING.md`: for each output file, the source, the line range kept,
  what was removed and why, words before and after, and a judgement of OCR quality from reading samples.

## Keep
The author's own running text: narrative, argument, dialogue the author wrote, and Bible quotations that
are part of the author's own sentences (a later step masks runs that match the King James Bible).

## Remove
1. Title pages, tables of contents, indexes, errata, advertisements, publishers' and printers' notices.
2. Anything by someone else: editors' introductions, prefaces and notes; footnotes; reviewers; appended
   documents, letters or testimonies by others; long quotations of other writers (a block quotation, or a
   passage the author introduces as someone else's and that runs more than a few lines).
3. Page furniture: running heads, page numbers, signature marks, catchwords, line numbers.
4. Verse and chapter numbers and chapter headings or summaries added by an editor. Keep chapter headings
   the author wrote only if they are prose; drop bare numbering.
5. OCR debris: lines that are mostly non-letters, scanning-library boilerplate, garbled fragments.

## Repair
- Join words hyphenated across line ends, and join wrapped lines within a paragraph.
- Long s: in eighteenth-century scans OCR often reads the long s as "f" ("fuch", "himfelf"). If a file shows
  this, repair it conservatively: replace "f" with "s" in a word only when the word is not in the reference
  word list and the repaired form is. Build the reference list from the corpus vocabulary,
  `prepare/vocabulary.parquet` (corpus words occurring 3 or more times). Report how many
  words were changed and list the 30 most frequent repairs in `CLEANING.md`.
- Do not otherwise correct spelling or OCR errors. Do not modernize.

## Check
Before finishing, read at least five passages of 200 words from each output file, spread through it, and
confirm they are the author's running text with no page furniture or editorial matter. Report the words per
output file and per side.
