"""Step 10: recompute every number the article quotes and check it against the published value.

Each check rounds the recomputed value to the precision the article prints. Shares of documents count each document
once; shares of the Book of Mormon count chunks.

Output: results/article_numbers.md
Run:    python pipeline/10_article_numbers.py
"""

import polars as pl

import config as C
from words import ARCHAIC, MODERN

R = C.RESULTS
SM, RG = C.SMITH, C.RIGDON
OUTCOMES = ["smith_only", "rigdon_only", "both", "neither"]
SHAKER = "Philemon Stewart (Shaker)"


def check(where: str, claim: str, published: float, value: float, digits: int = 0, pct: bool = True) -> tuple:
    """One table row: the published value, the recomputed one at the same precision, and whether they match."""
    shown = round(value * (100 if pct else 1), digits)
    return (where, claim, f"{published:g}{'%' if pct else ''}", f"{shown:g}{'%' if pct else ''}",
            "✓" if shown == published else "✗")


def outcomes(kind: str) -> pl.DataFrame:
    """Each development chunk's Smith-Rigdon set, per run."""
    ranks = (pl.read_parquet(R / f"dev_ranks_{kind}.parquet").filter(pl.col("class").is_in([SM, RG]))
             .with_columns((pl.col("rank") > C.TAU).alias("ok"))
             .pivot(on="class", index=["chunk_id", "klass", "unit_id", "run", "group"], values="ok"))
    s, r = pl.col(SM).fill_null(False), pl.col(RG).fill_null(False)
    return ranks.with_columns((s & ~r).alias("smith_only"), (~s & r).alias("rigdon_only"), (s & r).alias("both"),
                              (~s & ~r).alias("neither"))


def by_document(df: pl.DataFrame) -> dict:
    """Share of each outcome per class, each document counting once."""
    t = (df.group_by("klass", "unit_id").agg(pl.col(OUTCOMES).mean())
         .group_by("klass").agg(pl.col(OUTCOMES).mean()))
    return {d["klass"]: d for d in t.iter_rows(named=True)}


def control(refs: pl.DataFrame, klass: str, cls: str) -> float:
    """Share of a reference text compatible with `cls`, each document counting once."""
    return float(refs.filter(pl.col("klass") == klass).group_by("unit_id")
                 .agg(pl.col(f"compatible {cls}").mean())[f"compatible {cls}"].mean())


