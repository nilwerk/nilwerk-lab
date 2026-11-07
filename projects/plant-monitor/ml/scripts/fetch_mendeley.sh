#!/usr/bin/env bash
# Download the Mendeley irrigation dataset (CC BY 4.0, doi 10.17632/c837v6p8ph.2) into ml/data/raw/ (gitignored).
# Verifies the ZIP checksum recorded on 2026-11-06. The ZIP is 44.5 MB (> 5 MB), so it is never committed.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=data/raw; mkdir -p "$OUT"
EXPECT=a6043b8e44db7adfdfc5a7f5ff8157a0ed38d29a861a1555dcd73d0cec9853e8
curl -sS -L -o "$OUT/c837v6p8ph-2.zip" https://data.mendeley.com/public-api/zip/c837v6p8ph/download/2
echo "$EXPECT  $OUT/c837v6p8ph-2.zip" | sha256sum -c -
# the two raw valve/minute files are 396 MB and not used by the loader
unzip -q -o "$OUT/c837v6p8ph-2.zip" -d "$OUT/ex" -x '*raw_irrigation_actuators/raw_actuators.csv' '*raw_measurements.csv'
