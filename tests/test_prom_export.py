"""Gate metrics exercise the CLI and the textfile publication boundary."""

import errno
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from lore.prom_export import export_gate_verdict

ALLOW = [
    "gate",
    "--decision",
    "no-new-lesson",
    "--reason",
    "covered",
    "--ref",
    "TEST-1",
]
DENY = ["gate", "--decision", "no-new-lesson", "--reason", ""]


def run_gate(directory: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "H3_LORE_TEXTFILE_DIR": str(directory)}
    return subprocess.run(
        [sys.executable, "-m", "lore", *args],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def metrics(directory: Path) -> dict[str, int]:
    lines = (directory / "h3_lore.prom").read_text().splitlines()
    return {
        name: int(value)
        for name, value in (line.split() for line in lines if not line.startswith("#"))
    }


def test_fresh_write_and_increment(tmp_path):
    assert run_gate(tmp_path, ALLOW).returncode == 0
    assert metrics(tmp_path) == {"lore_gate_runs_total": 1, "lore_gate_last_success": 1}
    assert run_gate(tmp_path, ALLOW).returncode == 0
    assert metrics(tmp_path)["lore_gate_runs_total"] == 2
    assert not list(tmp_path.glob("*.tmp"))
    assert (tmp_path / "h3_lore.prom").stat().st_mode & 0o444 == 0o444


def test_corrupt_existing_file_recovers(tmp_path):
    (tmp_path / "h3_lore.prom").write_text("lore_gate_runs_total nonsense\n")
    assert run_gate(tmp_path, ALLOW).returncode == 0
    assert metrics(tmp_path)["lore_gate_runs_total"] == 1


def test_denied_verdict_is_exported(tmp_path):
    assert run_gate(tmp_path, ALLOW).returncode == 0
    assert run_gate(tmp_path, DENY).returncode == 1
    assert metrics(tmp_path) == {"lore_gate_runs_total": 2, "lore_gate_last_success": 0}


def test_unwritable_directory_fails_loudly(tmp_path):
    directory = tmp_path / "readonly"
    directory.mkdir()
    directory.chmod(0o555)
    try:
        if os.access(directory, os.W_OK):
            pytest.skip("current user bypasses directory permissions")
        result = run_gate(directory, ALLOW)
        assert result.returncode != 0
        assert str(directory) in result.stderr
        assert "Permission denied" in result.stderr
    finally:
        directory.chmod(0o700)


def test_missing_directory_fails_loudly(tmp_path):
    directory = tmp_path / "missing"
    result = run_gate(directory, ALLOW)
    assert result.returncode != 0
    assert str(directory) in result.stderr
    assert "No such file or directory" in result.stderr


def test_failed_replace_preserves_previous_file(tmp_path, monkeypatch):
    monkeypatch.setenv("H3_LORE_TEXTFILE_DIR", str(tmp_path))
    export_gate_verdict(True)
    target = tmp_path / "h3_lore.prom"
    before = target.read_bytes()

    def fail_replace(src, dst):
        assert Path(src).parent == target.parent
        assert Path(dst) == target
        raise OSError(errno.EIO, "injected failure", str(dst))

    monkeypatch.setattr("lore.prom_export.os.replace", fail_replace)
    with pytest.raises(OSError, match="injected failure"):
        export_gate_verdict(False)
    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_concurrent_processes_do_not_lose_updates(tmp_path):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run_gate(tmp_path, ALLOW), range(8)))
    assert all(result.returncode == 0 for result in results)
    assert metrics(tmp_path)["lore_gate_runs_total"] == len(results)