def main():
    # ------------------------------------------------------------ Q1 and Q2: development runs (Figs 8 and 9)
    dev = outcomes("F2")
    q1 = by_document(dev.filter((pl.col("group") == "same_author") & pl.col("klass").is_in([SM, RG])))
    q2 = by_document(dev.filter(pl.col("group") == "removed_author"))
    checks = [
        check("Fig 8", "Smith's held-out documents compatible with Smith", 88, q1[SM]["smith_only"] + q1[SM]["both"]),
        check("Fig 8", "Rigdon's held-out documents compatible with Rigdon", 93, q1[RG]["rigdon_only"] + q1[RG]["both"]),
        check("Fig 8", "Rigdon's documents: Rigdon alone", 90, q1[RG]["rigdon_only"]),
        check("Fig 8", "Smith's documents: Smith alone", 74, q1[SM]["smith_only"]),
        check("Fig 8", "Smith's documents: both", 14, q1[SM]["both"]),
    ]
    for name, published in [("Madison", 98), ("Hamilton", 96), (RG, 87), ("Solomon Spalding", 85), (SM, 69),
                            ("Parley P. Pratt", 62), ("Oliver Cowdery", 55), ("David Whitmer", 21)]:
        checks.append(check("Fig 9", f"{name}, left out of training: declined by both", published, q2[name]["neither"]))

    # ------------------------------------------------------------ the Book of Mormon (Fig 10)
    series = pl.read_csv(R / "target_series_F2.csv").sort("position")
    refs = pl.read_parquet(R / "target_references_F2.parquet")
    share = lambda s: series.filter(pl.col("set") == s).height / series.height
    roll = lambda cls: series[f"compatible {cls}"].cast(pl.Float64).rolling_mean(15, center=True, min_samples=1)
    checks += [
        check("Fig 10", "chunks compatible with both men", 4, share("both")),
        check("Fig 10", "Smith only (85 chunks)", 35, share("Smith only")),
        check("Fig 10", "Rigdon only (14 chunks)", 6, share("Rigdon only")),
        check("Fig 10", "neither (138 chunks)", 56, share("neither")),
        check("Coda", "share of the book compatible with Smith", 38, series[f"compatible {SM}"].mean()),
        check("Fig 10", "Rigdon's revelations compatible with Rigdon", 71, control(refs, C.RIGDON_REVELATIONS, RG)),
        check("Fig 10", "Smith's revelations compatible with Smith", 62, control(refs, C.SMITH_REVELATIONS, SM)),
        check("Fig 10", "Shaker roll (1843) compatible with Smith: the most Smith-like control", 66,
              control(refs, SHAKER, SM)),
        check("Fig 10", "Snowden compatible with Rigdon: the most Rigdon-like control", 11,
              control(refs, "Richard Snowden", RG)),
        check("Fig 10", "Smith's 15-chunk line above the Shaker roll's rate", 10,
              float((roll(SM) > control(refs, SHAKER, SM)).mean())),
        check("Fig 10", "Rigdon's 15-chunk line at its highest (\"nowhere near\" 71%)", 33, float(roll(RG).max())),
        check("Fig 10", "Cowdery, never seen, compatible with Smith (\"about as often as\" the book, 38%)", 43,
              q2["Oliver Cowdery"]["smith_only"] + q2["Oliver Cowdery"]["both"]),
        check("Fig 10", "Whitmer, never seen, compatible with Smith", 61,
              q2["David Whitmer"]["smith_only"] + q2["David Whitmer"]["both"]),
        check("Spalding", "average similarity of the book to Spalding (controls: 0.5)", 0.17,
              series["similarity Solomon Spalding"].mean(), 2, pct=False),
    ]
    most_smith = max(C.PSEUDO_BIBLICAL, key=lambda k: control(refs, k, SM))
    most_rigdon = max(C.PSEUDO_BIBLICAL, key=lambda k: control(refs, k, RG))

    # ------------------------------------------------------------ robustness: F1 keeps the King James forms
    f1 = pl.read_csv(R / "target_series_F1.csv")
    f1_rigdon = float(f1[f"compatible {RG}"].mean())
    f1_both = float((f1["set"] == "both").mean())

    # ------------------------------------------------------------ data and method facts
    chunks = pl.read_parquet(C.PROC / "chunks.parquet")
    k = lambda *names: chunks.filter(pl.col("klass").is_in(names)).height
    role = lambda r: chunks.filter(pl.col("role") == r).height
    facts = [
        ("Analysis", "function words in F2", "the article's list",
         f"{len(MODERN)} words, {len(ARCHAIC)} King James forms masked"),
        ("Fig 5", "Rigdon prose / revelations (k words)", "112 / 50", f"{k(RG)} / {k(C.RIGDON_REVELATIONS)}"),
        ("Fig 5", "Spalding / Cowdery / Pratt (k words)", "39 / 32 / 221",
         f"{k('Solomon Spalding')} / {k('Oliver Cowdery')} / {k('Parley P. Pratt')}"),
        ("Fig 5", "Smith / his revelations (k words)", "31 / 87", f"{k(SM)} / {k(C.SMITH_REVELATIONS)}"),
        ("Fig 5", "KJV (k words)", "723", f"{k('KJV')}"),
        ("Fig 5", "other authors the model learns (k words)", "815",
         f"{chunks.filter((pl.col('role') == 'class') & ~pl.col('klass').is_in(C.CANDIDATES + ['KJV'])).height}"),
        ("Fig 5", "biblical-style texts by others, 6 (k words)", "394", f"{role('pseudo_biblical')}"),
        ("Fig 5", "authors writing in both styles, 5 (k words)", "667", f"{role('two_register')}"),
        ("Fig 5", "Book of Mormon (k words)", "246", f"{chunks.filter(pl.col('layer') == 'target').height}"),
        ("Robustness", "F1 (King James forms kept): book compatible with Rigdon / with both", "\"robust\"",
         f"{f1_rigdon:.0%} / {f1_both:.0%} (F2: {series[f'compatible {RG}'].mean():.0%} / {share('both'):.0%})"),
        ("Fig 10", "most Smith-like / most Rigdon-like biblical-style control", "Shaker roll / Snowden",
         f"{most_smith} / {most_rigdon}"),
    ]
    jockers = (R / "jockers_replication.md").read_text()
    facts.append(("Fig 2", "Jockers et al. Table 1 reproduced on their data", "exactly",
                  "exactly" if "reproduces the published result exactly" in jockers else "not exactly"))

    lines = ["# The article's numbers, recomputed", "",
             "| Where | Claim | Article | Recomputed | |", "|---|---|---|---|---|"]
    lines += [f"| {' | '.join(c)} |" for c in checks]
    lines += ["", "| Where | Fact | Article | Recomputed |", "|---|---|---|---|"]
    lines += [f"| {' | '.join(f)} |" for f in facts]
    failed = [c for c in checks if c[-1] == "✗"]
    lines += ["", f"{len(checks) - len(failed)} of {len(checks)} checks match."]
    (R / "article_numbers.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
