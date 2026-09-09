#!/usr/bin/env bash
set -euo pipefail

# Verifier entry point for the rule-based checker (Part 11).
#
# Reward contract: verify.py writes the trial's reward as a FLOAT to
# /logs/verifier/reward.json ({"reward": <float>}). Grades FINAL OUTPUT
# FILES only, from /output/.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/verify.py"