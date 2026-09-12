#!/usr/bin/env python3
"""Rule-based verifier for the electronics-line-quality-comparison task.

Reads rubrics.json + test_weights.json (both bundled next to this file),
checks each rubric criterion against /workspace/output/[filename], and writes the
resulting reward to /logs/verifier/reward.json.

Deterministic by construction: no network calls, no randomness, no
reliance on the current time. Every check is a pure function of the
bytes already sitting in /workspace/output/.
"""
import csv
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUBRICS_PATH = HERE / "rubrics.json"
WEIGHTS_PATH = HERE / "test_weights.json"
OUTPUT_DIR = Path("/workspace/output")
REWARD_DIR = Path("/logs/verifier")

LINES = ["Line A", "Line B"]
VARIANTS = ["Standard", "Pro"]


def read_text(name):
    path = OUTPUT_DIR / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def read_csv_rows(name):
    text = read_text(name)
    if text is None:
        return None
    return list(csv.DictReader(text.splitlines()))


def parse_md_table(md_text):
    """Extract the Supporting Figures table rows as list of dicts."""
    if md_text is None:
        return []
    rows = []
    lines = md_text.splitlines()
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Line | Variant | Defect Rate (%) | Mix (%) |"):
            in_table = True
            continue
        if in_table:
            if stripped.startswith("|---") or stripped.startswith("|-"):
                continue
            if not stripped.startswith("|"):
                break
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) != 4:
                continue
            rows.append(
                {
                    "line": cells[0],
                    "variant": cells[1],
                    "defect_rate_pct": cells[2],
                    "mix_pct": cells[3],
                }
            )
    return rows


# Regex used to find the exact recommendation line. Anchored with ^/$ per
# line (re.MULTILINE) so it must be the WHOLE line, not a substring buried
# in other text — that's what "on its own line" in the rubric means.
RECOMMEND_LINE_RE = re.compile(r"^Recommended line: (Line A|Line B)$", re.MULTILINE)

SECTION_HEADING_RE = re.compile(r"^## +\S", re.MULTILINE)


def get_section(md, heading):
    """Return the text of the section starting at `## {heading}` up to
    (but not including) the next `## ` heading, or "" if the heading is
    missing. Used so checks scoped to a named section (per the
    instruction's "A section titled ...") can't be satisfied by matching
    text anywhere else in the document.
    """
    if not md:
        return ""
    idx = md.find(f"## {heading}")
    if idx == -1:
        return ""
    rest = md[idx:]
    m = SECTION_HEADING_RE.search(rest, 1)
    return rest[: m.start()] if m else rest


def check_item_01(md, csvrows, table):
    # The instruction requires the exact line inside "A section titled
    # `## Recommendation`" — not merely somewhere in the document. Scope
    # the search to that section so a submission that places the line
    # elsewhere does not pass.
    section = get_section(md, "Recommendation")
    return bool(RECOMMEND_LINE_RE.search(section))


def check_item_35(md, csvrows, table):
    # Correctness, independent of formatting: the recommended line must be
    # the objectively correct answer (Line A wins both variants
    # individually), not whichever the submission's own numbers happen to
    # imply. This guards against a mix-skewed blended rate looking better
    # AND against grading a self-consistent-but-wrong submission as correct.
    section = get_section(md, "Recommendation")
    matches = RECOMMEND_LINE_RE.findall(section)
    if len(set(matches)) != 1:
        return False
    return matches[0] == "Line A"


def check_csv_row_range(csvrows, line, variant, field, lo, hi):
    if not csvrows:
        return False
    for row in csvrows:
        if row.get("line") == line and row.get("product_variant") == variant:
            try:
                val = float(row[field])
            except (KeyError, ValueError):
                return False
            return lo <= val <= hi
    return False


def check_item_04(md, csvrows, table):
    return (OUTPUT_DIR / "recommendation.md").is_file()


def check_item_05(md, csvrows, table):
    return (OUTPUT_DIR / "summary.csv").is_file()


def check_item_06(md, csvrows, table):
    return bool(md) and re.search(r"^## Recommendation$", md, re.MULTILINE)


