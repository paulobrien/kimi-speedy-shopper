#!/bin/sh
# Package the candidate shopper (the only editable part) for the run step.
set -eu
mkdir -p out/shopper
for f in AGENTS.md settings.json; do
  [ -f "shopper/$f" ] || { echo "missing shopper/$f" >&2; exit 1; }
  cp "shopper/$f" out/shopper/
done
node -e 'JSON.parse(require("fs").readFileSync("out/shopper/settings.json","utf8"))'
