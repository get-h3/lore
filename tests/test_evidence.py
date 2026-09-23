"""Evidence-block extraction tests: vocabulary, parse, degrade, attach."""

from __future__ import annotations

import json

import pytest

from lore.compiler import compile_class
from lore.evidence import (
    KINDS,
    LOGSEY_EXPORT_CONTRACT_STATUS,
    EvidenceBlock,
    LogseyExportParseError,
    attach_evidence,
    degrade_to_command_output,
    is_known_kind,
    parse_logsey_export,
)
from lore.runbook import STATUS_PROPOSAL


# ------------------------------------------------------- curated vocabulary
def test_kind_vocabulary_is_closed_and_covers_existing_and_logsey_contract():
    # kinds already used by lore.compiler's curated tables
    for existing in ("board", "incident", "gap", "memory", "commit"):
        assert existing in KINDS
    # kinds the logsey export contract names
    for contracted in (
        "logsey-export",
        "command-output",
        "board-event",
        "duckbrain-row",
    ):
        assert contracted in KINDS
    assert is_known_kind("board")
    assert not is_known_kind("vibes")


def test_unknown_kind_is_refused_never_silently_accepted():
    with pytest.raises(ValueError):
        EvidenceBlock(kind="vibes", detail="feels healthy")


# ------------------------------------------------- EvidenceBlock shape/roundtrip
def test_to_trail_entry_is_exactly_kind_and_detail():
    b = EvidenceBlock(
        kind="logsey-export",
        detail="drain 503 at 18:31",
        source="gateway.service",
        observed_at="2026-09-23T18:31:00Z",
        window="18:30-19:10",
        fields={"severity": "err"},
    )
    entry = b.to_trail_entry()
    assert entry == {"kind": "logsey-export", "detail": "drain 503 at 18:31"}
    assert set(entry.keys()) == {"kind", "detail"}


def test_evidence_block_dict_roundtrip_is_lossless():
    b = EvidenceBlock(
        kind="command-output",
        detail="rc=0",
        source="/var/log/agent.log",
        observed_at="2026-09-23T10:00:00Z",
        window="09:55-10:05",
        fields={"level": "warn", "session-id": "s-1"},
    )
    assert EvidenceBlock.from_dict(b.to_dict()) == b


# ------------------------------------------------------------ parse contract
def test_contract_status_is_named_honestly():
    assert "unfrozen" in LOGSEY_EXPORT_CONTRACT_STATUS
    assert "not yet implemented" in LOGSEY_EXPORT_CONTRACT_STATUS


def test_non_export_text_yields_explicit_empty_result():
    # no fence, no export header -> "no blocks found" (empty, not an error)
    assert parse_logsey_export("not an export") == []


def test_empty_text_yields_empty_result():
    assert parse_logsey_export("") == []
    assert parse_logsey_export("   \n  ") == []


