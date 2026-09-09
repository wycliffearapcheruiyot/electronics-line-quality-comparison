# Gold solution (placeholder)

Replace this directory's contents with the complete gold solution:

- `gold.patch` — unified diff (git diff format) from the fresh workspace to
  the solved state. Keep exactly in sync with what `solve.sh` produces.
- `solve.sh` — deterministic script that materializes the gold outputs in a
  fresh environment. The oracle run must earn full reward; the nop run must
  earn exactly 0.

Nothing under `solution/` may be visible to the model: never COPY this
directory into the environment image.