def check_item_07(md, csvrows, table):
    return bool(md) and re.search(r"^## Supporting Figures$", md, re.MULTILINE)


def check_item_08(md, csvrows, table):
    if not md:
        return False
    idx = md.find("## Supporting Figures")
    if idx == -1:
        return False
    # The header row must appear AFTER the Supporting Figures heading, not
    # merely anywhere in the file (a table placed elsewhere previously
    # passed this check).
    return "| Line | Variant | Defect Rate (%) | Mix (%) |" in md[idx:]


def check_item_09(md, csvrows, table):
    text = read_text("summary.csv") or ""
    first_line = text.splitlines()[0] if text else ""
    return first_line == "line,product_variant,defect_rate_pct,mix_pct"


def check_item_10(md, csvrows, table):
    text = read_text("summary.csv") or ""
    lines = [l for l in text.splitlines() if l.strip()]
    return len(lines) == 5


def check_item_11(md, csvrows, table):
    return len(table) == 4


def check_item_18(md, csvrows, table):
    if not csvrows:
        return False
    return all(row.get("line") in LINES for row in csvrows)


def check_item_19(md, csvrows, table):
    if not csvrows:
        return False
    return all(row.get("product_variant") in VARIANTS for row in csvrows)


def check_item_20(md, csvrows, table):
    if not csvrows:
        return False
    return all(re.fullmatch(r"\d+\.\d", row.get("defect_rate_pct", "")) for row in csvrows)


def check_item_21(md, csvrows, table):
    if not csvrows:
        return False
    return all(re.fullmatch(r"\d+", row.get("mix_pct", "")) for row in csvrows)


def find_table_val(table, line, variant, field):
    for row in table:
        if row["line"] == line and row["variant"] == variant:
            return row[field]
    return None


def find_csv_val(csvrows, line, variant, field):
    for row in csvrows or []:
        if row.get("line") == line and row.get("product_variant") == variant:
            return row.get(field)
    return None


def check_cross_file_match(md, csvrows, table, line, variant):
    # The instruction requires the figures to "match exactly" between the
    # two files. float() equates differently-formatted-but-numerically-
    # equal strings (e.g. md "2.10" vs csv "2.1"), which isn't "exactly".
    # Compare the trimmed strings directly instead.
    md_val = find_table_val(table, line, variant, "defect_rate_pct")
    csv_val = find_csv_val(csvrows, line, variant, "defect_rate_pct")
    if md_val is None or csv_val is None:
        return False
    return md_val.strip() == csv_val.strip()


def check_table_row_presence(table, line, variant):
    return any(row["line"] == line and row["variant"] == variant for row in table)


def check_cross_file_match_mix(md, csvrows, table, line, variant):
    # Same reasoning as check_cross_file_match: int() equates differently
    # formatted-but-numerically-equal strings (e.g. md "045" vs csv "45").
    # Compare the trimmed strings directly instead.
    md_val = find_table_val(table, line, variant, "mix_pct")
    csv_val = find_csv_val(csvrows, line, variant, "mix_pct")
    if md_val is None or csv_val is None:
        return False
    return md_val.strip() == csv_val.strip()


def check_item_30(md, csvrows, table):
    if not OUTPUT_DIR.is_dir():
        return False
    allowed = {"recommendation.md", "summary.csv"}
    # Check ALL entries (files AND subdirectories), not just files, so an
    # extra directory under output/ is correctly rejected.
    actual = {p.name for p in OUTPUT_DIR.iterdir()}
    return bool(actual) and actual == allowed


def check_item_31_penalty(md, csvrows, table):
    """True (i.e. penalty TRIGGERS) only if BOTH lines appear."""
    matches = set(RECOMMEND_LINE_RE.findall(md or ""))
    return matches == {"Line A", "Line B"}


def check_csv_row_presence(csvrows, line, variant):
    # Standalone existence fact, split out of what check_csv_row_range used
    # to bundle: does the (line, variant) row exist at all, independent of
    # whether any particular figure in it is correct.
    if not csvrows:
        return False
    return any(row.get("line") == line and row.get("product_variant") == variant for row in csvrows)


