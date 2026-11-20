# So Who Wrote the Book of Mormon? Code

Code and results for the essay [So Who Wrote The Book of Mormon? Machine Learning Redux](https://goflaw.substack.com/p/so-who-wrote-the-book-of-mormon-machine). It is an open-set stylometric re-test of the Spalding–Rigdon theory: Jockers et al. (2008), answered by Schaalje et al. (2011).

## Layout

```
fetch/        download the sources into data/raw           (fetch/README.md)
prepare/      clean the two-register texts; assemble Rigdon's revelations from page transcriptions
pipeline/     the analysis, steps 1-10
figures/      the article's figures (fig03 ... fig10) and the scripts that draw them
results/      outputs of steps 5-10
data/         raw sources, prepared texts, processed tables  (data/SOURCES.md)
```

| Step | What it does | Article |
|---|---|---|
| `01_corpus.py` | Cleans each source to its author's own words. Masks quotations: any 15+ word run shared with the KJV, the Book of Mormon or another source | Data |
| `02_units.py` | Groups documents into units; each takes its fixed layer from `layers.tsv` | Figs 5, 6 |
| `03_normalize.py` | Lowercases, strips punctuation, maps manuscript spellings to print | Data |
| `04_chunks.py` | Cuts 1,000-word chunks | Fig 5 |
| `05_develop.py` | Q1: holds out a fifth of each class's documents. Q2: leaves one author out at a time | Figs 7, 8, 9 |
| `06_score_target.py` | Scores the Book of Mormon once, and the reference texts with the same model | Fig 10 |
| `07_two_register.py`, `08_two_register_cross_work.py` | Tests whether an author's scripture-style text is recognized from their prose | Fig 5 |
| `09_jockers.py` | Reproduces Jockers et al.'s Table 1 exactly, on their published data | Fig 2 |
| `10_article_numbers.py` | Recomputes every number the article quotes and checks it | `results/article_numbers.md` |

Feature set F2 (primary) keeps the 223 function words in `pipeline/words.py` and masks every other word, including King James forms such as *thee*, *unto* and *behold*. F1 keeps those forms; the article mentions it as a robustness check. Joseph Smith's class is what he composed alone. Each document's tier comes from its Joseph Smith Papers introduction and is listed in `pipeline/smith_tiers.tsv`.

About a quarter of each large class is held back from development. Those documents are the "audit" layer in `pipeline/layers.tsv`; this release never scores them.

## Running it

Python 3.11. Install the dependencies with `pip install -r requirements.txt`. Then:

```sh
# 1. The sources are in data/raw. To download them again from the original sites, see fetch/README.md.
# 2. Run everything from the repository root:
sh run_all.sh
```


`prepare/vocabulary.parquet` is a frozen word list that the OCR repairs in `prepare/` use. It was taken from one corpus build, because the cleaned texts feed the corpus.

Two inputs can't be downloaded by script. Rigdon's revelations were transcribed by hand from the Church History Library page images (`prepare/rigdon_protocol.md`); `fetch/` downloads the images, not the transcription. The selection of later Joseph Smith Papers documents and the composition notes ship in `fetch/jsp/`. `data/SOURCES.md` lists each source, where it comes from and whether it may be redistributed.
