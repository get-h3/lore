from __future__ import annotations

import json
from pathlib import Path

from lore.absorb import absorb_sweep
from lore.evidence import EvidenceBlock
from lore.trigger import (
    AugerDecisionTableAdapter,
    BoardEventWatcher,
    JsonCursorStore,
    parse_auger_export,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_board_event_watcher_reads_only_new_events_and_resumes(tmp_path):
    board = tmp_path / "events.jsonl"
    board.write_text((FIXTURES / "board-events.jsonl").read_text(), encoding="utf-8")
    cursor = tmp_path / "cursor.json"
    watcher = BoardEventWatcher(board, JsonCursorStore(cursor))

    first = watcher.consume()
    assert len(first) == 3
    assert all(isinstance(block, EvidenceBlock) for block in first)
    assert first[0].kind == "board-event"
    assert first[0].source == "board:LORE-003"
    assert first[0].fields["class_id"] == "gateway-drain-window"

    with board.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "id": 4,
                    "timestamp": "2026-09-23T10:00:00+00:00",
                    "event_type": "task_completed",
                    "task_id": "LORE-071",
                    "actor": "worker",
                    "detail": json.dumps(
                        {
                            "class_id": "gateway-drain-window",
                            "lesson": "wait for the drain window",
                        }
                    ),
                }
            )
            + "\n"
        )

    second = BoardEventWatcher(board, JsonCursorStore(cursor)).consume()
    assert len(second) == 1
    assert second[0].fields["task_id"] == "LORE-071"
    assert BoardEventWatcher(board, JsonCursorStore(cursor)).consume() == []


def test_cursor_resume_falsifier_fails_without_persistence(tmp_path):
    board = tmp_path / "events.jsonl"
    board.write_text((FIXTURES / "board-events.jsonl").read_text(), encoding="utf-8")
    cursor = tmp_path / "cursor.json"
    watcher = BoardEventWatcher(board, JsonCursorStore(cursor))
    assert len(watcher.consume()) == 3

    # Mutation proof: a memory-only cursor injected directly replays the old
    # suffix after a restart — the same board whose persisted store returned
    # only new events. (No monkeypatch: consume() uses the injected instance,
    # so patching the class attribute is dead code.)
    class MemoryOnlyCursor:
        def get(self, _board):
            return 0

        def set(self, _board, _offset):
            return None

    assert len(BoardEventWatcher(board, MemoryOnlyCursor()).consume()) == 3
    assert len(BoardEventWatcher(board, JsonCursorStore(cursor)).consume()) == 0


def test_board_event_watcher_ignores_non_class_events(tmp_path):
    board = tmp_path / "events.jsonl"
    board.write_text(
        json.dumps({"event_type": "task_updated", "task_id": "X", "detail": "{}"})
        + "\n",
        encoding="utf-8",
    )
    assert (
        BoardEventWatcher(board, JsonCursorStore(tmp_path / "cursor.json")).consume()
        == []
    )


def test_auger_adapter_provenance_names_table_and_row_id():
    blocks = parse_auger_export(
        (FIXTURES / "auger-export.md").read_text(encoding="utf-8")
    )
    assert len(blocks) == 4
    assert blocks[0].kind == "duckbrain-row"
    assert blocks[0].source == "auger:decisions:D-001"
    assert "pause before gateway restart" in blocks[0].detail
    assert blocks[0].fields["table"] == "decisions"
    assert blocks[0].fields["row_id"] == "D-001"


def test_adapter_is_read_only_and_flows_to_absorb_proposal(tmp_path):
    export = FIXTURES / "auger-export.md"
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    blocks = AugerDecisionTableAdapter(export).read()
    proposals = absorb_sweep(blocks, source="auger")
    after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    assert before == after
    assert proposals
    assert all(p["provenance"]["source"] == "auger" for p in proposals)
    assert any(p["action"] == "update" for p in proposals)


def test_board_event_trail_flows_to_proposal_without_runbook_write(tmp_path):
    board = tmp_path / "events.jsonl"
    board.write_text((FIXTURES / "board-events.jsonl").read_text(), encoding="utf-8")
    runbook_tree = tmp_path / "runbooks"
    runbook_tree.mkdir()
    marker = runbook_tree / "existing.md"
    marker.write_text("operator-owned", encoding="utf-8")
    blocks = BoardEventWatcher(
        board, JsonCursorStore(tmp_path / "cursor.json")
    ).consume()
    proposals = absorb_sweep(blocks, board=str(board), source="board-event")
    assert proposals
    assert all(p["provenance"]["kind"] == "absorb-sweep" for p in proposals)
    assert marker.read_text(encoding="utf-8") == "operator-owned"
    assert sorted(p.name for p in runbook_tree.iterdir()) == ["existing.md"]
