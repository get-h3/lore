"""Read-only absorb triggers for board events and Auger exports.

The trigger layer only turns external records into :class:`EvidenceBlock`
values.  It never publishes a runbook, writes a board, or talks to DuckBrain.
The board cursor is the one deliberate local side effect: a JSON file stores
that board's byte offset so a restarted watcher does not replay old events.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lore.classifier import classify
from lore.evidence import EvidenceBlock

__all__ = [
    "AugerDecisionTableAdapter",
    "BoardEventWatcher",
    "JsonCursorStore",
    "parse_auger_export",
]


class JsonCursorStore:
    """Persist byte offsets keyed by a board's resolved path."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get(self, board: Path) -> int:
        if not self.path.exists():
            return 0
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid cursor store {self.path}: {exc}") from exc
        value = payload.get(str(board.resolve()), 0)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid cursor offset for {board}")
        return value

    def set(self, board: Path, offset: int) -> None:
        if offset < 0:
            raise ValueError("cursor offset must be non-negative")
        payload: dict[str, int] = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    raise TypeError("cursor store must contain an object")
                payload = {str(k): int(v) for k, v in raw.items()}
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid cursor store {self.path}: {exc}") from exc
        payload[str(board.resolve())] = offset
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.path)


@dataclass(frozen=True)
class BoardEventWatcher:
    """Consume new JSONL board records without modifying the board."""

    board: Path
    cursor_store: JsonCursorStore

    def __init__(self, board: str | Path, cursor_store: JsonCursorStore):
        object.__setattr__(self, "board", Path(board))
        object.__setattr__(self, "cursor_store", cursor_store)

    def consume(self) -> list[EvidenceBlock]:
        start = self.cursor_store.get(self.board)
        blocks: list[EvidenceBlock] = []
        with self.board.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            end = stream.tell()
            if start > end:
                raise ValueError(
                    f"cursor offset {start} is past board size {end}; refusing replay"
                )
            stream.seek(start)
            for raw in stream:
                offset = stream.tell()
                if not raw.strip():
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid board event at byte {offset}: {exc}"
                    ) from exc
                if not isinstance(event, dict):
                    raise TypeError(f"board event at byte {offset} is not an object")
                block = _board_event_block(event)
                if block is not None:
                    blocks.append(block)
        # Advance only after the complete suffix has been read successfully.
        self.cursor_store.set(self.board, end)
        return blocks


def _detail_mapping(event: dict[str, Any]) -> dict[str, Any]:
    detail = event.get("detail")
    if isinstance(detail, dict):
        return detail
    if isinstance(detail, str) and detail.strip():
        try:
            decoded = json.loads(detail)
        except json.JSONDecodeError:
            return {"lesson": detail}
        return decoded if isinstance(decoded, dict) else {"lesson": str(decoded)}
    return {}


def _board_event_block(event: dict[str, Any]) -> EvidenceBlock | None:
    event_type = str(event.get("event_type") or "")
    detail = _detail_mapping(event)
    # Completion is the normal trigger.  Other event types are accepted only
    # when they carry an explicit class/lesson, preventing status noise from
    # becoming fabricated evidence.
    if event_type != "task_completed" and not (
        detail.get("class_id") or detail.get("lesson") or event.get("class_id")
    ):
        return None
    task_id = str(event.get("task_id") or event.get("id") or "unknown")
    class_id = event.get("class_id") or detail.get("class_id")
    lesson = detail.get("lesson") or detail.get("detail") or detail.get("message")
    if not lesson:
        lesson = event.get("detail") or event_type
    if not isinstance(lesson, str):
        lesson = json.dumps(lesson, sort_keys=True)
    if not class_id:
        candidate = classify(lesson)
        if candidate.class_id != "unclassified":
            class_id = candidate.class_id
    fields = dict(event)
    fields["detail"] = detail
    if class_id:
        fields["class_id"] = class_id
    return EvidenceBlock(
        kind="board-event",
        detail=f"{task_id}: {lesson}",
        source=f"board:{task_id}",
        observed_at=event.get("timestamp")
        if isinstance(event.get("timestamp"), str)
        else None,
        fields=fields,
    )


_SECTION_NAMES = {
    "decisions": "decisions",
    "assumptions": "assumptions",
    "unknowns": "unknowns",
    "break records": "breaks",
    "breaks": "breaks",
}
_SECTION_RE = re.compile(r"^##\s+(.+?)(?:\s+\(\d+ rows?\))?\s*$", re.IGNORECASE)
_ROW_RE = re.compile(r"^###\s+(\S+)\s*$")
_FIELD_RE = re.compile(r"^-\s+([^:]+):\s*(.*)$")


def parse_auger_export(text: str) -> list[EvidenceBlock]:
    """Parse Auger's deterministic Markdown export into row evidence blocks."""
    blocks: list[EvidenceBlock] = []
    section: str | None = None
    row_id: str | None = None
    row: dict[str, str] = {}

    def flush() -> None:
        nonlocal row_id, row
        if section in _SECTION_NAMES.values() and row_id and row:
            table = section
            parts = [f"{key}={value}" for key, value in row.items() if value != "—"]
            detail = f"{table} {row_id}: " + "; ".join(parts)
            blocks.append(
                EvidenceBlock(
                    kind="duckbrain-row",
                    detail=detail,
                    source=f"auger:{table}:{row_id}",
                    fields={"table": table, "row_id": row_id, "row": dict(row)},
                )
            )
        row_id, row = None, {}

    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            flush()
            title = section_match.group(1).strip().lower()
            section = _SECTION_NAMES.get(title)
            continue
        row_match = _ROW_RE.match(line.strip())
        if row_match:
            flush()
            row_id = row_match.group(1)
            continue
        field_match = _FIELD_RE.match(line.strip())
        if field_match and row_id:
            row[field_match.group(1).strip()] = field_match.group(2).strip()
    flush()
    return blocks


class AugerDecisionTableAdapter:
    """Read an Auger export file; no Auger/DuckBrain write path exists here."""

    def __init__(self, export: str | Path):
        self.export = Path(export)

    def read(self) -> list[EvidenceBlock]:
        return parse_auger_export(self.export.read_text(encoding="utf-8"))
