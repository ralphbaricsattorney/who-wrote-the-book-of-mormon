"""Step 9: reproduce Jockers, Witten & Criddle (2008) on their own published matrix (the article's Fig 2).

The recipe is the paper's section 4:
  words in every author's samples and in the Book of Mormon (521) -> mean relative frequency >= 0.1% (114)
  -> minus god, ye, thy, behold (110) -> relative frequencies -> each column centred and scaled over all
  456 samples -> nearest shrunken centroids (R package pamr) with all 110 words kept.

Two settings are not stated in the paper and were found by matching its results:
  THRESHOLD = 0.25   a small shrinkage that still keeps all 110 words (zero shrinkage does not reproduce it)
  equal priors       every author equally likely beforehand (pamr's default, class proportions, does not)
With these the first-choice counts match exactly and Alma 52 matches to four decimals.

Target: the paper's Table 1 first choices, and Alma 52 (chapter 147) as corrected in January 2009.

Output: results/jockers_replication.md
Run:    python pipeline/09_jockers.py
"""
import numpy as np
import polars as pl

import config as C

THRESHOLD = 0.25
REMOVED = ["god", "ye", "thy", "behold"]
AUTHOR = {"Cowdrey": "Cowdery", "Spaulding": "Spalding", "Isaiah": "Isaiah-Malachi", "Malachi": "Isaiah-Malachi"}
APPENDIX_B = """a after again against all among an and are as at away be because been before but by came children come day
did do down earth even every father for forth from go great had hand have he her him his i if in into is it king know
land made man many may me men might more my name no not now o of on one or our out over pass people power said say
shall should so son that the their them then there therefore these they things this those thus time to up upon us was
we were when which who will with words would you your""".split()
PUBLISHED = {"Rigdon": 93, "Isaiah-Malachi": 63, "Spalding": 52, "Cowdery": 20, "Pratt": 9, "Longfellow": 2, "Barlow": 0}

SRC = C.RAW / "jockers_witten_criddle_2008_supplement" / "dataMatrix.txt"   # their published data, CC BY 3.0


# ---------------------------------------------------------------- nearest shrunken centroids, as in pamr
def nsc_probabilities(X, y, X_new, threshold, equal_priors=True):
    """Tibshirani et al. (2002): class probabilities for X_new, and the number of words still in use."""
    classes, n = np.unique(y), len(y)
    overall = X.mean(0)
    centroid = np.stack([X[y == k].mean(0) for k in classes])
    size = np.array([(y == k).sum() for k in classes])
    s = np.sqrt(sum(((X[y == k] - centroid[i]) ** 2).sum(0) for i, k in enumerate(classes)) / (n - len(classes)))
    s = s + np.median(s)
    m = np.sqrt(1 / size - 1 / n)[:, None]
    d = (centroid - overall) / (m * s)
    d = np.sign(d) * np.maximum(np.abs(d) - threshold, 0)             # shrink towards the overall centroid
    shrunken = overall + m * s * d
    prior = np.full(len(classes), 1 / len(classes)) if equal_priors else size / n
    used = np.abs(d).sum(0) > 0                                       # words shrunk away for every author drop out
    score = ((((X_new[:, None, :] - shrunken[None]) / s) ** 2)[:, :, used]).sum(-1) - 2 * np.log(prior)
    p = np.exp(-(score - score.min(1, keepdims=True)) / 2)
    return classes, p / p.sum(1, keepdims=True), int(used.sum())


def run(relative, selected, author, number, threshold, equal_priors):
    """First-choice counts per author, Alma 52's probabilities, the words in use, and every chapter's probabilities."""
    known, bom = author != "Unknown", author == "Unknown"
    x = relative[:, selected]
    x = (x - x.mean(0)) / x.std(0, ddof=1)                             # over all 456 samples, as in the paper
    classes, p, n_words = nsc_probabilities(x[known], author[known], x[bom], threshold, equal_priors)
    first = classes[p.argmax(1)]
    chapter = number[bom]
    return {a: int((first == a).sum()) for a in classes}, dict(zip(classes, p[chapter == 147][0])), n_words, p


