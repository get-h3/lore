"""LORE-045: a real ``validate --execute`` run persists; consult/compile surface it.

The disease (dogfood run 5): a green live lint printed to stdout and
evaporated — ``lore consult --failure`` said ``last_validated=never`` and
``lore compile --format md`` said ``no data (never validated)`` on the SAME
box seconds later. The fix: one JSONL record PER CLASS appended to a local
history file (``.lore/validate-history.jsonl``, relative to the CURRENT
working directory) after every real --execute run, and consult/compile
surface it honestly:

    last lint-validated <timestamp> on this box (local history, not operator attestation)

HONESTY LAWS pinned here (never regressed):
- the lint/local history NEVER sets ``runbook.last_validated``;
- the lint/local history NEVER moves ``status`` to ``validated``;
- no history (missing/empty file, no record for the class) → the output
  stays EXACTLY as before ("never" / "no data (never validated)").

SAFETY: no real subprocess anywhere — the CLI ``--execute`` path is driven
through the same injectable runner seam the existing validate tests use
(``lore.validate._default_runner`` monkeypatch; plan-mode tripwires prove
plan-only runs write NOTHING).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lore.__main__ import main
from lore.compiler import compile_class
from lore.runbook import STATUS_PROPOSAL, STATUS_STALE, STATUS_VALIDATED, Runbook
from lore.validate import (
    HONESTY_LABEL,
    LOCAL_VALIDATION_NOTE,
    OUTCOME_TEMPLATE,
    last_local_validation,
    lint_runbook,
    local_validation_note,
    persist_validate_history,
)

# Canonical gateway symptom (matches the class signature).
GATEWAY_TEXT = "gateway drain window: scheduler restarting, 503s killing ticks"
# The --failure mode feeds guard-failure OUTPUT; gateway text still matches.
FAILURE_TEXT = "guard failed: drain 503s while requests drain during restart"

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


def _read_history(root: Path) -> list[dict]:
    path = root / HISTORY_REL
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _cli(argv, capsys):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ------------------------------------------------- record shape / persistence
def test_persist_writes_one_record_per_class_with_expected_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Every class in an --execute run lands ONE record; shape is pinned."""
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    reports = [lint_runbook(rb) for rb in [compile_class("gateway-drain-window")]]
    target = tmp_path / HISTORY_REL
    records = persist_validate_history(reports, path=target)

    assert len(records) == 1
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, "one JSONL line per class"
    rec = json.loads(lines[0])
    assert rec["class_id"] == "gateway-drain-window"
    assert rec["timestamp"] == reports[0].created_at, (
        "timestamp comes from the report (ISO-8601), never re-stamped"
    )
    assert rec["honesty_label"] == HONESTY_LABEL
    assert rec["outcomes"], "the class's lint outcomes are recorded in order"
    assert rec["drifted_orders"] == []  # all green through the injected runner
    assert all(isinstance(o, str) for o in rec["outcomes"])
    assert records == [rec]
    assert calls, "the injected runner genuinely executed the read-only checks"


def test_persist_is_append_not_overwrite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A second run APPENDS (both records readable); reads return the newest."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    rb = compile_class("gateway-drain-window")
    target = tmp_path / HISTORY_REL

    first = [lint_runbook(rb, runner=_run)]
    persist_validate_history(first, path=target)
    second = [lint_runbook(rb, runner=_run)]
    persist_validate_history(second, path=target)

    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2, "append, never overwrite"
    rec1, rec2 = (json.loads(ln) for ln in lines)
    assert rec2["timestamp"] >= rec1["timestamp"], (
        "the appended record carries the newer timestamp"
    )
    # newest-wins read path
    got = last_local_validation("gateway-drain-window", path=target)
    assert got is not None
    assert got["timestamp"] == rec2["timestamp"]


