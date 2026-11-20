#!/bin/sh
# Rebuild everything from data/raw: prepared texts, corpus, scores, the article's numbers and figures.
# About 3 hours on 8 cores; steps 5 and 8 take most of it.
set -e
cd "$(dirname "$0")"
run() { echo "== $*"; python "$@"; }

for author in strang white_richard_grant thompson_charles_b ilive memminger; do
  run prepare/two_register/clean_$author.py > /dev/null
done
run prepare/rigdon_revelations.py

run pipeline/01_corpus.py
run pipeline/02_units.py
run pipeline/03_normalize.py
run pipeline/04_chunks.py
for kind in F2 F1; do
  run pipeline/05_develop.py $kind
  run pipeline/06_score_target.py $kind
done
run pipeline/07_two_register.py
run pipeline/08_two_register_cross_work.py
run pipeline/09_jockers.py
run pipeline/10_article_numbers.py
sh figures/render.sh
