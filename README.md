# electronics-line-quality-comparison

Manufacturing/QC comparative-analysis task: given a defect log, QC
inspection spreadsheet, downtime log, and shift-handoff notes for two
production lines, recommend which line should get capital investment.

## Build

```bash
docker build -t task-env:latest environment/
```

## Test

```bash
./solution/solve.sh && bash tests/test.sh
cat logs/verifier/reward.json
```

On Windows 11 in Git Bash, prefix any `docker run` that uses `-v` mounts
with `MSYS_NO_PATHCONV=1` (see Part 13) — without it, Git Bash rewrites
the container-side paths as if they were Windows paths and the mounts
resolve wrong.

## Expected scores

- `nop` agent (empty attempt): reward `0`
- `oracle` agent (reference solution applied): reward `1.0`

These are Part 12's golden checks; anything else means the verifier and
the reference solution have drifted apart.