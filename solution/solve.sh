#!/usr/bin/env bash
set -euo pipefail

# Materializes the gold solution outputs from the task's input data.
# Deterministic: same input -> same output, byte-for-byte.

# Prefer the container's runtime layout (input at /data, output at
# /output — matching environment/Dockerfile's COPY destination and
# tests/verify.py's OUTPUT_DIR (now /workspace/output)) so this produces identical bytes whether
# Harbor runs it inside the oracle container or you run it locally
# against a repo checkout for testing.
if [ -d /data ]; then
  DATA_DIR=/data
  OUT_DIR=/workspace/output
else
  cd "$(dirname "$0")/.."   # repo root, for local testing outside a container
  DATA_DIR=environment/data
  OUT_DIR=output
fi

mkdir -p "$OUT_DIR"

DATA_DIR="$DATA_DIR" OUT_DIR="$OUT_DIR" python3 - <<'PY'
import csv
import os
from collections import defaultdict

DATA_DIR = os.environ["DATA_DIR"]
OUT_DIR = os.environ["OUT_DIR"]

counts = defaultdict(lambda: {"units": 0, "defects": 0})
totals = defaultdict(int)

with open(f"{DATA_DIR}/defect_log.csv", newline="") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        line = row["line"]
        variant = row["product_variant"]
        key = (line, variant)
        counts[key]["units"] += 1
        totals[line] += 1
        if row["defect_found"].strip().upper() == "TRUE":
            counts[key]["defects"] += 1

rows = []
for line in ["Line A", "Line B"]:
    for variant in ["Standard", "Pro"]:
        c = counts[(line, variant)]
        defect_rate = round(100 * c["defects"] / c["units"], 1)
        mix = round(100 * c["units"] / totals[line])
        rows.append((line, variant, defect_rate, mix))

# Force \n line endings (not csv's default \r\n) so the file matches the
# gold bytes on every platform, including Windows/Git Bash.
with open(f"{OUT_DIR}/summary.csv", "w", newline="") as fh:
    writer = csv.writer(fh, lineterminator="\n")
    writer.writerow(["line", "product_variant", "defect_rate_pct", "mix_pct"])
    for line, variant, rate, mix in rows:
        writer.writerow([line, variant, f"{rate:.1f}", mix])

# Derive the recommendation instead of hardcoding it: Line A wins only if
# it beats or ties Line B on BOTH variants individually.
by_variant = {(line, variant): rate for line, variant, rate, mix in rows}
line_a_wins_both = (
    by_variant[("Line A", "Standard")] <= by_variant[("Line B", "Standard")]
    and by_variant[("Line A", "Pro")] <= by_variant[("Line B", "Pro")]
)
recommended = "Line A" if line_a_wins_both else "Line B"

# Same reasoning as the newline="" above: plain open("w") on Windows
# silently translates every \n to \r\n, which would make this file
# byte-different from the gold answer on Windows even though the content
# is identical. newline="" disables that translation.
blended = {
    line: round(100 * sum(counts[(line, v)]["defects"] for v in ["Standard", "Pro"]) / totals[line], 1)
    for line in ["Line A", "Line B"]
}

with open(f"{OUT_DIR}/recommendation.md", "w", newline="") as fh:
    fh.write("## Recommendation\n\n")
    fh.write(f"Recommended line: {recommended}\n\n")
    fh.write(
        f"Line A's overall/blended defect rate ({blended['Line A']}%) looks worse "
        f"than Line B's aggregate rate ({blended['Line B']}%), but that gap is an "
        "artifact of product mix, not process quality: once defect rate is "
        "computed per variant, Line A wins on both Standard and Pro.\n\n"
    )
    fh.write("## Supporting Figures\n\n")
    fh.write("| Line | Variant | Defect Rate (%) | Mix (%) |\n")
    fh.write("|------|---------|------------------|---------|\n")
    for line, variant, rate, mix in rows:
        fh.write(f"| {line} | {variant} | {rate:.1f} | {mix} |\n")
PY

echo "Wrote $OUT_DIR/recommendation.md and $OUT_DIR/summary.csv"