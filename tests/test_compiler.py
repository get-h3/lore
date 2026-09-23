"""Compiler tests: per-class runbooks, propose-not-write, honesty rules."""

from __future__ import annotations

import builtins
import json

import pytest

from lore.classes import UNCLASSIFIED_ID, get_registry
from lore.compiler import (
    NO_VALID_EVIDENCE,
    Check,
    Runbook,
    compile_all,
    compile_class,
    propose,
    render_proposal_diff,
)
from lore.runbook import STATUS_PROPOSAL, STATUS_VALIDATED


# ------------------------------------------------------------- basic compile
def test_compile_all_covers_every_registry_class():
    reg_ids = [c.id for c in get_registry().all_classes()]
    runbooks = compile_all()
    assert [rb.class_id for rb in runbooks] == reg_ids
    assert len(runbooks) == len(reg_ids)


def test_runbook_closes_prd_sections_for_every_class():
    for rb in compile_all():
        assert rb.name
        assert rb.signature, "signature must never be empty"
        assert rb.provenance
        assert isinstance(rb.recovery_ladder, list)
        assert isinstance(rb.guardrails, list)
        assert isinstance(rb.evidence_trail, list)


def test_gateway_runbook_has_real_read_only_checks():
    rb = compile_class("gateway-drain-window")
    assert rb.checks, "the doctrine class must carry its compiled checks"
    assert rb.checks == sorted(rb.checks, key=lambda c: c.order), "checks ordered"
    for c in rb.checks:
        assert c.command
        assert c.expected_healthy
        assert c.expected_incident
        assert c.decision
        assert isinstance(c.read_only, bool)
        assert all(set(e.keys()) >= {"kind", "detail"} for e in c.evidence)
    assert all(c.read_only for c in rb.checks), "doctrine checks are read-only probes"


def test_guardrails_carry_the_never_x_laws():
    assert any(
        "--apply" in g and "cooldown" in g.lower()
        for g in compile_class("cooldown-pin-drift").guardrails
    )
    sc = compile_class("shared-checkout-collision")
    assert any("reap --all" in g and "end-of-tick" in g for g in sc.guardrails)
    assert any(
        "two workers" in g.lower() or "never put two workers" in g.lower()
        for g in sc.guardrails
    )
    gd = compile_class("guard-degradation")
    assert any(
        "not gate-equivalent" in g or "control worktree" in g for g in gd.guardrails
    )
    ib = compile_class("ingest-backfill-gap")
    assert any("unannotated" in g and "window" in g for g in ib.guardrails)


def test_evidence_trail_present_for_curated_classes():
    for rb in compile_all():
        if rb.class_id == UNCLASSIFIED_ID:
            continue
        assert rb.evidence_trail, f"{rb.class_id}: curated class must carry its trail"
        kinds = {e["kind"] for e in rb.evidence_trail}
        assert kinds, "evidence entries carry kinds"
        assert all(e.get("detail") for e in rb.evidence_trail)


# ------------------------------------------------------------- honesty rules
def test_no_evidence_means_never_validated():
    rb = compile_class("gateway-drain-window")
    assert rb.last_validated is None
    assert rb.status == STATUS_PROPOSAL


def test_last_validated_only_by_explicit_attestation():
    rb = compile_class(
        "gateway-drain-window", last_validated="2026-09-23T00:00:00-05:00"
    )
    assert rb.last_validated == "2026-09-23T00:00:00-05:00"
    assert rb.status == STATUS_VALIDATED


def test_absent_sections_render_as_no_data():
    rb = Runbook(class_id="x", name="x", signature="sig", provenance="p")
    md = rb.to_markdown()
    assert "no data" in md
    assert md.count("no data") >= 3  # checks, ladder, guardrails, trail all absent


