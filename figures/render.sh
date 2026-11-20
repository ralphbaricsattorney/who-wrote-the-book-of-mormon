#!/bin/sh
# Draw the article's figures and render each to a PNG at 2x with headless Chrome (or Chromium).
# Run from the repository root: sh figures/render.sh
set -e
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
for script in fig*.py; do
  python "$script"
done
for f in fig*.svg; do
  w=$(grep -o 'width="[0-9]*"' "$f" | head -1 | tr -dc 0-9)
  h=$(grep -o 'height="[0-9]*"' "$f" | head -1 | tr -dc 0-9)
  "$CHROME" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size="$w,$h" \
    --screenshot="${f%.svg}.png" "file://$PWD/$f" 2>/dev/null
  rm "$f"
  echo "wrote figures/${f%.svg}.png"
done
