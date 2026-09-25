"""Count-sync guard tests (LORE-029).

Pins the canonical test count against the LIVE collected count, so a wave that
adds tests without syncing docs (README/INSTALL `N passed` literals) goes red
in its own suite instead of shipping stale counts. The count file
`scripts/test-count.txt` is the single source of truth; the shell guard
`scripts/check-test-count.sh` sweeps living docs for drift.
"""

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COUNT_FILE = REPO_ROOT / "scripts" / "test-count.txt"
GUARD_SCRIPT = REPO_ROOT / "scripts" / "check-test-count.sh"


def _read_canonical() -> int:
    """Read and parse the canonical count; fails the test if malformed."""
    assert COUNT_FILE.exists(), (
        f"{COUNT_FILE} missing: the canonical test-count file must exist"
    )
    text = COUNT_FILE.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+", text), (
        f"{COUNT_FILE} must contain exactly one number, got: {text!r}"
    )
    return int(text)


def test_canonical_count_file_is_a_single_int() -> None:
    count = _read_canonical()
    assert count >= 0


def test_canonical_count_matches_live_collected_count() -> None:
    canonical = _read_canonical()
    proc = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    last_line = (
        (proc.stdout or "").strip().splitlines()[-1]
        if (proc.stdout or "").strip()
        else ""
    )
    match = re.search(r"(\d+)", last_line)
    if match is None:
        # Collection must succeed for parity to be meaningful; only skip when
        # the subprocess environment cannot run pytest at all.
        if proc.returncode != 0 and not (proc.stdout or "").strip():
            import pytest

            pytest.skip(
                f"pytest --collect-only unusable in this env: rc={proc.returncode}"
            )
        raise AssertionError(f"no count in collect-only tail: {last_line!r}")
    live = int(match.group(1))
    assert live == canonical, (
        f"canonical count {canonical} != live collected count {live} "
        "(a wave added/removed tests without syncing scripts/test-count.txt)"
    )
