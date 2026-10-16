"""LORE-056: gate --record must create parent directories if missing.

Reproduces the bug where `lore gate --record /nonexistent/path/record.jsonl`
prints GATE: ALLOW then crashes with FileNotFoundError. The fix creates
parent directories before opening the record file.
"""

import json
import subprocess
import sys


def test_gate_record_creates_missing_parent_dir(tmp_path):
    """gate --record with a non-existent parent directory must create it."""
    record_path = tmp_path / "deep" / "nested" / "path" / "record.jsonl"
    assert not record_path.parent.exists(), "parent should not exist initially"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "covered",
            "--record",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Must exit 0 (ALLOW) and not crash
    assert result.returncode == 0, (
        f"exit code should be 0, got {result.returncode}\nstderr: {result.stderr}"
    )
    assert "GATE: ALLOW" in result.stdout, (
        f"expected GATE: ALLOW in stdout, got: {result.stdout}"
    )
    assert "FileNotFoundError" not in result.stderr, (
        f"must not crash with FileNotFoundError\nstderr: {result.stderr}"
    )

    # Parent directory must now exist
    assert record_path.parent.exists(), "parent directory should be created"

    # Record file must exist and contain exactly one JSON line
    assert record_path.exists(), "record file should be created"
    lines = record_path.read_text().strip().split("\n")
    assert len(lines) == 1, f"expected 1 record line, got {len(lines)}"

    # Record must be valid JSON with expected fields
    rec = json.loads(lines[0])
    assert "decision" in rec
    assert rec["decision"] == "no-new-lesson"
    assert "reason" in rec
    assert rec["reason"] == "covered"


def test_gate_record_existing_parent_dir(tmp_path):
    """gate --record with an existing parent directory must still work."""
    record_path = tmp_path / "record.jsonl"
    assert record_path.parent.exists(), "parent should exist initially"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "gate",
            "--decision",
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "test lesson",
            "--record",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"exit code should be 0, got {result.returncode}\nstderr: {result.stderr}"
    )
    assert "GATE: ALLOW" in result.stdout
    assert record_path.exists()

    lines = record_path.read_text().strip().split("\n")
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["decision"] == "absorb"


def test_gate_record_append_to_existing_file(tmp_path):
    """gate --record must append to an existing record file."""
    record_path = tmp_path / "record.jsonl"

    # First record
    result1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "first",
            "--record",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result1.returncode == 0

    # Second record (append)
    result2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "second",
            "--record",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result2.returncode == 0

    # File must contain exactly 2 records
    lines = record_path.read_text().strip().split("\n")
    assert len(lines) == 2, f"expected 2 record lines, got {len(lines)}"

    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    assert rec1["reason"] == "first"
    assert rec2["reason"] == "second"


def test_gate_deny_does_not_create_record(tmp_path):
    """gate DENY must not create a record file even if --record is given."""
    record_path = tmp_path / "deep" / "nested" / "record.jsonl"

    # DENY: absorb without required --class
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "gate",
            "--decision",
            "absorb",
            "--lesson",
            "missing class",
            "--record",
            str(record_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, (
        f"exit code should be 1 (DENY), got {result.returncode}"
    )
    assert "GATE: DENY" in result.stdout

    # Parent directory must NOT be created (no record written)
    assert not record_path.parent.exists(), "parent should not be created for DENY"
    assert not record_path.exists(), "record file should not be created for DENY"