HYPOTHESIZE_RE = re.compile(r"\b(blended|aggregate|overall)\b", re.IGNORECASE)

# Words/phrases indicating the prose actually explains WHY the blended
# figure does or doesn't tell you something, not just stating a number.
EXPLANATION_HINT_RE = re.compile(
    r"\b(mix|sample|skew|composition|volume|confound|misleading|driven|"
    r"because|however|since|although|despite|due to|account|weight(ed)?)\b",
    re.IGNORECASE,
)


def check_item_40(md, csvrows, table):
    # The instruction requires naming the overall/blended defect rate "for
    # each line" — a figure for BOTH Line A and Line B, not a bare keyword
    # anywhere in the prose. Scope to the Recommendation section and
    # require a numeric figure plus both line names alongside the keyword.
    section = get_section(md, "Recommendation")
    if not section:
        return False
    if not HYPOTHESIZE_RE.search(section):
        return False
    has_number = bool(re.search(r"\d+(\.\d+)?", section))
    mentions_both_lines = "Line A" in section and "Line B" in section
    return has_number and mentions_both_lines


def check_item_44(md, csvrows, table):
    # Previously-uncovered requirement: "briefly explaining your
    # reasoning ... what it does or doesn't tell you" — not just stating
    # the figure. Require substantive text after the keyword containing
    # an explanation-style hint.
    section = get_section(md, "Recommendation")
    if not section:
        return False
    m = HYPOTHESIZE_RE.search(section)
    if not m:
        return False
    after = section[m.end():]
    words_after = len(after.split())
    return words_after >= 8 and bool(EXPLANATION_HINT_RE.search(after))


EXPECTED_ROW_ORDER = [
    ("Line A", "Standard"),
    ("Line A", "Pro"),
    ("Line B", "Standard"),
    ("Line B", "Pro"),
]


def check_item_45(md, csvrows, table):
    # Instruction specifies this exact top-to-bottom row order for the
    # Supporting Figures table; presence checks (26-29) don't cover order.
    if len(table) != 4:
        return False
    actual = [(r["line"], r["variant"]) for r in table]
    return actual == EXPECTED_ROW_ORDER


def check_item_46(md, csvrows, table):
    # Same requirement, for summary.csv's data rows.
    if not csvrows or len(csvrows) != 4:
        return False
    actual = [(r.get("line"), r.get("product_variant")) for r in csvrows]
    return actual == EXPECTED_ROW_ORDER


def check_mix_sum_penalty(csvrows, line):
    vals = []
    for variant in VARIANTS:
        v = find_csv_val(csvrows, line, variant, "mix_pct")
        if v is None:
            return False  # can't evaluate -> penalty does not trigger
        try:
            vals.append(int(v))
        except ValueError:
            return False
    return sum(vals) != 100


