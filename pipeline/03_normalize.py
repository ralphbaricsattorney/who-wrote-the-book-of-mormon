"""Step 3: normalize orthography so manuscript transcriptions and printed texts look alike to the model.

Every text becomes lowercase words with no punctuation; "&" becomes "and"; editorial [brackets] in the Joseph Smith
Papers transcriptions are removed; manuscript spellings are mapped to printed ones (pipeline/orthography_map.tsv).

Output: data/processed/normalized.parquet (doc_id, source_id, text_norm, words_norm)
"""
import polars as pl

import config as C


def main():
    docs = pl.read_parquet(C.PROC / "documents.parquet")
    tokens = (
        pl.when(pl.col("edition").str.contains("JSP")).then(pl.col("text_masked").str.replace_all(r"\[[^\]]*\]", " "))
        .otherwise("text_masked")
        .str.to_lowercase()
        .str.replace_all(r"&c\b", " etc ")
        .str.replace_all("&", " and ")
        .str.extract_all(r"[a-z]+(?:'[a-z]+)?")
    )
    reviewed = pl.read_csv(C.ROOT / "pipeline" / "orthography_map.tsv", separator="\t", comment_prefix="#")
    mapping = dict(zip(reviewed["variant"], reviewed["target"]))

    docs = docs.with_columns(tokens.alias("tokens"))
    out = docs.select(
        "doc_id", "source_id",
        pl.col("tokens").list.eval(pl.element().replace(mapping)).list.join(" ").alias("text_norm"),
        pl.col("tokens").list.len().alias("words_norm"),
    )
    out.write_parquet(C.PROC / "normalized.parquet")
    changed = docs.select(pl.col("tokens").explode().is_in(list(mapping)).sum()).item()
    print(f"documents: {out.height} | words: {out['words_norm'].sum():,} | respelled: {changed:,} ({len(mapping)} spellings)")


if __name__ == "__main__":
    main()
