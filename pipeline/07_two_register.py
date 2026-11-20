"""Step 7: the two-register study. Does the model recognize an author's scripture-style text from his prose?
Development text only.

One procedure is built on the training pool plus each two-register author's prose as a class of its own. Scored,
all held out of that procedure:
  scripture         every two-register author's scripture-style text: the five two-register authors, Smith's
                    revelations and Rigdon's revelations
  other work        a prose work the procedure did not see: for each two-register author with two or more prose works,
                    one drawn by seeded hash; for Rigdon, his late letters (same years and source as his
                    revelations). Same register, different work: it separates "new register" from "new work".
  biblical control  the biblical-style controls

Measures per author A:
  scripture recall           A's scripture-style text accepted as A
  other-work recall          A's held-out prose work accepted as A
  register false acceptance  other authors' scripture-style text accepted as A, each author counting once
  margin                     scripture recall minus register false acceptance
  head to head               on A's scripture, against each other author B: share accepted as A and not B,
                             minus share accepted as B and not A

Output: results/two_register_ranks.parquet (one row per chunk x class), results/two_register.md
Run:    python pipeline/07_two_register.py
"""
import hashlib
import time

import polars as pl

import config as C
from features import counts
from folds import training_pool
from model import build_procedure, ranks

KIND = "F2"
SCRIPTURE = {a: f"{a} (scripture)" for a in C.TWO_REGISTER} | {C.SMITH: C.SMITH_REVELATIONS,
                                                                 C.RIGDON: C.RIGDON_REVELATIONS}
AUTHORS = sorted(SCRIPTURE)


def table(title: str, df: pl.DataFrame, note: str = "") -> list[str]:
    """A titled markdown table, with an optional note."""
    with pl.Config(tbl_formatting="MARKDOWN", tbl_hide_dataframe_shape=True, tbl_hide_column_data_types=True,
                   tbl_rows=200, tbl_cols=20, fmt_str_lengths=60, float_precision=2, tbl_width_chars=300):
        return [f"## {title}", ""] + ([note, ""] if note else []) + [str(df), ""]


