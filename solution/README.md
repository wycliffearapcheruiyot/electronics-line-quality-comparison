# Gold solution

## Method

`solve.sh` reads `environment/data/defect_log.csv` and computes defect
rate **stratified by `product_variant` within each line** — never the
blended per-line rate. This is the one step a careless attempt skips (see
the crux in the Decisions Log at the top of this repo's build guide).

For each (line, variant) pair it computes:
- `defect_rate_pct` = defects / units for that pair, rounded to 1 decimal
- `mix_pct` = that pair's units / that line's total units, rounded to the
  nearest whole number

The recommendation is derived, not hardcoded: Line A is recommended only
if its per-variant defect rate is less-than-or-equal to Line B's on
*both* variants. This mirrors the actual reasoning (Line A wins Standard
and wins Pro individually) rather than baking "Line A" into the script.

## Expected result

| Line | Variant | Defect Rate (%) | Mix (%) |
|---|---|---|---|
| Line A | Standard | 2.1 | 45 |
| Line A | Pro | 6.4 | 55 |
| Line B | Standard | 2.6 | 85 |
| Line B | Pro | 7.8 | 15 |

Recommended line: **Line A**. It beats Line B on both variants
individually; Line B's better-looking blended rate (3.4% vs Line A's
4.5%) is purely a product-mix artifact, since Line B runs mostly the
easier Standard variant.

## Files

- `solve.sh` — deterministic script that reads `environment/data/`, and
  writes `output/recommendation.md` and `output/summary.csv`.
- `gold.patch` — unified diff of the two output files `solve.sh`
  produces, kept in sync with it.

Nothing under `solution/` may be visible to the model: never `COPY` this
directory into the environment image.