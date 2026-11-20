# Fetching the raw data

These scripts rebuild every `data/raw/<dir>` that the analysis reads from the original sites.
`../data/SOURCES.md` lists each directory with its source, edition and redistribution status.

## Requirements

Python 3.9 or later with `requests` and `lxml`. Run every script from the repository root. Each one writes
under `data/raw/`, skips files that are already there (so an interrupted run can simply be restarted), uses
one connection with a pause after every request, and identifies itself as `stylometry-research-script/1.0`.

## Order

The scripts do not depend on one another, so they can run in any order, or in parallel since each site gets
its own connection. This order puts the quick ones first:

| step | command | makes | requests, approx. time |
|---|---|---|---|
| 1 | `python fetch/direct_downloads.py` | `gutenberg/pg18.txt`, `pratt_parley/`, `lds_scriptures_json/`, `jockers_witten_criddle_2008_supplement/dataMatrix.txt`, the Aquarian Gospel and Strang files in `kjv_register_controls/` | 13, under a minute |
| 2 | `python fetch/archive_org.py` | Internet Archive OCR: `spalding_manuscript_story/`, `late_war_hunt_1816/`, `view_of_hebrews_ethan_smith/`, `kjv_pastiche_other/`, Oahspe and the Shaker Roll in `kjv_register_controls/`, `whitmer_address_1887/`, `lucy_mack_smith_1853/`, the three `campbell_*` directories, and the five authors in `two_register_authors/` (strang, white_richard_grant, thompson_charles_b, ilive, memminger) | 66, a few minutes |
| 3 | `python fetch/wikisource_bom1830.py` | `bom_1830_wikisource/` (117 chapters of the 1830 Book of Mormon) | about 140, 6 minutes |
| 4 | `python fetch/centerplace.py` | `messenger_and_advocate_centerplace/` and `evening_and_morning_star_centerplace/`, then `oliver_cowdery_periodical_writings/` built from them | 67, 2 minutes |
| 5 | `python fetch/sidneyrigdon_com.py` | `sidney_rigdon_broadhurst/`, `sidney_rigdon_broadhurst_additional/` | 19, under a minute |
| 6 | `python fetch/jsp.py` | the six `jsp_*` directories (Smith's early and later writings, Cowdery's letters, Revelation Books 1 and 2, the Book of Commandments, the Lectures on Faith) | about 1,360 pages, 30 minutes or more |
| 7 | `python fetch/chl_post_papers.py` | `sidney_rigdon_revelations_post_papers_chl/` (234 page images, 260 MB) | about 250, 10 minutes or more |

`fetch/jsp.py <dir> ...` fetches only the named directories. The JSP site has slowed to 20-35 s per page at
times; the script waits it out and can be restarted.

## Checking the result

`fetch/checksums.sha256` lists SHA-256 sums of the 812 files the study read. From the repository root:

    shasum -a 256 -c fetch/checksums.sha256      # or: sha256sum -c fetch/checksums.sha256

A mismatch means the source has changed since the study's download in November 2026. Project Gutenberg
revises its files, archive.org sometimes re-runs OCR, and the JSP and other sites correct their
transcriptions. `pipeline/01_build_corpus.py` and the two-register cleaners cut several OCR texts by line
number or by pattern, so a changed file can fail an assertion or shift a cut and will need checking by hand.
The JSP `text/*.meta.json` files are not in the list because they record the download date.

## What the scripts do not cover

- **Hand-made inputs.** Two inputs came from human judgement, not from a download. Both are stored here and
  copied into place:
  - `jsp/uris_smith_*.txt` and `jsp/uris_cowdery.txt` list the JSP documents fetched. The later-writings list
    came from screening page 1 of 4,141 JSP documents for Smith's handwriting, and those 4,141 screening
    requests are not repeated.
  - `jsp/composition_notes.tsv` records who composed each later document, judged from the JSP introductions.
- **Line ranges and slices.** The Cowdery letters are cut by hand-checked line ranges in `centerplace.py`.
  Four Rigdon items are cut by hand-written patterns in `sidneyrigdon_com.py`.
- **The Rigdon revelations text.** `chl_post_papers.py` fetches only the page images. The transcription the
  analysis uses was made from those images for this study and is not produced by any fetch script.
- **Unused files.** Only the files the analysis reads are fetched. Some original directories also held
  alternative scans or editions, and those are left out. So are the Book of Mormon manuscript images.

## Terms of use

Several sources do not allow redistribution: the Joseph Smith Papers transcriptions, the Church History
Library images, and the strangite.org text (see `../data/SOURCES.md`).
