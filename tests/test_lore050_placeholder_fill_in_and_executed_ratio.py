"""LORE-050: placeholder fill-in hints + executed-ratio honesty.

Dogfood run 7 measured two honesty gaps on `validate --execute` from a
scratch dir (1/7 checks executed, 6/7 template-skipped, drift verdict
`drifted_orders: []`):

GAP A — the operator-facing surfaces print `<placeholder>` slots with no
instruction about what fills them. Fix: every surface that renders a
check command (runbook markdown, validate plan/execute text, consult
--failure) ALSO prints one fill-in hint per slot, describing WHERE the
value comes from (a log path, a URL, an env key) — deployment-neutral,
never this host's paths, never secrets' values.

GAP B — `drifted_orders: []` is computed over EXECUTED commands only, so
a class whose checks never ran grades "not drifted" and no field says
how many were exercised. Fix: the history record carries derived
`executed_count`/`total_checks`, and consult's lint line shows the ratio
(`executed 1/7`). All counts DERIVED — in tests too (from SEED_CLASSES /
compile_all / the injected runner's call log), never literals.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lore.__main__ import main
from lore.compiler import compile_all, compile_class
from lore.placeholders import (
    DEFAULT_HINT,
    PLACEHOLDER_HINTS,
    placeholder_hints,
    placeholder_tokens,
)
from lore.runbook import Runbook
from lore.validate import (
    EXECUTED_OUTCOMES,
    OUTCOME_TEMPLATE,
    lint_runbook,
    local_validation_note,
    persist_validate_history,
)

HISTORY_REL = ".lore/validate-history.jsonl"


def _all_ok_runner():
    """Injectable runner: every command answers exit 0 (records calls)."""
    calls: list[str] = []

    def _run(command: str):
        calls.append(command)

        class _R:
            returncode = 0
            stdout = "out"
            stderr = ""
            timed_out = False

        return _R()

    return _run, calls


def _cli(argv, capsys):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ================================================================ GAP A
# ------------------------------------------------------- the hint table
def test_hint_table_covers_every_seed_placeholder_name() -> None:
    """Every <placeholder> the seed checks use resolves to a NAMED hint.

    The seed set is the source of truth (derived from compile_all); a
    check gaining a new slot must add its hint here or this goes red —
    unknown names would otherwise render the honest generic, which is
    the fallback's job, not the seed's.
    """
    names: set[str] = set()
    for rb in compile_all():
        for c in rb.checks:
            names.update(t[1:-1] for t in placeholder_tokens(c.command))
    uncovered = sorted(n for n in names if n not in PLACEHOLDER_HINTS)
    assert uncovered == [], (
        f"seed placeholders missing a named fill-in hint: {uncovered}"
    )


def test_hints_describe_sources_never_deployment_values() -> None:
    """Deployment-neutral by construction: no host paths, URLs, or values.

    A hint must describe WHERE a value comes from; anything beginning a
    POSIX path, a URL scheme, or carrying a placeholder/slot inside it
    would be hardcoding a deployment — refused here.
    """
    for name, hint in PLACEHOLDER_HINTS.items():
        assert "://" not in hint, f"hint for {name} embeds a URL: {hint}"
        assert not hint.lstrip().startswith("/"), (
            f"hint for {name} embeds an absolute path: {hint}"
        )
        assert "<" not in hint, f"hint for {name} nests a slot: {hint}"


def test_placeholder_hints_order_dedup_and_default_fallback() -> None:
    """Pairs arrive in first-appearance order, deduped; unknown → default."""
    cmd = "ls <dir> <dir> && cat <other>"
    pairs = placeholder_hints(cmd)
    assert [t for t, _h in pairs] == ["<dir>", "<other>"]
    assert pairs[1][1] == DEFAULT_HINT, "an unnamed slot gets the generic"
    assert placeholder_hints("git status --short") == [], (
        "a filled command carries no fill-in lines"
    )


def test_markdown_render_carries_fill_in_hints_at_point_of_use() -> None:
    """compile --format md: each placeholder slot gets its hint line under
    the check block; a check without slots gets none."""
    rb = compile_class("gateway-drain-window")
    md = rb.to_markdown()
    for c in rb.checks:
        tokens = placeholder_tokens(c.command)
        if not tokens:
            continue
        # the hint line sits inside the check's own block
        check_start = md.find(f"### Check {c.order}")
        nxt = md.find("### Check", check_start + 1)
        if nxt == -1:
            nxt = md.find("## Recovery ladder")
        block = md[check_start:nxt]
        for token, hint in placeholder_hints(c.command):
            line = f"- Fill-in: `{token}` — {hint}"
            assert line in block, f"check {c.order} missing its fill-in line"
    filled = compile_class("shared-checkout-collision")
    filled_md = filled.to_markdown()
    cmd_nohint = "### Check 1"
    block = filled_md[filled_md.find(cmd_nohint) : filled_md.find("### Check 2")]
    assert "Fill-in:" not in block, (
        "a check whose command has no slots renders no fill-in lines"
    )


def test_markdown_json_contract_unchanged_by_hints() -> None:
    """to_dict round-trips unchanged (hints are a RENDERING affordance)."""
    rb = compile_class("gateway-drain-window")
    data = rb.to_dict()
    assert Runbook.from_dict(data).to_dict() == data


def test_cli_validate_plan_prints_fill_in_hints(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Plan mode: every would-run check with a slot prints its hints."""
    code, out, _err = _cli(
        ["validate", "--class", "gateway-drain-window", "--format", "md"], capsys
    )
    assert code == 0
    assert "would run:" in out
    assert "fill-in:" in out
    rb = compile_class("gateway-drain-window")
    hinted = rb.checks[1].command  # carries <gateway-log-path>
    token = placeholder_tokens(hinted)[0]
    assert token in out


