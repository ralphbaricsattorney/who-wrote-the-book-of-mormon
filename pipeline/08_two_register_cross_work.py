"""Step 8: the two-register study with a cross-work reference. Development text only.

In step 7 a two-register author's reference comes from segments of the same works the author was trained on. That
reference is too tight: even an unseen prose work by the author fails. Here the reference is built across works.

Scripture-style text and controls. For each two-register author A with two or more prose works, and each of A's works
u, one model is trained on the step-7 pool (all classes, every two-register author's prose) without u; u's chunks,
scored by it, are A's reference from u. rank_A(x) = average over u of the share of u's chunks at least as atypical
as x, each comparison under the model that held u out (works as folds).

Unseen prose (authors with three or more works). Each work o is held out of everything: for every other work u, a
model is trained without o and u, u's chunks under it are the reference, and o's chunks are ranked against it under
the same model. o is scored exactly as scripture-style text is, by a procedure that never saw it.

Output: results/two_register_cross_work_ranks.parquet, results/two_register_cross_work.md
Run:    python pipeline/08_two_register_cross_work.py
"""
import time

import numpy as np
import polars as pl

import config as C
from features import counts
from folds import training_pool
from model import fit_reference_model, score_chunks

KIND = "F2"
SCRIPTURE = {a: f"{a} (scripture)" for a in C.TWO_REGISTER} | {C.SMITH: C.SMITH_REVELATIONS,
                                                                 C.RIGDON: C.RIGDON_REVELATIONS}
author_of = {v: k for k, v in SCRIPTURE.items()}


def long(df: pl.DataFrame, scores: np.ndarray, i: int, **tags) -> pl.DataFrame:
    """Scores of `df`'s chunks for one class, one row per chunk."""
    return df.select("chunk_id").with_columns(pl.Series("value", scores[:, i].astype(np.float64)),
                                              *[pl.lit(v).alias(k) for k, v in tags.items()])


def rank(pairs: pl.DataFrame) -> pl.DataFrame:
    """Share of each reference work at least as atypical as the chunk, averaged over works."""
    return (pairs.group_by("author", "chunk_id", "model").agg((pl.col("ref") >= pl.col("value")).mean())
            .group_by("author", "chunk_id").agg(pl.col("ref").mean().alias("rank")))


def table(title: str, df: pl.DataFrame, note: str = "") -> list[str]:
    """A titled markdown table, with an optional note."""
    with pl.Config(tbl_formatting="MARKDOWN", tbl_hide_dataframe_shape=True, tbl_hide_column_data_types=True,
                   tbl_rows=200, tbl_cols=20, fmt_str_lengths=70, float_precision=2, tbl_width_chars=300):
        return [f"## {title}", ""] + ([note, ""] if note else []) + [str(df), ""]


