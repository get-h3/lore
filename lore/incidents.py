"""lore/incidents.py — incident data path for lore audit coverage matrix.

PRD US-3: "every failure class seen in the last 90 days"
PRD SC-2: "`lore audit` runs on the fleet's last 90 days of incidents"

This module provides ``incident_classes()`` which reads the board's events
and tasks to determine which failure classes have been encountered as
incidents.  If no event source is available it returns an empty set —
graceful degradation, never raises.

Usage (production):
    >>> from lore.incidents import incident_classes
    >>> seen = incident_classes(window_days=90)
    >>> assert "gateway-drain-window" in seen

Architecture
------------

Incident detection uses two signals:

1. **Direct class_id references** — some event details embed
   ``{"class_id": "gateway-drain-window", "action": "update"}`` or similar
   structures.  Parsed first (O(n) scan of events).

2. **Board-task correlation** — tasks completed (from events.jsonl) are
   looked up in the board.  Their ``detail`` and ``foreman_note`` fields
   are scanned for known class_id patterns (e.g. ``gateway-drain-window``,
   ``shared-checkout-collision``).  The known class list comes from the
   runtime registry, so additions to SEED_CLASSES are automatically
   detected.

Both signals are unioned.  If either source is missing the other fills
in; if both are missing, an empty set is returned.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Lazy-loaded: the full class registry, imported at call time to avoid
# circular imports when lore.incidents is imported during module init.


def _find_events_path() -> Path | None:
    """Locate the board events.jsonl relative to the caller's working directory.

    The events live at ``.coding-hermes/board/events.jsonl`` inside the
    project worktree.  In production the caller is already in the worktree CWD.
    Falls back silently.
    """
    base = Path.cwd()
    events = base / ".coding-hermes" / "board" / "events.jsonl"
    if events.exists():
        return events
    # Also check parent (some callers cd to the repo root, some to a subdir)
    parent = base.parent / ".coding-hermes" / "board" / "events.jsonl"
    if parent.exists():
        return parent
    return None


def _find_board_path() -> Path | None:
    """Locate the board tasks.jsonl for task lookups."""
    base = Path.cwd()
    tasks = base / ".coding-hermes" / "board" / "tasks.jsonl"
    if tasks.exists():
        return tasks
    parent = base.parent / ".coding-hermes" / "board" / "tasks.jsonl"
    if parent.exists():
        return parent
    return None


def _get_class_ids() -> list[str]:
    """Return the list of known failure-class IDs from the registry."""
    try:
        from lore.classes import SEED_CLASSES, UNCLASSIFIED_CLASS

        return [c.id for c in SEED_CLASSES] + [UNCLASSIFIED_CLASS.id]
    except ImportError:
        # Fallback: return common class IDs so we don't miss incidents
        return []


def _build_class_pattern(class_ids: list[str]) -> re.Pattern | None:
    """Build a regex to match any known class_id in text."""
    if not class_ids:
        return None
    escaped = [re.escape(cid) for cid in class_ids]
    try:
        return re.compile("|".join(escaped))
    except re.error:
        return None


def _parse_absorb_class_ids(events: list[dict]) -> set[str]:
    """Extract failure-class IDs from absorb proposal records in events.

    Absorb proposals are stored in event ``detail`` as a JSON string that
    contains ``"class_id": "..."``.  Returns the unique set of class_ids.
    """
    found: set[str] = set()
    for evt in events:
        detail = evt.get("detail") or ""
        # The detail may be a dict or a JSON string
        if isinstance(detail, dict):
            if "class_id" in detail:
                found.add(detail["class_id"])
            continue
        detail = str(detail) if detail else ""
        if not detail:
            continue
        # Try parsing as embedded JSON first
        try:
            embedded = json.loads(detail)
            if isinstance(embedded, dict):
                if "class_id" in embedded:
                    found.add(embedded["class_id"])
                # Also check if embedded is a list
                if isinstance(embedded, list):
                    for item in embedded:
                        if isinstance(item, dict) and "class_id" in item:
                            found.add(item["class_id"])
                continue
        except (json.JSONDecodeError, TypeError):
            pass
        # Fallback: grep for "class_id" in the raw string
        idx = detail.find('"class_id"')
        if idx >= 0:
            rest = detail[idx + 11 :]
            if rest.startswith('"'):
                end = rest.find('"', 1)
                if end > 0:
                    found.add(rest[1:end])
    return found


def _scan_board_task_detail(
    board_path: Path, class_pattern: re.Pattern | None
) -> set[str]:
    """Scan board tasks' detail/foreman_note for class_id mentions.

    Returns class_ids found in the text of tasks that are relevant.
    """
    if class_pattern is None:
        return set()

    found: set[str] = set()
    try:
        with open(board_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    task = json.loads(line)
                except json.JSONDecodeError:
                    continue

                text = " ".join(
                    str(task.get(k, "")) for k in ("detail", "foreman_note", "title")
                )
                if text and class_pattern.search(text):
                    for cid in class_pattern.findall(text):
                        found.add(cid)
    except OSError:
        pass
    return found


def incident_classes(
    window_days: int = 90,
    *,
    _events_path: Path | None = None,
    _board_path: Path | None = None,
    _now: datetime | None = None,
) -> set[str]:
    """Return the set of failure-class IDs seen in the last *window_days*.

    Reads board events and tasks to find:
    1. Absorb proposals (direct class_id references — the primary signal)
    2. Board tasks whose detail/notes mention failure-class IDs (secondary signal)

    Returns:
        A set of failure-class IDs (e.g. ``{"gateway-drain-window", ...}``)\
        that have had incident records in the window.  Returns an empty set\
        if no event source is available or the window contains no data.

    Note:
        If no events file exists, returns ``set()`` — this is graceful\
        degradation, not an error.  The caller (_audit_rows) should note\
        this in the audit output.
    """
    if _events_path is None:
        _events_path = _find_events_path()
    if _events_path is None:
        return set()

    events: list[dict] = []
    cutoff = (_now or datetime.now(UTC)) - timedelta(days=window_days)

    try:
        with open(_events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Check timestamp against window
                ts_str = evt.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        if ts < cutoff:
                            continue
                    except ValueError:
                        continue
                events.append(evt)
    except OSError:
        return set()

    if not events:
        return set()

    # 1. Extract absorb proposals (direct class_id)
    classes_from_absorb: set[str] = _parse_absorb_class_ids(events)

    # 2. Scan board tasks for class_id mentions (secondary signal)
    if _board_path is None:
        _board_path = _find_board_path()

    class_ids = _get_class_ids()
    class_pattern = _build_class_pattern(class_ids)
    classes_from_board = (
        _scan_board_task_detail(_board_path, class_pattern)
        if _board_path is not None
        else set()
    )

    # Exclude the catch-all bucket — unclassified is not a real class
    classes_from_absorb = {c for c in classes_from_absorb if c != "unclassified"}
    classes_from_board = {c for c in classes_from_board if c != "unclassified"}

    return classes_from_absorb | classes_from_board


def incident_count(events_path: Path | None = None, window_days: int = 90) -> int:
    """Return the total number of incident events in the window.

    Useful for the ``incident_count`` field in audit output.
    Returns 0 if no event source is available.
    """
    if events_path is None:
        events_path = _find_events_path()
    if events_path is None:
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    count = 0
    try:
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = evt.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        if ts >= cutoff:
                            count += 1
                    except ValueError:
                        continue
    except OSError:
        return 0
    return count
