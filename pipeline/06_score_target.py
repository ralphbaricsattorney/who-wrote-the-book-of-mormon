"""Step 6: score the Book of Mormon once (article Fig 10).

The procedure is built from the whole development pool: five reference models and their reference scores. Every
Book of Mormon chunk gets, in text order:
  rank and compatibility for each ranked class (Smith, Rigdon, KJV, Hamilton), and the Smith-Rigdon set
  (Smith only, Rigdon only, both, neither)
  a similarity index for each descriptive candidate (Spalding, Pratt, Cowdery) against the biblical-style controls
The development controls (biblical-style texts, both men's revelations, the other controls) are scored by the same
procedure, so the reference lines in Fig 10 are like-for-like comparisons with the book.

Output: results/target_series_{kind}.csv, results/target_references_{kind}.parquet
Run:    python pipeline/06_score_target.py [F2|F1]
"""
import sys

import polars as pl

import config as C
from features import counts
from folds import training_pool
from model import build_procedure, ranks, similarity

DESCRIPTIVE = ["Solomon Spalding", "Parley P. Pratt", "Oliver Cowdery"]
RANKED = (C.SMITH, C.RIGDON, "KJV", "Hamilton")


def label(procedure, X, df: pl.DataFrame) -> pl.DataFrame:
    """Ranks, compatibility and the Smith-Rigdon set for the chunks in `df`."""
    classes = list(procedure[0].classes)
    ranked = [k for k in classes if k in RANKED]
    r = ranks(procedure, X[df["row"].to_numpy()])
    df = df.with_columns(*[pl.Series(f"rank {k}", r[:, classes.index(k)]) for k in ranked],
                         *[pl.Series(f"compatible {k}", r[:, classes.index(k)] > C.TAU) for k in ranked])
    sm, rg = pl.col(f"compatible {C.SMITH}"), pl.col(f"compatible {C.RIGDON}")
    return df.with_columns(pl.when(sm & rg).then(pl.lit("both")).when(sm).then(pl.lit("Smith only"))
                           .when(rg).then(pl.lit("Rigdon only")).otherwise(pl.lit("neither")).alias("set"))


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "F2"
    chunks = pl.read_parquet(C.PROC / "chunks.parquet").with_row_index("row")
    X = counts(chunks, kind)
    procedure = build_procedure(training_pool(chunks), X, seed=C.SEED + 9000)

    # ------------------------------------------------------------ the Book of Mormon, in text order
    target = (chunks.filter(pl.col("layer") == "target")
              .with_columns(pl.col("source_ids").list.first().alias("first_source"))
              .sort("first_source", "chunk_index").with_row_index("position"))
    chapters = (pl.read_parquet(C.PROC / "documents.parquet").filter(pl.col("role") == "target")
                .select("source_id", "bom_chapter_1830"))
    chapter_range = (target.select("chunk_id", pl.col("source_ids").alias("source_id")).explode("source_id")
                     .join(chapters, on="source_id")
                     .group_by("chunk_id").agg(pl.col("bom_chapter_1830").min().alias("chapter_from"),
                                               pl.col("bom_chapter_1830").max().alias("chapter_to")))
    series = label(procedure, X, target).select("position", "chunk_id", "bom_book", "bom_narrator", "^rank .*$",
                                                "^compatible .*$", "set").join(chapter_range, on="chunk_id", how="left")
    controls = [X[chunks.filter(pl.col("klass") == c)["row"].to_numpy()] for c in C.PSEUDO_BIBLICAL]
    rows = X[target["row"].to_numpy()]
    series = series.with_columns(*[pl.Series(f"similarity {k}", similarity(procedure, rows, controls, k))
                                   for k in DESCRIPTIVE]).sort("position")
    series.write_csv(C.RESULTS / f"target_series_{kind}.csv")

    # ------------------------------------------------------------ reference texts, scored by the same procedure
    refs = label(procedure, X, chunks.filter((pl.col("layer") == "development") & (pl.col("role") != "class"))).select(
        "chunk_id", "klass", "role", "unit_id", "chunk_index", "^rank .*$", "^compatible .*$", "set")
    refs.write_parquet(C.RESULTS / f"target_references_{kind}.parquet")

    with pl.Config(tbl_rows=40, tbl_width_chars=200, float_precision=2, fmt_str_lengths=50):
        print(series.group_by("set").len().sort("set"))
        print(series.select(pl.col("^compatible .*$").mean(), pl.col("^similarity .*$").mean()))


if __name__ == "__main__":
    main()
