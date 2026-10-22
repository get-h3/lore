"""LORE-066: persist_validate_history skips 0-check classes.

The unclassified bucket and any other zero-check class must NOT
produce a history record — a 0-check record claims "commands parse
and answer" on a run with no commands, which is false.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from lore.validate import CheckResult, LintReport, persist_validate_history


@pytest.fixture()
def zero_check_report() -> LintReport:
    """A report with zero results (e.g. the unclassified bucket)."""
    return LintReport(class_id="unclassified", results=[])


@pytest.fixture()
def one_check_report() -> LintReport:
    """A normal report with one check."""
    return LintReport(
        class_id="gateway-drain-window",
        results=[
            CheckResult(
                class_id="gateway-drain-window",
                order=1,
                command="true",
                outcome="ok",
                exit_code=0,
            ),
        ],
    )


def test_zero_check_report_skipped(zero_check_report: LintReport) -> None:
    """persist_validate_history MUST NOT write a record for a 0-check class."""
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "validate-history.jsonl"
        records = persist_validate_history(
            [zero_check_report],
            path=path,
        )
        assert records == []
        assert not path.exists() or path.read_text().strip() == ""


def test_zero_check_mixed_with_real(
    zero_check_report: LintReport,
    one_check_report: LintReport,
) -> None:
    """When a 0-check class is mixed with real classes, only real ones write."""
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "validate-history.jsonl"
        records = persist_validate_history(
            [zero_check_report, one_check_report, zero_check_report],
            path=path,
        )
        assert len(records) == 1
        assert records[0]["class_id"] == "gateway-drain-window"
        assert records[0]["total_checks"] == 1
        # Only one line in the file
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1


def test_zero_check_record_never_written(
    zero_check_report: LintReport,
) -> None:
    """A 0-check record must never appear in the history file."""
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "validate-history.jsonl"
        persist_validate_history([zero_check_report], path=path)
        # The file should not exist or be empty
        if path.exists():
            content = path.read_text()
            assert content.strip() == ""
            assert '"unclassified"' not in content
