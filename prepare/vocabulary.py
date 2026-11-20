"""The corpus vocabulary the cleaning scripts use to repair OCR (long s, words broken at line ends).

It is frozen in prepare/vocabulary.parquet, taken once from the normalized corpus (step 3). The cleaned texts feed that
corpus, so reading it live would make the cleaning depend on its own output.
  word   [a-z]+ runs, count >= 3
  token  whole normalized tokens (apostrophes kept: "don't"), count >= 3
  pair   adjacent [a-z]+ runs, count >= 5 (rarer pairs never change a joining decision)
  dict   a general English word list (Webster's Second, as shipped in /usr/share/dict/words on macOS)

Rebuild: python prepare/vocabulary.py   (needs data/processed/normalized.parquet and /usr/share/dict/words)
"""
from pathlib import Path

import polars as pl

FILE = Path(__file__).with_name("vocabulary.parquet")


def _load(kind: str) -> pl.DataFrame:
    return pl.read_parquet(FILE).filter(pl.col("kind") == kind)


def words() -> dict[str, int]:
    return dict(_load("word").select("a", "count").iter_rows())


def tokens() -> dict[str, int]:
    return dict(_load("token").select("a", "count").iter_rows())


def pairs() -> dict[tuple[str, str], int]:
    return {(a, b): n for a, b, n in _load("pair").select("a", "b", "count").iter_rows()}


def dictionary() -> set[str]:
    return set(_load("dict")["a"])


if __name__ == "__main__":
    text = pl.read_parquet(Path(__file__).resolve().parents[1] / "data/processed/normalized.parquet", columns=["text_norm"])
    runs = text.select(pl.col("text_norm").str.extract_all(r"[a-z]+").alias("t"))
    count = lambda df, *cols: df.group_by(*cols).len("count")
    word = count(runs.explode("t").rename({"t": "a"}), "a").filter(pl.col("count") >= 3)
    token = count(text.select(pl.col("text_norm").str.split(" ").alias("a")).explode("a"), "a").filter((pl.col("count") >= 3) & (pl.col("a") != ""))
    pair = count(runs.select(pl.col("t").list.head(pl.col("t").list.len() - 1).alias("a"), pl.col("t").list.slice(1).alias("b"))
                 .explode("a", "b").drop_nulls(), "a", "b").filter(pl.col("count") >= 5)
    dict_words = pl.DataFrame({"a": sorted({w.lower() for w in Path("/usr/share/dict/words").read_text().split()})})
    out = pl.concat([word.with_columns(pl.lit("word").alias("kind")),
                     token.with_columns(pl.lit("token").alias("kind")),
                     pair.with_columns(pl.lit("pair").alias("kind")),
                     dict_words.with_columns(pl.lit("dict").alias("kind"), pl.lit(1).alias("count"))], how="diagonal")
    out.select("kind", "a", "b", pl.col("count").cast(pl.Int64)).sort("kind", "a", "b").write_parquet(FILE)
    print(out.group_by("kind").len())