def test_unclassified_is_honest_catch_all():
    rb = compile_class(UNCLASSIFIED_ID)
    assert rb.class_id == UNCLASSIFIED_ID
    assert rb.last_validated is None
    assert rb.status == STATUS_PROPOSAL
    assert not rb.checks, "catch-all compiles NO invented checks"
    assert len(rb.recovery_ladder) == 1
    assert "no recovery ladder" in rb.recovery_ladder[0].lower()
    assert "never invent" in " ".join(rb.guardrails).lower()


def test_unknown_class_raises_keyerror():
    with pytest.raises(KeyError):
        compile_class("does-not-exist")


def test_caller_evidence_is_used_but_never_fabricates_validation():
    trail = [{"kind": "incident", "detail": "caller-supplied 09-16 trail"}]
    rb = compile_class("gateway-drain-window", evidence=trail)
    assert rb.evidence_trail == trail
    assert rb.last_validated is None
    assert rb.status == STATUS_PROPOSAL


# ------------------------------------------------------------- propose-not-write
def test_no_publish_entrypoint_on_compiler_module():
    """The compiler must expose NO publish/write/save entry point."""
    import lore.compiler as mod

    forbidden = {"publish", "write_runbook", "save", "write", "commit"}
    exposed = set(dir(mod))
    leaked = forbidden & exposed
    assert not leaked, f"compiler leaks write-shaped entry points: {leaked}"


def test_compiler_module_source_never_opens_files_for_writing():
    """No compile path performs a filesystem write of runbooks."""
    import inspect

    import lore.compiler as mod

    src = inspect.getsource(mod)
    for marker in ("open(", "write_text", "write_bytes", "os.remove", "shutil"):
        assert marker not in src, f"compiler module contains {marker!r}"


def test_compile_is_stdout_only(tmp_path, monkeypatch, capsys):
    """Compile and render produce stdout; nothing lands on disk anywhere."""
    monkeypatch.chdir(tmp_path)
    rbs = compile_all()
    for rb in rbs:
        rb.to_markdown()
        rb.to_dict()
    render_proposal_diff("gateway-drain-window")
    propose("gateway-drain-window", None)
    captured = capsys.readouterr()
    assert captured.out == "", "compile/render must not print as a side effect"
    assert captured.err == ""
    # The only filesystem effect allowed: pytest/pycache noise, no runbooks.
    for p in tmp_path.rglob("*"):
        text = p.read_text(errors="ignore") if p.is_file() else ""
        assert "runbook" not in text.lower() or "signature" not in text.lower(), (
            f"runbook content leaked to disk at {p}"
        )


# ------------------------------------------------------------- proposals
def test_propose_new_runbook_is_full_addition():
    proposal = propose("gateway-drain-window", None)
    assert proposal["action"] == "new"
    assert proposal["added"]["class_id"] == "gateway-drain-window"
    assert proposal["note"], "proposal must say it needs operator approval"


def test_propose_against_unchanged_existing_is_empty_diff():
    rb = compile_class("gateway-drain-window")
    proposal = propose("gateway-drain-window", rb)
    assert proposal["action"] == "update"
    assert proposal["added"] == {}
    assert proposal["removed"] == {}
    assert proposal["changed"] == {}


def test_propose_detects_check_changes():
    rb = compile_class("gateway-drain-window")
    new_check = Check.from_dict(rb.checks[0].to_dict())  # frozen: rebuild mutated copy
    new_check_dict = new_check.to_dict()
    new_check_dict["command"] = "totally different command"
    mutated = Runbook.from_dict(
        {
            **rb.to_dict(),
            "checks": [new_check_dict] + [c.to_dict() for c in rb.checks[1:]],
        }
    )
    proposal = propose("gateway-drain-window", mutated)
    assert proposal["changed"]["checks"], "mutated check must appear in changed"
    # frozen dataclasses: the mutation must not have leaked into compile output
    fresh = compile_class("gateway-drain-window")
    assert fresh.checks[0].command != "totally different command"


