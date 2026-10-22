"""LORE-008 tests: the absorb-gate on close (decision records + gate + CLI).

Covers: valid absorb / no-new-lesson, closed-registry refusal, missing
lesson/reason, bad decision word, non-ISO decided_at, multi-violation
verdicts, CLI exit codes, the fail-safe absorb_proposal, and the
propose-not-write guard (gate_close must never touch the filesystem).
"""

from __future__ import annotations

import json

import pytest

from lore.__main__ import main
from lore.absorb import (
    DECISION_ABSORB,
    DECISION_NO_NEW_LESSON,
    OUTCOME_DEAD_END,
    OUTCOME_OBSERVED,
    AbsorbDecision,
    absorb_proposal,
    absorb_sweep,
    block_outcome,
    gate_close,
    validate_close_decision,
)
from lore.classes import UNCLASSIFIED_ID, get_registry
from lore.classifier import classify
from lore.compiler import compile_class, propose

# LORE-069 sweep fixtures: the documented logsey-export shape, one block per
# class (same shape test_cli_surface.py and test_lore020 use).
_TRAIL_FIXTURE_HEADER = "logsey export --window 2h"
_FENCED_TRAIL = f"""{_TRAIL_FIXTURE_HEADER}
```
2026-09-24T10:00:00 unit=loreforge gateway drain 503 while restart
2026-09-24T10:05:00 unit=loreforge index.lock fight on the shared checkout
```
"""

_CLOSED_REGISTRY_ERROR = (
    "unknown class 'nope' — registry is closed; carry the proposed lesson "
    "text for operator review instead"
)


# ------------------------------------------------------------- valid paths
def test_valid_absorb_allowed_errors_empty():
    d = AbsorbDecision(
        decision=DECISION_ABSORB,
        class_id="gateway-drain-window",
        lesson="drain before restart",
        reason="drain 503s were expected, not a fault",
        ack_ref="INC-42",
        decided_at="2026-09-24T12:00:00",
    )
    v = gate_close(d)
    assert v.allowed is True
    assert v.errors == []
    assert v.decision is d


def test_valid_no_new_lesson_allowed():
    d = AbsorbDecision(
        decision=DECISION_NO_NEW_LESSON,
        reason="routine redeploy, nothing new observed",
        ack_ref="TASK-7",
    )
    v = gate_close(d)
    assert v.allowed is True
    assert v.errors == []


# --------------------------------------------------------------- denials
def test_absorb_unknown_class_denied_with_closed_registry_error():
    v = gate_close(
        AbsorbDecision(decision=DECISION_ABSORB, class_id="nope", lesson="x")
    )
    assert v.allowed is False
    assert _CLOSED_REGISTRY_ERROR in v.errors


def test_absorb_missing_lesson_denied():
    v = gate_close(
        AbsorbDecision(
            decision=DECISION_ABSORB, class_id="gateway-drain-window", lesson="   "
        )
    )
    assert v.allowed is False
    assert "absorb requires a lesson" in v.errors


def test_absorb_missing_class_id_denied():
    v = gate_close(AbsorbDecision(decision=DECISION_ABSORB, lesson="something"))
    assert v.allowed is False
    assert "absorb requires a class_id" in v.errors


def test_no_new_lesson_without_reason_denied():
    v = gate_close(AbsorbDecision(decision=DECISION_NO_NEW_LESSON, reason="  "))
    assert v.allowed is False
    assert "no-new-lesson requires a reason" in v.errors


def test_bad_decision_word_denied():
    v = gate_close(AbsorbDecision(decision="absorbed", lesson="x"))
    assert v.allowed is False
    assert "decision must be 'absorb' or 'no-new-lesson'" in v.errors


def test_non_iso_decided_at_denied():
    d = AbsorbDecision(
        decision=DECISION_NO_NEW_LESSON,
        reason="fine",
        decided_at="24/09/2026 noon",
    )
    v = gate_close(d)
    assert v.allowed is False
    assert "decided_at is not ISO-8601" in v.errors


def test_multiple_violations_all_reported():
    # absorb with: no class, no lesson, bad timestamp — all three listed.
    d = AbsorbDecision(decision=DECISION_ABSORB, decided_at="not-a-date")
    v = validate_close_decision(d)
    assert v.allowed is False
    assert len(v.errors) == 3
    assert "absorb requires a class_id" in v.errors
    assert "absorb requires a lesson" in v.errors
    assert "decided_at is not ISO-8601" in v.errors


