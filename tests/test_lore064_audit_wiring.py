"""LORE-064: audit wiring — the history-driven freshness signal (PRD SC-3).

The disease: ``validate --execute`` produced LintReports with drift data and
persisted them to ``.lore/validate-history.jsonl`` (LORE-045), but
``_audit_rows()`` read runbooks straight from the static registry and never
consulted the history — ``lore audit --format json`` showed every class as
``proposal`` forever, even seconds after a drifted lint on the same box.

The fix: ``_audit_rows()`` reads each class's newest local history record
and, when the record shows drift (non-empty ``drifted_orders``), flips the
ROW to ``status=stale`` with a ``stale_reason`` built from the persisted
drift data — the same flip ``apply_lint`` makes (``"lint drift: check N
(outcome)"``), now driven by persisted evidence instead of a live report.

HONESTY LAWS pinned here (never regressed):
- the history is EVIDENCE a lint ran on this box, NEVER operator
  attestation: ``last_validated`` stays ``no data`` in every drifted row;
- a class whose newest record is green (or env-absent-only, or template-
  only) does NOT flip — honest absence and plan-only checks are not rot;
- no history (missing/empty file, no record for the class, malformed
  lines) → audit output is exactly what it was before;
- the registry runbook is never mutated — audit is read-only (rows are
  copies; a later compile of the same class still reports ``proposal``).

SAFETY: no real subprocess anywhere — drift evidence is written directly
as history records (the shape ``persist_validate_history`` writes) and, in
the apply_lint integration tests, produced through the injectable runner
seam (``lore.validate._default_runner`` monkeypatch). CLI tests use
``monkeypatch.chdir`` so the CWD-relative ``HISTORY_FILE`` resolves into
the tmp dir (same pattern as the LORE-045 tests). An explicit
``history_path`` parameter is the unit-test seam for ``_audit_rows``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lore.__main__ import _audit_rows, _history_drift_reason, main
from lore.compiler import compile_all, compile_class
from lore.runbook import STATUS_PROPOSAL, STATUS_STALE, Check, Runbook
from lore.validate import (
    DRIFT_OUTCOMES,
    HONESTY_LABEL,
    apply_lint,
    lint_runbook,
    persist_validate_history,
)

HISTORY_REL = ".lore/validate-history.jsonl"

A_CLASS = "fast-forward-push-reject"
B_CLASS = "shared-checkout-collision"


# ----------------------------------------------------------------- helpers
def _history_path(tmp_path: Path) -> Path:
    return tmp_path / HISTORY_REL


def _write_history(path: Path, *records: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )


def _drift_record(class_id: str, orders: list[int], outcomes: list[str]) -> dict:
    """A history record shaped exactly like persist_validate_history writes."""
    return {
        "class_id": class_id,
        "timestamp": "2026-10-17T00:00:00+00:00",
        "honesty_label": HONESTY_LABEL,
        "outcomes": outcomes,
        "drifted_orders": list(orders),
        "executed_count": len(outcomes),
        "total_checks": len(outcomes),
    }


def _row_for(rows: list[dict], class_id: str) -> dict:
    hit = next((r for r in rows if r["class_id"] == class_id), None)
    assert hit is not None, f"class {class_id} missing from audit rows"
    return hit


def _cli(argv, capsys):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _fail_runner():
    """Injectable runner: every command exits 1 (drift)."""

    def _run(command: str):
        class _R:
            returncode = 1
            stdout = ""
            stderr = "unexpected exit"
            timed_out = False

        return _R()

    return _run


def _ok_runner():
    """Injectable runner: every command exits 0 (green)."""

    def _run(command: str):
        class _R:
            returncode = 0
            stdout = "out"
            stderr = ""
            timed_out = False

        return _R()

    return _run


def _real_drift_runbook() -> Runbook:
    """A one-check runbook whose command fails under the failing runner."""
    return Runbook(
        class_id="probe-only",
        name="Probe only",
        signature="probe",
        checks=[
            Check(
                order=1,
                command="git status --short",
                expected_healthy="clean",
                expected_incident="dirty",
                decision="d",
                read_only=True,
            )
        ],
    )


# ---------------------------------------------- core wiring: _audit_rows
class TestAuditRowsWiring:
    """_audit_rows applies the history drift signal, per PRD SC-3."""

    def test_history_with_drift_flips_row_to_stale(self, tmp_path: Path) -> None:
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [2], ["ok", "error"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, A_CLASS)
        assert row["status"] == STATUS_STALE
        assert row["stale_reason"] == "lint drift: check 2 (error)"

    def test_green_history_keeps_proposal_and_no_reason(self, tmp_path: Path) -> None:
        _write_history(
            _history_path(tmp_path),
            _drift_record(B_CLASS, [], ["ok", "ok", "ok"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, B_CLASS)
        assert row["status"] == STATUS_PROPOSAL
        assert "stale_reason" not in row, "clean history must not add stale_reason"

    def test_no_history_file_leaves_rows_untouched(self, tmp_path: Path) -> None:
        missing = tmp_path / "nowhere" / HISTORY_REL
        rows = _audit_rows(history_path=missing)
        assert len(rows) == len(compile_all()), "all registry classes still listed"
        for row in rows:
            assert row["status"] == STATUS_PROPOSAL
            assert "stale_reason" not in row

    def test_env_absent_only_history_is_not_drift(self, tmp_path: Path) -> None:
        """REVIEW-LORE-003 honesty: a not-found tool is absence, not rot."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(
                B_CLASS,
                [],
                ["env-absent", "env-absent", "env-absent"],
            ),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, B_CLASS)
        assert row["status"] == STATUS_PROPOSAL
        assert "stale_reason" not in row

    def test_template_only_history_is_not_drift(self, tmp_path: Path) -> None:
        """LORE-026 plan-only checks never flip the audit row either."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(B_CLASS, [], ["template", "template"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, B_CLASS)
        assert row["status"] == STATUS_PROPOSAL
        assert "stale_reason" not in row

    def test_multiple_classes_mixed_states(self, tmp_path: Path) -> None:
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
            _drift_record(B_CLASS, [], ["ok", "ok"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        stale_ids = {r["class_id"] for r in rows if r.get("stale_reason")}
        assert stale_ids == {A_CLASS}, "only the drifted class flips"
        assert _row_for(rows, B_CLASS)["status"] == STATUS_PROPOSAL
        assert _row_for(rows, A_CLASS)["status"] == STATUS_STALE

    def test_newest_history_record_wins_drift_then_green(self, tmp_path: Path) -> None:
        """An older drifted run followed by a green run: the class is NOT stale."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
            _drift_record(A_CLASS, [], ["ok", "ok"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, A_CLASS)
        assert row["status"] == STATUS_PROPOSAL
        assert "stale_reason" not in row

    def test_newest_history_record_wins_green_then_drift(self, tmp_path: Path) -> None:
        """A green run followed by a drifted run: the class IS stale."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [], ["ok", "ok"]),
            _drift_record(A_CLASS, [1], ["ok", "timeout"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, A_CLASS)
        assert row["status"] == STATUS_STALE
        assert row["stale_reason"] == "lint drift: check 1 (timeout)"

    def test_malformed_history_lines_skipped_not_fatal(self, tmp_path: Path) -> None:
        path = _history_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "{not json at all",
                    json.dumps(
                        {  # a non-dict record is skipped too
                            "class_id": A_CLASS,
                            "drifted_orders": [1],
                        }
                    ),
                    json.dumps(
                        _drift_record(A_CLASS, [3], ["refused"]), sort_keys=True
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        rows = _audit_rows(history_path=path)
        row = _row_for(rows, A_CLASS)
        assert row["status"] == STATUS_STALE
        assert row["stale_reason"] == "lint drift: check 3 (refused)"

    def test_history_for_unknown_class_ignored(self, tmp_path: Path) -> None:
        """A record for a class no longer in the registry must not crash."""
        _write_history(
            _history_path(tmp_path),
            _drift_record("class-from-the-future", [1], ["error"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        for row in rows:
            assert "stale_reason" not in row

    def test_all_drift_outcomes_flip(self, tmp_path: Path) -> None:
        """Every DRIFT_OUTCOMES member flips the row; reason names the outcome."""
        for outcome in DRIFT_OUTCOMES:
            _write_history(
                _history_path(tmp_path),
                _drift_record(A_CLASS, [1], [outcome]),
            )
            rows = _audit_rows(history_path=_history_path(tmp_path))
            row = _row_for(rows, A_CLASS)
            assert row["status"] == STATUS_STALE, outcome
            assert row["stale_reason"] == f"lint drift: check 1 ({outcome})"

    def test_last_validated_stays_no_data_when_drifted(self, tmp_path: Path) -> None:
        """HONESTY LAW: drift evidence never becomes attestation."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, A_CLASS)
        assert row["last_validated"] == "no data"

    def test_audit_is_read_only_registry_runbook_not_mutated(
        self, tmp_path: Path
    ) -> None:
        """The stale flip lands on the ROW copy, never the registry runbook."""
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        assert _row_for(rows, A_CLASS)["status"] == STATUS_STALE
        # The registry runbook is untouched: a fresh compile is still proposal.
        rb = compile_class(A_CLASS)
        assert rb.status == STATUS_PROPOSAL

    def test_row_gains_only_expected_new_keys(self, tmp_path: Path) -> None:
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
        )
        rows = _audit_rows(history_path=_history_path(tmp_path))
        row = _row_for(rows, A_CLASS)
        expected = {
            "class_id",
            "name",
            "runbook_compiled",
            "check_count",
            "command_count",
            "last_validated",
            "status",
            "stale_reason",
        }
        # LORE-067: incident data path adds these keys
        expected.add("incident_seen")
        expected.add("coverage_note")
        assert set(row) == expected