def test_propose_detects_guardrail_and_ladder_changes():
    rb = compile_class("shared-checkout-collision")
    d = rb.to_dict()
    d["guardrails"] = d["guardrails"][:-1]
    d["recovery_ladder"] = ["only step"]
    fewer = Runbook.from_dict(d)
    proposal = propose("shared-checkout-collision", fewer)
    assert len(proposal["added"]["guardrails"]) == 1
    assert proposal["added"]["recovery_ladder"], "replaced ladder must show as added"


def test_render_proposal_diff_is_unified_text():
    rb = compile_class("gateway-drain-window")
    mutated = Runbook.from_dict(rb.to_dict())
    object.__setattr__(mutated, "checks", [])  # frozen dataclass: strip checks
    diff = render_proposal_diff("gateway-drain-window", mutated)
    assert diff.startswith("---")
    assert "+++ " in diff
    assert "+-" in diff or "\n+" in diff or "@@" in diff


def test_render_proposal_diff_new_runbook_differs_against_empty():
    diff = render_proposal_diff("gateway-drain-window", None)
    assert diff.startswith("---")
    assert "runbook/gateway-drain-window/proposed" in diff


# ------------------------------------------------------------- round-trip
def test_runbook_round_trip_is_lossless():
    for rb in compile_all():
        d = json.loads(json.dumps(rb.to_dict()))
        rt = Runbook.from_dict(d)
        assert rt == rb, f"{rb.class_id}: round-trip must be lossless"
        assert json.loads(json.dumps(rt.to_dict())) == d


def test_check_round_trip_is_lossless():
    c = Check(
        order=2,
        command="sqlite3 db 'PRAGMA quick_check;'",
        expected_healthy="ok",
        expected_incident="corrupt",
        decision="repair path",
        read_only=True,
        evidence=[{"kind": "incident", "detail": "ENOSPC wipe"}],
    )
    d = json.loads(json.dumps(c.to_dict()))
    assert Check.from_dict(d) == c


def test_no_valid_evidence_sentinel_is_honest():
    assert NO_VALID_EVIDENCE == "no data"


# ------------------------------------------------------------- CLI: compile
def _run_main(argv):
    from lore.__main__ import main

    return main(argv)


def test_cli_compile_all_json(capsys):
    code = _run_main(["compile", "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert [rb["class_id"] for rb in data] == [
        c.id for c in get_registry().all_classes()
    ]
    assert all(
        set(rb) >= {"class_id", "name", "signature", "checks", "guardrails", "status"}
        for rb in data
    )


def test_cli_compile_one_class_md(capsys):
    code = _run_main(["compile", "--class", "gateway-drain-window", "--format", "md"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.startswith("# Runbook:")
    assert "## Guardrails" in out
    assert "drain" in out


def test_cli_compile_unknown_class_exits_nonzero(capsys):
    code = _run_main(["compile", "--class", "does-not-exist"])
    assert code != 0
    err = capsys.readouterr().err
    assert "does-not-exist" in err
    assert "closed" in err.lower()


def test_cli_compile_defaults_to_json(capsys):
    code = _run_main(["compile"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == len(get_registry())


def test_cli_match_still_works(capsys):
    code = _run_main(["match", "drain 503"])
    assert code == 0
    assert "gateway-drain-window" in capsys.readouterr().out


# ------------------------------------------------------------- builtins guard
def test_compile_does_not_touch_filesystem_writes_via_builtins(monkeypatch):
    """Patch builtins.open to fail on write modes; a full compile must not trip it."""
    real_open = builtins.open

    def guarded_open(file, mode="r", *a, **kw):
        if any(m in mode for m in ("w", "a", "x", "+")):
            raise AssertionError(
                f"compile path opened {file!r} with write mode {mode!r}"
            )
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", guarded_open)
    rbs = compile_all()
    assert len(rbs) == len(get_registry())
    for rb in rbs:
        rb.to_markdown()
        rb.to_dict()
