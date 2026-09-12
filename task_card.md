# Task description

The AI is playing the role of a manufacturing/quality analyst at a mid-size
electronics plant. Leadership has budget for one round of capital investment
and wants it directed at whichever of two production lines (Line A or Line B)
is actually the higher-quality line. The AI is given six real-sized files —
a row-level defect log, a QC inspection spreadsheet, a production/downtime
log, shift-handoff notes, a production schedule, and a leadership summary
PDF — none of which fully agree with each other, and must decide which line
to recommend and back it with numbers. It must deliver exactly two files:
`output/recommendation.md` (a recommendation sentence plus a supporting
table) and `output/summary.csv` (the same figures in machine-readable form).

# Reasoning challenges

1. **[CRUX] Aggregate vs. stratified defect rate (Simpson's Paradox).**
   `defect_log.csv` mixes both lines and both variants together. Line A's
   raw aggregate defect rate looks worse than Line B's, but only because
   Line A ran a much higher share of the harder Pro variant. A correct
   attempt computes defect rate separately per (line, variant) pair before
   comparing anything. A careless attempt filters by line only, recomputes
   the same misleading blended number the data already invites, and
   recommends Line B. This is the one step that actually determines the
   right answer — everything else in the package is supporting texture.

2. **Competing, non-equivalent data sources.**
   `qc_inspection_log.xlsx` reports pass/fail rates from a separate,
   smaller inspection sample using a different definition of "fail" than
   the defect log's "defect_found" flag. A correct attempt treats the
   defect log as the primary source for the requested defect-rate figures
   and uses the QC log only as context. A careless attempt quotes the QC
   log's numbers directly, or averages the two sources as if they measured
   the same thing, producing figures that don't match the locked ground
   truth.

3. **Downtime as a quality red herring.**
   `production_downtime_log.json` shows Line A with more downtime than
   Line B overall. A correct attempt recognizes that downtime measures
   availability, not defect quality, and keeps it out of the quality
   determination. A careless attempt treats higher downtime as evidence
   that Line B is the "better-run" line and lets that flip or hedge the
   recommendation.

4. **Anecdotal notes reinforcing the wrong narrative.**
   `shift_handoff_notes.txt` contains informal comments noting Line A
   "struggling" on days it runs Pro units. A correct attempt recognizes
   these notes as consistent with the mix effect (Line A runs the harder
   variant more often) rather than as independent evidence of poor
   process quality. A careless attempt reads them naively as confirmation
   that Line A is the problem line.

# Taxonomy tags

- **Domain:** Manufacturing & Quality Engineering
- **Primary analytical objective:** Comparative Analysis & Explanation
- **Additional objectives:** Root-Cause Analysis, Data Quality
- **Reasoning phases:** Explore/Discover, Hypothesize, Analyze & Validate,
  Synthesize, Recommend

# Expected difficulty

A strong model is expected to average **60% or less** and a weaker model
**35% or less** across sweeps. The task is not "too easy" because three of
the six files actively support the wrong (Line B) conclusion if read at
face value — the aggregate defect log split by line only, the leadership
PDF's pre-blended figures, and the downtime log all point toward Line B.
Reaching the correct answer requires the solver to (a) distrust the most
authoritative-looking document in the package (the PDF), (b) perform the
stratification calculation itself rather than citing a precomputed number,
and (c) correctly set aside two plausible-looking but irrelevant signals
(downtime, anecdotal notes). A sloppy analysis lands on a different,
wrong final answer (Line B) rather than accidentally the right one.

# Ground-truth answer

| | Line A | Line B |
|---|---|---|
| Standard defect rate | ≈2.1% | ≈2.6% |
| Pro defect rate | ≈6.4% | ≈7.8% |
| Product mix (% Pro) | ≈55% | ≈15% |
| Blended defect rate | ≈4.5% | ≈3.4% |

**Correct recommendation: Line A.** It beats Line B on both variants
individually (2.1% vs 2.6% Standard, 6.4% vs 7.8% Pro). Line B's better-
looking blended number (3.4% vs 4.5%) is an artifact of running mostly the
easier Standard variant, not evidence of better process quality.

**Why the tempting alternatives are wrong:**

- *"Invest in Line B — its overall defect rate is lower."* This is the
  trap answer produced by reading the aggregate defect log or the
  leadership PDF at face value. It never controls for product mix.
- *"It's a wash — use a tiebreaker like downtime or throughput."* This
  undershoots the data. The per-variant gap is consistent and non-trivial
  on both variants, not marginal or noisy, so "no real difference" isn't
  supported once the stratified numbers are computed.
- *"Invest in Line B and shift more Pro volume onto it."* This inverts
  causality, treating Line B's favorable mix as a sign of operational
  skill rather than the reason its aggregate number looks good — and
  ignores that Line B is specifically worse at Pro (7.8% vs 6.4%).
- *"Recommend Line A, but for the wrong reason"* (e.g., citing total
  defect count instead of rate, or citing downtime/throughput instead of
  defect rate). This can land on the correct line by accident without
  demonstrating the actual mechanism, which is why the rubric requires
  the specific per-variant figures (items 2–3, 12–13), not just the
  final recommendation sentence.

# Expected reasoning trajectory

A full worked solution exists in `solution/`. In summary: load
`defect_log.csv`, group by (line, product_variant), compute defect rate
per group; cross-check the resulting mix percentages against
`line_schedule.csv`; note that `qc_inspection_log.xlsx` and
`plant_capacity_report.pdf` report different, non-stratified figures and
are not used as the basis for the final numbers; note that
`production_downtime_log.json` and `shift_handoff_notes.txt` are reviewed
and explicitly set aside as non-quality signals; write the four
(line, variant) rows and the recommendation to the two output files.