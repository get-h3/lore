"""LORE-052 — bash-capable runner + env-absent for missing target files.

Two authoring/runner defects used to flip healthy curated classes stale:

1. The default runner went through ``/bin/sh`` (``shell=True``), which
   rejects bash process substitution (``diff <(grep …) <(grep …)``) with a
   syntax error (exit 2) — reading as drift.
2. A check that greps a config file the box simply lacks (e.g.
   ``fleet.toml``) exits 1 with "No such file or directory" — also reading
   as drift, when the honest outcome is ``env-absent`` (REVIEW-LORE-003
   vocabulary: the ENVIRONMENT is absent, not the runbook's expectation).

SAFETY: mostly fake runners; the two real-execution tests touch only a
pytest tmp_path (no fleet paths, no network).
"""

from __future__ import annotations

from lore.compiler import Check, compile_class
from lore.runbook import Runbook
from lore.validate import (
    OUTCOME_ENV_ABSENT,
    _default_runner,
    apply_lint,
    lint_runbook,
)


class _R:
    def __init__(self, returncode, stderr="", timed_out=False):
        self.returncode = returncode
        self.stdout = ""
        self.stderr = stderr
        self.timed_out = timed_out


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
        class_id="lore052-fixture",
        name="LORE-052 fixture",
        signature="fixture",
        checks=list(checks),
    )


# ------------------------------------------------------- cause 1: bash
class TestBashCapableRunner:
    def test_default_runner_executes_process_substitution(self):
        """Real execution: bash process substitution must parse and answer.

        Under /bin/sh this is exit 2 ``Syntax error: \"(\" unexpected``.
        """
        result = _default_runner("diff <(echo a) <(echo a) && echo IDENTICAL")
        assert result.returncode == 0, f"stderr: {result.stderr!r}"
        assert "IDENTICAL" in result.stdout

    def test_default_runner_keeps_capture_and_timeout_semantics(self):
        """Bash path must preserve stdout capture + stderr + non-interactive."""
        result = _default_runner("echo out-payload; echo err-payload 1>&2")
        assert "out-payload" in result.stdout
        assert "err-payload" in result.stderr
        assert result.returncode == 0
        assert result.timed_out is False

    def test_curated_env_clobber_check_no_longer_shell_error(
        self, monkeypatch, tmp_path
    ):
        """The seeded ``diff <(grep … .env)`` check parses under the runner.

        Simulates a box WITH both files present (tmp cwd) — the check must
        run (not a shell syntax error) and classify honestly.
        """
        (tmp_path / ".env").write_text("A=1\nB=2\n")
        (tmp_path / ".env.example").write_text("A=1\nB=2\n")
        cmd = (
            "diff <(grep -o '^[A-Z_]*' .env | sort) "
            "<(grep -o '^[A-Z_]*' .env.example | sort)"
        )
        real_runner = _default_runner

        def cwd_runner(command: str):
            import os

            old = os.getcwd()
            os.chdir(tmp_path)
            try:
                return real_runner(command)
            finally:
                os.chdir(old)

        rb = _rb_with(_check(1, cmd))
        report = lint_runbook(rb, runner=cwd_runner)
        assert report.results[0].outcome == "ok", report.results[0].stderr


# --------------------------------------- cause 2: missing file = env-absent
class TestMissingTargetFileEnvAbsent:
    def test_missing_relative_file_is_env_absent_not_error(self):
        """grep names the missing file in stderr AND the command references it."""
        runner_results = {
            "grep -A2 '[[projects]]' fleet.toml": _R(
                1, "grep: fleet.toml: No such file or directory\n"
            ),
        }

        def runner(command: str):
            return runner_results[command]

        rb = _rb_with(
            _check(1, "grep -A2 '[[projects]]' fleet.toml"),
        )
        report = lint_runbook(rb, runner=runner)
        r = report.results[0]
        assert r.outcome == OUTCOME_ENV_ABSENT
        assert report.drifted_orders == []
        assert report.env_absent_orders == [1]
        assert report.stale_reason is None
        assert apply_lint(report, rb).status == rb.status  # NOT stale

    def test_missing_absolute_path_is_env_absent(self):
        """Arm B: referenced absolute path stat-verified absent."""

        def runner(command: str):
            return _R(
                2, "cat: /nonexistent/lore052/nope.conf: No such file or directory\n"
            )

        rb = _rb_with(_check(1, "cat /nonexistent/lore052/nope.conf | head"))
        report = lint_runbook(rb, runner=runner)
        assert report.results[0].outcome == OUTCOME_ENV_ABSENT
        assert report.env_absent_orders == [1]
        assert report.stale_reason is None

    def test_env_absent_does_not_flip_stale_with_other_ok_checks(self):
        runner_results = {
            "grep -A2 'x' /no/such/fleet.toml": _R(
                2, "grep: /no/such/fleet.toml: No such file or directory\n"
            ),
            "git log --oneline -1": _R(0, "abc123 ok\n"),
        }

        def runner(command: str):
            return runner_results[command]

        rb = _rb_with(
            _check(1, "grep -A2 'x' /no/such/fleet.toml"),
            _check(2, "git log --oneline -1"),
        )
        report = lint_runbook(rb, runner=runner)
        assert report.env_absent_orders == [1]
        assert report.drifted_orders == []
        assert apply_lint(report, rb).status == rb.status  # no stale flip


