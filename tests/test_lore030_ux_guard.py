"""LORE-030 regression tests: fail-fast guard for pytest without dev extra.

Pins the tests/conftest.py guard: when the running interpreter cannot import
the ``lore`` package (the bare-``uv sync`` fresh-clone state, where ``uv run
pytest`` falls back to a host pytest that cannot see the project), pytest must
fail FAST with ONE clear error naming ``uv sync --extra dev`` and exit code 4
(UsageError) — instead of the flood of per-module ModuleNotFoundError
collection errors (15 on a fresh clone).

The no-lore environment is simulated (monkeypatched builtins import), not
rebuilt with real venvs.
"""

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFTEST = REPO_ROOT / "tests" / "conftest.py"
FIX = "uv sync --extra dev"


def _break_lore_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate the fresh-clone state: ``import lore`` raises ModuleNotFoundError."""

    real_import = builtins.__import__

    def broken_import(name, *args, **kwargs):
        if name == "lore" or name.startswith("lore."):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", broken_import)
    monkeypatch.delitem(sys.modules, "lore", raising=False)


def _load_conftest_hook() -> dict:
    """Execute tests/conftest.py in a fresh namespace, as pytest would."""
    ns: dict = {}
    exec(CONFTEST.read_text(encoding="utf-8"), ns)  # noqa: S102 - pinned file
    return ns


class TestGuardHook:
    """The guard hook's contract, exercised via the real conftest file."""

    def test_raises_usage_error_naming_fix_when_lore_unimportable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _break_lore_import(monkeypatch)
        hook = _load_conftest_hook()["pytest_configure"]
        with pytest.raises(pytest.UsageError) as excinfo:
            hook(None)
        message = str(excinfo.value)
        assert FIX in message, message
        assert "uv run pytest" in message, message

    def test_silent_when_lore_imports(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The documented path must never hit the guard: with lore importable
        # (dev venv), the hook is a no-op.
        monkeypatch.delitem(sys.modules, "lore", raising=False)
        hook = _load_conftest_hook()["pytest_configure"]
        assert hook(None) is None

    def test_conftest_file_present_at_tests_level(self) -> None:
        # The guard lives where pytest loads it for every collection run, and
        # fires at the earliest hook that can abort the whole run.
        assert CONFTEST.is_file()
        text = CONFTEST.read_text(encoding="utf-8")
        assert "pytest_configure" in text
        assert FIX in text


class TestGuardEndToEnd:
    """The guard wired into a real pytest run, not just called directly."""

    def test_bare_sync_failure_is_one_clear_error_not_a_traceback_flood(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        scratch = tmp_path / "scratch"
        scratch.mkdir()
        # The REAL conftest, in a scratch root whose ``lore`` is unimportable:
        # same shape the bare-uv-sync venv's host pytest hits.
        (scratch / "conftest.py").write_text(
            CONFTEST.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (scratch / "test_placeholder.py").write_text(
            "def test_placeholder():\n    assert True\n", encoding="utf-8"
        )
        # Simulate the fresh-clone import break for the whole in-process run.
        _break_lore_import(monkeypatch)
        result = pytest.main(
            ["-q", "-p", "no:cacheprovider", "--rootdir", str(scratch), str(scratch)]
        )
        captured = capsys.readouterr()
        out = captured.out + captured.err
        # Fail FAST at the right gate: UsageError exit code, ONE clear error
        # naming the fix, zero per-module tracebacks.
        assert result == pytest.ExitCode.USAGE_ERROR, (result, out)
        assert FIX in out, out
        assert out.count("ModuleNotFoundError") == 0, out
