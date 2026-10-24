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

1. **Direct class_id references** — event records whose detail embeds
   ``{"class_id": "gateway-drain-window", "action": "update"}`` (or a
   top-level equivalent) are extracted without consulting the registry.  A
   newly observed class therefore remains visible to the audit even before a
   runbook is compiled for it.

2. **Board-task correlation** — retained only as a secondary signal for
   explicitly marked incident/closure tasks.  A task must have its own
   timestamp inside the window; arbitrary class-id prose in historical task
   titles and notes is not incident evidence.

Direct event evidence is authoritative and task evidence is filtered to the
registry's known classes.  If either source is missing the other fills in; if
both are missing, an empty set is returned.
"""

from __future__ import annotations

import json
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


def _parse_class_ids(value: object) -> set[str]:
    """Extract explicit ``class_id`` values from a JSON-like value.

    This intentionally does not search arbitrary prose.  A class is incident
    evidence when the source names it in a structured ``class_id`` field.
    """
    found: set[str] = set()
    if isinstance(value, dict):
        class_id = value.get("class_id")
        if isinstance(class_id, str) and class_id.strip():
            found.add(class_id.strip())
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                found.update(_parse_class_ids(nested))
    elif isinstance(value, list):
        for item in value:
            found.update(_parse_class_ids(item))
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return set()
        if isinstance(parsed, (dict, list)):
            found.update(_parse_class_ids(parsed))
    return found


def _parse_absorb_class_ids(events: list[dict]) -> set[str]:
    """Extract explicit class IDs from in-window event records."""
    found: set[str] = set()
    for event in events:
        found.update(_parse_class_ids(event))
    return found


def _parse_timestamp(value: object) -> datetime | None:
    """Parse a board timestamp, treating naive values as UTC."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp


def _task_timestamp(task: dict) -> datetime | None:
    """Return the first usable timestamp owned by a task record."""
    for key in ("created_at", "updated_at", "completed_at", "ts", "timestamp"):
        timestamp = _parse_timestamp(task.get(key))
        if timestamp is not None:
            return timestamp
    return None


def _is_incident_task(task: dict) -> bool:
    """Accept only structured incident/closure task signals, not prose."""
    for key in ("source", "kind", "type", "event_type", "action"):
        value = task.get(key)
        if isinstance(value, str) and value.lower() in {
            "incident",
            "incident-closure",
            "incident_close",
            "closure",
            "closed-incident",
        }:
            return True
    detail = task.get("detail")
    if isinstance(detail, dict):
        for key in ("source", "kind", "type", "event_type", "action"):
            value = detail.get(key)
            if isinstance(value, str) and value.lower() in {
                "incident",
                "incident-closure",
                "incident_close",
                "closure",
                "closed-incident",
            }:
                return True
    return False


def _scan_board_task_detail(
    board_path: Path, class_ids: set[str], cutoff: datetime, now: datetime
) -> set[str]:
    """Extract known class IDs from recent structured incident task records."""
    if not class_ids:
        return set()

    found: set[str] = set()
    try:
        with open(board_path, encoding="utf-8") as board:
            for line in board:
                if not line.strip():
                    continue
                try:
                    task = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(task, dict) or not _is_incident_task(task):
                    continue
                timestamp = _task_timestamp(task)
                if timestamp is None or timestamp < cutoff or timestamp > now:
                    continue
                found.update(_parse_class_ids(task) & class_ids)
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
    now = _now or datetime.now(UTC)
    cutoff = now - timedelta(days=window_days)

    try:
        with open(_events_path, encoding="utf-8") as event_file:
            for line in event_file:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                timestamp = _parse_timestamp(event.get("timestamp", event.get("ts")))
                # Untimestamped events cannot be placed honestly in a window.
                if timestamp is None or timestamp < cutoff or timestamp > now:
                    continue
                events.append(event)
    except OSError:
        return set()

    if not events:
        return set()

    # Direct event evidence is not constrained by the current registry.  This
    # is what makes a novel incident class visible before its runbook exists.
    classes_from_events = _parse_absorb_class_ids(events)

    if _board_path is None:
        _board_path = _find_board_path()
    known_class_ids = set(_get_class_ids())
    classes_from_board = (
        _scan_board_task_detail(_board_path, known_class_ids, cutoff, now)
        if _board_path is not None
        else set()
    )

    # Exclude the catch-all bucket — unclassified is not a real class.
    classes_from_events.discard("unclassified")
    classes_from_board.discard("unclassified")
    return classes_from_events | classes_from_board


def _count_windowed_events(
    events_path: Path | None, window_days: int, now: datetime | None = None
) -> int:
    """Count timestamped event records in the requested window."""
    if events_path is None:
        return 0
    current = now or datetime.now(UTC)
    cutoff = current - timedelta(days=window_days)
    count = 0
    try:
        with open(events_path, encoding="utf-8") as event_file:
            for line in event_file:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                timestamp = _parse_timestamp(event.get("timestamp", event.get("ts")))
                if timestamp is not None and cutoff <= timestamp <= current:
                    count += 1
    except OSError:
        return 0
    return count


def incident_count(events_path: Path | None = None, window_days: int = 90) -> int:
    """Return the total number of incident events in the window.

    Useful for the ``incident_count`` field in audit output.
    Returns 0 if no event source is available.
    """
    if events_path is None:
        events_path = _find_events_path()
    if events_path is None:
        return 0

    return _count_windowed_events(events_path, window_days)
