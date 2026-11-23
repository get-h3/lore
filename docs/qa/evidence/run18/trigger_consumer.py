"""Run-18 dogfood consumer for LORE-071 (docs/ABSORB-TRIGGER.md, verbatim shape).

BoardEventWatcher over the repo's OWN board events.jsonl (read-only),
cursor in scratch (owner-managed per docs), then absorb_sweep.
"""

import json
import sys

from lore.absorb import absorb_sweep
from lore.trigger import AugerDecisionTableAdapter, BoardEventWatcher, JsonCursorStore

BOARD = "/home/kara/get-h3/lore/.coding-hermes/board/events.jsonl"
CURSOR = "/home/kara/.hermes/cache/scratch/lore-df-20261123-tick/board-cursor.json"

# Arm A: first consume over the real board (fresh cursor).
w = BoardEventWatcher(BOARD, JsonCursorStore(CURSOR))
blocks = w.consume()
print(f"arm-A blocks={len(blocks)}")
props = absorb_sweep(blocks, source="board-event")
print(f"arm-A proposals={len(props)}")
for p in props[:5]:
    print(
        json.dumps(
            {
                "class_id": getattr(p, "class_id", None),
                "action": getattr(p, "action", None),
                "blocks": len(getattr(p, "evidence", []) or []),
            },
            default=str,
        )
    )

# Arm B: restart semantics — consume again, same cursor; must NOT replay.
w2 = BoardEventWatcher(BOARD, JsonCursorStore(CURSOR))
blocks2 = w2.consume()
print(f"arm-B blocks={len(blocks2)} (restart, expect 0)")

# Arm C: Auger adapter on the shipped fixture.
a = AugerDecisionTableAdapter("/home/kara/get-h3/lore/tests/fixtures/auger-export.md")
ablocks = a.parse()
print(f"arm-C auger_blocks={len(ablocks)}")
for b in ablocks[:4]:
    prov = getattr(b, "provenance", None) or getattr(b, "source", None)
    print(f"  provenance={prov}")
aprops = absorb_sweep(ablocks, source="auger")
print(f"arm-C proposals={len(aprops)}")
sys.exit(0)