def main():
    # ---------------------------------------------------------------- the published matrix and the paper's word selection
    words = np.array(SRC.open().readline().replace('"', "").split())
    raw = pl.read_csv(SRC, separator="\t", has_header=False, skip_rows=1, quote_char='"', infer_schema_length=0)
    sample = raw[:, 0].to_numpy()
    counts = raw[:, 1:].cast(pl.Float64).to_numpy()
    name = np.array([t.rstrip("0123456789") for t in sample])
    number = np.array([int(t[len(n):]) for t, n in zip(sample, name)])     # sample number within its author
    author = np.array([AUTHOR.get(n, n) for n in name])
    known, bom = author != "Unknown", author == "Unknown"
    size = counts.sum(1)                                                   # words in each sample
    relative = counts / size[:, None]

    # The paper's three-step word selection
    everywhere = np.all([counts[author == a].sum(0) > 0 for a in np.unique(author)], axis=0)
    frequent = everywhere & (relative.mean(0) >= 0.001)
    selected = frequent & ~np.isin(words, REMOVED)

    lines = ["# Replication of Jockers, Witten & Criddle (2008) on their published matrix", "",
             f"Samples: {known.sum()} of known authorship, {bom.sum()} Book of Mormon chapters.", "",
             "## Word selection", "",
             "| Step | Paper | Here |", "|---|---|---|",
             f"| In every author's samples and in the Book of Mormon | 521 | {everywhere.sum()} |",
             f"| Mean relative frequency at least 0.1% | 114 | {frequent.sum()} |",
             f"| Minus god, ye, thy, behold | 110 | {selected.sum()} |", "",
             f"Words here but not in the paper's Appendix B: {sorted(set(words[selected]) - set(APPENDIX_B)) or 'none'}. "
             f"In Appendix B but not here: {sorted(set(APPENDIX_B) - set(words[selected])) or 'none'}.", ""]

    variants = {
        f"Threshold {THRESHOLD}, equal priors": (THRESHOLD, True),
        "No shrinkage, equal priors": (0.0, True),
        f"Threshold {THRESHOLD}, priors by class size": (THRESHOLD, False),
    }
    results = {v: run(relative, selected, author, number, *args) for v, args in variants.items()}
    lines += ["## First-choice chapters, seven authors", "",
              "The paper's Table 1 predates the January 2009 correction, which moved Alma 52 (chapter 147) from Rigdon "
              "to Spalding. The published matrix is the corrected one, so the counts to match are Rigdon 92 and Spalding 53.", "",
              "| Author | Paper, corrected | " + " | ".join(variants) + " |", "|---|---|" + "---|" * len(variants)]
    corrected = PUBLISHED | {"Rigdon": 92, "Spalding": 53}
    for a in corrected:
        lines.append(f"| {a} | {corrected[a]} | " + " | ".join(str(results[v][0].get(a, 0)) for v in variants) + " |")
    lines.append("| Words in use | 110 | " + " | ".join(str(results[v][2]) for v in variants) + " |")
    lines.append("| Alma 52: Rigdon | 0.4626 | " + " | ".join(f"{results[v][1]['Rigdon']:.4f}" for v in variants) + " |")
    lines.append("| Alma 52: Spalding | 0.46525 | " + " | ".join(f"{results[v][1]['Spalding']:.4f}" for v in variants) + " |")
    exact = results[f"Threshold {THRESHOLD}, equal priors"][0] == corrected
    lines += ["", f"**The first column reproduces the published result {'exactly' if exact else 'only approximately'}.** "
              "The paper does not state the threshold or the priors; both were found by matching.", ""]

    # How confident are the forced choices? (the closed-set problem in one number)
    top = results[f"Threshold {THRESHOLD}, equal priors"][3].max(1)
    lines += ["## How confident the forced choices are", "",
              f"Every chapter must go to one of the seven. The winning probability is above 0.5 for {(top > 0.5).mean():.0%} "
              f"of chapters, above 0.9 for {(top > 0.9).mean():.0%}, and its median is {np.median(top):.2f}. "
              "These probabilities say which author is nearest, not whether any author is near.", ""]

    C.RESULTS.mkdir(parents=True, exist_ok=True)
    (C.RESULTS / "jockers_replication.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
