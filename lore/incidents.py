"""lore/incidents.py — incident data path for lore audit coverage matrix.

PRD US-3: "every failure class seen in the last 90 days"
PRD SC-2: "`lore audit` runs on the fleet's last 90 days of incidents"

This module provides `incident_classes()` which reads the board's events.jsonl
to determine which failure classes have been encountered as incidents (via absorb
proposals or task completions referencing failure classes).  If no event source
is available it returns an empty set — graceful degradation, never raises.

Usage (production):
    >>> from lore.incidents import incident_classes
    >>> seen = incident_classes(window_days=90)
    >>> assert "gateway-drain-window" in seen
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path


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


def _classify_task_ids(
    task_ids: list[str],
) -> set[str]:
    """Map task IDs (from events) to failure-class IDs via the classifier.

    Uses the classifier's ``classify()`` function.  Returns a set of
    class_ids that matched incidents in the last window_days.
    Tasks that don't classify to any class are silently skipped.
    """
    # Import here to avoid circular imports and to allow graceful degradation
    try:
        from lore.classifier import classify, classify_all
    except ImportError:
        return set()

    class_set: set[str] = set()
    for task_id in task_ids:
        # Only LORE-* prefixed task IDs map to failure classes
        if not task_id.startswith("LORE-"):
            continue
        # Classify the task_id string to find its failure class
        result = classify(task_id)
        # Classification uses confidence > 0 as the "matched" signal
        matched = result.confidence > 0
        if matched and result.class_id == "unclassified":
            # Get near-misses from classify_all for this task_id
            all_results = classify_all(task_id)
            for r in all_results:
                if r.confidence > 0 and r.class_id != "unclassified":
                    class_set.add(r.class_id)
        elif matched and result.class_id and result.class_id != "unclassified":
            class_set.add(result.class_id)
    return class_set


def incident_classes(
    window_days: int = 90,
    *,
    _events_path: Path | None = None,
    _now: datetime | None = None,
) -> set[str]:
    """Return the set of failure-class IDs seen in the last *window_days*.

    Reads board events to find:
    1. Absorb proposals (direct class_id references — the primary signal)
    2. Completed task IDs that map to failure classes via classification

    Returns:
        A set of failure-class IDs (e.g. ``{"gateway-drain-window", ...}``)
        that have had incident records in the window.  Returns an empty set
        if no event source is available or the window contains no data.

    Note:
        If no events file exists, returns ``set()`` — this is graceful
        degradation, not an error.  The caller (_audit_rows) should note
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

    # 2. Extract task IDs and classify them
    task_ids = [evt["task_id"] for evt in events if evt.get("task_id")]
    classes_from_tasks = _classify_task_ids(task_ids)

    return classes_from_absorb | classes_from_tasks


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