# ------------------------------------------- apply_lint wording parity
class TestApplyLintWordingParity:
    """The audit stale_reason uses the same wording apply_lint writes."""

    def test_apply_lint_integration_produces_same_reason_via_history(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The end-to-end loop: real lint → persist → audit shows stale."""
        # Real (runner-seamed) lint of a probe runbook whose check fails.
        rb = _real_drift_runbook()
        monkeypatch.setattr("lore.validate._default_runner", _fail_runner())
        report = lint_runbook(rb)
        assert report.stale_reason == "lint drift: check 1 (error)"
        flipped = apply_lint(report, rb)
        assert flipped.status == STATUS_STALE

        # Persist the report the way validate --execute does, then audit.
        target = _history_path(tmp_path)
        (records,) = persist_validate_history([report], path=target)
        assert records["class_id"] == "probe-only"
        assert not [
            r for r in _audit_rows(history_path=target) if r["class_id"] == "probe-only"
        ], "probe-only is not a registry class"

        # A REGISTRY class: apply_lint's flip on the real runbook must match
        # what audit computes from the same report persisted to history.
        reg_rb = compile_class(A_CLASS)
        reg_report = lint_runbook(reg_rb)
        assert reg_report.drifted_orders, "premise: the registry lint drifted"
        assert apply_lint(reg_report, reg_rb).status == STATUS_STALE

        persist_validate_history([reg_report], path=target)
        audit_rows = _audit_rows(history_path=target)
        row = _row_for(audit_rows, A_CLASS)
        assert row["status"] == STATUS_STALE
        assert row["stale_reason"] == report_stale_core(reg_report)

    def test_apply_lint_green_loop_keeps_audit_proposal(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A green lint persisted → audit stays proposal, apply_lint no-ops."""
        monkeypatch.setattr("lore.validate._default_runner", _ok_runner())
        reg_rb = compile_class(B_CLASS)
        report = lint_runbook(reg_rb)
        assert report.stale_reason is None, "premise: green lint"
        assert apply_lint(report, reg_rb) is reg_rb  # no flip, same object

        target = _history_path(tmp_path)
        persist_validate_history([report], path=target)
        rows = _audit_rows(history_path=target)
        row = _row_for(rows, B_CLASS)
        assert row["status"] == STATUS_PROPOSAL
        assert "stale_reason" not in row


def report_stale_core(report) -> str:
    """The drift core of a LintReport, in apply_lint's exact wording."""
    drift = [
        (r.order, r.outcome) for r in report.results if r.outcome in DRIFT_OUTCOMES
    ]
    return "lint drift: " + ", ".join(f"check {o} ({out})" for o, out in drift)


# --------------------------------------------------- _history_drift_reason
class TestHistoryDriftReasonUnit:
    def test_empty_or_missing_drifted_orders_is_none(self) -> None:
        assert _history_drift_reason({"drifted_orders": []}) is None
        assert _history_drift_reason({}) is None
        assert _history_drift_reason({"drifted_orders": "1"}) is None, (
            "a non-list drifted_orders is malformed, never drift"
        )

    def test_reason_pairs_orders_with_outcomes(self) -> None:
        rec = {
            "drifted_orders": [1, 7],
            "outcomes": ["ok", "ok", "ok", "ok", "ok", "ok", "error", "timeout"],
        }
        assert _history_drift_reason(rec) == (
            "lint drift: check 1 (error), check 7 (timeout)"
        )

    def test_reason_survives_unpairable_outcomes(self) -> None:
        """Drift is never dropped: unpairable outcomes still name the orders."""
        rec = {"drifted_orders": [2], "outcomes": ["ok"]}  # outcomes too short
        assert _history_drift_reason(rec) == "lint drift: check 2"
        assert _history_drift_reason({"drifted_orders": [2]}) == "lint drift: check 2"
        assert (
            _history_drift_reason({"drifted_orders": [2], "outcomes": "bogus"})
            == "lint drift: check 2"
        )

    def test_env_absent_outcomes_never_make_a_reason(self) -> None:
        """drifted_orders=[] with env-absent outcomes → None (honest absence)."""
        rec = {"drifted_orders": [], "outcomes": ["env-absent", "ok"]}
        assert _history_drift_reason(rec) is None


# ------------------------------------------------------- CLI: three formats
class TestAuditCliFormats:
    """audit --format json/table/md surface the stale signal via CWD history."""

    def test_json_shows_stale_class_and_summary_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["error"]),
        )
        code, out, _err = _cli(["audit", "--format", "json"], capsys)
        assert code == 0
        data = json.loads(out)
        row = _row_for(data["classes"], A_CLASS)
        assert row["status"] == STATUS_STALE
        assert row["stale_reason"] == "lint drift: check 1 (error)"
        assert row["last_validated"] == "no data"
        assert data["summary"]["stale_classes"] == 1

    def test_json_clean_history_shows_no_stale(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [], ["ok", "ok"]),
        )
        code, out, _err = _cli(["audit", "--format", "json"], capsys)
        assert code == 0
        data = json.loads(out)
        assert data["summary"]["stale_classes"] == 0
        for row in data["classes"]:
            assert "stale_reason" not in row

    def test_json_no_history_unchanged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code, out, _err = _cli(["audit", "--format", "json"], capsys)
        assert code == 0
        data = json.loads(out)
        assert data["summary"]["stale_classes"] == 0
        for row in data["classes"]:
            assert row["status"] == STATUS_PROPOSAL
            assert "stale_reason" not in row

    def test_table_shows_stale_reason_column(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [2], ["refused"]),
        )
        code, out, _err = _cli(["audit"], capsys)  # table is the default
        assert code == 0
        assert "stale_reason" in out.splitlines()[0], "header gained the column"
        stale_line = next(ln for ln in out.splitlines() if ln.startswith(A_CLASS))
        assert "stale" in stale_line
        assert "lint drift: check 2 (refused)" in stale_line
        assert "1 stale (lint drift via local validate history)" in out

    def test_table_clean_history_has_no_stale_clause(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [], ["ok"]),
        )
        code, out, _err = _cli(["audit"], capsys)
        assert code == 0
        assert "stale (lint drift" not in out

    def test_md_shows_stale_reason_cell(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_history(
            _history_path(tmp_path),
            _drift_record(A_CLASS, [1], ["unknown"]),
        )
        code, out, _err = _cli(["audit", "--format", "md"], capsys)
        assert code == 0
        assert "stale_reason" in out.splitlines()[0], "md header gained the cell"
        stale_line = next(
            ln for ln in out.splitlines() if ln.startswith(f"| {A_CLASS} ")
        )
        assert "stale" in stale_line
        assert "lint drift: check 1 (unknown)" in stale_line
        assert "1 stale (lint drift via local validate history)" in out

    def test_md_no_history_has_no_broken_cells(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        code, out, _err = _cli(["audit", "--format", "md"], capsys)
        assert code == 0
        for ln in out.splitlines():
            if ln.startswith("|") and not ln.startswith("| class_id"):
                assert ln.count("|") == 11, f"row must have 10 cells: {ln}"

    def test_cli_reads_history_from_current_working_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ) -> None:
        """The history file is CWD-relative (LORE-045 contract): a run in a
        directory WITHOUT history shows proposal."""
        monkeypatch.chdir(tmp_path)
        assert not (_history_path(tmp_path)).exists()
        code, out, _err = _cli(["audit", "--format", "json"], capsys)
        assert code == 0
        data = json.loads(out)
        assert data["summary"]["stale_classes"] == 0

    def test_cli_validate_then_audit_full_flow(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ) -> None:
        """The PRD SC-3 user flow: validate --execute (drift) → audit stale."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("lore.validate._default_runner", _fail_runner())
        code, _out, _err = _cli(["validate", "--execute"], capsys)
        assert code == 0, "the drifted validate run succeeded (drift is data)"
        history = _history_path(tmp_path)
        assert history.is_file(), "the run persisted history (LORE-045)"
        drifted = [
            json.loads(ln)
            for ln in history.read_text(encoding="utf-8").splitlines()
            if ln.strip() and json.loads(ln).get("drifted_orders")
        ]
        assert drifted, "premise: at least one class drifted in the run"

        code, out, _err = _cli(["audit", "--format", "json"], capsys)
        assert code == 0
        data = json.loads(out)
        stale_ids = {r["class_id"] for r in data["classes"] if r.get("stale_reason")}
        assert stale_ids == {r["class_id"] for r in drifted}, (
            "every drifted class shows stale in audit, and only those"
        )
        assert data["summary"]["stale_classes"] == len(drifted)
