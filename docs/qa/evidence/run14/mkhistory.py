#!/usr/bin/env python3
"""Build synthetic validate-history ledgers at several sizes, in scratch dirs.

Mirrors lore's real record shape (keys sorted, one JSON object per line) so the
read path parses identical work per line. Purely scratch: nothing touches the repo.
"""

import json
import os
import shutil
from datetime import UTC, datetime, timedelta

CLASSES = [
    "gateway-drain-window",
    "secret-env-clobber",
    "shared-checkout-collision",
    "cooldown-pin-drift",
    "disk-pressure-corruption",
    "docs-count-drift",
    "fast-forward-push-reject",
    "gateway-guard-violation",
    "guard-degradation",
    "ingest-backfill-gap",
    "key-rotation-expiry",
    "spawn-hot-loop",
    "worktree-reap-data-loss",
    "unclassified",
]

ROOT = "/tmp/lore-df14"


def rec(class_id, ts, total):
    outcomes = ["ok"] * total
    return {
        "class_id": class_id,
        "drifted_orders": [],
        "executed_count": total,
        "honesty_label": (
            "lint-verified: commands parse and answer on the live system; "
            "this does NOT prove recovery succeeds"
        ),
        "outcomes": outcomes,
        "timestamp": ts,
        "total_checks": total,
    }


def build(name, rows):
    d = os.path.join(ROOT, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, ".lore"), exist_ok=True)
    base = datetime(2026, 7, 1, tzinfo=UTC)
    with open(os.path.join(d, ".lore", "validate-history.jsonl"), "w") as fh:
        for i in range(rows):
            c = CLASSES[i % len(CLASSES)]
            ts = (base + timedelta(minutes=i)).isoformat()
            fh.write(json.dumps(rec(c, ts, 7), sort_keys=True) + "\n")
    size = os.path.getsize(os.path.join(d, ".lore", "validate-history.jsonl"))
    print(f"{name}: rows={rows} bytes={size}")


if __name__ == "__main__":
    build("zero", 0)
    build("x1", 3161)  # ~ today's real ledger size on this box
    build("x10", 31610)  # 10x the data a real user accumulates
    build("x100", 316100)  # 100x
