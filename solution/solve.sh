#!/usr/bin/env bash
set -euo pipefail

# Materializes the gold solution outputs from the task's input data.
# Deterministic: same input -> same output, byte-for-byte.

cd "$(dirname "$0")/.."   # repo root, so paths match the environment layout

mkdir -p output

python3 - <<'PY'
import csv
from collections import defaultdict

counts = defaultdict(lambda: {"units": 0, "defects": 0})
totals = defaultdict(int)

with open("environment/data/defect_log.csv", newline="") as fh:
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
with open("output/summary.csv", "w", newline="") as fh:
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
with open("output/recommendation.md", "w", newline="") as fh:
    fh.write("## Recommendation\n\n")
    fh.write(f"Recommended line: {recommended}\n\n")
    fh.write("## Supporting Figures\n\n")
    fh.write("| Line | Variant | Defect Rate (%) | Mix (%) |\n")
    fh.write("|------|---------|------------------|---------|\n")
    for line, variant, rate, mix in rows:
        fh.write(f"| {line} | {variant} | {rate:.1f} | {mix} |\n")
PY

echo "Wrote output/recommendation.md and output/summary.csv"