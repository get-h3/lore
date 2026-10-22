"""LORE-061: env_absent orders surfaced in validate output + audit table/json/md.

Acceptance:
1. ``validate --execute`` text output shows ``env_absent: checks N,M``
   when the report carries env-absent results.
2. ``_audit_rows()`` attaches ``env_absent_orders`` from the history record
   so JSON/table/md renderers carry it into the output.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from lore.runbook import Check, Runbook
from lore.validate import (
    OUTCOME_ENV_ABSENT,
    CheckResult,
    LintReport,
)

# ---------------------------------------------------------------------------
# Validate --execute text output
# ---------------------------------------------------------------------------


class TestValidateEnvAbsentTextOutput:
    def test_env_absent_line_appears_when_checks_absent(self, tmp_path: Path) -> None:
        results = [
            CheckResult(
                class_id="test",
                order=1,
                command="true",
                outcome="ok",
                exit_code=0,
                timed_out=False,
                timestamp="",
            ),
            CheckResult(
                class_id="test",
                order=3,
                command="logsey query --pattern X",
                outcome=OUTCOME_ENV_ABSENT,
                exit_code=127,
                timed_out=False,
                timestamp="",
            ),
        ]
        reports = [LintReport(class_id="test", results=results)]
        captured = StringIO()
        with (
            patch("sys.stdout", captured),
            patch("lore.__main__.HISTORY_FILE", str(tmp_path / "h.jsonl")),
            patch("lore.__main__.persist_validate_history", return_value=reports),
            patch("lore.__main__.lint_runbook", return_value=reports[0]),
        ):
            from lore.__main__ import _cmd_validate

            _cmd_validate(
                MagicMock(
                    class_id=None,
                    execute=True,
                    format="text",
                    history_path=None,
                    runner=None,
                )
            )
        output = captured.getvalue()
        assert "env_absent: checks 3" in output
        assert "did not run" in output
        assert "tool or file absent on this box" in output
        assert "env_absent: checks 1" not in output

    def test_no_env_absent_line_when_all_ok(self, tmp_path: Path) -> None:
        results = [
            CheckResult(
                class_id="test",
                order=1,
                command="true",
                outcome="ok",
                exit_code=0,
                timed_out=False,
                timestamp="",
            ),
        ]
        reports = [LintReport(class_id="test", results=results)]
        captured = StringIO()
        with (
            patch("sys.stdout", captured),
            patch("lore.__main__.HISTORY_FILE", str(tmp_path / "h.jsonl")),
            patch("lore.__main__.persist_validate_history", return_value=reports),
            patch("lore.__main__.lint_runbook", return_value=reports[0]),
        ):
            from lore.__main__ import _cmd_validate

            _cmd_validate(
                MagicMock(
                    class_id=None,
                    execute=True,
                    format="text",
                    history_path=None,
                    runner=None,
                )
            )
        output = captured.getvalue()
        assert "env_absent:" not in output

    def test_multiple_absent_orders_listed(self, tmp_path: Path) -> None:
        results = [
            CheckResult(
                class_id="test",
                order=1,
                command="logsey query X",
                outcome=OUTCOME_ENV_ABSENT,
                exit_code=127,
                timed_out=False,
                timestamp="",
            ),
            CheckResult(
                class_id="test",
                order=3,
                command="fleet.toml grep X",
                outcome=OUTCOME_ENV_ABSENT,
                exit_code=1,
                timed_out=False,
                timestamp="",
            ),
        ]
        reports = [LintReport(class_id="test", results=results)]
        captured = StringIO()
        with (
            patch("sys.stdout", captured),
            patch("lore.__main__.HISTORY_FILE", str(tmp_path / "h.jsonl")),
            patch("lore.__main__.persist_validate_history", return_value=reports),
            patch("lore.__main__.lint_runbook", return_value=reports[0]),
        ):
            from lore.__main__ import _cmd_validate

            _cmd_validate(
                MagicMock(
                    class_id=None,
                    execute=True,
                    format="text",
                    history_path=None,
                    runner=None,
                )
            )
        output = captured.getvalue()
        assert "env_absent: checks 1, 3" in output


# ---------------------------------------------------------------------------
# Audit JSON / table / md include env_absent_orders
# ---------------------------------------------------------------------------


class TestAuditEnvAbsentOrders:
    def _make_runbook(self, class_id: str, n_checks: int) -> Runbook:
        return Runbook(
            class_id=class_id,
            name=f"Test {class_id}",
            signature=f"test.{class_id}",
            checks=[
                Check(
                    order=i,
                    command="true",
                    expected_healthy="healthy",
                    expected_incident="incident",
                    decision="check",
                    read_only=True,
                )
                for i in range(1, n_checks + 1)
            ],
            evidence_trail=[],
            recovery_ladder=[],
            guardrails=[],
            status="proposal",
            last_validated=None,
        )

    def test_audit_json_includes_env_absent_orders(self, tmp_path: Path) -> None:
        import json

        rec = {
            "class_id": "test",
            "drifted_orders": [],
            "env_absent_orders": [1, 3],
            "executed_count": 1,
            "honesty_label": "test",
            "outcomes": ["env-absent", "ok", "env-absent"],
            "timestamp": "",
            "total_checks": 3,
        }
        with (
            patch(
                "lore.__main__.last_local_validation_batch",
                return_value={"test": rec},
            ),
            patch(
                "lore.__main__.compile_all",
                return_value=[self._make_runbook("test", 3)],
            ),
        ):
            captured = StringIO()
            with patch("sys.stdout", captured):
                from lore.__main__ import _cmd_audit

                _cmd_audit(
                    MagicMock(
                        format="json",
                        class_id=None,
                        history_path=None,
                        runner=None,
                    )
                )
            output = captured.getvalue()
            data = json.loads(output)
            rows = data["classes"]
            test_row = next(r for r in rows if r["class_id"] == "test")
            assert "env_absent_orders" in test_row
            assert test_row["env_absent_orders"] == [1, 3]

    def test_audit_json_without_env_absent_no_field(self, tmp_path: Path) -> None:
        import json

        rec = {
            "class_id": "test",
            "drifted_orders": [],
            "env_absent_orders": [],
            "executed_count": 1,
            "honesty_label": "test",
            "outcomes": ["ok"],
            "timestamp": "",
            "total_checks": 1,
        }
        with (
            patch(
                "lore.__main__.last_local_validation_batch",
                return_value={"test": rec},
            ),
            patch(
                "lore.__main__.compile_all",
                return_value=[self._make_runbook("test", 1)],
            ),
        ):
            captured = StringIO()
            with patch("sys.stdout", captured):
                from lore.__main__ import _cmd_audit

                _cmd_audit(
                    MagicMock(
                        format="json",
                        class_id=None,
                        history_path=None,
                        runner=None,
                    )
                )
            output = captured.getvalue()
            data = json.loads(output)
            rows = data["classes"]
            test_row = next(r for r in rows if r["class_id"] == "test")
            assert "env_absent_orders" not in test_row

    def test_audit_table_includes_env_absent_column(self, tmp_path: Path) -> None:
        rec = {
            "class_id": "test",
            "drifted_orders": [],
            "env_absent_orders": [1, 3],
            "executed_count": 1,
            "honesty_label": "test",
            "outcomes": ["env-absent", "ok", "env-absent"],
            "timestamp": "",
            "total_checks": 3,
        }
        with (
            patch(
                "lore.__main__.last_local_validation_batch",
                return_value={"test": rec},
            ),
            patch(
                "lore.__main__.compile_all",
                return_value=[self._make_runbook("test", 3)],
            ),
        ):
            captured = StringIO()
            with patch("sys.stdout", captured):
                from lore.__main__ import _cmd_audit

                _cmd_audit(
                    MagicMock(
                        format="table",
                        class_id=None,
                        history_path=None,
                        runner=None,
                    )
                )
            output = captured.getvalue()
            assert "env_absent" in output or "[1, 3]" in output

    def test_audit_md_includes_env_absent_column(self, tmp_path: Path) -> None:
        rec = {
            "class_id": "test",
            "drifted_orders": [],
            "env_absent_orders": [2],
            "executed_count": 1,
            "honesty_label": "test",
            "outcomes": ["ok", "env-absent"],
            "timestamp": "",
            "total_checks": 2,
        }
        with (
            patch(
                "lore.__main__.last_local_validation_batch",
                return_value={"test": rec},
            ),
            patch(
                "lore.__main__.compile_all",
                return_value=[self._make_runbook("test", 2)],
            ),
        ):
            captured = StringIO()
            with patch("sys.stdout", captured):
                from lore.__main__ import _cmd_audit

                _cmd_audit(
                    MagicMock(
                        format="md",
                        class_id=None,
                        history_path=None,
                        runner=None,
                    )
                )
            output = captured.getvalue()
            assert "env_absent" in output or "[2]" in output