# item -> callable(md, csvrows, table) -> bool (True = criterion satisfied /
# penalty triggers, per that item's own polarity)
CHECKS = {
    1: check_item_01,
    2: lambda md, c, t: check_csv_row_range(c, "Line A", "Standard", "defect_rate_pct", 2.0, 2.2),
    3: lambda md, c, t: check_csv_row_range(c, "Line A", "Pro", "defect_rate_pct", 6.3, 6.5),
    4: check_item_04,
    5: check_item_05,
    6: check_item_06,
    7: check_item_07,
    8: check_item_08,
    9: check_item_09,
    10: check_item_10,
    11: check_item_11,
    12: lambda md, c, t: check_csv_row_range(c, "Line B", "Standard", "defect_rate_pct", 2.5, 2.7),
    13: lambda md, c, t: check_csv_row_range(c, "Line B", "Pro", "defect_rate_pct", 7.7, 7.9),
    14: lambda md, c, t: check_csv_row_range(c, "Line A", "Standard", "mix_pct", 44, 46),
    15: lambda md, c, t: check_csv_row_range(c, "Line A", "Pro", "mix_pct", 54, 56),
    16: lambda md, c, t: check_csv_row_range(c, "Line B", "Standard", "mix_pct", 84, 86),
    17: lambda md, c, t: check_csv_row_range(c, "Line B", "Pro", "mix_pct", 14, 16),
    18: check_item_18,
    19: check_item_19,
    20: check_item_20,
    21: check_item_21,
    22: lambda md, c, t: check_cross_file_match(md, c, t, "Line A", "Standard"),
    23: lambda md, c, t: check_cross_file_match(md, c, t, "Line B", "Pro"),
    24: lambda md, c, t: check_cross_file_match(md, c, t, "Line A", "Pro"),
    25: lambda md, c, t: check_cross_file_match(md, c, t, "Line B", "Standard"),
    26: lambda md, c, t: check_table_row_presence(t, "Line A", "Standard"),
    27: lambda md, c, t: check_table_row_presence(t, "Line A", "Pro"),
    28: lambda md, c, t: check_table_row_presence(t, "Line B", "Standard"),
    29: lambda md, c, t: check_table_row_presence(t, "Line B", "Pro"),
    30: check_item_30,
    31: lambda md, c, t: check_item_31_penalty(md, c, t),
    32: lambda md, c, t: check_mix_sum_penalty(c, "Line A"),
    33: lambda md, c, t: check_mix_sum_penalty(c, "Line B"),
    34: lambda md, c, t: check_cross_file_match_mix(md, c, t, "Line A", "Standard"),
    35: check_item_35,
    36: lambda md, c, t: check_csv_row_presence(c, "Line A", "Standard"),
    37: lambda md, c, t: check_csv_row_presence(c, "Line A", "Pro"),
    38: lambda md, c, t: check_csv_row_presence(c, "Line B", "Standard"),
    39: lambda md, c, t: check_csv_row_presence(c, "Line B", "Pro"),
    40: check_item_40,
    41: lambda md, c, t: check_cross_file_match_mix(md, c, t, "Line A", "Pro"),
    42: lambda md, c, t: check_cross_file_match_mix(md, c, t, "Line B", "Standard"),
    43: lambda md, c, t: check_cross_file_match_mix(md, c, t, "Line B", "Pro"),
    44: check_item_44,
    45: check_item_45,
    46: check_item_46,
}


def score(rubrics, weights_by_item):
    """Sum weight[i] for every item whose CHECKS[i] returns True.

    Positive items (weight > 0) add points only when satisfied. Penalty
    items (weight < 0, items 31-33) are written so their check function
    returns True exactly when the BAD condition is present — so summing
    "weight when True" naturally subtracts points only when the penalty
    condition actually fires, and adds nothing when it doesn't.
    """
    md = read_text("recommendation.md")
    csvrows = read_csv_rows("summary.csv")
    table = parse_md_table(md)

    total = 0.0
    detail = []
    for r in rubrics:
        item = r["item"]
        weight = weights_by_item[item]["weight"]
        fn = CHECKS[item]
        triggered = bool(fn(md, csvrows, table))
        if triggered:
            total += weight
        detail.append({"item": item, "weight": weight, "triggered": triggered})
    return total, detail


def main():
    rubrics = json.load(open(RUBRICS_PATH))
    weights = json.load(open(WEIGHTS_PATH))
    weights_by_item = {w["item"]: w for w in weights}

    total, detail = score(rubrics, weights_by_item)

    max_positive = sum(w["weight"] for w in weights if w["weight"] > 0)
    reward = max(0.0, total) / max_positive if max_positive else 0.0
    reward = round(reward, 6)

    # exist_ok=True matters here because the verifier can be invoked more
    # than once against the same trial (retries, re-runs of test.sh) and
    # /logs/verifier may already exist from a prior run in this container.
    # Without exist_ok=True, the second run raises FileExistsError and the
    # whole verifier crashes instead of just overwriting reward.json.
    REWARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(REWARD_DIR / "reward.json", "w", newline="") as fh:
        json.dump({"reward": reward}, fh)

    print(f"raw_total={total} max_positive={max_positive} reward={reward}")
    for d in detail:
        print(d)


if __name__ == "__main__":
    main()