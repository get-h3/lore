"""Run-18 arm A/C, corrected shapes: inspect proposal objects + adapter.read()."""

import json
import sys

from lore.absorb import absorb_sweep
from lore.trigger import AugerDecisionTableAdapter, BoardEventWatcher, JsonCursorStore

BOARD = "/home/kara/get-h3/lore/.coding-hermes/board/events.jsonl"
CURSOR = "/home/kara/.hermes/cache/scratch/lore-df-20261123-tick/board-cursor2.json"

blocks = BoardEventWatcher(BOARD, JsonCursorStore(CURSOR)).consume()
props = absorb_sweep(blocks, source="board-event")
print(f"arm-A blocks={len(blocks)} proposals={len(props)}")
for p in props:
    if isinstance(p, dict):
        print(
            json.dumps(
                {
                    k: (
                        len(v)
                        if isinstance(v, (list, dict, str)) and k == "added"
                        else v
                    )
                    for k, v in p.items()
                    if k != "added"
                },
                default=str,
            )[:400]
        )
    else:
        print(type(p).__name__, [a for a in dir(p) if not a.startswith("_")][:15])
        print(
            json.dumps(p.__dict__, default=str)[:400]
            if hasattr(p, "__dict__")
            else str(p)[:400]
        )

a = AugerDecisionTableAdapter("/home/kara/get-h3/lore/tests/fixtures/auger-export.md")
ablocks = a.read()
print(f"arm-C auger_blocks={len(ablocks)}")
for b in ablocks[:5]:
    print(
        json.dumps(b.__dict__, default=str)[:300]
        if hasattr(b, "__dict__")
        else str(b)[:300]
    )
aprops = absorb_sweep(ablocks, source="auger")
print(f"arm-C proposals={len(aprops)}")
sys.exit(0)