def main():
    t0 = time.time()
    chunks = pl.read_parquet(C.PROC / "chunks.parquet").with_row_index("row")
    dev = chunks.filter(pl.col("layer") == "development")
    X = counts(chunks, KIND)

    prose = dev.filter(pl.col("klass").is_in(C.TWO_REGISTER))
    pool = training_pool(chunks, extra=prose)
    works = (prose.group_by("klass").agg(pl.col("unit_id").unique().sort()).filter(pl.col("unit_id").list.len() >= 2)
             .sort("klass"))
    scored = pl.concat([
        dev.filter(pl.col("klass").is_in(list(author_of)))
        .with_columns(pl.col("klass").replace_strict(author_of).alias("speaker"), pl.lit("scripture").alias("text")),
        dev.filter(pl.col("klass").is_in(C.PSEUDO_BIBLICAL))
        .with_columns(pl.col("klass").alias("speaker"), pl.lit("biblical control").alias("text")),
    ])
    assert scored.join(pool, on="chunk_id").height == 0, "a scored chunk is in the training pool"

    # ---------------------------------------------------------------- one model per held-out work
    ref_rows, x_rows, outer_ref, outer_x = [], [], [], []
    for n, (author, author_works) in enumerate(works.iter_rows()):
        for j, w in enumerate(author_works):
            held = pool.filter(pl.col("unit_id") == w)
            m = fit_reference_model(pool.filter(pl.col("unit_id") != w), X, seed=C.SEED + 6000 + 10 * n + j)
            i = int(np.flatnonzero(m.classes == author)[0])
            ref_rows.append(long(held, score_chunks(m, X[held["row"].to_numpy()]), i, author=author, model=w))
            x_rows.append(long(scored, score_chunks(m, X[scored["row"].to_numpy()]), i, author=author, model=w))
            print(f"{author} without {w}: {held.height} reference chunks, setting {m.setting} "
                  f"({time.time() - t0:.0f}s)", flush=True)
        if len(author_works) < 3:
            continue
        for j, o in enumerate(author_works):                  # o is held out of every model and reference below
            target = pool.filter(pl.col("unit_id") == o)
            for k, u in enumerate(w for w in author_works if w != o):
                held = pool.filter(pl.col("unit_id") == u)
                m = fit_reference_model(pool.filter(~pl.col("unit_id").is_in([o, u])), X,
                                        seed=C.SEED + 7000 + 100 * n + 10 * j + k)
                i = int(np.flatnonzero(m.classes == author)[0])
                outer_ref.append(long(held, score_chunks(m, X[held["row"].to_numpy()]), i, author=author, outer=o, model=u))
                outer_x.append(long(target, score_chunks(m, X[target["row"].to_numpy()]), i, author=author, outer=o, model=u))
                print(f"{author}, {o} held out, without {u} ({time.time() - t0:.0f}s)", flush=True)
    ref, xs = pl.concat(ref_rows), pl.concat(x_rows)

    # ---------------------------------------------------------------- ranks
    reference = ref.select("author", "model", pl.col("value").alias("ref"))

    scripture_ranks = rank(xs.join(reference, on=["author", "model"])).join(
        scored.select("chunk_id", "klass", "speaker", "text"), on="chunk_id")
    other_work_ranks = (
        pl.concat(outer_x).join(pl.concat(outer_ref).select("author", "outer", "model", pl.col("value").alias("ref")),
                                on=["author", "outer", "model"])
        .group_by("author", "outer", "chunk_id", "model").agg((pl.col("ref") >= pl.col("value")).mean())
        .group_by("author", "outer", "chunk_id").agg(pl.col("ref").mean().alias("rank"))
        .rename({"outer": "klass"}).with_columns(pl.col("author").alias("speaker"), pl.lit("other work").alias("text")))
    ranked = (pl.concat([scripture_ranks, other_work_ranks], how="diagonal")
              .with_columns((pl.col("rank") > C.TAU).alias("accepted")))
    ranked.write_parquet(C.RESULTS / "two_register_cross_work_ranks.parquet")

    # ---------------------------------------------------------------- measures
    own = ranked.filter(pl.col("speaker") == pl.col("author"))
    scripture = own.filter(pl.col("text") == "scripture").group_by("author").agg(
        pl.len().alias("scripture_chunks"), pl.col("accepted").mean().alias("scripture_recall"))
    per_work = own.filter(pl.col("text") == "other work").group_by("author", "klass").agg(pl.len().alias("chunks"),
                                                                                          pl.col("accepted").mean())
    other_work = per_work.group_by("author").agg(pl.len().alias("works"), pl.col("accepted").mean().alias("other_work_recall"))
    false_acceptance = (ranked.filter((pl.col("text") != "other work") & (pl.col("speaker") != pl.col("author")))
                        .group_by("author", "speaker").agg(pl.col("accepted").mean())
                        .sort("accepted", descending=True).group_by("author", maintain_order=True)
                        .agg(pl.col("accepted").mean().alias("register_false_acceptance"),
                             pl.col("speaker").first().alias("worst_other"), pl.col("accepted").first().alias("worst_rate")))
    summary = (scripture.join(other_work, on="author", how="left").join(false_acceptance, on="author")
               .with_columns((pl.col("scripture_recall") - pl.col("register_false_acceptance")).alias("margin"))
               .select("author", "works", "other_work_recall", "scripture_chunks", "scripture_recall",
                       "register_false_acceptance", "margin", "worst_other", "worst_rate")
               .sort("author"))

    lines = [f"# Two-register study, cross-work reference: features {KIND}, threshold {C.TAU}", "",
             "Development text only. Scripture-style text is ranked against each prose work under the model that held that "
             "work out. Each prose work (authors with three or more) is held out of every model and reference, then "
             "ranked the same way.", ""]

    lines += table("Per author", summary,
                   "`other_work_recall`: each prose work, held out of every model and reference, accepted as the author; works "
                   "count equally; authors with three or more works only. `scripture_recall`: the author's scripture-style text "
                   "accepted as the author. `register_false_acceptance`: other authors' scripture-style text and the biblical-style "
                   "controls accepted as the author, each text counting once.")
    lines += table("Each prose work", per_work.sort("author", "klass").rename({"klass": "work"}))
    (C.RESULTS / "two_register_cross_work.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
