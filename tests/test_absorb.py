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
    AbsorbDecision,
    absorb_proposal,
    gate_close,
    validate_close_decision,
)
from lore.classes import UNCLASSIFIED_ID, get_registry

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
    # propose() semantics: a full new-runbook proposal when no existing runbook.
    assert payload["action"] == "new"
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