def test_cli_validate_execute_prints_fill_in_hints_under_template_checks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--execute text: template-skipped checks explain WHAT fills each slot."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    code, out, _err = _cli(
        ["validate", "--class", "gateway-drain-window", "--format", "md", "--execute"],
        capsys,
    )
    assert code == 0
    rb = compile_class("gateway-drain-window")
    template_checks = [c for c in rb.checks if placeholder_tokens(c.command)]
    assert template_checks, "premise: the seed has placeholder checks"
    for c in template_checks:
        assert f"check {c.order}: {OUTCOME_TEMPLATE}" in out
    for token, hint in placeholder_hints(template_checks[0].command):
        assert f"fill-in: {token} = {hint}" in out, out


def test_cli_consult_failure_prints_fill_in_hints(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """consult --failure: the ordered check list carries hints too."""
    monkeypatch.chdir(tmp_path)
    code, out, _err = _cli(
        ["consult", "--failure", "drain 503s while requests drain"], capsys
    )
    assert code == 0
    assert "this class has a runbook" in out
    assert "fill-in:" in out
    # a hinted slot the gateway runbook carries, next to its check line
    rb = compile_class("gateway-drain-window")
    for token, _hint in placeholder_hints(rb.checks[1].command):
        assert token in out


# ================================================================ GAP B
# ------------------------------------------------- derived report counts
def test_executed_and_not_executed_orders_partition_the_results() -> None:
    """executed+not_executed == every result exactly once; orders derived."""
    rb = compile_class("gateway-drain-window")
    _run, calls = _all_ok_runner()
    report = lint_runbook(rb, runner=_run)
    execd = report.executed_orders
    not_execd = report.not_executed_orders
    all_orders = [r.order for r in report.results]
    assert sorted(execd + not_execd) == sorted(all_orders)
    assert not (set(execd) & set(not_execd))
    assert len(execd) == len(calls), (
        "executed_orders matches the runner's real invocations"
    )
    assert report.to_dict()["executed_orders"] == execd


def test_env_absent_is_an_execution_not_a_skip() -> None:
    """exit 127 IS an answer: env-absent counts as executed (GAP B).

    Run-7's real shape: the two logsey checks executed (127: env-absent),
    the placeholder checks in between never ran. The env-absent checks
    COUNT toward executed — the ratio separates them from the skips.
    """

    def _not_found(_cmd: str):
        class _R:
            returncode = 127
            stdout = ""
            stderr = "command not found"
            timed_out = False

        return _R()

    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=_not_found)
    env_absent = report.env_absent_orders
    assert env_absent, "premise: some checks classify env-absent here"
    placeholders = report.not_executed_orders  # template checks skipped
    assert placeholders, "premise: placeholder checks never ran"
    assert report.drifted_orders == []  # env-absent is not drift
    assert set(env_absent) <= set(report.executed_orders), (
        "env-absent checks count as executed: exit 127 IS an answer"
    )
    assert set(env_absent).isdisjoint(set(placeholders))


