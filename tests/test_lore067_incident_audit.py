"""LORE-067-R3 regression coverage for incident audit evidence."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_audit(root: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "lore", "audit", "--format", "json"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_audit_reports_novel_class_from_windowed_event(tmp_path: Path) -> None:
    """Structured event class IDs survive registry filtering as uncovered."""
    now = datetime.now(UTC)
    _write_jsonl(
        tmp_path / ".coding-hermes/board/events.jsonl",
        [
            {
                "timestamp": now.isoformat(),
                "detail": {"class_id": "postgres-deadlock-storm", "action": "new"},
            }
        ],
    )

    payload = _run_audit(tmp_path)

    assert payload["summary"]["incident_count"] == 1
    assert "postgres-deadlock-storm" in payload["summary"]["uncovered_classes"]


def test_audit_ignores_old_prose_only_tasks(tmp_path: Path) -> None:
    """Historical task prose is not an incident signal."""
    old = (datetime.now(UTC) - timedelta(days=365)).isoformat()
    _write_jsonl(
        tmp_path / ".coding-hermes/board/events.jsonl",
        [{"timestamp": datetime.now(UTC).isoformat(), "detail": {"action": "new"}}],
    )
    _write_jsonl(
        tmp_path / ".coding-hermes/board/tasks.jsonl",
        [
            {
                "created_at": old,
                "updated_at": old,
                "title": "mention gateway-drain-window in passing",
                "detail": "documentation prose only",
            }
        ],
    )

    payload = _run_audit(tmp_path)

    assert payload["summary"]["incident_count"] == 1
    assert not [row for row in payload["classes"] if row["incident_seen"]]
    assert payload["summary"]["uncovered_classes"] == []
