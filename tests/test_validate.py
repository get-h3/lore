"""Tests for lore.validate — the read-only command lint (LORE-006).

SAFETY: these tests NEVER execute a real command. Every lint call injects
a fake runner; only the gate and the closed outcome vocabulary are
exercised against real command STRINGS.
"""

from __future__ import annotations

import json

import pytest

from lore.compiler import Check, compile_all, compile_class
from lore.runbook import STATUS_PROPOSAL, STATUS_STALE, STATUS_VALIDATED, Runbook
from lore.validate import (
    DRIFT_OUTCOMES,
    HONESTY_LABEL,
    OUTCOME_VOCABULARY,
    apply_lint,
    is_read_only_command,
    lint_all,
    lint_runbook,
)


class FakeRunner:
    """Injectable runner: records commands, returns a canned exit-code queue."""

    def __init__(self, *codes: int):
        self.codes = list(codes)
        self.calls: list[str] = []

    def __call__(self, command: str):
        self.calls.append(command)
        code = self.codes.pop(0) if self.codes else 0

        class _R:
            returncode = code
            stdout = "out"
            stderr = ""
            timed_out = False

        return _R()


class TimeoutRunner:
    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, command: str):
        self.calls.append(command)

        class _R:
            returncode = None
            stdout = ""
            stderr = ""
            timed_out = True

        return _R()


class GarbageRunner:
    """Returns something the linter cannot classify."""

    def __call__(self, command: str):
        return "not-a-result"


def _kind_runner(kind: str):
    """Runner producing one specific outcome kind for a single command."""

    def _run(command: str):
        class _R:
            returncode = 1 if kind == "error" else None
            stdout = ""
            stderr = ""
            timed_out = kind == "timeout"

        if kind == "unknown":
            return "garbage"
        return _R()

    return _run


# ---------------------------------------------------------------- gate
GATE_CASES = [
    # --- accepted: the shapes the fleet's runbooks actually use
    ("logsey query --pattern 'drain 503' --since 30m", True),
    ("grep -c 'drain 503' <gateway-log-path>", True),
    ("curl -s -o /dev/null -w '%{http_code}' <gateway-health-url>", True),
    ("git status --short", True),
    (
        "git -C <main-tree> rev-parse HEAD && git -C <worktree> rev-parse HEAD",
        True,
    ),
    ("git worktree list", True),
    ("git log --oneline -5", True),
    ("git diff HEAD~1", True),
    ("ls .git/index.lock 2>/dev/null; ps aux | grep -c '[g]it '", True),
    ("df -h <affected-volume>", True),
    ("sqlite3 <db> 'PRAGMA quick_check;'", True),
    ("sqlite3 <db> 'SELECT count(*) FROM t;'", True),
    (
        (
            "tail -c 200 <truncated.jsonl> | python3 -c "
            '"import sys,json; [json.loads(l) for l in sys.stdin if l.strip()]"'
        ),
        True,
    ),
    (
        (
            "jq -r 'select(.id==\"<project-row>\") | .status' <board>/tasks.jsonl "
            "| tail -1"
        ),
        True,
    ),
    (
        "grep -A2 '\\[\\[projects\\]\\]' fleet.toml | grep -E 'name|enabled'",
        True,
    ),
    ("<scheduler-cli> set-cooldown <project> --verify", True),
    ("docker inspect <container> --format '{{.Config.Env}}' | head -20", True),
    (
        (
            "diff <(grep -o '^[A-Z_]*' .env | sort) "
            "<(grep -o '^[A-Z_]*' .env.example | sort)"
        ),
        True,
    ),
    ("systemctl status lore-lint.timer", True),
    ("systemctl is-active nginx", True),
    ("wc -l <destination.jsonl>", True),
    ("cat /etc/hostname", True),
    ("stat -c %s <worker-log>", True),
    ("ps -o pid,etime,pcpu,cmd -p <worker-pid>", True),
    # --- refused: mutating / unrecognizable (default-deny)
    ("no data", False),
    ("", False),
    ("   ", False),
    ("git worktree add /tmp/x HEAD", False),
    ("git commit -m x", False),
    ("git push origin main", False),
    ("git reset --hard HEAD~1", False),
    ("git clean -fd", False),
    ("git checkout main", False),
    ("rm -rf /tmp/x", False),
    ("mv a b", False),
    ("kill -9 1234", False),
    ("systemctl restart foo", False),
    ("systemctl stop foo", False),
    ("systemctl start foo", False),
    ("curl -X POST https://api.example.com -d '{}'", False),
    ("curl https://x -d payload", False),
    ("curl -o /etc/passwd https://x", False),
    ("sed -i 's/a/b/' file", False),
    ("echo hi > /etc/motd", False),
    ("echo hi >> /etc/motd", False),
    ("sort < unsorted.txt", False),
    ("apt install foo", False),
    ("pip install requests", False),
    ("uv add requests", False),
    ("shutdown -h now", False),
    ("docker rm foo", False),
    ("docker system prune", False),
    ("sqlite3 <db> 'DELETE FROM t;'", False),
    ("sqlite3 <db> 'UPDATE t SET x=1;'", False),
    ("python3 -c \"import os; os.remove('/tmp/x')\"", False),
    ("echo `rm -rf /`", False),
    ("echo $(rm -rf /)", False),
    ("true &", False),
    ("grep x\nrm -rf /", False),
    ("diff <(rm -rf /) /dev/null", False),
    ("awk '{print}' file", False),  # not on the allow-list: default-deny
    ("python3 script.py", False),  # file execution: not positively read-only
    ("<scheduler-cli> set-cooldown <project>", False),  # no read-only marker
]


