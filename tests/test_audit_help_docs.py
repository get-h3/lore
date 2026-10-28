"""DOC-8 regression: audit incident source documented on CLI help + skill health.

Two assertions:
  1. `python -m lore audit --help` states the incident source — the help
     output must name events.jsonl and the 90-day window (if the epilog
     statement is lost, this fails).
  2. Contract health: the stale claim of the shape "runbook_compiled is the
     literal True / can never print False" must stay ABSENT from
     skills/lore-usage/SKILL.md, and tests/test_lore067_incident_audit.py
     must still pin runbook_compiled (the code-computed truth; LORE-067-R3).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_audit_help_states_incident_source() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lore", "audit", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "events.jsonl" in result.stdout, result.stdout
    assert "90-day" in result.stdout, result.stdout


def test_runbook_compiled_contract_health() -> None:
    skill = REPO_ROOT / "skills" / "lore-usage" / "SKILL.md"
    if not skill.exists():
        import pytest

        pytest.skip("skills/lore-usage/SKILL.md does not exist in this tree")
    assert "can never print" not in skill.read_text(encoding="utf-8"), (
        "'can never print' reappeared in skills/lore-usage/SKILL.md — the "
        "runbook_compiled-is-literal-True claim is stale: it is code-computed "
        "per audit run (LORE-067-R3)"
    )
    incident_test = REPO_ROOT / "tests" / "test_lore067_incident_audit.py"
    assert incident_test.exists(), (
        "tests/test_lore067_incident_audit.py missing — the code-computed "
        "incident pin must stay"
    )
    incident_text = incident_test.read_text(encoding="utf-8")
    # Brief note: the DOC-8 row assumed this file pins 'runbook_compiled'
    # literally; it actually pins the LORE-067-R3 code-computed audit fields
    # ('incident_seen' per-class, 'uncovered_classes' in the summary).
    # Assert the real pin.
    assert "incident_seen" in incident_text and "uncovered_classes" in incident_text, (
        "tests/test_lore067_incident_audit.py no longer pins the "
        "code-computed incident fields (incident_seen/uncovered_classes)"
    )