def test_persist_records_drifted_runs_too(tmp_path: Path) -> None:
    """Drift is data: a drifted lint run is persisted with its drift named."""
    from lore.runbook import Check

    rb = Runbook(
        class_id="gateway-drain-window",
        name="Gateway drain window",
        signature="drain 503",
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

    def _fail(_cmd: str):
        class _R:
            returncode = 1
            stdout = ""
            stderr = "drift"
            timed_out = False

        return _R()

    report = lint_runbook(rb, runner=_fail)
    assert report.drifted_orders == [1]  # premise: this run drifted
    target = tmp_path / HISTORY_REL
    (records,) = persist_validate_history([report], path=target)
    assert records["drifted_orders"] == [1]
    assert records["outcomes"] == ["error"]
    assert records["honesty_label"] == HONESTY_LABEL, (
        "drifted runs carry the same honesty label — still a lint run"
    )


def test_last_local_validation_handles_missing_empty_and_malformed(
    tmp_path: Path,
) -> None:
    """Missing/empty file → None; a malformed line is skipped, not fatal."""
    missing = tmp_path / "nowhere" / HISTORY_REL
    assert last_local_validation("gateway-drain-window", path=missing) is None

    _empty = tmp_path / HISTORY_REL
    _empty.parent.mkdir(parents=True, exist_ok=True)
    _empty.write_text("", encoding="utf-8")
    assert last_local_validation("gateway-drain-window", path=_empty) is None

    other_class = tmp_path / HISTORY_REL
    other_class.write_text(
        "\n".join(
            [
                "{not json at all",  # malformed: skipped, rest still reads
                json.dumps(
                    {
                        "class_id": "shared-checkout-collision",
                        "timestamp": "2026-10-01T00:00:00+00:00",
                        "honesty_label": HONESTY_LABEL,
                        "outcomes": ["ok"],
                        "drifted_orders": [],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert last_local_validation("gateway-drain-window", path=other_class) is None, (
        "no record for THIS class"
    )
    got = last_local_validation("shared-checkout-collision", path=other_class)
    assert got is not None and got["timestamp"] == "2026-10-01T00:00:00+00:00"


def test_unclassified_or_never_linted_class_has_no_record(tmp_path: Path) -> None:
    """A run NEVER --execute'd on this box has no record (missing → None)."""
    assert last_local_validation("unclassified", path=tmp_path / HISTORY_REL) is None


# ------------------------------------------------ CLI --execute persists
def test_cli_validate_execute_appends_history_in_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A real CLI --execute run lands in <cwd>/.lore/validate-history.jsonl."""
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    code, out, _err = _cli(
        ["validate", "--class", "gateway-drain-window", "--execute"], capsys
    )
    assert code == 0
    payload = json.loads(out)
    assert payload and payload[0]["class_id"] == "gateway-drain-window"
    records = _read_history(tmp_path)
    assert len(records) == 1
    (rec,) = records
    assert rec["class_id"] == "gateway-drain-window"
    assert rec["outcomes"] and rec["outcomes"][0] in ("ok",)
    executed = [r for r in payload[0]["results"] if r["outcome"] == "ok"]
    assert calls == [r["command"] for r in executed], (
        "every executed check reached the injected runner; nothing ran for real"
    )
    assert set(rec) == {
        "class_id",
        "timestamp",
        "honesty_label",
        "outcomes",
        "drifted_orders",
    }


def test_cli_validate_execute_full_registry_one_record_per_class(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No --class: one record per registry class (curated + unclassified)."""
    from lore.classes import SEED_CLASSES

    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    code, _out, _err = _cli(["validate", "--execute"], capsys)
    assert code == 0
    records = _read_history(tmp_path)
    expected_ids = [fc.id for fc in SEED_CLASSES] + ["unclassified"]
    assert [r["class_id"] for r in records] == expected_ids


def test_cli_validate_plan_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Plan-only runs write NOTHING anywhere (LORE-045 scope)."""

    def _boom(*_a, **_kw):
        raise AssertionError("plan mode must never execute or write")

    monkeypatch.setattr("lore.validate._default_runner", _boom)
    monkeypatch.setattr("lore.validate.subprocess.run", _boom)
    monkeypatch.chdir(tmp_path)

    def _forbidden_open(*_a, **_kw):  # any file open() is a write leak
        raise AssertionError("plan mode opened a file")

    monkeypatch.setattr("builtins.open", _forbidden_open)
    for argv in (
        ["validate"],
        ["validate", "--class", "gateway-drain-window"],
        ["validate", "--format", "md"],
    ):
        code, _out, _err = _cli(argv, capsys)
        assert code == 0
    assert not (tmp_path / ".lore").exists(), "plan mode must write NOTHING"


def test_cli_validate_execute_refused_command_still_persists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A run with gate-refused checks persists too; refused never executed.

    Real-shape drive: the unclassified class compiles with a template
    check (`guard-degradation`'s MUTATING mark) so the run mixes outcomes
    without stubbing the registry.
    """
    run_id = "guard-degradation"  # carries a plan-only (read_only=False) check
    _run, calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    code, _out, _err = _cli(["validate", "--class", run_id, "--execute"], capsys)
    assert code == 0
    (rec,) = _read_history(tmp_path)
    assert rec["class_id"] == "guard-degradation"
    assert rec["outcomes"], "the MUTATING check's template outcome is recorded"
    assert OUTCOME_TEMPLATE in rec["outcomes"], (
        "the plan-only check is visible in the record (never hidden)"
    )
    assert all(r is not None for r in rec["outcomes"])
    assert rec["outcomes"] == [OUTCOME_TEMPLATE] * len(rec["outcomes"]), (
        "guard-degradation compiles one MUTATING check + template slots"
    )
    assert calls == [], "a MUTATING check must never reach the runner"


# ------------------------------------- consult: honest local-history surface
def test_local_validation_note_names_lint_run_not_attestation() -> None:
    """The exact honest wording, pinned (task requirement verbatim)."""
    rec = {
        "class_id": "gateway-drain-window",
        "timestamp": "2026-10-01T19:15:06+00:00",
        "honesty_label": HONESTY_LABEL,
        "outcomes": ["ok"],
        "drifted_orders": [],
    }
    line = local_validation_note(rec)
    assert line == (
        "last lint-validated 2026-10-01T19:15:06+00:00 on this box "
        "(local history, not operator attestation)"
    )
    assert LOCAL_VALIDATION_NOTE in line
    assert "attestation" in line and "not" in line


def test_consult_title_mode_surfaces_local_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Title-mode consult: unattested class + local history → the lint line."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()  # drain validate's own output

    code, out, _err = _cli(["consult", GATEWAY_TEXT], capsys)
    assert code == 0
    assert "runbook: gateway-drain-window" in out
    assert "last_validated=never" in out, (
        "the runbook's OWN last_validated stays 'never' — the runbook is untouched"
    )
    assert "last lint-validated" in out
    assert LOCAL_VALIDATION_NOTE in out, out


def test_consult_failure_mode_surfaces_local_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--failure consult: history hit surfaces BELOW the runbook header line."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()

    code, out, _err = _cli(["consult", "--failure", FAILURE_TEXT], capsys)
    assert code == 0
    assert "this class has a runbook: gateway-drain-window" in out
    assert "last lint-validated" in out and LOCAL_VALIDATION_NOTE in out
    header_idx = out.find("this class has a runbook")
    lint_idx = out.find("last lint-validated")
    checks_idx = out.find("check 1:")
    assert -1 not in (header_idx, lint_idx, checks_idx)
    assert header_idx < lint_idx < checks_idx, (
        "the lint line lands between the header and the ordered checks"
    )


def test_consult_no_history_output_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No history file → consult output is EXACTLY today's (no lint line)."""
    monkeypatch.chdir(tmp_path)
    code, out, _err = _cli(["consult", GATEWAY_TEXT], capsys)
    assert code == 0
    assert "runbook: gateway-drain-window" in out
    assert "last_validated=never" in out
    assert "last lint-validated" not in out
    assert LOCAL_VALIDATION_NOTE not in out


def test_consult_attested_runbook_does_not_surface_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An operator-attested runbook shows its OWN date, not the lint line.

    Attestation wins: ``compile_class`` with a last_validated timestamp
    produces the validated runbook via the class registry — monkeypatched
    here (read-only test, the registry itself is NEVER mutated).
    """
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()

    def _attested(class_id: str) -> Runbook:
        assert class_id == "gateway-drain-window"
        from lore.runbook import Check

        return Runbook(
            class_id=class_id,
            name="Gateway drain window",
            signature="drain 503",
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
            last_validated="2026-09-30T00:00:00-05:00",
            status=STATUS_VALIDATED,
        )

    monkeypatch.setattr("lore.compiler.compile_class", _attested)
    code, out, _err = _cli(["consult", GATEWAY_TEXT], capsys)
    assert code == 0
    assert "last_validated=2026-09-30T00:00:00-05:00" in out
    assert "last lint-validated" not in out, (
        "the local-history line is for the NEVER-validated case only"
    )


# ------------------------------------- compile md: honest local-history line
def test_compile_md_surfaces_local_history_line(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """compile --format md: 'Last lint-validated' under the 'no data' line."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()

    code, out, _err = _cli(
        ["compile", "--class", "gateway-drain-window", "--format", "md"], capsys
    )
    assert code == 0
    assert "**Last validated:** no data (never validated)" in out, (
        "the runbook's own freshness line stays exactly as today"
    )
    assert "**Last lint-validated:** last lint-validated" in out
    assert LOCAL_VALIDATION_NOTE in out
    validated_idx = out.find("**Last validated:**")
    lint_idx = out.find("**Last lint-validated:**")
    provenance_idx = out.find("**Provenance:**")
    assert -1 not in (validated_idx, lint_idx, provenance_idx)
    assert validated_idx < lint_idx < provenance_idx, (
        "the lint line sits right under Last validated, before Provenance"
    )


def test_compile_md_without_history_has_no_lint_line(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No history → compile --format md output is unchanged byte-for-byte
    vs the pre-pin expectation (no 'Last lint-validated' text anywhere)."""
    monkeypatch.chdir(tmp_path)
    code, out, _err = _cli(
        ["compile", "--class", "gateway-drain-window", "--format", "md"], capsys
    )
    assert code == 0
    assert "**Last validated:** no data (never validated)" in out
    assert "lint-validated" not in out


def test_compile_json_output_unchanged_shape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """compile --format json round-trips unchanged — the lint line is a
    markdown-surface affordance, the JSON contract does not grow a field."""
    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()

    code, out, _err = _cli(
        ["compile", "--class", "gateway-drain-window", "--format", "json"], capsys
    )
    assert code == 0
    (data,) = json.loads(out)
    assert data["class_id"] == "gateway-drain-window"
    assert data["last_validated"] is None
    assert data["status"] == STATUS_PROPOSAL
    assert Runbook.from_dict(data).to_dict() == data  # lossless, unchanged shape


# ------------------------------------------------------- honesty-law pins
def test_honesty_laws_after_full_execute_cycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The END-TO-END honesty pin: after a real persisted --execute run,
    compile's runbook still has last_validated=None and status=proposal,
    consult still says last_validated=never, and nothing anywhere says
    'validated' as an attestation."""
    from lore.runbook import STATUS_PROPOSAL as _PROPOSAL

    _run, _calls = _all_ok_runner()
    monkeypatch.setattr("lore.validate._default_runner", _run)
    monkeypatch.chdir(tmp_path)
    main(["validate", "--class", "gateway-drain-window", "--execute"])
    capsys.readouterr()

    # 1. runbook fields untouched (compile json)
    _code, out, _err = _cli(
        ["compile", "--class", "gateway-drain-window", "--format", "json"], capsys
    )
    (data,) = json.loads(out)
    assert data["last_validated"] is None
    assert data["status"] == _PROPOSAL
    assert data["status"] != STATUS_VALIDATED

    # 2. consult still reports never + the LABELED lint line
    _code, cout, _err = _cli(["consult", GATEWAY_TEXT], capsys)
    assert "last_validated=never" in cout
    assert LOCAL_VALIDATION_NOTE in cout
    # the words 'status=validated' never appear
    assert "status=validated" not in cout

    # 3. compile md: 'no data (never validated)' intact + labeled lint line
    _code, mout, _err = _cli(
        ["compile", "--class", "gateway-drain-window", "--format", "md"], capsys
    )
    assert "**Last validated:** no data (never validated)" in mout
    assert LOCAL_VALIDATION_NOTE in mout


def test_history_line_distinct_from_attestation_vocabulary() -> None:
    """The surfaced phrase can never be misread as attestation: it names a
    lint run, its source file family, and the not-attestation qualifier."""
    rec = {"timestamp": "2026-10-01T19:15:06+00:00"}
    line = local_validation_note(rec)
    assert line.startswith("last lint-validated"), "a LINT run, not validation"
    assert "local history" in line
    assert "not operator attestation" in line
    # and it is NOT the attested phrase shape ('Last validated: <date>')
    assert not line.startswith("Last validated")


def test_apply_lint_still_never_sets_last_validated_or_validated_status() -> None:
    """Regression pin re-run for THIS task's surface: drift through the
    lint→history→consult path can never become attestation either."""
    from lore.runbook import Check
    from lore.validate import apply_lint

    rb = Runbook(
        class_id="gateway-drain-window",
        name="Gateway drain window",
        signature="drain 503",
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

    def _fail(_cmd: str):
        class _R:
            returncode = 1
            stdout = ""
            stderr = ""
            timed_out = False

        return _R()

    report = lint_runbook(rb, runner=_fail)
    new = apply_lint(report, rb)
    assert new.status == STATUS_STALE
    assert new.last_validated is None
