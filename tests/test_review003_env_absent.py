"""REVIEW-LORE-003 — exit-127 / FileNotFoundError is ``env-absent``, not drift.

On a box WITHOUT logsey, ``validate --execute`` used to report the logsey
checks as ``error`` (exit 127) and flip their runbooks to ``stale`` —
conflating "the environment lacks the tool" with "the runbook drifted".
These tests pin the new distinct outcome and the honest stale_reason.
SAFETY: no real command execution — every lint call injects a fake runner.
"""

from __future__ import annotations

from lore.compiler import Check, compile_class
from lore.runbook import STATUS_STALE, Runbook
from lore.validate import (
    DRIFT_OUTCOMES,
    OUTCOME_ENV_ABSENT,
    OUTCOME_VOCABULARY,
    apply_lint,
    lint_runbook,
)


class _R:
    """Canned runner result."""

    def __init__(self, returncode, stderr="", timed_out=False):
        self.returncode = returncode
        self.stdout = ""
        self.stderr = stderr
        self.timed_out = timed_out


class Exit127Runner:
    """Simulates a shell that cannot find the binary (exit 127)."""

    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, command: str):
        self.calls.append(command)
        return _R(127, "/bin/sh: 1: logsey: not found\n")


class FileNotFoundErrorRunner:
    """Simulates a runner whose subprocess raised FileNotFoundError."""

    def __call__(self, command: str):
        return _R(None, FileNotFoundError(2, "No such file or directory"))


def _check(order: int, command: str) -> Check:
    return Check(
        order=order,
        command=command,
        expected_healthy="healthy",
        expected_incident="incident",
        decision="decision",
        read_only=True,
    )


def _rb_with(*checks: Check) -> Runbook:
    return Runbook(
        class_id="gateway-drain-window",
        name="Gateway drain window",
        signature="drain 503",
        checks=list(checks),
    )


def test_env_absent_in_vocabulary_and_not_drift():
    assert OUTCOME_ENV_ABSENT in OUTCOME_VOCABULARY
    assert OUTCOME_ENV_ABSENT not in DRIFT_OUTCOMES


def test_exit_127_classified_env_absent_runbook_not_stale():
    rb = _rb_with(_check(1, "logsey query --pattern 'drain 503' --since 30m"))
    runner = Exit127Runner()
    report = lint_runbook(rb, runner=runner)
    assert report.results[0].outcome == OUTCOME_ENV_ABSENT
    assert report.results[0].exit_code == 127
    assert "not found" in report.results[0].stderr
    assert runner.calls == [rb.checks[0].command], "the check WAS executed"
    assert report.drifted_orders == []
    assert report.stale_reason is None, "env-absent alone must not stale"
    assert report.env_absent_orders == [1]
    new = apply_lint(report, rb)
    assert new.status != STATUS_STALE
    assert new is rb  # apply_lint returns the input unchanged when not stale


def test_runner_filenotfound_error_classified_env_absent():
    rb = _rb_with(_check(1, "logsey query --since 30m"))
    report = lint_runbook(rb, runner=FileNotFoundErrorRunner())
    assert report.results[0].outcome == OUTCOME_ENV_ABSENT
    assert report.results[0].exit_code is None
    assert report.stale_reason is None
    assert report.env_absent_orders == [1]


def test_genuine_drift_still_stales():
    rb = _rb_with(_check(1, "grep -c 'drain 503' /var/log/gateway"))
    report = lint_runbook(rb, runner=lambda _cmd: _R(2, "grep: no match"))
    assert report.results[0].outcome == "error"
    assert report.stale_reason is not None
    assert "check 1 (error)" in report.stale_reason
    assert apply_lint(report, rb).status == STATUS_STALE


def test_exit_128_and_other_nonzero_stay_drift():
    # exit 128 (git-level error) is NOT claimed as env-absent: it may mean
    # the runbook's expectation is broken on this box.
    rb = _rb_with(_check(1, "git -C /tmp rev-parse HEAD"))
    report = lint_runbook(rb, runner=lambda _cmd: _R(128, "not a git repository"))
    assert report.results[0].outcome == "error"
    assert report.stale_reason is not None


def test_mixed_report_stale_reason_names_only_drifted_check():
    rb = _rb_with(
        _check(1, "logsey query --pattern 'drain 503' --since 30m"),
        _check(2, "grep -c 'drain 503' /var/log/gateway"),
        _check(3, "ls /tmp"),
    )
    codes = {"logsey": 127, "grep": 2, "ls": 0}

    def runner(command: str):
        prog = command.split()[0]
        return _R(codes[prog], "logsey: not found" if codes[prog] == 127 else "")

    report = lint_runbook(rb, runner=runner)
    assert [r.outcome for r in report.results] == [
        OUTCOME_ENV_ABSENT,
        "error",
        "ok",
    ]
    assert report.drifted_orders == [2]
    assert report.env_absent_orders == [1]
    assert report.stale_reason is not None
    assert "check 2 (error)" in report.stale_reason
    assert "check 1" not in report.stale_reason, (
        "stale_reason must name only the drifted check, never the env-absent one"
    )
    assert "env-absent" not in report.stale_reason
    new = apply_lint(report, rb)
    assert new.status == STATUS_STALE


def test_real_logsey_absent_case_end_to_end():
    """The REPORT-LORE-003 scenario: gateway-drain-window on a logsey-less box.

    Both logsey checks report env-absent; the runbook does NOT go stale.
    """
    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=Exit127Runner())
    logsey_results = [r for r in report.results if r.command.startswith("logsey")]
    assert logsey_results, "gateway seed has logsey checks"
    assert all(r.outcome == OUTCOME_ENV_ABSENT for r in logsey_results)
    assert all(r.exit_code == 127 for r in logsey_results)
    # the only executed checks were the logsey ones (templates never ran)
    assert report.drifted_orders == []
    assert report.stale_reason is None
    assert apply_lint(report, rb).status != STATUS_STALE