@pytest.mark.parametrize(("command", "expected"), GATE_CASES)
def test_gate_table(command, expected):
    assert is_read_only_command(command) == expected, f"gate({command!r})"


def test_gate_matches_every_compiled_read_only_check():
    """The gate must accept every compiled read_only=True check command."""
    for rb in compile_all():
        for check in rb.checks:
            if check.read_only and check.command != "no data":
                assert is_read_only_command(check.command), (
                    f"{rb.class_id} check {check.order} refused: {check.command!r}"
                )


# ---------------------------------------------------------------- lint
def _rb_with(*checks: Check) -> Runbook:
    return Runbook(
        class_id="gateway-drain-window",
        name="Gateway drain window",
        signature="drain 503",
        checks=list(checks),
    )


def test_lint_uses_injected_runner_never_real_commands():
    runner = FakeRunner(0, 0)
    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=runner)
    assert [r.outcome for r in report.results] == ["ok", "ok", "ok"]
    assert runner.calls == [c.command for c in rb.checks]
    assert all(r.exit_code == 0 for r in report.results)
    assert report.honesty_label == HONESTY_LABEL
    assert report.results[0].timestamp


def test_lint_outcome_vocabulary_is_closed():
    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=FakeRunner(0, 1, 3))
    assert [r.outcome for r in report.results] == ["ok", "error", "error"]
    for r in report.results:
        assert r.outcome in OUTCOME_VOCABULARY


def test_lint_timeout_and_unknown_are_distinct_outcomes():
    rb = _rb_with(_check(1, "ls"))
    report = lint_runbook(rb, runner=TimeoutRunner())
    assert report.results[0].outcome == "timeout"
    assert report.results[0].timed_out is True
    report2 = lint_runbook(rb, runner=GarbageRunner())
    assert report2.results[0].outcome == "unknown"


def test_lint_no_data_sentinel_is_absent_never_executed():
    runner = FakeRunner()
    rb = _rb_with(
        _check(1, "no data", read_only=False),
        _check(2, "ls"),
    )
    report = lint_runbook(rb, runner=runner)
    assert [r.outcome for r in report.results] == ["absent", "ok"]
    assert runner.calls == ["ls"], "the no-data sentinel must never reach the runner"
    assert report.results[0].exit_code is None


def test_lint_refused_commands_are_reported_not_skipped():
    runner = FakeRunner()
    rb = _rb_with(_check(1, "rm -rf /tmp/x", read_only=False))
    report = lint_runbook(rb, runner=runner)
    assert report.results[0].outcome == "refused"
    assert runner.calls == [], "refused commands must never reach the runner"
    assert 1 in report.drifted_orders


def test_lint_report_to_dict_roundtrip_fields():
    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=FakeRunner(0))
    d = report.to_dict()
    assert d["class_id"] == "gateway-drain-window"
    assert d["honesty_label"] == HONESTY_LABEL
    assert "NOT prove recovery succeeds" in d["honesty_label"]
    assert len(d["results"]) == len(rb.checks)
    for r in d["results"]:
        assert set(r) >= {
            "class_id",
            "order",
            "command",
            "outcome",
            "exit_code",
            "timestamp",
        }
    json.dumps(d)  # machine-checkable: serializes