class TestOrdinaryFailureStillError:
    def test_failure_with_file_present_still_error_and_stales(self):
        """The file EXISTS; grep still fails (bad pattern) — real drift."""
        runner_results = {
            "grep '[' fleet.toml": _R(2, "grep: Invalid regular expression\n"),
        }

        def runner(command: str):
            return runner_results[command]

        rb = _rb_with(_check(1, "grep '[' fleet.toml"))
        report = lint_runbook(rb, runner=runner)
        r = report.results[0]
        assert r.outcome == "error"
        assert report.drifted_orders == [1]
        assert report.stale_reason == "lint drift: check 1 (error)"
        assert apply_lint(report, rb).status == "stale"

    def test_file_not_found_without_command_reference_stays_error(self):
        """stderr says missing, but the command never references that file:
        conservative conjunction fails → still ``error`` (no loosening)."""
        runner_results = {
            "cat report.txt": _R(1, "cat: missing.conf: No such file or directory\n"),
        }

        def runner(command: str):
            return runner_results[command]

        rb = _rb_with(_check(1, "cat report.txt"))
        report = lint_runbook(rb, runner=runner)
        assert report.results[0].outcome == "error"
        assert report.stale_reason is not None

    def test_timeout_not_reclassified_env_absent(self):
        def runner(command: str):
            return _R(None, "grep: x: No such file or directory\n", timed_out=True)

        rb = _rb_with(_check(1, "grep x /no/such/fleet.toml"))
        report = lint_runbook(rb, runner=runner)
        assert report.results[0].outcome == "timeout"


# ------------------------------- seeded curated classes end-to-end shape
class TestSeededCuratedChecks:
    def test_secret_env_clobber_process_sub_check_bash_ok_or_env_absent(
        self, monkeypatch, tmp_path
    ):
        """On a box WITH .env/.env.example present: the seeded diff <(…) check
        must classify ok (never the /bin/sh syntax error)."""
        (tmp_path / ".env").write_text("A=1\n")
        (tmp_path / ".env.example").write_text("A=1\n")
        import os

        rb = compile_class("secret-env-clobber")
        assert any("<(" in c.command for c in rb.checks), "seeded check expected"
        real_runner = _default_runner

        def cwd_runner(command: str):
            old = os.getcwd()
            os.chdir(tmp_path)
            try:
                return real_runner(command)
            finally:
                os.chdir(old)

        report = lint_runbook(rb, runner=cwd_runner)
        sub_results = [r for r in report.results if "<(" in r.command]
        assert sub_results, "seeded process-substitution check must be linted"
        for r in sub_results:
            assert r.outcome == "ok", (r.outcome, r.stderr[:200])

    def test_fleet_toml_check_env_absent_on_box_without_file(
        self, monkeypatch, tmp_path
    ):
        """Real execution from a cwd WITHOUT fleet.toml: env-absent, not stale."""
        import os

        rb = compile_class("cooldown-pin-drift")
        real_runner = _default_runner

        def cwd_runner(command: str):
            old = os.getcwd()
            os.chdir(tmp_path)
            try:
                return real_runner(command)
            finally:
                os.chdir(old)

        report = lint_runbook(rb, runner=cwd_runner)
        fleet_results = [r for r in report.results if "fleet.toml" in r.command]
        assert fleet_results, "seeded fleet.toml check expected"
        for r in fleet_results:
            if r.outcome in ("error",):
                raise AssertionError(
                    f"fleet.toml check classified {r.outcome}: {r.stderr[:200]}"
                )
            assert r.outcome in (OUTCOME_ENV_ABSENT, "template"), r.outcome
        # the runbook must NOT flip stale from the missing-file checks
        assert report.stale_reason is None or "env-absent" not in (
            report.stale_reason or ""
        )
