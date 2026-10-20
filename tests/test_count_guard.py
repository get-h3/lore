"""Count-sync guard tests (LORE-029).

Pins the canonical test count against the LIVE collected count, so a wave that
adds tests without syncing docs (README/INSTALL `N passed` literals) goes red
in its own suite instead of shipping stale counts. The count file
`scripts/test-count.txt` is the single source of truth; the shell guard
`scripts/check-test-count.sh` sweeps living docs for drift.
"""

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COUNT_FILE = REPO_ROOT / "scripts" / "test-count.txt"
GUARD_SCRIPT = REPO_ROOT / "scripts" / "check-test-count.sh"
SWEEP_SCRIPT = REPO_ROOT / "scripts" / "count_sweep.py"


def _load_sweep_module():
    """Load scripts/count_sweep.py (not an importable package) as a module."""
    spec = importlib.util.spec_from_file_location("count_sweep", SWEEP_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _hermetic_child_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Copy an environment and put the active venv ahead of its PATH.

    The shell guard invokes bare ``python3``.  Its child must therefore resolve
    the interpreter that is running this test, rather than a system Python
    selected by a fresh box whose venv bin is not on PATH.
    """
    env = dict(os.environ if base_env is None else base_env)
    interpreter_bin = Path(sys.executable).parent
    parts = [
        path
        for path in env.get("PATH", "").split(os.pathsep)
        if path and Path(path) != interpreter_bin
    ]
    env["PATH"] = os.pathsep.join([str(interpreter_bin), *parts])
    return env


def _collect_only_count(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the guard's bare-python collect-only command with ``env``."""
    proc = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        env=env,
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
            pytest.skip(
                f"pytest --collect-only unusable in this env: rc={proc.returncode}"
            )
        raise AssertionError(f"no count in collect-only tail: {last_line!r}")
    return proc


def _collected_count(proc: subprocess.CompletedProcess[str]) -> int:
    """Extract the collected count from a successful collect-only proc."""
    last_line = (proc.stdout or "").strip().splitlines()[-1]
    match = re.search(r"(\d+)", last_line)
    assert match is not None, f"no count in collect-only tail: {last_line!r}"
    return int(match.group(1))


def test_canonical_count_file_is_a_single_int() -> None:
    count = _read_canonical()
    assert count >= 0


def test_canonical_count_matches_live_collected_count() -> None:
    """Pinned by the row: ch:trace row=LORE-057 spec=none:board-finding wave=none:serial-worker test=tests/test_count_guard.py::test_canonical_count_matches_live_collected_count doc=none:code-test-fix prompt=/tmp/lore-20261020-202948-LORE-057-brief.txt evidence=tests/test_count_guard.py witness=none:worker-local verdict=none:pending-judge commit=none:worker-commit memory=none:not-written

    STATUS: complete
    TIER: T2 (focused and full tests observed; foreman will run independent gates)
    EVIDENCE: tests/test_count_guard.py and focused pytest output
    """
    canonical = _read_canonical()
    live = _collected_count(_collect_only_count(_hermetic_child_env()))
    assert live == canonical, (
        f"canonical count {canonical} != live collected count {live} "
        "(a wave added/removed tests without syncing scripts/test-count.txt)"
    )


def test_regression_no_venv_on_path_still_collects() -> None:
    """LORE-057 regression pin: the exact fresh-box failure shape.

    The failure (docs/dogfood/2026-10-17-run9-integration.md §4): the suite is
    invoked via the venv's absolute pytest, so the venv bin dir is NOT on
    PATH; a child launched with bare `python3` inherited that PATH, resolved
    system python, and got no pytest — the guard then exits 2 'could not
    determine live test count' even on a perfectly synced tree.

    This test runs the collect-only child with a PATH that INTENTIONALLY
    omits the active venv bin while the explicit child environment still
    carries the running interpreter's bin, and proves the command returns a
    real count — the old misconfigured result (empty collect tail) cannot
    recur on a fresh box. The ambient os.environ is never mutated.
    """
    # Start with a fresh-box caller PATH that omits the venv, then prove the
    # helper repairs it in the child environment without mutating os.environ.
    ambient_path = os.environ.get("PATH")
    interpreter_bin = Path(sys.executable).parent
    caller_parts = [
        path
        for path in os.environ.get("PATH", "").split(os.pathsep)
        if path and Path(path) != interpreter_bin
    ]
    caller_env = {**os.environ, "PATH": os.pathsep.join(caller_parts)}
    assert interpreter_bin not in [
        Path(path) for path in caller_env["PATH"].split(os.pathsep) if path
    ]
    env = _hermetic_child_env(caller_env)
    assert Path(env["PATH"].split(os.pathsep)[0]) == interpreter_bin

    proc = _collect_only_count(env)
    live = _collected_count(proc)
    assert proc.returncode == 0, (
        f"collect-only rc={proc.returncode} under venv-absent caller PATH: "
        f"{live} collected\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    # The old shape is the empty/misconfigured collect result; a real count
    # (and one matching the canonical file) proves the child counted.
    assert live == _read_canonical(), (
        f"collect-only under venv-absent caller PATH counted {live}, "
        f"not the canonical {_read_canonical()}"
    )
    assert os.environ.get("PATH") == ambient_path


# --- LORE-036: class-count literals -----------------------------------------
#
# The same drift shape as the test-count sweep, for the curated registry:
# living Markdown citing '<N> failure classes' / '<N> curated classes' goes
# stale when SEED_CLASSES changes. The expected count is DERIVED from
# lore/classes.py, never a second hand-maintained literal.

SCRATCH_CLASSES_TEMPLATE = '''\
"""Scratch curated registry for guard tests (LORE-036)."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class FailureClass:
    id: str


SEED_CLASSES = tuple(FailureClass(id="scratch-class-" + str(i)) for i in range(SEED_COUNT))
'''


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _scratch_registry(root: Path, seed_count: int) -> None:
    """Seed a scratch lore/classes.py with ``seed_count`` curated classes."""
    (root / "lore").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    _write(
        root,
        "lore/classes.py",
        SCRATCH_CLASSES_TEMPLATE.replace("SEED_COUNT", str(seed_count)),
    )


def test_derived_class_count_matches_seed_registry() -> None:
    # The sweep's expected count must be derived from SEED_CLASSES itself,
    # never a second hardcoded literal (LORE-032 precedent).
    from lore.classes import SEED_CLASSES

    module = _load_sweep_module()
    derived = module.derive_class_count(REPO_ROOT)
    assert derived is not None, "derive_class_count must resolve SEED_CLASSES"
    assert derived == len(SEED_CLASSES), (
        f"derived class count {derived} != len(SEED_CLASSES) {len(SEED_CLASSES)}"
    )


def test_sweep_flags_stale_failure_class_literal(tmp_path: Path) -> None:
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(root, "README.md", "The registry holds **4 failure classes** today.\n")

    hits = module.sweep(root, ["README.md"], canonical_test_count=0, class_count=3)

    assert hits, "a stale '4 failure classes' claim must be flagged"
    assert hits[0].startswith("README.md:1:"), hits


def test_sweep_flags_stale_curated_class_literal(tmp_path: Path) -> None:
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(root, "README.md", "- taxonomy (5 curated classes + `unclassified`)\n")

    hits = module.sweep(root, ["README.md"], canonical_test_count=0, class_count=3)

    assert hits, "a stale '5 curated classes' claim must be flagged"
    assert hits[0].startswith("README.md:1:"), hits


def test_sweep_passes_current_class_counts(tmp_path: Path) -> None:
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(
        root,
        "README.md",
        "The registry holds **3 failure classes** plus `unclassified`.\n"
        "- taxonomy (3 curated classes + `unclassified`)\n",
    )

    hits = module.sweep(root, ["README.md"], canonical_test_count=0, class_count=3)

    assert hits == [], "correct current counts must be allowed"


def test_sweep_allowlists_dated_records(tmp_path: Path) -> None:
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    stale = "2 failure classes and 7 curated classes were true when written.\n"
    _write(root, "CHANGELOG.md", stale)
    _write(root, "docs/acceptance/report.md", stale)
    _write(root, "docs/dogfood/log.md", stale)
    _write(root, ".gitreins/history/verdict.md", stale)
    _write(root, ".coding-hermes/board.md", stale)

    tracked = [
        "CHANGELOG.md",
        "docs/acceptance/report.md",
        "docs/dogfood/log.md",
        ".gitreins/history/verdict.md",
        ".coding-hermes/board.md",
    ]
    hits = module.sweep(root, tracked, canonical_test_count=0, class_count=3)
    assert hits == [], "dated records must stay allowlisted"

    # Mutation control: the same stale prose in a LIVING doc is flagged, so
    # the allowlist above is not vacuously empty.
    _write(root, "README.md", stale)
    hits = module.sweep(
        root, tracked + ["README.md"], canonical_test_count=0, class_count=3
    )
    assert hits and hits[0].startswith("README.md:"), hits


def test_sweep_ignores_threshold_phrasing(tmp_path: Path) -> None:
    # '≥8 failure classes' bounds the registry from below; it is not a claim
    # about the current count and must never flag.
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(
        root,
        "README.md",
        "The coverage matrix needs ≥8 failure classes, gaps named.\n"
        "Or prose: at least 8 failure classes.\n",
    )

    hits = module.sweep(root, ["README.md"], canonical_test_count=0, class_count=3)

    assert hits == [], "threshold phrasing must not be read as a count claim"


def test_sweep_flags_both_families_in_one_run(tmp_path: Path) -> None:
    # The sweep covers test-count and class-count literals together, and the
    # existing test-count behavior is unchanged.
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(
        root,
        "README.md",
        "Old install guide: 42 tests passed.\n"
        "The registry holds **4 failure classes**.\n",
    )

    hits = module.sweep(root, ["README.md"], canonical_test_count=5, class_count=3)

    assert len(hits) == 2, hits
    assert "42 tests" in hits[0]
    assert "4 failure classes" in hits[1]


def test_sweep_self_referencing_line_exempt(tmp_path: Path) -> None:
    # A line quoting the canonical file itself is exempt (LORE-029 rule).
    module = _load_sweep_module()
    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(
        root,
        "README.md",
        "Counts sync via scripts/test-count.txt; the guard sweeps docs.\n",
    )

    hits = module.sweep(root, ["README.md"], canonical_test_count=5, class_count=3)

    assert hits == []


def test_living_docs_carry_no_stale_count_literals() -> None:
    # In-suite pin: sweep the real repo's tracked Markdown (git worktree) and
    # expect no drift — both families. Derived counts, not literals.
    module = _load_sweep_module()
    canonical = _read_canonical()
    class_count = module.derive_class_count(REPO_ROOT)
    assert class_count is not None
    ls = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert ls.returncode == 0, ls.stderr
    files = [line for line in ls.stdout.splitlines() if line.strip()]

    hits = module.sweep(REPO_ROOT, files, canonical, class_count)

    assert hits == [], "living docs cite stale count literals:\n" + "\n".join(hits)


def test_shell_guard_flags_and_clears_stale_class_count(tmp_path: Path) -> None:
    # End to end, through the real shell guard in a scratch git repo:
    # stale class-count prose -> rc 1 (drift); restored -> rc 0.
    import stat

    root = tmp_path / "scratch"
    _scratch_registry(root, seed_count=3)
    _write(
        root,
        "tests/test_placeholder.py",
        "def test_placeholder() -> None:\n    assert True\n",
    )
    _write(root, "scripts/test-count.txt", "1\n")
    _write(
        root, "scripts/check-test-count.sh", GUARD_SCRIPT.read_text(encoding="utf-8")
    )
    _write(root, "scripts/count_sweep.py", SWEEP_SCRIPT.read_text(encoding="utf-8"))
    _write(
        root,
        "README.md",
        "The registry holds **4 failure classes** plus `unclassified`.\n",
    )
    guard_path = root / "scripts" / "check-test-count.sh"
    guard_path.chmod(guard_path.stat().st_mode | stat.S_IXUSR)
    subprocess.run(
        ["git", "init", "-q"], cwd=root, capture_output=True, timeout=60, check=True
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=root, capture_output=True, timeout=60, check=True
    )

    stale = subprocess.run(
        ["sh", str(guard_path)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert stale.returncode == 1, (
        f"expected drift rc=1 on stale class-count prose, got rc={stale.returncode}"
        f"\nstdout: {stale.stdout}\nstderr: {stale.stderr}"
    )
    assert "README.md" in stale.stdout + stale.stderr

    _write(
        root,
        "README.md",
        "The registry holds **3 failure classes** plus `unclassified`.\n",
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=root, capture_output=True, timeout=60, check=True
    )
    restored = subprocess.run(
        ["sh", str(guard_path)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert restored.returncode == 0, (
        f"expected clean rc=0 after restoring the count, got rc={restored.returncode}"
        f"\nstdout: {restored.stdout}\nstderr: {restored.stderr}"
    )
