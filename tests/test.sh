#!/usr/bin/env bash
set -uo pipefail

# Verifier entry point. The reward contract:
#
#   - Write the trial's reward as a FLOAT to /logs/verifier/reward.json
#     ({"reward": <float>}). Partial credit is real signal — never round a
#     fraction to 0 or 1.
#   - Emit per-check results in CTRF to /logs/verifier/ctrf.json.
#   - Grade FINAL OUTPUT FILES only.

mkdir -p /logs/verifier

uvx --with pytest==9.1.1 --with pytest-json-ctrf==0.5.2 \
  pytest --ctrf /logs/verifier/ctrf.json -rA /tests/test_outputs.py

python3 - <<'PY'
import json

with open("/logs/verifier/ctrf.json") as fh:
    summary = json.load(fh)["results"]["summary"]

total = summary.get("tests") or 1
reward = summary.get("passed", 0) / total
with open("/logs/verifier/reward.json", "w") as fh:
    json.dump({"reward": round(reward, 6)}, fh)
PY