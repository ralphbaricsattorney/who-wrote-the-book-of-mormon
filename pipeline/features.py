"""Feature sets. F2 (primary): the 223 modern function words, every other word masked. F1: F2 plus King James forms.

Two stages, so that nothing is fitted on text outside a model's training rows:
  counts(chunks, kind)   tokenization only: 1-3 word n-gram counts for every chunk. No labels, no selection.
  Features.fit(...)      vocabulary choice and scaling, fitted on the training rows passed in.

Every chunk has exactly 1000 words, so a count is already a rate per 1000 words.
"""
from dataclasses import dataclass

import numpy as np
import polars as pl
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer

from words import ARCHAIC, W

MASK = "_"                                    # stands in for every word that is not kept
KEEP = {"F1": W, "F2": W - ARCHAIC}
MAX_FEATURES = 3000
MIN_CHUNK_SHARE = 0.02                        # a feature must occur in this share of training chunks
MIN_CLASSES = 3                               # ... and in at least this many classes
PREFILTER_DF = 10                             # looser than any training rule, so it loses nothing


def counts(chunks: pl.DataFrame, kind: str) -> sparse.csr_matrix:
    """N-gram counts for every chunk, rows in the order of `chunks`."""
    keep = KEEP[kind]
    texts = [" ".join(w if w in keep else MASK for w in t.split(" ")) for t in chunks["text"]]
    vec = CountVectorizer(token_pattern=r"\S+", ngram_range=(1, 3), lowercase=False, min_df=PREFILTER_DF)
    X = vec.fit_transform(texts).tocsr()
    informative = np.array([any(tok != MASK for tok in n.split(" ")) for n in vec.get_feature_names_out()])
    return X[:, informative]


@dataclass
class Features:
    """Vocabulary and scaling, fitted on training rows only."""
    cols: np.ndarray = None
    mean: np.ndarray = None
    sd: np.ndarray = None

    def fit(self, X: sparse.csr_matrix, labels: np.ndarray) -> "Features":
        present = (X > 0).astype(np.int32)
        df = np.asarray(present.sum(0)).ravel()
        n_classes = sum((np.asarray(present[labels == c].sum(0)).ravel() > 0).astype(int) for c in np.unique(labels))
        ok = np.flatnonzero((df >= MIN_CHUNK_SHARE * X.shape[0]) & (n_classes >= MIN_CLASSES))
        self.cols = np.sort(ok[np.argsort(-df[ok], kind="stable")[:MAX_FEATURES]])
        Z = np.sqrt(X[:, self.cols].toarray())
        self.mean, self.sd = Z.mean(0), Z.std(0) + 1e-9
        return self

    def transform(self, X: sparse.csr_matrix) -> np.ndarray:
        return ((np.sqrt(X[:, self.cols].toarray()) - self.mean) / self.sd).astype(np.float32)
