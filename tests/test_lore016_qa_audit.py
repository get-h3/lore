"""LORE-016 QA audit: coverage hardening for the v0.1.0 CLI + API surface.

Fills the audit gaps the shipped surface had no tests for: per-subcommand
error paths (exit codes 0/1/2 exactly as implemented), the consult /
consult_failure no-match fail-open contract at the CLI layer, the
``lore validate`` PLAN-ONLY default (executes NO commands — side-effect
free, proven with a booby-trapped runner), the ``--execute`` opt-in
runner wiring, and CLI-level JSON round-trips for runbook serialization.

Tests only — no product behavior is changed by this file.
"""

from __future__ import annotations

import json

import pytest

from lore.__main__ import main
from lore.classes import SEED_CLASSES
from lore.compiler import compile_class
from lore.runbook import Runbook

# Canonical gateway symptom (signature-level match, per test_classifier).
GATEWAY_TEXT = "drain 503s while requests drain during restart"
NO_MATCH_TEXT = "coffee machine broken"


def _run(argv, capsys):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ------------------------------------------------------- match error paths
def test_cli_match_missing_text_is_argparse_exit2():
    # argparse usage error: SystemExit with code 2, message on stderr.
    with pytest.raises(SystemExit) as exc:
        main(["match"])
    assert exc.value.code == 2


def test_cli_match_no_match_prints_honest_unclassified_exit0(capsys):
    # Implemented behavior: classify_all always carries the unclassified
    # fallback, so a no-match is an honest unclassified row at exit 0.
    code, out, _err = _run(["match", NO_MATCH_TEXT], capsys)
    assert code == 0
    assert out.startswith("unclassified\tconfidence=0.00\tevidence: none")


def test_cli_match_no_candidates_branch_exits_1(capsys, monkeypatch):
    # The implemented exit-1 path: zero candidates -> "no candidates", rc 1.
    monkeypatch.setattr("lore.__main__.classify_all", lambda _text: [])
    code, out, _err = _run(["match", NO_MATCH_TEXT], capsys)
    assert code == 1
    assert "no candidates" in out


def test_cli_match_explain_without_near_misses_prints_none(capsys):
    code, out, _err = _run(["match", "--explain", NO_MATCH_TEXT], capsys)
    assert code == 0
    assert "near-misses: none" in out


# ----------------------------------------------------- consult error paths
def test_cli_consult_without_title_fail_open_exit0(capsys):
    # Fail-open contract: no title and no --failure is NOT an error.
    code, out, _err = _run(["consult"], capsys)
    assert code == 0
    assert "no matching runbook" in out


