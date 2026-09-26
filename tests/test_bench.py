"""LORE-042: benchmark harness contract (scripts/bench.py).

These tests pin the harness CONTRACT, never timing numbers: setup validation
(exit 2 on broken behaviour), exit codes, and named-operation output shape.
pytest never executes the timing loops (the benchmark is a scripts/ runner,
not collected pytest work) except through subprocess with --check-only,
which runs no timing loops at all.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH = REPO_ROOT / "scripts" / "bench.py"


def _run_bench(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BENCH), *argv],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO_ROOT,
        check=False,
    )


# ------------------------------------------------------------ setup contract
def test_check_only_passes_on_current_tree():
    proc = _run_bench("--check-only")
    assert proc.returncode == 0, proc.stderr
    assert "benchmark setup valid" in proc.stdout
    # --check-only must not print measured numbers.
    assert "us/op" not in proc.stdout


def test_named_operations_listed_in_setup_validation():
    proc = _run_bench("--check-only")
    stdout = proc.stdout
    # The representative hot paths the task names, each by name.
    assert "classify_signature_hit" in stdout
    assert "classify_keyword_hit" in stdout
    assert "classify_full_miss_scan" in stdout
    assert "compile_class_gateway" in stdout
    assert "validate_read_only_gate" in stdout


def test_usage_error_is_exit_2_not_a_traceback():
    proc = _run_bench("--number", "0")
    assert proc.returncode == 2
    assert "--number and --repeats must be >= 1" in proc.stderr
    assert "Traceback" not in (proc.stdout + proc.stderr)


def test_broken_setup_fails_closed_before_timing():
    """The benchmark must exit 2 when the measured code's contract breaks."""
    # Prove the fail-closed path directly on the validation entry point:
    # poison a fixture that must classify as gateway-drain-window and the
    # setup validator must refuse to run (SetupError, no numbers printed).
    script = (
        f"import sys; sys.path.insert(0, {str(BENCH.parent)!r}); "
        + "import bench; "
        + "bench.SIGNATURE_HIT_TEXT = 'poisoned fixture that matches nothing'; "
        + "sys.exit(bench.main(['--check-only']))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=REPO_ROOT,
        check=False,
    )
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert "invalid benchmark setup" in proc.stderr
    assert "us/op" not in proc.stdout


# ----------------------------------------------------- deterministic inputs
def test_benchmark_inputs_are_module_constants_not_random():
    """Deterministic inputs: import and compare against the frozen literals."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("lore_bench", BENCH)
    assert spec and spec.loader
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    assert bench.SIGNATURE_HIT_TEXT and isinstance(bench.SIGNATURE_HIT_TEXT, str)
    assert bench.KEYWORD_HIT_TEXT and isinstance(bench.KEYWORD_HIT_TEXT, str)
    assert bench.FULL_MISS_TEXT and isinstance(bench.FULL_MISS_TEXT, str)
    assert bench.GATE_COMMAND and isinstance(bench.GATE_COMMAND, str)
    # Same constants returned by build_operations() every call (deterministic).
    ops1 = bench.build_operations()
    ops2 = bench.build_operations()
    assert [op.name for op in ops1] == [op.name for op in ops2]
    assert [op.what for op in ops1] == [op.what for op in ops2]
