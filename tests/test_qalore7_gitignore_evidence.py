"""Regression test for QA-LORE-7: no tracked file may be gitignored.

The local-scratch rule ``*.log`` shadowed 10 tracked evidence files under
``docs/qa/evidence/`` (run9 and run14). If one of those tracked files were
ever deleted, ``git add -A`` could never re-add it, because the ignore rule
blocks re-adding untracked paths that match — silently dropping product
evidence from every export that regenerates it.

The fix adds a negation ``!docs/qa/evidence/**/*.log`` immediately after the
scratch rule in .gitignore; this test proves NO tracked file is ignored, so
the shadowing shape can never recur for any tracked path.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PREFIX = "docs/qa/evidence/"
EVIDENCE_RUNS = ("docs/qa/evidence/run9/", "docs/qa/evidence/run14/")


def _git(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command at the repo root (subprocess style of test_count_guard)."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("git is genuinely unavailable on this box")


def test_no_tracked_file_is_gitignored() -> None:
    """QA-LORE-7 regression: git check-ignore must be empty over git ls-files.

    Feeds every tracked path to ``git check-ignore --stdin`` and asserts the
    ignored set is empty (exit code 1 = none of the input paths are ignored).
    A non-empty result means a tracked file is shadowed by an ignore rule:
    deletable and unrecoverable via ``git add -A``.
    """
    tracked = [
        line for line in (_git("ls-files").stdout or "").splitlines() if line.strip()
    ]
    assert tracked, "git ls-files returned no tracked files"

    proc = _git("check-ignore", "--stdin", stdin="\n".join(tracked) + "\n")
    # check-ignore exits 0 when at least one input path is ignored, 1 when
    # none are, 128 on usage/error.
    assert proc.returncode == 1, (
        f"git check-ignore rc={proc.returncode}; ignored tracked files: "
        f"{proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
    )
    ignored = [line for line in proc.stdout.splitlines() if line.strip()]
    assert ignored == [], f"tracked files shadowed by .gitignore rules: {ignored}"


def test_qa_evidence_logs_tracked_and_not_ignored() -> None:
    """The 10 known evidence logs under run9/run14 are tracked and unignored.

    The tracked set is derived from ``git ls-files`` filtered to the
    docs/qa/evidence prefix and the .log suffix, then re-checked through
    ``git check-ignore --stdin`` so the negation rule is proven against the
    exact files it exists to protect.
    """
    tracked = [
        line for line in (_git("ls-files").stdout or "").splitlines() if line.strip()
    ]
    evidence_logs = sorted(
        path
        for path in tracked
        if path.startswith(EVIDENCE_PREFIX) and path.endswith(".log")
    )
    assert len(evidence_logs) == 10, (
        f"expected 10 tracked evidence logs, found {len(evidence_logs)}: "
        f"{evidence_logs}"
    )
    for run_dir in EVIDENCE_RUNS:
        assert any(path.startswith(run_dir) for path in evidence_logs), (
            f"no tracked evidence logs under {run_dir}: {evidence_logs}"
        )

    proc = _git("check-ignore", "--stdin", stdin="\n".join(evidence_logs) + "\n")
    assert proc.returncode == 1, (
        f"evidence logs still ignored (rc={proc.returncode}): {proc.stdout.strip()}"
    )
    ignored = [line for line in proc.stdout.splitlines() if line.strip()]
    assert ignored == [], f"evidence logs shadowed by .gitignore: {ignored}"