def test_lint_all_covers_every_registry_class():
    runner = FakeRunner(0)
    reports = lint_all(runner=runner)
    assert [rep.class_id for rep in reports] == [rb.class_id for rb in compile_all()]
    unclassified = reports[-1]
    assert unclassified.class_id == "unclassified"
    assert unclassified.results == []
    assert unclassified.stale_reason is None


# ------------------------------------------------------ stale transition
def _check(order: int, command: str, read_only: bool = True) -> Check:
    return Check(
        order=order,
        command=command,
        expected_healthy="healthy",
        expected_incident="incident",
        decision="decision",
        read_only=read_only,
    )


def _fresh_runbook() -> Runbook:
    return compile_class("gateway-drain-window")


def test_apply_lint_flips_stale_on_error():
    rb = _fresh_runbook()
    report = lint_runbook(rb, runner=FakeRunner(0, 0, 1))
    assert report.results[-1].outcome == "error"
    new = apply_lint(report, rb)
    assert new.status == STATUS_STALE
    assert new is not rb, "frozen dataclass: returns a NEW runbook"
    assert rb.status != STATUS_STALE, "input runbook must not be mutated"
    assert report.stale_reason is not None
    assert "check 3" in report.stale_reason


@pytest.mark.parametrize("outcome", DRIFT_OUTCOMES)
def test_apply_lint_flips_stale_on_every_drift_outcome(outcome):
    if outcome == "refused":
        rb = _rb_with(_check(1, "rm -rf /tmp/x", read_only=False))
        runner = FakeRunner()
    else:
        rb = _fresh_runbook()
        runner = _kind_runner(outcome)
    report = lint_runbook(rb, runner=runner)
    assert report.results[0].outcome == outcome
    new = apply_lint(report, rb)
    assert new.status == STATUS_STALE


def test_apply_lint_does_not_flip_when_all_ok_or_absent():
    runner = FakeRunner(0)
    rb = _fresh_runbook()
    report = lint_runbook(rb, runner=runner)
    assert all(r.outcome in ("ok", "absent") for r in report.results)
    new = apply_lint(report, rb)
    assert new.status == STATUS_PROPOSAL
    assert new.last_validated is None


def test_apply_lint_absent_only_is_not_stale():
    rb = _rb_with(_check(1, "no data", read_only=False))
    report = lint_runbook(rb, runner=FakeRunner())
    assert [r.outcome for r in report.results] == ["absent"]
    new = apply_lint(report, rb)
    assert new.status == STATUS_PROPOSAL
    assert report.stale_reason is None


def test_apply_lint_never_sets_last_validated_or_validated_status():
    rb = _fresh_runbook()
    drift_report = lint_runbook(rb, runner=FakeRunner(1))
    stale = apply_lint(drift_report, rb)
    assert stale.last_validated is None
    assert stale.status == STATUS_STALE

    clean_report = lint_runbook(rb, runner=FakeRunner(0))
    kept = apply_lint(clean_report, rb)
    assert kept.last_validated is None
    assert kept.status == STATUS_PROPOSAL  # NOT validated: lint is not attestation
    assert kept.status != STATUS_VALIDATED


def test_apply_lint_validated_runbook_drifts_to_stale():
    base = _fresh_runbook()
    base_d = base.to_dict()
    base_d["status"] = STATUS_VALIDATED
    base_d["last_validated"] = "2026-09-01T00:00:00+00:00"
    attested = Runbook.from_dict(base_d)
    report = lint_runbook(attested, runner=FakeRunner(1))
    new = apply_lint(report, attested)
    assert new.status == STATUS_STALE
    assert new.last_validated == "2026-09-01T00:00:00+00:00"  # untouched


def test_apply_lint_reason_is_renderable():
    rb = _fresh_runbook()
    report = lint_runbook(rb, runner=FakeRunner(0, 1, 2))
    new = apply_lint(report, rb)
    assert new.status == STATUS_STALE
    reason = report.stale_reason or ""
    assert "check 2" in reason and "check 3" in reason
    assert report.to_dict()["stale_reason"] == reason