def test_json_line_inside_fence_parses_to_logsey_export_block():
    row = {
        "ts": "2026-09-23T18:31:00Z",
        "unit": "gateway.service",
        "severity": "err",
        "message": "drain 503 on in-flight request",
    }
    text = (
        "# logsey export --window 18:30-19:10\n```jsonl\n" + json.dumps(row) + "\n```"
    )
    blocks = parse_logsey_export(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.kind == "logsey-export"
    assert b.detail == "drain 503 on in-flight request"
    assert b.observed_at == "2026-09-23T18:31:00Z"
    assert b.source == "gateway.service"
    assert b.fields == row  # native passthrough preserved


def test_timestamped_source_attributed_text_line_parses():
    line = "2026-09-23T18:32:10Z unit=gateway.service severity=err drain 503 count=3"
    text = f"# logsey export --window 18:30-19:10\n```\n{line}\n```"
    blocks = parse_logsey_export(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.kind == "logsey-export"
    assert b.observed_at == "2026-09-23T18:32:10Z"
    assert b.source == "gateway.service"
    assert "drain 503 count=3" in b.detail


def test_structured_looking_line_that_fails_to_parse_is_an_explicit_failure():
    # a line that claims to be JSON but is not parseable must NOT be reported
    # as success in any shape — it raises the typed parse error.
    text = '# logsey export --window 18:30-19:10\n```\n{"ts": not-valid-json\n```'
    with pytest.raises(LogseyExportParseError):
        parse_logsey_export(text)


def test_export_header_without_block_is_an_explicit_failure():
    with pytest.raises(LogseyExportParseError):
        parse_logsey_export("logsey export --window 18:30-19:10\n(nothing else)")


# ------------------------------------------------------------- degrade path
def test_degrade_is_command_output_and_never_a_logsey_export():
    b = degrade_to_command_output(
        "git status --short", " M lore/compiler.py", returncode=0
    )
    assert b.kind == "command-output"
    assert b.kind != "logsey-export"
    assert is_known_kind(b.kind)


def test_degrade_carries_exact_command_and_raw_stdout():
    stdout = " M lore/evidence.py\n M tests/test_evidence.py\n"
    b = degrade_to_command_output("git status --short", stdout, returncode=0)
    assert "git status --short" in b.detail
    assert stdout in b.detail
    assert b.fields["command"] == "git status --short"
    assert b.fields["stdout"] == stdout
    assert b.fields["returncode"] == 0


def test_degrade_records_nonzero_returncode_honestly():
    b = degrade_to_command_output("grep -c 'drain 503' gw.log", "0", returncode=1)
    assert b.fields["returncode"] == 1
    assert "returncode=1" in b.detail


# ----------------------------------------------------------- attach evidence
def _rb():
    return compile_class("gateway-drain-window")


def test_attach_returns_new_runbook_original_untouched():
    rb = _rb()
    blocks = [degrade_to_command_output("git status --short", "clean", returncode=0)]
    rb2 = attach_evidence(rb, blocks)
    assert rb2 is not rb
    assert rb2.evidence_trail != rb.evidence_trail
    assert rb.evidence_trail == [
        {"kind": "board", "detail": "LORE-003 seed class 'gateway drain window'"},
        {
            "kind": "incident",
            "detail": "PRD §The problem, measured case 1 (four incidents + compaction-boundary loss)",
        },
        {"kind": "memory", "detail": "curated note 'drain 503s kill ticks'"},
    ]


def test_attach_extends_trail_in_deterministic_order():
    rb = _rb()
    blocks = [
        EvidenceBlock(kind="board-event", detail="row LORE-005"),
        EvidenceBlock(kind="duckbrain-row", detail="table checks, key gw-1"),
    ]
    rb2 = attach_evidence(rb, blocks)
    assert rb2.evidence_trail[-2:] == [b.to_trail_entry() for b in blocks]
    rb3 = attach_evidence(rb, list(reversed(blocks)))
    assert rb3.evidence_trail[-2:] == [
        EvidenceBlock(
            kind="duckbrain-row", detail="table checks, key gw-1"
        ).to_trail_entry(),
        EvidenceBlock(kind="board-event", detail="row LORE-005").to_trail_entry(),
    ]


def test_attach_is_deterministic_byte_identical_to_dict():
    rb = _rb()
    blocks = [degrade_to_command_output("git status --short", "clean", returncode=0)]
    a = json.dumps(attach_evidence(rb, blocks).to_dict(), sort_keys=True)
    b = json.dumps(attach_evidence(rb, blocks).to_dict(), sort_keys=True)
    assert a == b


def test_attach_per_check_mapping_lands_on_matching_checks():
    rb = _rb()
    blocks = {
        1: [
            degrade_to_command_output(
                "logsey query --pattern 'drain 503' --since 30m", "0 rows", returncode=0
            )
        ]
    }
    rb2 = attach_evidence(rb, [], per_check=blocks)
    check1 = next(c for c in rb2.checks if c.order == 1)
    assert check1.evidence[-1] == {
        "kind": "command-output",
        "detail": blocks[1][0].detail,
    }
    # a check that was not mapped keeps its curated evidence untouched
    check2 = next(c for c in rb2.checks if c.order == 2)
    assert check2.evidence == next(c for c in rb.checks if c.order == 2).evidence


def test_attach_per_check_unknown_order_is_refused_not_dropped():
    rb = _rb()
    with pytest.raises(ValueError):
        attach_evidence(rb, [], per_check={99: [degrade_to_command_output("x", "y")]})


def test_attach_does_not_attest_validation():
    rb = _rb()
    rb2 = attach_evidence(rb, [EvidenceBlock(kind="commit", detail="abc123")])
    assert rb2.last_validated is None
    assert rb2.status == STATUS_PROPOSAL
    assert rb2.status == rb.status
    assert rb2.last_validated == rb.last_validated


def test_attached_runbook_survives_runbook_roundtrip_losslessly():
    rb = _rb()
    blocks = [degrade_to_command_output("git status --short", "clean", returncode=0)]
    rb2 = attach_evidence(rb, blocks)
    assert rb2.to_dict() == rb2.from_dict(rb2.to_dict()).to_dict()
    # the trail entries keep the exact {"kind","detail"} shape the model uses
    assert all(set(e.keys()) == {"kind", "detail"} for e in rb2.evidence_trail)
    assert all(
        set(e.keys()) >= {"kind", "detail"} for c in rb2.checks for e in c.evidence
    )


def test_parsed_blocks_attach_end_to_end_refindable():
    row = {
        "ts": "2026-09-23T18:31:00Z",
        "unit": "gateway.service",
        "message": "drain 503 on in-flight request",
    }
    text = (
        "# logsey export --window 18:30-19:10\n```jsonl\n" + json.dumps(row) + "\n```"
    )
    blocks = parse_logsey_export(text)
    rb2 = attach_evidence(_rb(), blocks)
    assert {
        "kind": "logsey-export",
        "detail": "drain 503 on in-flight request",
    } in rb2.evidence_trail
