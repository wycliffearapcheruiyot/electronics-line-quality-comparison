# Line Investment Recommendation

You've got a pile of records from a -size electronics plant. Two production

lines, **Line A** and **Line B**. Each one builds two variants: **Standard**

and **Pro**.

Here's the deal. Leadership has money for one round of capital investment.

They want it on whichever line is actually better on quality. Your job: look

at what's here and recommend **Line A** or **Line B**. Back it up with real

numbers.

You'll find these in `data/`:

- `defect_log.csv`. Row-level defect records

- `qc_inspection_log.xlsx`. Sampled QC inspection results

- `production_downtime_log.json`. Per-line per-day downtime events

- `shift_handoff_notes.txt`. Shift-change notes from line supervisors

- `line_schedule.csv`. Daily production schedule by line and variant

- `plant_capacity_report.pdf`. A prior-quarter leadership summary report

Not all of these agree. Not all of them deserve trust. Figuring out

which numbers to lean on is part of the job. How you work through it is up to

you.

## What to deliver

Save your results as these two files.

### 1. `output/recommendation.md`

A file with at minimum:

- A section titled `## Recommendation` with one sentence in the form:

`Recommended line: Line A` (or `Line B`). This exact phrase must appear

verbatim on its own line.

- A section titled `## Supporting Figures` with a table. Use these

column headers in this order: `| Line | Variant | Defect Rate (%) |

Mix (%) |`. One row per (line variant) combination. Line A Standard, Line A

Pro, Line B Standard, Line B Pro.

### 2. `output/summary.csv`

A CSV file with these column headers in this order:

```
line,product_variant,defect_rate_pct,mix_pct
```

One row per (line variant) combination. Four rows total: Line A/Standard,

Line A/Pro, Line B/Standard, Line B/Pro. `line` values must be exactly `Line A`

or `Line B`. `product_variant` values must be exactly `Standard` or `Pro`.

**Precision:** round `defect_rate_pct` to 1 decimal. `mix_pct` to the

nearest whole number in both files. The figures, in `recommendation.md` and

`summary.csv` need to match exactly. Automated grading checks each figure

against the value a correct calculation from the provided data produces,

allowing ±0.1 percentage point on `defect_rate_pct` and ±1 percentage point on `mix_pct` — a correctly computed and rounded figure will always pass within that tolerance.

Don't put anything else under `output/`.