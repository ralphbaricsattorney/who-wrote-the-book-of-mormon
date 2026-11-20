"""The training pool and its folds.

training_pool(chunks, extra)   development chunks of the classes the model learns, labelled by class
split(pool, k, seed)           k (train, held_out) pairs; a document never sits on both sides

How a class is split depends on how many units (documents, or bundles of short ones) it has:
  "unit"     15 or more: whole units go to folds
  "segment"  fewer: each work is cut into k contiguous segments, one per fold, and the training chunks next to a
             held-out segment are dropped. These classes appear in every training set.
"""
import polars as pl

MIN_UNITS_FOR_UNIT_SPLIT = 15


def training_pool(chunks: pl.DataFrame, extra: pl.DataFrame | None = None) -> pl.DataFrame:
    """Development chunks with `label` (the class) and `split_by`. `extra`: more chunks, each labelled by its klass."""
    pool = chunks.filter((pl.col("layer") == "development") & (pl.col("role") == "class"))
    if extra is not None:
        pool = pl.concat([pool, extra])
    return pool.with_columns(pl.col("klass").alias("label")).with_columns(
        pl.when(pl.col("unit_id").n_unique().over("label") >= MIN_UNITS_FOR_UNIT_SPLIT)
        .then(pl.lit("unit")).otherwise(pl.lit("segment")).alias("split_by"))


def folds(pool: pl.DataFrame, k: int, seed: int) -> pl.Series:
    """Fold number (0..k-1) per row of `pool`, stratified by class."""
    units = (pool.select("label", "unit_id").unique().sort("label", "unit_id")
             .with_columns(pl.int_range(pl.len()).shuffle(seed=seed).over("label").alias("unit_rank")))
    out = pool.join(units, on=["label", "unit_id"], how="left", maintain_order="left").with_columns(
        (pl.col("chunk_index").rank("ordinal").over("unit_id") - 1).alias("pos"),
        pl.len().over("unit_id").alias("n"))
    segment = (pl.col("pos") * k // pl.col("n") + pl.col("unit_rank")) % k     # contiguous, rotated per work
    return out.select(pl.when(pl.col("split_by") == "unit").then(pl.col("unit_rank") % k).otherwise(segment)
                      .cast(pl.Int8).alias("fold"))["fold"]


def buffers(train: pl.DataFrame, held_out: pl.DataFrame) -> pl.Series:
    """True for training chunks next to a held-out chunk of the same unit (segment splits only)."""
    neighbours = pl.concat([held_out.select("unit_id", pl.col("chunk_index") + d) for d in (-1, 1)]).unique()
    return train.join(neighbours.with_columns(pl.lit(True).alias("buffer")), on=["unit_id", "chunk_index"],
                      how="left", maintain_order="left")["buffer"].fill_null(False)


def split(pool: pl.DataFrame, k: int, seed: int):
    """Yield (j, train, held_out) for each of k folds, with buffer chunks removed from train."""
    pool = pool.with_columns(folds(pool, k, seed))
    for j in range(k):
        held_out, rest = pool.filter(pl.col("fold") == j), pool.filter(pl.col("fold") != j)
        yield j, rest.filter(~buffers(rest, held_out)).drop("fold"), held_out.drop("fold")
