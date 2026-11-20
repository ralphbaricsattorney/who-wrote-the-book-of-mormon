"""Step 2: turn documents into units, the things that are split between training and testing.

  1. one row per source document (all hands and copies of a document together; printed twins left out)
  2. documents under 1000 words are bundled with others of the same class, register and layer, in date order,
     until the bundle reaches 1000 words; a short document with nothing to bundle with is dropped
  3. each unit takes its layer from pipeline/layers.tsv: "development" (everything the method was built and
     tested on) or "audit" (about a quarter of each large class, drawn by seeded hash and held back; not used here)
  4. a class with at least 20 development units is "ranked": it gets a compatibility line. Fewer: "descriptive"

The Book of Mormon is not unitized; it is never part of any split.

Output: data/processed/units.parquet (one row per unit), data/processed/units_summary.csv
"""
import polars as pl

import config as C


def bundle_ids(words: list[int]) -> list[int]:
    """Greedy bundles in the given order: close a bundle once it reaches CHUNK_WORDS; a short tail joins the last."""
    ids, current, total = [], 0, 0
    for w in words:
        ids.append(current)
        total += w
        if total >= C.CHUNK_WORDS:
            current, total = current + 1, 0
    if total and current:
        ids = [min(i, current - 1) for i in ids]
    return ids


def main():
    # ---------------------------------------------------------------- 1. source documents
    docs = pl.read_parquet(C.PROC / "documents.parquet").filter(~pl.col("role").is_in(["target", "twin"]))
    scripture = pl.col("register") == "revealed_scripture"
    klass = (pl.when((pl.col("author") == C.SMITH) & scripture).then(pl.lit(C.SMITH_REVELATIONS))
             .when((pl.col("author") == C.RIGDON) & scripture).then(pl.lit(C.RIGDON_REVELATIONS))
             .when((pl.col("author") == C.RIGDON) & (pl.col("year") >= 1856)).then(pl.lit(C.RIGDON_LATE_LETTERS))
             .when(pl.col("author").is_in(C.TWO_REGISTER) & scripture).then(pl.format("{} (scripture)", "author"))
             .otherwise("author"))
    layers = pl.read_csv(C.ROOT / "pipeline" / "layers.tsv", separator="\t")
    sources = (
        docs.with_columns(klass.alias("klass"))
        .group_by("source_id")
        .agg(pl.col("klass").first(), pl.col("register").first(), pl.col("date_key").min(), pl.col("words").sum(),
             # a document is only as secure as its least secure part
             pl.col("source_type").sort_by(pl.col("source_type") == "single_author").first())
        .sort("klass", "register", "date_key", "source_id")           # date order, for bundling
        .join(layers, on="source_id", how="left").with_columns(pl.col("layer").fill_null("unassigned"))
    )

    # ---------------------------------------------------------------- 2. bundle short documents
    short = pl.col("words") < C.CHUNK_WORDS
    bundled = pl.concat(
        g.with_columns(pl.Series("bundle", bundle_ids(g["words"].to_list())))
        for g in sources.filter(short).partition_by("klass", "register", "layer", maintain_order=True)
    ).with_columns(pl.format("{}::{}::{}::bundle{}", "klass", "register", "layer", pl.col("bundle").cast(pl.String).str.zfill(2))
                   .alias("unit_id")).drop("bundle")
    single = sources.filter(~short).with_columns(pl.col("source_id").alias("unit_id"))

    units = (
        pl.concat([single, bundled])
        .group_by("unit_id")
        .agg(pl.col("klass").first(), pl.col("register").first(), pl.col("date_key").min(), pl.col("words").sum(),
             pl.col("source_id").sort().alias("source_ids"), pl.len().alias("n_sources"),
             pl.col("source_type").sort_by(pl.col("source_type") == "single_author").first(), pl.col("layer").first())
        .with_columns((pl.col("words") // C.CHUNK_WORDS).alias("n_chunks"))
        .filter(pl.col("n_chunks") > 0)
        .sort("klass", "register", "date_key", "unit_id")
    )
    assert units.filter(pl.col("layer") == "unassigned").height == 0, "a unit has no layer in pipeline/layers.tsv"

    # ---------------------------------------------------------------- 3. role of each class of text
    units = units.with_columns(
        pl.when(pl.col("klass").is_in(C.CLASSES)).then(pl.lit("class"))
        .when(pl.col("klass") == C.SMITH_REVELATIONS).then(pl.lit("smith_revelations"))
        .when(pl.col("klass").is_in([C.RIGDON_REVELATIONS, C.RIGDON_LATE_LETTERS])).then(pl.lit("rigdon_late"))
        .when(pl.col("klass").is_in(C.PSEUDO_BIBLICAL + C.PSEUDO_BIBLICAL_AUDIT)).then(pl.lit("pseudo_biblical"))
        .when(pl.col("klass").str.replace(r" \(scripture\)$", "").is_in(C.TWO_REGISTER)).then(pl.lit("two_register"))
        .otherwise(pl.lit("other_control")).alias("role"))

    # ---------------------------------------------------------------- 4. ranked or descriptive
    summary = (
        units.group_by("klass", "role")
        .agg(pl.col("n_sources").sum().alias("documents"), pl.len().alias("units"), pl.col("n_chunks").sum().alias("chunks"),
             (pl.col("layer") == "development").sum().alias("dev_units"), (pl.col("layer") == "audit").sum().alias("audit_units"))
        .with_columns(pl.when(pl.col("role") != "class").then(pl.lit("control"))
                      .when(pl.col("dev_units") >= C.MIN_RANKED_UNITS).then(pl.lit("ranked"))
                      .otherwise(pl.lit("descriptive")).alias("kind"))
        .sort("role", "units", descending=[False, True])
    )
    units = units.join(summary.select("klass", "kind"), on="klass")

    units.write_parquet(C.PROC / "units.parquet")
    summary.write_csv(C.PROC / "units_summary.csv")
    with pl.Config(tbl_rows=40, tbl_width_chars=170, fmt_str_lengths=45):
        print(summary)
    print("units:", units.height, "| chunks:", units["n_chunks"].sum())


if __name__ == "__main__":
    main()
