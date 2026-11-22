"""LORE-072: the ``unclassified`` bucket row is compiled-by-design in the audit matrix.

The disease: ``_audit_rows()`` derived ``runbook_compiled`` from
``check_count > 0`` for EVERY row, so the bucket row printed
``runbook_compiled: false`` (it must keep zero executable checks by
design — LORE-051/LORE-066). External consumers (the h3-board PM cadence)
read that False as a compile gap and filed recurring phantom rows.

The fix, pinned here:
- the bucket row's ``runbook_compiled`` becomes True — compiled-by-design:
  the bucket's registry runbook object IS compiled (signature, recovery
  ladder, guardrails); only its executable-checks list is empty BY DESIGN;
- the bucket row still carries ``bucket: true`` and keeps check_count==0,
  command_count==0 and ``last_validated: "no data"`` exactly as before —
  executability health stays readable from the counts;
- only the bucket row gains a ``compile_note`` — curated rows carry neither
  ``compile_note`` nor ``bucket`` (mirrors the LORE-051 marker convention);
- the ARM: every row in the audit ``classes`` output reports
  ``runbook_compiled`` True (sum == len), so no consumer can ever again
  read a false "uncompiled" from the matrix.

SAFETY: read-only CLI runs over the static registry. ``monkeypatch.chdir``
keeps the CWD-relative history/incident lookups in an empty tmp dir (same
pattern as the LORE-051/LORE-064 CLI tests).
"""

from __future__ import annotations

import json

from lore.__main__ import main
from lore.classes import UNCLASSIFIED_ID, get_registry

COMPILE_NOTE_TEXT = "compiled-by-design"


def _run_audit_json(monkeypatch, tmp_path, capsys) -> dict:
    empty = tmp_path / f"cwd-{id(monkeypatch)}"
    (empty / ".lore").mkdir(parents=True)
    monkeypatch.chdir(empty)
    code = main(["audit", "--format", "json"])
    assert code == 0
    return json.loads(capsys.readouterr().out)


def _rows(data: dict) -> dict:
    return {r["class_id"]: r for r in data["classes"]}


# ------------------------------------------------------------------- THE ARM
def test_arm_every_class_row_reports_compiled(monkeypatch, tmp_path, capsys):
    """THE ARM (LORE-072 AC-1): sum(runbook_compiled) == len(classes)."""
    data = _run_audit_json(monkeypatch, tmp_path, capsys)
    compiled = sum(1 for c in data["classes"] if c["runbook_compiled"])
    assert compiled == len(data["classes"]) == 14


# ------------------------------------------------------------------ the bucket
def test_bucket_row_compiled_by_design_with_untouched_counts(
    monkeypatch, tmp_path, capsys
):
    """Bucket row: compiled True, but the zero-check design contract holds."""
    data = _run_audit_json(monkeypatch, tmp_path, capsys)
    row = _rows(data)[UNCLASSIFIED_ID]
    assert row["bucket"] is True
    assert row["runbook_compiled"] is True
    assert row["check_count"] == 0
    assert row["command_count"] == 0
    assert row["last_validated"] == "no data"


def test_bucket_row_carries_compile_note_only(monkeypatch, tmp_path, capsys):
    """compile_note explains compiled-by-design and lives ONLY on the bucket."""
    data = _run_audit_json(monkeypatch, tmp_path, capsys)
    row = _rows(data)[UNCLASSIFIED_ID]
    assert COMPILE_NOTE_TEXT in row["compile_note"]
    assert "no executable checks" in row["compile_note"]

    curated = [c for c in get_registry().all_classes() if c.id != UNCLASSIFIED_ID]
    assert len(curated) == 13, "premise: 13 curated classes in the registry"
    for cls in curated:
        crow = _rows(data)[cls.id]
        assert "compile_note" not in crow, (
            f"curated class {cls.id} must not carry a compile_note"
        )
        assert "bucket" not in crow, (
            f"curated class {cls.id} must not carry a bucket marker"
        )


# --------------------------------------------------- renderer contract (table)
def test_table_bucket_row_renders_compiled_true(monkeypatch, tmp_path, capsys):
    """The table renderer reads the same rows dict — the bucket renders True."""
    empty = tmp_path / "tbl"
    (empty / ".lore").mkdir(parents=True)
    monkeypatch.chdir(empty)
    assert main(["audit", "--format", "table"]) == 0
    out = capsys.readouterr().out
    bucket_rows = [ln for ln in out.splitlines() if ln.startswith("[bucket] ")]
    assert len(bucket_rows) == 1
    assert " True " in bucket_rows[0]
    assert " False " not in bucket_rows[0]


# ----------------------------------------------------- registry stays 13+1
def test_registry_size_unchanged_by_compiled_flag(monkeypatch, tmp_path, capsys):
    data = _run_audit_json(monkeypatch, tmp_path, capsys)
    ids = [r["class_id"] for r in data["classes"]]
    assert len(ids) == 14
    assert UNCLASSIFIED_ID in ids
    assert len([i for i in ids if i != UNCLASSIFIED_ID]) == 13
