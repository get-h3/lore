#!/bin/sh
# check-test-count.sh — count-sync guard (LORE-029).
#
# Exits: 0 = pass, 1 = drift found, 2 = guard misconfigured (canonical count
# missing/unreadable) — a misconfigured guard must never read as "drift".
#
# ALLOWLIST (dated records — a number there was true when written, never flag):
#   - CHANGELOG.md and docs/dogfood/**
#   - .gitreins/history/** and .coding-hermes/dogfood-log.md (dated judge
#     verdicts / dogfood log, tracked but historical)
#   - docs/acceptance/** (dated acceptance records)
# Lines quoting the canonical file itself are also ignored (self-reference).
# The guard's own files and *.sh are excluded from the sweep (self-match).

set -u

cd "$(dirname "$0")/.." || exit 2

COUNT_FILE="scripts/test-count.txt"

# --- canonical count: must exist and be numeric, else exit 2 ---------------
if [ ! -f "$COUNT_FILE" ]; then
    echo "ERROR: canonical count file $COUNT_FILE not found (guard misconfigured, not drift)" >&2
    exit 2
fi
CANONICAL=$(tr -d '[:space:]' < "$COUNT_FILE")
if [ -z "$CANONICAL" ] || ! printf '%s' "$CANONICAL" | grep -qE '^[0-9]+$'; then
    echo "ERROR: $COUNT_FILE is not a single number (got '$CANONICAL'; guard misconfigured, not drift)" >&2
    exit 2
fi

# --- parity: live collected count vs canonical ------------------------------
LIVE_RAW=$(python3 -m pytest --collect-only -q 2>/dev/null | tail -1)
LIVE=$(printf '%s' "$LIVE_RAW" | grep -oE '[0-9]+' | head -1)
if [ -z "$LIVE" ]; then
    echo "ERROR: could not determine live test count (pytest --collect-only produced no count; guard misconfigured, not drift)" >&2
    exit 2
fi
if [ "$LIVE" != "$CANONICAL" ]; then
    echo "FAIL: test-count drift: scripts/test-count.txt says $CANONICAL, live pytest --collect-only says $LIVE" >&2
    exit 1
fi

# --- stale sweep: living docs must not carry an old count literal -----------
# Date/record paths are allowlisted above; a self-referencing line (quoting
# scripts/test-count.txt or the canonical number as the sync target) is
# exempt, as is this guard itself.
#
# LORE-036: the sweep lives in scripts/count_sweep.py and covers BOTH
# families — test-count literals ('N passed'/'N tests', vs the canonical
# count) and class-count literals ('N failure classes'/'N curated classes',
# vs len(SEED_CLASSES) derived from lore/classes.py). Delegating keeps one
# allowlist and one implementation; exit 2 here means misconfigured.
SWEEP_OUT=$(python3 scripts/count_sweep.py "$CANONICAL" . 2>&1)
SWEEP_RC=$?
if [ "$SWEEP_RC" -eq 2 ]; then
    printf '%s\n' "$SWEEP_OUT" >&2
    exit 2
fi
if [ "$SWEEP_RC" -ne 0 ]; then
    printf '%s\n' "$SWEEP_OUT" >&2
    exit 1
fi

# Banner only: the derived class count (already swept above) for the PASS line.
CLASS_COUNT=$(python3 scripts/count_sweep.py --class-count . 2>/dev/null) || exit 2

echo "PASS: test-count guard: canonical=$CANONICAL matches live=$LIVE; class-count=$CLASS_COUNT; no stale count literals in living docs"
exit 0