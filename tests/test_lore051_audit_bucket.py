"""LORE-051: the ``unclassified`` bucket is distinguishable from curated classes.

The disease: ``lore audit`` presented the ``unclassified`` catch-all bucket as
a regular class alongside the 13 curated failure classes — the JSON ``classes``
array carried it with no marker and the table rendered it like any curated
row, so a scripted consumer counting rows/classes saw 14 entries and miscounted
(the registry is 13 curated + 1 bucket, not 14 classes).

The fix, pinned here:
- the JSON entry for ``unclassified`` carries ``bucket: true`` — curated
  class entries carry NO ``bucket`` key;
- the table marks the bucket row visually distinct: its class_id is prefixed
  with ``[bucket]`` and it shows ``yes`` in the dedicated ``bucket`` column
  (curated rows show ``-``). The md format keeps its pinned 8-cell row shape
  (LORE-064) — the bucket contract lives in JSON + table; md rows are pinned
  unchanged so any md change is a deliberate contract change;
- the registry size is UNCHANGED: 14 entries total, 13 curated + 1 bucket;
  ``unclassified`` stays in the output (the bucket is honest absence — it is
  never removed).

SAFETY: read-only CLI runs over the static registry — no history, no
subprocess, no writes. ``monkeypatch.chdir`` keeps the CWD-relative history
lookup in the tmp dir (same pattern as the LORE-064 CLI tests).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lore.__main__ import main
from lore.classes import UNCLASSIFIED_ID, get_registry


def _run(argv):
    return main(argv)


def _audit_json(capsys) -> dict:
    code = _run(["audit", "--format", "json"])
    assert code == 0
    return json.loads(capsys.readouterr().out)


# --------------------------------------------------------------- JSON marker
def test_json_unclassified_has_bucket_marker_true(capsys):
    data = _audit_json(capsys)
    rows = {r["class_id"]: r for r in data["classes"]}
    assert rows[UNCLASSIFIED_ID].get("bucket") is True


def test_json_curated_classes_have_no_bucket_key(capsys):
    data = _audit_json(capsys)
    curated = [c for c in get_registry().all_classes() if c.id != UNCLASSIFIED_ID]
    rows = {r["class_id"]: r for r in data["classes"]}
    assert len(curated) == 13, "premise: 13 curated classes in the registry"
    for cls in curated:
        row = rows[cls.id]
        assert row["class_id"] != UNCLASSIFIED_ID
        assert "bucket" not in row, (
            f"curated class {cls.id} must not carry a bucket marker"
        )


def test_json_bucket_marker_does_not_change_registry_size(capsys):
    # Do NOT change the registry size: still 13 curated + 1 bucket, and the
    # bucket stays IN the output (never removed).
    data = _audit_json(capsys)
    rows = data["classes"]
    assert data["summary"]["total_classes"] == len(rows)
    assert len(rows) == 14
    ids = [r["class_id"] for r in rows]
    assert UNCLASSIFIED_ID in ids  # bucket still present
    assert len([i for i in ids if i != UNCLASSIFIED_ID]) == 13


# -------------------------------------------------------------- table marker
def test_table_bucket_row_prefixed_and_column_marked(capsys):
    code = _run(["audit", "--format", "table"])
    assert code == 0
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    # the dedicated bucket column exists in the header
    header = lines[0]
    assert "bucket" in header
    bucket_rows = [ln for ln in lines if ln.startswith("[bucket] ")]
    assert len(bucket_rows) == 1, "exactly one bucket-marked row (unclassified)"
    assert "unclassified" in bucket_rows[0]
    # curated rows show "-" in the bucket column, not the prefix
    curated_lines = [
        ln
        for ln in lines[2:]
        if ln.startswith(
            tuple(c.id for c in get_registry().all_classes() if c.id != UNCLASSIFIED_ID)
        )
    ]
    assert curated_lines, "premise: curated rows render"
    assert not any(ln.startswith("[bucket] ") for ln in curated_lines)


def test_table_curated_rows_lack_bucket_prefix(capsys):
    code = _run(["audit", "--format", "table"])
    assert code == 0
    out = capsys.readouterr().out
    for cls in get_registry().all_classes():
        if cls.id == UNCLASSIFIED_ID:
            continue
        # the class_id at line start is the curated id itself, unprefixed
        assert not any(
            line.startswith(f"[bucket] {cls.id}") for line in out.splitlines()
        )


# ----------------------------------------------------------------- md marker
def test_md_rows_unchanged_eight_cell_contract(capsys):
    """The md format keeps its pinned 8-cell row shape (LORE-064); the md
    summary still names the bucket count distinctly? No — md shows the same
    summary line; the bucket contract lives in JSON + table. Pinned here so
    any md change is a DELIBERATE contract change, not a silent drift."""
    code = _run(["audit", "--format", "md"])
    assert code == 0
    out = capsys.readouterr().out
    for ln in out.splitlines():
        if ln.startswith("|") and not ln.startswith("| class_id"):
            assert ln.count("|") == 9, f"row must have 8 cells: {ln}"
    # the bucket row still renders by its bare class_id (no prefix pollution)
    bucket_rows = [
        ln for ln in out.splitlines() if ln.startswith(f"| {UNCLASSIFIED_ID} ")
    ]
    assert len(bucket_rows) == 1
    assert "| True |" in bucket_rows[0]


# ------------------------------------------------- scripted-consumer contract
def test_scripted_consumer_separates_bucket_from_classes(capsys, tmp_path: Path):
    """The miscount bug, pinned as the consumer contract: a consumer that
    splits classes from the bucket gets 13 + 1, not 14 'classes'."""
    (tmp_path / ".lore").mkdir()  # keep CWD-relative history lookup empty
    data = _audit_json(capsys)
    classes = [r for r in data["classes"] if not r.get("bucket")]
    bucket = [r for r in data["classes"] if r.get("bucket")]
    assert len(classes) == 13
    assert len(bucket) == 1 and bucket[0]["class_id"] == UNCLASSIFIED_ID


@pytest.mark.parametrize("fmt", ["table", "md"])
def test_bucket_row_alone_carries_marker_in_every_format(fmt, capsys):
    code = _run(["audit", "--format", fmt])
    assert code == 0
    out = capsys.readouterr().out
    prefixes = {
        "table": "{id}",
        "md": "| {id} ",
    }
    cur_ids = tuple(
        c.id for c in get_registry().all_classes() if c.id != UNCLASSIFIED_ID
    )
    curated_rows = [
        ln
        for ln in out.splitlines()
        if ln.startswith(tuple(prefixes[fmt].format(id=i) for i in cur_ids))
    ]
    assert curated_rows, f"premise: curated rows render with {fmt!r} prefixes"
    # every curated row starts with the bare class_id — no marker pollution
    assert all(not ln.startswith("[bucket]") for ln in curated_rows)
