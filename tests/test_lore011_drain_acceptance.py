"""LORE-011 acceptance: drain-window trail replay.

The trail fixture (tests/fixtures/trails/2026-09-16-drain-window-trail.md)
carries ONLY raw pre-2026-09-16 observations. These tests prove lore's real
machinery consumes it: the logsey fence parses into evidence blocks, every
kind-labeled line uses the closed vocabulary, the trail classifies to the
gateway-drain-window class, and the compiler's gateway checks carry one
evidence citation per trail line they were derived from.
"""

from __future__ import annotations

from pathlib import Path

from lore.classifier import classify_all
from lore.compiler import compile_class
from lore.evidence import KINDS, parse_logsey_export
from lore.validate import is_read_only_command

TRAIL_PATH = (
    Path(__file__).parent / "fixtures" / "trails" / "2026-09-16-drain-window-trail.md"
)

# Trail lines (verbatim) each added compiler check was derived from. The
# mapping is the acceptance contract: no check without its trail citation.
CHECK_TRAIL_LINES = {
    4: "config writes during a gateway restart 503'd",
    5: "SIGKILL received during load; 214 in-flight requests terminated with 503",
    6: "restart executed with queue_depth=14 unflushed rows; queued state lost on restart",
    7: "96 503s inside the incident window; baseline outside the window measured 0 per hour",
}


def test_trail_fixture_exists_and_is_scoped_pre_doctrine():
    text = TRAIL_PATH.read_text()
    assert "2026-09-16" in TRAIL_PATH.name
    # No baseline-doctrine language smuggled in as evidence: the doctrine
    # bullets are the scoring baseline, never trail lines.
    for doctrine_marker in (
        "recovery ladder",
        "restart order:",
        "verify with read-only probes:",
    ):
        assert doctrine_marker not in text, (
            f"doctrine leaked into trail: {doctrine_marker!r}"
        )


def test_trail_logsey_fence_parses_into_evidence_blocks():
    text = TRAIL_PATH.read_text()
    blocks = parse_logsey_export(text)
    assert len(blocks) >= 8, "the four incidents' raw lines must parse"
    assert all(b.kind == "logsey-export" for b in blocks)
    assert all(b.observed_at for b in blocks), "every raw line is timestamped"


def test_trail_kind_labeled_lines_use_closed_vocabulary():
    text = TRAIL_PATH.read_text()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- [") and "]" in line:
            kind = line[3 : line.index("]")]
            assert kind in KINDS, f"unknown trail kind {kind!r} (closed vocabulary)"


def test_trail_classifies_to_gateway_drain_window():
    text = TRAIL_PATH.read_text()
    candidates = classify_all(text)
    assert candidates, "the trail must classify"
    assert candidates[0].class_id == "gateway-drain-window"
    assert candidates[0].confidence >= 0.9


def test_drain_checks_carry_trail_evidence_citations():
    rb = compile_class("gateway-drain-window")
    by_order = {c.order: c for c in rb.checks}
    for order, trail_line in CHECK_TRAIL_LINES.items():
        check = by_order[order]
        assert any(trail_line in e["detail"] for e in check.evidence), (
            f"check {order} must cite its trail line ({trail_line!r})"
        )


def test_drain_checks_are_all_gate_approved_read_only():
    rb = compile_class("gateway-drain-window")
    assert len(rb.checks) >= 7, (
        "the drain-window runbook needs the full doctrine check set"
    )
    for c in rb.checks:
        assert c.read_only, f"check {c.order} must stay read-only"
        assert is_read_only_command(c.command), (
            f"check {c.order} refused by the gate: {c.command}"
        )


def test_pause_first_check_orders_before_restart_checks():
    """Doctrine order: pause writes / queue depth BEFORE touching the gateway."""
    rb = compile_class("gateway-drain-window")
    by_order = {c.order: c for c in rb.checks}
    assert "enabled" in by_order[4].command, "check 4 = pause-first (writes paused)"
    assert "wc -l" in by_order[6].command, "check 6 = queue depth before restart"
