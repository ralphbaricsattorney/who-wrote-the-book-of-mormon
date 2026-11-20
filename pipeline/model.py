"""Reference models, scores and ranks: the compatibility rule.

A *procedure* is five reference models built from one set of training chunks. Reference model j is trained without
fold j and scores fold j: those are the reference scores, text by each class's own authors that the model never saw.
A new chunk is scored by each model and compared only with the fold that model held out.

score   1 - P(class | chunk): higher means less like the class
rank    the share of class k's held-out units that score at least as high as the chunk. A chunk is compatible with k
        when its rank is above TAU = 0.10, i.e. it looks at least as much like k as k's least typical 10% of writing.

build_procedure(pool, X)                         -> list of five ReferenceModel
ranks(procedure, X_rows)                         -> (chunks x classes) ranks
similarity(procedure, X_rows, controls, k)       -> per chunk, how much more like class k it looks than control text
"""
from dataclasses import dataclass

import numpy as np
import polars as pl
from joblib import Parallel, delayed

from config import SEED
from features import Features
from folds import split
from solver import ElasticNetLogit

N_REFERENCE_FOLDS, N_TUNING_FOLDS = 5, 4
GRID = [(float(c), l1) for l1 in (0.2, 0.8) for c in np.logspace(-3, 2.6, 8)]   # (C, L1 ratio)
RETRY_ITERATIONS = 6000


def weights(df: pl.DataFrame) -> np.ndarray:
    """Classes count equally; within a class, units count equally. Scaled to sum to the number of rows."""
    w = df.select((1 / (pl.col("label").n_unique() * pl.col("unit_id").n_unique().over("label")
                        * pl.len().over("unit_id"))).alias("w"))["w"].to_numpy()
    return w * len(w) / w.sum()


def fit_checked(c, l1, X, y, w, init=None) -> ElasticNetLogit:
    """Fit; if the iteration budget runs out, continue once from where it stopped."""
    m = ElasticNetLogit(c, l1).fit(X, y, w, init=init)
    if not m.converged_:
        m = ElasticNetLogit(c, l1, max_iter=RETRY_ITERATIONS).fit(X, y, w, init=m)
    return m


def fit_path(X, y, w) -> list[ElasticNetLogit]:
    """One fit per GRID setting, each warm-started from the previous, more heavily penalized, solution."""
    fits = []
    for c, l1 in GRID:
        start = fits[-1] if fits and fits[-1].l1_ratio == l1 else None
        fits.append(fit_checked(c, l1, X, y, w, init=start))
    return fits


@dataclass
class ReferenceModel:
    features: Features
    clf: ElasticNetLogit
    setting: tuple                  # the chosen (C, L1 ratio)
    reference: pl.DataFrame = None  # label, unit_id of the held-out fold's chunks
    reference_scores: np.ndarray = None

    @property
    def classes(self) -> np.ndarray:
        return self.clf.classes_


def fit_reference_model(train: pl.DataFrame, X, seed: int) -> ReferenceModel:
    """Choose the setting by cross-validation within `train`, then fit on all of it. Nothing outside `train` is used."""
    y = train["label"].to_numpy()

    def tune_fold(tr, ho):
        f = Features().fit(X[tr["row"].to_numpy()], tr["label"].to_numpy())
        fits = fit_path(f.transform(X[tr["row"].to_numpy()]), tr["label"].to_numpy(), weights(tr))
        Xho = f.transform(X[ho["row"].to_numpy()])
        return ho, [m.predict_log_proba(Xho) for m in fits], fits[0].classes_, [m.converged_ for m in fits]

    folds_out = Parallel(n_jobs=N_TUNING_FOLDS)(
        delayed(tune_fold)(tr, ho) for _, tr, ho in split(train, N_TUNING_FOLDS, seed))
    held = pl.concat([f[0] for f in folds_out])
    classes = folds_out[0][2]
    assert all((f[2] == classes).all() for f in folds_out), "a class is missing from a tuning fold"
    truth, w_held = np.searchsorted(classes, held["label"].to_numpy()), weights(held)
    loss = [-(w_held * np.concatenate([f[1][g] for f in folds_out])[np.arange(len(truth)), truth]).mean()
            for g in range(len(GRID))]
    eligible = np.all([f[3] for f in folds_out], axis=0)       # converged in every tuning fold
    assert eligible.any(), "no setting converged in every tuning fold"
    best = [g for g in np.argsort(loss) if eligible[g]][0]

    features = Features().fit(X[train["row"].to_numpy()], y)
    clf = fit_checked(*GRID[best], features.transform(X[train["row"].to_numpy()]), y, weights(train))
    assert clf.converged_, f"the reference model did not converge (residual {clf.residual_:.2g})"
    assert (clf.classes_ == classes).all()
    return ReferenceModel(features, clf, GRID[best])


