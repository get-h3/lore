#!/usr/bin/env python3
"""Probe the audit freshness path (LORE-064 wiring) in scratch ledgers.

Arms:
  A: no ledger                      -> status proposal (no signal)
  B: drifted record for a class     -> status stale + stale_reason
  C: clean record then drifted rec  -> stale  (newest wins, file order)
  D: drifted record then clean rec  -> proposal (newest wins, file order)
Read-only: writes only under /tmp. Prints the audit row per arm.
"""

import json
import os
import shutil
import subprocess

ROOT = "/tmp/lore-df14/probe"
PY = "/home/kara/get-h3/lore/.venv/bin/python"
CLS = "gateway-drain-window"

LABEL = "lint-verified: commands parse and answer on the live system; this does NOT prove recovery succeeds"


def rec(class_id, ts, outcomes, drifted):
    return {
        "class_id": class_id,
        "drifted_orders": drifted,
        "executed_count": len(outcomes),
        "honesty_label": LABEL,
        "outcomes": outcomes,
        "timestamp": ts,
        "total_checks": len(outcomes),
    }


ARMS = {
    "A-no-ledger": None,
    "B-drifted": [rec(CLS, "2026-10-20T01:00:00+00:00", ["ok", "error", "ok"], [2])],
    "C-clean-then-drifted": [
        rec(CLS, "2026-10-20T01:00:00+00:00", ["ok", "ok", "ok"], []),
        rec(CLS, "2026-10-20T02:00:00+00:00", ["ok", "error", "ok"], [2]),
    ],
    "D-drifted-then-clean": [
        rec(CLS, "2026-10-20T01:00:00+00:00", ["ok", "error", "ok"], [2]),
        rec(CLS, "2026-10-20T02:00:00+00:00", ["ok", "ok", "ok"], []),
    ],
}


def run_arm(name, records):
    d = os.path.join(ROOT, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    if records is not None:
        os.makedirs(os.path.join(d, ".lore"), exist_ok=True)
        with open(os.path.join(d, ".lore", "validate-history.jsonl"), "w") as fh:
            fh.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    p = subprocess.run(
        [PY, "-m", "lore", "audit", "--format", "json"],
        cwd=d,
        capture_output=True,
        text=True,
        check=False,
    )
    out = json.loads(p.stdout)
    row = next(r for r in out["classes"] if r["class_id"] == CLS)
    print(
        f"{name:24s} rc={p.returncode} status={row['status']:9s} "
        f"stale_reason={row.get('stale_reason')!r}"
    )
    return row


if __name__ == "__main__":
    for name, recs in ARMS.items():
        run_arm(name, recs)
