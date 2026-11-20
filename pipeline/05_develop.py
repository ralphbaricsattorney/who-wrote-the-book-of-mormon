"""Step 5: how well the rule works on text whose author is known (article Figs 8 and 9). Development text only.

Two kinds of run, each building a full procedure (five reference models) and ranking text it never saw:
  eval0..eval4     Question 1. Built without one fifth of every class's documents; ranks those documents, and every
                   development control (biblical-style texts, both men's revelations, the other controls).
  minus::<author>  Question 2. Built without one author; ranks that author's text: an author the model never saw.

Output: results/dev_ranks_{kind}.parquet, one row per run x chunk x class
Run:    python pipeline/05_develop.py [F2|F1]
"""
import sys
import time

import polars as pl

import config as C
from features import counts
from folds import split, training_pool
from model import build_procedure, ranks

N_EVALUATION_FOLDS = 5
REMOVABLE = ("single_author", "attributed")        # only real authors are removed, not collections


def rank_run(run: str, procedure, X, texts: pl.DataFrame, group: str) -> pl.DataFrame:
    """Rank `texts` against every class with one procedure: one row per chunk x class."""
    assert texts["layer"].unique().to_list() == ["development"], "only development text is scored here"
    r = ranks(procedure, X[texts["row"].to_numpy()])
    ident = texts.select("chunk_id", "klass", "unit_id", "chunk_index").with_columns(
        pl.lit(run).alias("run"), pl.lit(group).alias("group"))
    return pl.concat(ident.with_columns(pl.lit(k).alias("class"), pl.Series("rank", r[:, i]))
                     for i, k in enumerate(procedure[0].classes))


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "F2"
    C.RESULTS.mkdir(parents=True, exist_ok=True)
    chunks = pl.read_parquet(C.PROC / "chunks.parquet").with_row_index("row")
    X = counts(chunks, kind)
    pool = training_pool(chunks)
    controls = chunks.filter((pl.col("layer") == "development") & (pl.col("role") != "two_register")  # step 7 scores those
                             & ~pl.col("chunk_id").is_in(pool["chunk_id"].implode()))
    rows = []

    t0 = time.time()
    for e, build, held_out in split(pool, N_EVALUATION_FOLDS, C.SEED - 1):
        procedure = build_procedure(build, X, seed=C.SEED + 100 * e)
        rows.append(rank_run(f"eval{e}", procedure, X, held_out, "same_author"))
        rows.append(rank_run(f"eval{e}", procedure, X, controls, "control"))
        print(f"eval{e}: built on {build.height} chunks, ranked {held_out.height} held-out + {controls.height} control "
              f"chunks ({time.time() - t0:.0f}s)", flush=True)

    sources = pl.read_parquet(C.PROC / "units.parquet").select("unit_id", "source_type")
    authors = (pool.join(sources, on="unit_id").group_by("label")
               .agg(pl.col("source_type").is_in(REMOVABLE).all().alias("ok")).filter("ok")["label"].sort().to_list())
    for a in authors:
        procedure = build_procedure(pool.filter(pl.col("label") != a), X, seed=C.SEED + 1000 + len(a))
        texts = pool.filter(pl.col("label") == a).drop("label", "split_by")
        rows.append(rank_run(f"minus::{a}", procedure, X, texts, "removed_author"))
        print(f"minus::{a}: ranked {texts.height} chunks ({time.time() - t0:.0f}s)", flush=True)

    pl.concat(rows).write_parquet(C.RESULTS / f"dev_ranks_{kind}.parquet")
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