def main():
    t0 = time.time()
    chunks = pl.read_parquet(C.PROC / "chunks.parquet").with_row_index("row")
    dev = chunks.filter(pl.col("layer") == "development")
    X = counts(chunks, KIND)

    # ---------------------------------------------------------------- what is trained on and what is scored
    prose = dev.filter(pl.col("klass").is_in(C.TWO_REGISTER))
    works = (prose.select("klass", "unit_id").unique()
             .with_columns(pl.col("unit_id").map_elements(lambda u: hashlib.md5(f"{C.SEED}:{u}".encode()).hexdigest(),
                                                          return_dtype=pl.String).alias("draw"),
                           pl.len().over("klass").alias("works")))
    held_works = works.filter(pl.col("works") >= 2).sort("draw").group_by("klass").first().sort("klass")
    pool = training_pool(chunks, extra=prose.join(held_works, on="unit_id", how="anti"))

    author_of = {v: k for k, v in SCRIPTURE.items()}
    scored = pl.concat([
        dev.filter(pl.col("klass").is_in(list(author_of)))
        .with_columns(pl.col("klass").replace_strict(author_of).alias("author"), pl.lit("scripture").alias("text")),
        dev.join(held_works.select("unit_id"), on="unit_id")
        .with_columns(pl.col("klass").alias("author"), pl.lit("other work").alias("text")),
        dev.filter(pl.col("klass") == C.RIGDON_LATE_LETTERS)
        .with_columns(pl.lit(C.RIGDON).alias("author"), pl.lit("other work").alias("text")),
        dev.filter(pl.col("klass").is_in(C.PSEUDO_BIBLICAL))
        .with_columns(pl.col("klass").alias("author"), pl.lit("biblical control").alias("text")),
    ])
    assert scored.join(pool, on="chunk_id").height == 0, "a scored chunk is in the training pool"
    assert set(AUTHORS) <= set(pool["label"].unique()), "a two-register author has no prose class"
    print(f"pool: {pool.height} chunks, {pool['label'].n_unique()} classes | scored: {scored.height} chunks", flush=True)
    print("held-out prose works:", held_works["unit_id"].to_list(), flush=True)

    # ---------------------------------------------------------------- one procedure, every scored chunk ranked
    procedure = build_procedure(pool, X, seed=C.SEED + 5000)
    print(f"procedure built ({time.time() - t0:.0f}s)", flush=True)
    classes, rows = procedure[0].classes, X[scored["row"].to_numpy()]
    ident = scored.select("chunk_id", "klass", "unit_id", "chunk_index", "author", "text")
    r = ranks(procedure, rows)
    ranked = pl.concat(
        ident.with_columns(pl.lit(k).alias("class"), pl.Series("rank", r[:, i])) for i, k in enumerate(classes)
    ).with_columns((pl.col("rank") > C.TAU).alias("accepted"))
    ranked.write_parquet(C.RESULTS / "two_register_ranks.parquet")

    # ---------------------------------------------------------------- measures
    # Authorship itself in doubt (Ilive, Memminger), judged from the prose classes
    attributed = (pl.read_parquet(C.PROC / "units.parquet").filter(pl.col("klass").is_in(AUTHORS))
                  .group_by("klass").agg((pl.col("source_type") == "attributed").all().alias("attributed"))
                  .rename({"klass": "author"}))
    as_self = (ranked.filter(pl.col("class") == pl.col("author"))
               .group_by("author", "text").agg(pl.col("accepted").mean(), pl.len().alias("chunks")))
    recall = (as_self.filter(pl.col("text") == "scripture")
              .select("author", pl.col("chunks").alias("scripture_chunks"), pl.col("accepted").alias("scripture_recall"))
              .join(as_self.filter(pl.col("text") == "other work")
                    .select("author", pl.col("chunks").alias("other_work_chunks"),
                            pl.col("accepted").alias("other_work_recall")), on="author", how="left"))
    false_acceptance = (
        ranked.filter(pl.col("text").is_in(["scripture", "biblical control"]) & pl.col("class").is_in(AUTHORS)
                      & (pl.col("author") != pl.col("class")))
        .group_by("class", "author").agg(pl.col("accepted").mean())
        .sort("accepted", descending=True)
        .group_by("class", maintain_order=True)
        .agg(pl.col("accepted").mean().alias("register_false_acceptance"),
             pl.col("author").first().alias("worst_other"), pl.col("accepted").first().alias("worst_rate"))
        .rename({"class": "author"}))
    summary = (recall.join(false_acceptance, on="author").join(attributed, on="author")
               .with_columns((pl.col("scripture_recall") - pl.col("register_false_acceptance")).alias("margin"))
               .select("author", "attributed", "scripture_chunks", "scripture_recall", "other_work_chunks",
                       "other_work_recall", "register_false_acceptance", "margin", "worst_other", "worst_rate")
               .sort("author"))

    scripture = ranked.filter((pl.col("text") == "scripture") & pl.col("class").is_in(AUTHORS))
    own = scripture.filter(pl.col("class") == pl.col("author")).select("chunk_id", "author", pl.col("accepted").alias("a"))
    rival = scripture.filter(pl.col("class") != pl.col("author")).select("chunk_id", pl.col("class").alias("rival"),
                                                                         pl.col("accepted").alias("b"))
    head_to_head = (own.join(rival, on="chunk_id").group_by("author", "rival")
                    .agg(((pl.col("a") & ~pl.col("b")).mean() - (pl.col("b") & ~pl.col("a")).mean()).alias("D")))
    d_table = (head_to_head.with_columns(pl.col("rival").str.split(" ").list.last())
               .pivot(on="rival", index="author", values="D", sort_columns=True).sort("author"))

    # ---------------------------------------------------------------- report
    lines = [f"# Two-register study: features {KIND}, threshold {C.TAU}", "",
             "Development text only. One procedure, trained on the pool plus each two-register author's prose; every row "
             "below is text that procedure never saw.", "",
             f"Held-out prose works: {', '.join(held_works['unit_id'].to_list())}; for Rigdon, his letters of 1863-76.", ""]

    lines += table("Per author", summary,
                   "`scripture_recall`: own scripture-style text accepted as the author. `other_work_recall`: an unseen prose work "
                   "accepted as the author (none for Smith or for Thompson, who has one prose work). `register_false_acceptance`: "
                   "other authors' scripture-style text, and the biblical-style controls, accepted as the author, each text counting "
                   "once. Chunks within a work are not independent: each author is one case.")
    lines += table("Head to head on each author's scripture-style text", d_table,
                   "Row: whose scripture-style text. Column: the rival. D = share accepted as the row author and not the rival, "
                   "minus share accepted as the rival and not the row author. Positive points to the right author.")
    (C.RESULTS / "two_register.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