def test_cli_consult_json_no_match_exit0(capsys):
    code, out, _err = _run(["consult", NO_MATCH_TEXT, "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["matched"] is False
    assert payload["matched_classes"] == []
    assert payload["runbook_refs"] == []


def test_cli_consult_failure_json_no_match_exit0(capsys):
    # Guard-failure mode keeps the fail-open contract: no match = exit 0.
    code, out, _err = _run(["consult", "--failure", NO_MATCH_TEXT, "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["matched"] is False
    assert payload["suggestions"] == []


# ------------------------------------------------- compile / show error paths
def test_cli_compile_unknown_class_exit2_stderr_named(capsys):
    code, out, err = _run(["compile", "--class", "does-not-exist"], capsys)
    assert code == 2
    assert out == ""
    assert "error:" in err
    assert "does-not-exist" in err


# ---------------------------------------------------- validate error paths
def test_cli_validate_unknown_class_exit2(capsys):
    code, out, err = _run(["validate", "--class", "nope"], capsys)
    assert code == 2
    assert out == ""
    assert "error:" in err
    assert "registry is closed" in err
    assert "gateway-drain-window" in err  # the known-classes honesty list


# ------------------------------------------------------- gate error paths
def test_cli_gate_missing_decision_is_argparse_exit2():
    with pytest.raises(SystemExit) as exc:
        main(["gate"])
    assert exc.value.code == 2


def test_cli_no_subcommand_is_argparse_exit2():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


# ------------------------------------------------------ absorb error paths
def test_cli_absorb_unknown_class_failsafe_payload_exit0(capsys):
    # Implemented behavior: absorb_proposal's fail-safe error payload is
    # printed at exit 0 (propose-not-write: the error IS the stdout payload).
    code, out, _err = _run(["absorb", "--class", "nope", "--lesson", "x"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload == {"error": "unknown class 'nope'"}


# ---------------------------------------------- validate PLAN-ONLY default
def test_cli_validate_plan_mode_executes_no_commands(capsys, monkeypatch):
    """The side-effect-free law: plan mode must NEVER reach the runner.

    Two independent tripwires: the injectable default runner records and
    fails, and subprocess.run itself is booby-trapped — if plan mode
    executes anything, this test explodes instead of passing quietly.
    """
    calls: list[str] = []

    def forbidden_runner(command):
        calls.append(command)
        raise AssertionError(f"plan mode executed a command: {command!r}")

    def forbidden_subprocess_run(*_a, **_kw):
        raise AssertionError("plan mode called subprocess.run")

    monkeypatch.setattr("lore.validate._default_runner", forbidden_runner)
    monkeypatch.setattr("lore.validate.subprocess.run", forbidden_subprocess_run)

    for argv in (
        ["validate"],
        ["validate", "--class", "gateway-drain-window"],
        ["validate", "--format", "md"],
    ):
        code, _out, _err = _run(argv, capsys)
        assert code == 0
    assert calls == [], "plan mode must execute NOTHING"


def test_cli_validate_plan_json_shape(capsys):
    code, out, _err = _run(
        ["validate", "--class", "gateway-drain-window", "--format", "json"], capsys
    )
    assert code == 0
    (plan,) = json.loads(out)
    assert plan["class_id"] == "gateway-drain-window"
    assert plan["mode"] == "plan"
    assert "no command was executed" in plan["note"]
    assert "--execute" in plan["note"]
    orders = [c["order"] for c in plan["would_run"]]
    assert orders == sorted(orders), "would_run is ordered"
    # every would_run command passes the read-only gate (plan lists only
    # gate-approved shapes as runnable; refusals live in would_refuse)
    from lore.validate import is_read_only_command

    assert all(is_read_only_command(c["command"]) for c in plan["would_run"])
    for c in plan["would_refuse"]:
        assert not is_read_only_command(c["command"])


def test_cli_validate_plan_names_gate_refusals_honestly(capsys):
    # guard-degradation carries a check the gate refuses: the plan names it
    # as would_refuse (json) and "would REFUSE:" (md) — never silently run.
    code, out, _err = _run(["validate", "--class", "guard-degradation"], capsys)
    assert code == 0
    (plan,) = json.loads(out)
    assert plan["would_refuse"], "the refused check must be named"
    from lore.validate import is_read_only_command

    assert all(not is_read_only_command(c["command"]) for c in plan["would_refuse"])
    _code, out_md, _err = _run(
        ["validate", "--class", "guard-degradation", "--format", "md"], capsys
    )
    assert "would REFUSE:" in out_md


def test_cli_validate_plan_md_labels_nothing_executed(capsys):
    code, out, _err = _run(
        ["validate", "--class", "gateway-drain-window", "--format", "md"], capsys
    )
    assert code == 0
    assert "# gateway-drain-window — plan (nothing executed)" in out
    assert "would run:" in out
    assert "would execute" not in out.lower().replace("nothing executed", "")


def test_cli_validate_plan_absent_check_is_honest_no_data(capsys):
    # The unclassified class compiles no checks: plan says so, honestly.
    code, out, _err = _run(["validate", "--class", "unclassified"], capsys)
    assert code == 0
    (plan,) = json.loads(out)
    assert plan["would_run"] == []
    assert plan["would_refuse"] == []
    _code, out_md, _err = _run(
        ["validate", "--class", "unclassified", "--format", "md"], capsys
    )
    assert "no data (no checks)" in out_md


def test_cli_validate_execute_uses_injected_runner_gate_approved_only(
    capsys, monkeypatch
):
    """--execute runs ONLY gate-approved commands through the runner.

    The default runner is injectable at the module seam; refused and
    absent ('no data') checks must never reach it.
    """
    calls: list[str] = []

    def fake_runner(command):
        calls.append(command)

        class _R:
            returncode = 0
            stdout = "out"
            stderr = ""
            timed_out = False

        return _R()

    monkeypatch.setattr("lore.validate._default_runner", fake_runner)
    code, out, _err = _run(["validate", "--execute"], capsys)
    assert code == 0
    reports = json.loads(out)
    assert reports, "all registry classes are linted"
    expected = len(SEED_CLASSES) + 1  # curated + unclassified
    assert len(reports) == expected
    ran = {
        r["command"] for rep in reports for r in rep["results"] if r["outcome"] == "ok"
    }
    assert calls and set(calls) == ran, "runner saw exactly the ok-executed set"
    from lore.validate import is_read_only_command

    assert all(is_read_only_command(c) for c in calls), (
        "--execute must never run a gate-refused command"
    )
    # refused/absent checks still appear in results, but with exit_code None
    for rep in reports:
        for r in rep["results"]:
            if r["outcome"] in ("refused", "absent"):
                assert r["exit_code"] is None
    # the honesty label rides every report
    assert all(
        "does NOT prove recovery succeeds" in rep["honesty_label"] for rep in reports
    )


# ------------------------------------------- runbook serialization via CLI
def test_cli_show_json_round_trips_to_equal_runbook(capsys):
    code, out, _err = _run(["show", "gateway-drain-window", "--format", "json"], capsys)
    assert code == 0
    d = json.loads(out)
    rt = Runbook.from_dict(d)
    assert rt.to_dict() == d, "CLI JSON must round-trip losslessly"
    assert rt == compile_class("gateway-drain-window")


def test_cli_compile_json_round_trips_for_every_class(capsys):
    code, out, _err = _run(["compile", "--format", "json"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data, "every registry class compiles"
    for d in data:
        rt = Runbook.from_dict(d)
        assert rt.to_dict() == d
        assert rt.class_id == d["class_id"]


# --------------------------------------------------------- misc CLI surface
def test_cli_compile_md_all_classes_renders_every_runbook(capsys):
    code, out, _err = _run(["compile", "--format", "md"], capsys)
    assert code == 0
    from lore.classes import get_registry

    n = len(get_registry())
    assert out.count("# Runbook:") == n
    assert out.count("## Checks (in order)") == n