def score_chunks(m: ReferenceModel, X_rows) -> np.ndarray:
    """(chunks x classes): 1 - P(class), higher means less like the class."""
    return 1 - m.clf.predict_proba(m.features.transform(X_rows))


def build_procedure(pool: pl.DataFrame, X, seed: int = SEED) -> list[ReferenceModel]:
    """Five reference models from `pool` (needs columns row, label, unit_id, chunk_index, split_by)."""
    procedure = []
    for j, train, ref in split(pool, N_REFERENCE_FOLDS, seed):
        m = fit_reference_model(train, X, seed + 1 + j)
        print(f"  reference model {j}: C={m.setting[0]:.3g}, L1 ratio {m.setting[1]}", flush=True)
        m.reference = ref.select("label", "unit_id")
        m.reference_scores = score_chunks(m, X[ref["row"].to_numpy()])
        procedure.append(m)
    return procedure


def ranks(procedure: list[ReferenceModel], X_rows) -> np.ndarray:
    """rank_k(x): the share of class k's held-out units that score at least as high as x. Each comparison is made under
    the model that held the reference unit out, and each unit counts once."""
    classes = procedure[0].classes
    n_units = {k: sum(m.reference.filter(pl.col("label") == k)["unit_id"].n_unique() for m in procedure) for k in classes}
    out = np.zeros((X_rows.shape[0], len(classes)))
    for m in procedure:
        s_x = score_chunks(m, X_rows)
        label = m.reference["label"].to_numpy()
        unit_weight = m.reference.select((1 / pl.len().over("unit_id")).alias("w"))["w"].to_numpy()
        for i, k in enumerate(classes):
            ref = m.reference_scores[label == k, i]
            if len(ref) == 0:
                continue
            order = np.argsort(ref)
            at_least = np.concatenate([np.cumsum(unit_weight[label == k][order][::-1])[::-1], [0.0]])
            out[:, i] += at_least[np.searchsorted(ref[order], s_x[:, i], side="left")]
    return out / np.array([n_units[k] for k in classes])


def tail_share(ref: np.ndarray, x: np.ndarray) -> np.ndarray:
    """For each x: share of ref strictly above x, plus half the share equal to it."""
    ref = np.sort(ref)
    above = len(ref) - np.searchsorted(ref, x, side="right")
    equal = np.searchsorted(ref, x, side="right") - np.searchsorted(ref, x, side="left")
    return (above + equal / 2) / len(ref)


def similarity(procedure: list[ReferenceModel], X_rows, controls: list, k: str) -> np.ndarray:
    """For classes too small to have a compatibility line (Spalding: one work). The probability that a chunk looks more
    like k than a random chunk of a biblical-style control does, averaged over the controls (each counting once) and the
    five models. 0.5: no more like k than the controls; 1: more like k than all of them.
    `controls`: one row-matrix of chunks per control author."""
    i = int(np.flatnonzero(procedure[0].classes == k)[0])
    out = np.zeros(X_rows.shape[0])
    for m in procedure:
        s_x = score_chunks(m, X_rows)[:, i]
        out += np.mean([tail_share(score_chunks(m, c)[:, i], s_x) for c in controls], axis=0)
    return out / len(procedure)
