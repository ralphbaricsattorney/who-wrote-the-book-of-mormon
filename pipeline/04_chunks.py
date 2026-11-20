"""Step 4: cut 1000-word chunks inside each unit.

A unit's documents are joined in date order and cut into consecutive 1000-word chunks; the remainder is
dropped. No chunk holds text from two units. The Book of Mormon is chunked by book, in 1830 order.

Output: data/processed/chunks.parquet: one row per chunk, with its unit's class, layer and kind
"""
import polars as pl

import config as C


def main():
    docs = (pl.read_parquet(C.PROC / "documents.parquet")
            .filter(pl.col("role") != "twin")
            .select("doc_id", "source_id", "role", "date_key", "order", "bom_book", "bom_narrator", "dictation_rank")
            .join(pl.read_parquet(C.PROC / "normalized.parquet").select("doc_id", "text_norm"), on="doc_id",
                  validate="1:1"))
    units = pl.read_parquet(C.PROC / "units.parquet")

    # Each document's unit. The target has no units: each Book of Mormon book stands in for one.
    in_units = (units.select("unit_id", "klass", "register", "role", "layer", "kind", pl.col("source_ids").alias("source_id"))
                .explode("source_id")
                .join(docs.drop("role"), on="source_id"))
    target = docs.filter(pl.col("role") == "target").with_columns(
        pl.format("bom::{}", "bom_book").alias("unit_id"), pl.lit("Book of Mormon").alias("klass"),
        pl.lit("revealed_scripture").alias("register"), pl.lit("target").alias("layer"), pl.lit("target").alias("kind"))
    rows = pl.concat([in_units, target], how="diagonal")

    # One row per word, numbered within its unit, then regrouped into chunks
    words = (
        rows.sort("unit_id", "date_key", "source_id", "order", "doc_id")
        .with_columns(pl.col("text_norm").str.split(" ").alias("word"))
        .explode("word")
        .with_columns(pl.int_range(pl.len()).over("unit_id").alias("i"), pl.len().over("unit_id").alias("n"))
        .filter(pl.col("i") < pl.col("n") // C.CHUNK_WORDS * C.CHUNK_WORDS)        # drop the remainder
        .with_columns((pl.col("i") // C.CHUNK_WORDS).alias("chunk_index"))
    )
    chunks = (
        words.group_by("unit_id", "chunk_index", maintain_order=True)
        .agg(pl.col("klass", "register", "role", "layer", "kind", "bom_book", "bom_narrator", "dictation_rank").first(),
             pl.col("source_id").unique(maintain_order=True).alias("source_ids"),
             pl.col("word").str.join(" ").alias("text"))
        .with_columns(pl.format("{}::{}", "unit_id", pl.col("chunk_index").cast(pl.String).str.zfill(3)).alias("chunk_id"))
    )
    chunks.write_parquet(C.PROC / "chunks.parquet")

    with pl.Config(tbl_rows=40, tbl_width_chars=140, fmt_str_lengths=45):
        print(chunks.group_by("role", "klass", "kind")
              .agg(pl.col("unit_id").n_unique().alias("units"), (pl.col("layer") == "development").sum().alias("dev_chunks"),
                   (pl.col("layer") == "audit").sum().alias("audit_chunks"), (pl.col("layer") == "target").sum().alias("target_chunks"))
              .sort("role", "dev_chunks", descending=[False, True]))
    print("chunks:", chunks.height)


if __name__ == "__main__":
    main()