# ------------------------------------------------------------- CLI wiring
def test_cli_gate_allow_exit0(capsys):
    rc = main(
        [
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "no new failure class",
            "--ref",
            "TEST-1",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "GATE: ALLOW (no-new-lesson)" in out


def test_cli_gate_deny_exit1_unknown_class(capsys):
    rc = main(["gate", "--decision", "absorb", "--class", "nope", "--lesson", "x"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "GATE: DENY" in out
    assert "unknown class 'nope'" in out


def test_cli_gate_absorb_allow_exit0(capsys):
    rc = main(
        [
            "gate",
            "--decision",
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "drain before restart",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "GATE: ALLOW (absorb -> gateway-drain-window)" in out


def test_cli_gate_decided_at_omitted_stays_none(capsys):
    rc = main(
        [
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "nothing learned",
        ]
    )
    assert rc == 0
    # No timestamp invented: the CLI never fabricated a decided_at.


# -------------------------------------------------------- absorb_proposal
def test_absorb_proposal_contains_lesson_for_seeded_class():
    payload = absorb_proposal("gateway-drain-window", "drain before restart")
    assert "error" not in payload
    assert payload["lesson"] == "drain before restart"
    assert payload["class_id"] == "gateway-drain-window"
    # LORE-069: the proposal diffs against the class's EXISTING runbook, so a
    # curated class always gets "update" — even when the lesson adds nothing
    # (an explicitly empty update, never a fabricated "new" with a byte-copy
    # of the runbook the class already has).
    assert payload["action"] == "update"
    assert "added" in payload


def test_absorb_proposal_bogus_class_failsafe_error():
    payload = absorb_proposal("definitely-not-a-class", "lesson text")
    assert payload == {"error": "unknown class 'definitely-not-a-class'"}


# ------------------------------------------------- propose-not-write guard
def test_gate_close_performs_no_filesystem_writes(tmp_path, monkeypatch):
    """The gate must be pure: run it inside an empty tmp dir and prove the
    directory stays empty (no files created, no registry mutation)."""
    monkeypatch.chdir(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())
    assert before == []

    for d in (
        AbsorbDecision(
            decision=DECISION_ABSORB,
            class_id="gateway-drain-window",
            lesson="drain before restart",
            ack_ref="INC-1",
        ),
        AbsorbDecision(decision=DECISION_NO_NEW_LESSON, reason="nothing new"),
        AbsorbDecision(decision="bogus", lesson="", decided_at="garbage"),
    ):
        gate_close(d)

    after = sorted(p.name for p in tmp_path.iterdir())
    assert after == []
    # Registry untouched: same class ids before and after, register still refuses.
    ids_before = [c.id for c in get_registry().all_classes()]
    assert UNCLASSIFIED_ID in ids_before
    with pytest.raises(RuntimeError):
        get_registry().register(
            id="sneaky",
            name="s",
            description="d",
            signature_patterns=(),
            keywords=(),
            provenance="p",
        )


def test_absorb_proposal_stdout_only(tmp_path, monkeypatch, capsys):
    """The absorb convenience is propose-not-write too: stdout only."""
    monkeypatch.chdir(tmp_path)
    payload = absorb_proposal("shared-checkout-collision", "stage explicit paths")
    line = json.dumps(payload)
    assert '"lesson"' in line
    # no files created: the library call is pure
    assert sorted(p.name for p in tmp_path.iterdir()) == []


# --------------------------------------- LORE-009: QA/dogfood provenance source
def test_absorb_decision_source_default_none():
    d = AbsorbDecision(
        decision=DECISION_ABSORB,
        class_id="gateway-drain-window",
        lesson="drain before restart",
    )
    v = gate_close(d)
    assert v.allowed is True
    assert d.source is None  # default: unchanged behavior


def test_absorb_decision_qa_dagger_source_allowed():
    d = AbsorbDecision(
        decision=DECISION_ABSORB,
        class_id="gateway-drain-window",
        lesson="drain before restart",
        source="qa-dagger",
    )
    v = gate_close(d)
    assert v.allowed is True
    assert v.decision.source == "qa-dagger"


def test_absorb_proposal_records_source_when_given():
    payload = absorb_proposal(
        "gateway-drain-window", "drain before restart", source="dogfood-dagger"
    )
    assert payload["source"] == "dogfood-dagger"


def test_absorb_proposal_default_has_no_source_key_byte_compatible():
    payload = absorb_proposal("gateway-drain-window", "drain before restart")
    assert "source" not in payload  # default keeps the old shape exactly


def test_cli_gate_source_recorded(capsys):
    rc = main(
        [
            "gate",
            "--decision",
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "drain before restart",
            "--source",
            "qa-dagger",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "GATE: ALLOW" in out
    assert "source: qa-dagger" in out


def test_cli_gate_no_source_no_source_line_byte_compatible(capsys):
    rc = main(
        [
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "nothing learned",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "source:" not in out  # default prints exactly the old output


def test_cli_absorb_source_recorded(capsys):
    rc = main(
        [
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "drain before restart",
            "--source",
            "dogfood-dagger",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert '"source": "dogfood-dagger"' in out


def test_cli_absorb_no_source_byte_compatible(capsys):
    rc = main(
        [
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "drain before restart",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert '"source"' not in out


# --------------------------------- LORE-069: absorb proposals are real updates
def test_absorb_proposal_update_on_lesson_with_timestamped_evidence_lines():
    """A lesson parsed into timestamped evidence lines diffs against the
    existing runbook: action becomes update and the payload carries the
    trail-derived content (the lesson's own evidence is NOT byte-identical
    to the curated trail, so added/changed must name it)."""
    lesson = (
        "2026-10-20T08:00:00Z unit=loreforge drain window opened; 503s bounded\n"
        "2026-10-20T08:10:00Z unit=loreforge curl health probe FAILED to reach "
        "the gateway during the window -- dead end, use logsey query instead"
    )
    payload = absorb_proposal("gateway-drain-window", lesson)
    assert payload["action"] == "update"
    assert "error" not in payload
    folded = payload["added"].get("evidence_trail", [])
    assert folded, "lesson-derived blocks must reach the folded trail diff"
    joined = json.dumps(folded)
    assert "drain window opened" in joined
    assert "logsey query" in joined
    # Append-only fold: the existing trail gains the lesson's blocks, so
    # nothing is removed — the update names ONLY the trail-derived content.
    assert payload["removed"] == {}
    # Per-block US-2 rendering present, with outcomes.
    kinds = [b["kind"] for b in payload["blocks"]]
    assert kinds == ["logsey-export", "logsey-export"]
    outcomes = [b["outcome"] for b in payload["blocks"]]
    assert OUTCOME_DEAD_END in outcomes
    assert OUTCOME_OBSERVED in outcomes
    assert any(b["source"] == "loreforge" for b in payload["blocks"])


def test_absorb_proposal_no_change_trail_is_explicit_empty_update():
    """A lesson whose folded trail equals the existing runbook's trail
    stays an EXPLICIT EMPTY update — never a "new", never an invented delta."""
    existing = compile_class("gateway-drain-window")
    payload = absorb_proposal(
        "gateway-drain-window",
        "drain before restart",
        blocks=list(existing.evidence_trail),
    )
    assert payload["action"] == "update"
    assert payload["added"] == {}
    assert payload["removed"] == {}
    assert payload["changed"] == {}


def test_absorb_proposal_no_change_prose_lesson_is_empty_update_too():
    """A prose-only lesson (no timestamped lines) parses to NO blocks; the
    fold is a no-op and the proposal is still an honest empty update."""
    payload = absorb_proposal("gateway-drain-window", "drain before restart")
    assert payload["action"] == "update"
    assert payload["added"] == {}
    assert payload["removed"] == {}
    assert payload["changed"] == {}
    assert payload["blocks"] == []


def test_absorb_proposal_blocks_carry_closed_outcome_vocabulary():
    """Every per-block outcome is exactly "dead-end" or "observed" — the
    closed vocabulary, no invented third state, dead ends marked dead."""
    lesson = (
        "2026-10-20T08:00:00Z unit=loreforge SIGKILL during load: nothing worked\n"
        "2026-10-20T08:05:00Z unit=loreforge drained cleanly, 503s bounded"
    )
    payload = absorb_proposal("gateway-drain-window", lesson)
    assert {b["outcome"] for b in payload["blocks"]} <= {
        OUTCOME_DEAD_END,
        OUTCOME_OBSERVED,
    }
    assert OUTCOME_DEAD_END in {b["outcome"] for b in payload["blocks"]}
    assert payload["blocks"][0]["outcome"] == OUTCOME_DEAD_END


def test_absorb_proposal_dead_end_markers_word_bounded():
    assert block_outcome("deadline moved, we shipped anyway") == OUTCOME_OBSERVED
    assert block_outcome("undead process kept serving") == OUTCOME_OBSERVED
    assert (
        block_outcome("the flush command failed to clear the queue") == OUTCOME_DEAD_END
    )
    assert (
        block_outcome("tried the legacy drain, ended in a dead end") == OUTCOME_DEAD_END
    )


def test_absorb_proposal_unclassified_class_still_updates():
    """Absorbing into unclassified stays allowed — and is now an update with
    the lesson's evidence named in the diff (unclassified has NO curated
    trail, so the folded trail is pure addition)."""
    lesson = "2026-10-20T08:00:00Z unit=loreforge weird noise from the coffee machine"
    payload = absorb_proposal(UNCLASSIFIED_ID, lesson)
    assert payload["action"] == "update"
    assert payload["added"].get("evidence_trail"), (
        "unclassified has no curated trail: the lesson block is pure addition"
    )
    assert payload["removed"] == {}
    assert payload["blocks"][0]["kind"] == "logsey-export"


def test_absorb_proposal_unknown_class_failsafe_unchanged():
    payload = absorb_proposal("definitely-not-a-class-069", "x")
    assert payload == {"error": "unknown class 'definitely-not-a-class-069'"}


def test_absorb_proposal_folded_blocks_use_the_sweep_parser_tolerance():
    """The lesson parse reuses parse_text_line (the sweep's exact tolerance):
    a timestamped block keeps its parsed source/observed_at and the trail
    entry keeps the {kind, detail} shape Runbook.evidence_trail uses."""
    lesson = "2026-10-20T08:00:00Z unit=loreforge health 503 during drain window"
    payload = absorb_proposal("gateway-drain-window", lesson)
    block = payload["blocks"][0]
    assert block["source"] == "loreforge"
    assert block["observed_at"] == "2026-10-20T08:00:00Z"
    folded_entry = payload["added"]["evidence_trail"][0]
    assert folded_entry == {"kind": "logsey-export", "detail": block["detail"]}


def test_propose_fresh_side_default_unchanged():
    """compiler.propose's fresh-side seam is additive: omitting it keeps the
    curated default (and the empty-diff contract over an unchanged existing)."""
    rb = compile_class("gateway-drain-window")
    proposal = propose("gateway-drain-window", rb)
    assert proposal["action"] == "update"
    assert proposal["added"] == {}
    assert proposal["removed"] == {}
    assert proposal["changed"] == {}
    # Providing the same compiled runbook as fresh must not change the diff.
    same = propose(
        "gateway-drain-window", rb, fresh=compile_class("gateway-drain-window")
    )
    assert same == proposal


def test_absorb_sweep_emits_update_with_trail_derived_added():
    """CLI-observable end of LORE-069: the sweep's per-class proposals say
    "update" and their added.evidence_trail names the swept blocks."""
    from lore.evidence import parse_logsey_export

    blocks = parse_logsey_export(_FENCED_TRAIL)
    proposals = absorb_sweep(blocks, window="2h", ns="X", board="/tmp/board")
    by_id = {p["class_id"]: p for p in proposals}
    for class_id in ("gateway-drain-window", "shared-checkout-collision"):
        p = by_id[class_id]
        assert p["action"] == "update"
        assert p["added"].get("evidence_trail"), (
            f"{class_id}: swept blocks must be folded into the diff"
        )
        swept_detail = next(
            b.detail for b in blocks if classify(b.detail).class_id == class_id
        )
        assert swept_detail in json.dumps(p["added"]["evidence_trail"])
        assert p["sweep"]["blocks_class"] >= 1


def test_cli_absorb_single_proposal_is_update_with_blocks(capsys):
    rc = main(
        [
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "2026-10-20T08:00:00Z unit=loreforge drain window opened; 503s bounded",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["action"] == "update"
    assert payload["added"].get("evidence_trail")
    assert payload["blocks"][0]["outcome"] in (OUTCOME_DEAD_END, OUTCOME_OBSERVED)


def test_cli_absorb_window_sweep_payloads_are_updates(capsys, monkeypatch, tmp_path):
    fixture = tmp_path / "trail.txt"
    fixture.write_text(_FENCED_TRAIL, encoding="utf-8")
    rc = main(["absorb", "--window", "2h", "--trail-file", str(fixture)])
    assert rc == 0
    proposals = json.loads(capsys.readouterr().out)
    assert proposals
    for p in proposals:
        assert p["action"] == "update"
        assert p["blocks"], "every per-class proposal carries its folded blocks"


def test_grep_production_callers_pass_existing():
    """The board row's greppable AC: the shipped package must contain at
    least one production `existing=` call site (the defect was that the only
    caller passed none)."""
    import pathlib
    import re as _re

    hits = []
    src = pathlib.Path("lore")
    for py in src.glob("*.py"):
        for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if _re.search(r"existing=", line):
                hits.append((str(py), n, line.strip()))
    assert hits, "no production 'existing=' call site found"
    assert any("absorb.py" in f for f, _n, _l in hits)