def test_history_record_carries_derived_executed_ratio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The run-7 record now says 0/7: drifted_orders=[] can never again
    read as 'lint ran clean over the whole runbook'."""
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    rb = compile_class("gateway-drain-window")
    report = lint_runbook(rb, runner=_run)
    target = tmp_path / HISTORY_REL
    (rec,) = persist_validate_history([report], path=target)
    assert rec["drifted_orders"] == []  # all green
    assert rec["executed_count"] == len(calls)
    assert rec["total_checks"] == len(report.results)
    # honest derived shape: the logsey checks run (no slots), the five
    # placeholder checks never do — exactly the run-7 asymmetry, now
    # VISIBLE in the record instead of hidden behind drifted_orders: []
    template_slots = len([c for c in rb.checks if placeholder_tokens(c.command)])
    assert rec["total_checks"] - rec["executed_count"] == template_slots
    # derived, never a literal: the check count comes from the seed
    assert rec["total_checks"] == len(rb.checks)


def test_history_record_of_never_executed_class_says_zero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A class whose checks all template-skip records executed_count 0.

    The run-7 shape: logsey env-absent (executed) + placeholders — the
    all-template guard-degradation variant proves the 0 side; the ratio
    is what separates 'lint ran clean' from 'lint never ran anything'.
    """
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    rb = compile_class("guard-degradation")
    report = lint_runbook(rb, runner=_run)
    assert calls == [], "premise: this class's checks all template-skip"
    assert report.results, "premise: it still has checks to count"
    target = tmp_path / HISTORY_REL
    (rec,) = persist_validate_history([report], path=target)
    assert rec["executed_count"] == 0
    assert rec["total_checks"] == len(report.results)
    assert rec["drifted_orders"] == [], (
        "template skips are not drift — but the ratio below now says so"
    )


def test_local_validation_note_carries_executed_ratio() -> None:
    """The consult lint line shows the ratio when the record has counts."""
    rec = {
        "class_id": "gateway-drain-window",
        "timestamp": "2026-10-01T19:15:06+00:00",
        "executed_count": 1,
        "total_checks": 7,
    }
    line = local_validation_note(rec)
    assert line == (
        "last lint-validated 2026-10-01T19:15:06+00:00 on this box "
        "(local history, not operator attestation); executed 1/7 checks"
    )


def test_local_validation_note_pre050_record_stays_byte_identical() -> None:
    """A record predating the fields renders the OLD line exactly."""
    rec = {"timestamp": "2026-10-01T19:15:06+00:00"}
    line = local_validation_note(rec)
    assert line == (
        "last lint-validated 2026-10-01T19:15:06+00:00 on this box "
        "(local history, not operator attestation)"
    )
    assert "executed" not in line


def test_local_validation_note_malformed_counts_render_no_ratio() -> None:
    """A malformed/absurd ratio renders honestly, never lies about it."""
    for bad in (
        {"executed_count": 8, "total_checks": 7},  # executed > total
        {"executed_count": -1, "total_checks": 7},
        {"executed_count": "1", "total_checks": 7},  # wrong types
    ):
        line = local_validation_note({"timestamp": "t", **bad})
        assert "executed" not in line, bad


# --------------------------------------------------- Consult lint line (ratio)
def test_consult_lint_line_shows_executed_ratio_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """validate --execute, then consult: the surfaced lint line names the
    honest ratio derived from the run that persisted the record."""
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()
    code, out, _err = _cli(
        ["consult", "gateway drain window: 503s killing ticks"], capsys
    )
    assert code == 0
    expected = f"executed {len(calls)}/{len(compile_class('gateway-drain-window').checks)} checks"
    assert expected in out, f"missing ratio line {expected!r} in:\n{out}"


# ------------------------------------------- LORE-054-era pins re-checked
def test_full_registry_every_drift_verdict_sits_on_an_executed_base() -> None:
    """Every class's record ratio is internally consistent across the
    whole registry: executed+not_executed == total, for an all-ok run."""
    _run, _calls = _all_ok_runner()
    for rb in compile_all():
        report = lint_runbook(rb, runner=_run)
        assert len(report.executed_orders) + len(report.not_executed_orders) == len(
            report.results
        ), rb.class_id


def test_executed_outcomes_vocabulary_documents_itself() -> None:
    """The executed set is exactly the vocabulary minus the never-ran
    outcomes (closed-set cross-check, derived from the two constants)."""
    never_ran = {"refused", "absent", "template"}
    assert never_ran.isdisjoint(set(EXECUTED_OUTCOMES))
    from lore.validate import OUTCOME_VOCABULARY

    assert set(EXECUTED_OUTCOMES) | never_ran == set(OUTCOME_VOCABULARY)
