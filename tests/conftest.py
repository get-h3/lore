"""Fail-fast guard for a pytest run without the dev extra (LORE-030).

A fresh public clone that runs bare ``uv sync`` (without ``--extra dev``) gets
a venv with no pytest. ``uv run pytest`` then falls back to whatever pytest it
finds on PATH, whose interpreter cannot import this project — and collection
dies with one ModuleNotFoundError per test module (15 misleading tracebacks on
a fresh clone).

This conftest turns that into ONE clear, actionable error before any test
module is imported, naming the fix: ``uv sync --extra dev``. The documented
quickstart (``uv sync --extra dev`` then ``uv run pytest``) is unchanged and
stays green: the guard only fires when the running interpreter cannot import
the project package at all.
"""

from __future__ import annotations

import pytest

#: Shown verbatim when the guard fires. Must name the exact fix command.
_FIX_MESSAGE = (
    "pytest could not import the 'lore' package from this checkout, so the "
    "test suite cannot run. This venv was provisioned without the dev extra: "
    "bare 'uv sync' is NOT enough for running tests. "
    "Fix: run 'uv sync --extra dev', then 'uv run pytest'. See docs/INSTALL.md."
)


def pytest_configure(config: pytest.Config) -> None:
    """Raise one clear UsageError when ``lore`` is unimportable.

    Fires before collection, so the failure is a single ``ERROR:`` line with
    exit code 4 instead of a flood of per-file ModuleNotFoundError
    collection errors. Silent when the project imports normally.
    """
    del config
    try:
        import lore  # noqa: F401
    except ModuleNotFoundError:
        raise pytest.UsageError(_FIX_MESSAGE) from None
