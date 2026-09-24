"""lore.absorb — the absorb-gate on work/incident closure (LORE-008).

PROPOSE-NOT-WRITE (hard design law, same doctrine as lore.compiler):

    This gate VALIDATES a lesson decision at closure time; it NEVER writes
    a runbook anywhere. It performs no filesystem writes, mutates nothing —
    the registry stays closed (lore.classes ``register`` still refuses), and
    an 'absorb' decision yields an in-memory/stdout PROPOSAL that an operator
    approves, never a published runbook. Enforced by a test
    (``tests/test_absorb.py::test_gate_close_performs_no_filesystem_writes``).

A closure (work/incident/foreman task) carries a machine-checked decision
record: either

- ``decision="absorb"`` — the incident taught something: a class_id that
  EXISTS in the registry plus the proposed lesson text, handed to the
  operator as a runbook-update proposal; or
- ``decision="no-new-lesson"`` — an explicit acknowledgement that nothing
  was learned, backed by a non-empty reason.

The machine gate is deliberately dumb (all checks are string/dict/parse
checks, no LLM): it can be called from any closure flow — a foreman, a
board appender, or a human — and its exit code is machine-checkable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from lore.classes import get_registry
from lore.classifier import classify
from lore.compiler import propose
from lore.evidence import EvidenceBlock

__all__ = [
    "DECISION_ABSORB",
    "DECISION_NO_NEW_LESSON",
    "AbsorbDecision",
    "GateVerdict",
    "absorb_proposal",
    "absorb_sweep",
    "gate_close",
    "validate_close_decision",
]

DECISION_ABSORB = "absorb"
DECISION_NO_NEW_LESSON = "no-new-lesson"
_DECISION_VOCABULARY = frozenset({DECISION_ABSORB, DECISION_NO_NEW_LESSON})

_ERR_BAD_DECISION = "decision must be 'absorb' or 'no-new-lesson'"
_ERR_NO_REASON = "no-new-lesson requires a reason"
_ERR_NO_LESSON = "absorb requires a lesson"
_ERR_NO_CLASS = "absorb requires a class_id"
_ERR_ISO = "decided_at is not ISO-8601"


@dataclass(frozen=True)
class AbsorbDecision:
    """One closure's lesson decision (pure data, never written anywhere)."""

    decision: str
    class_id: str | None = None
    lesson: str = ""
    reason: str = ""
    ack_ref: str | None = None
    decided_at: str | None = None
    source: str | None = None  # provenance: e.g. "qa-dagger" / "dogfood-dagger"


@dataclass(frozen=True)
class GateVerdict:
    """Outcome of the machine check over one AbsorbDecision."""

    allowed: bool
    errors: list[str] = field(default_factory=list)
    decision: AbsorbDecision | None = None

    def summary(self) -> str:
        if self.allowed:
            assert (
                self.decision is not None
            )  # allowed verdicts always carry the decision
            if self.decision.decision == DECISION_ABSORB:
                line = f"GATE: ALLOW (absorb -> {self.decision.class_id})"
            else:
                line = "GATE: ALLOW (no-new-lesson)"
            if self.decision.source:
                # LORE-009: provenance (qa-dagger / dogfood-dagger / incident).
                line += f" source: {self.decision.source}"
            return line
        return f"GATE: DENY ({len(self.errors)} errors)"


def validate_close_decision(d: AbsorbDecision) -> GateVerdict:
    """Machine-check one closure decision; lists ALL violations, not the first."""
    errors: list[str] = []

    if d.decision not in _DECISION_VOCABULARY:
        errors.append(_ERR_BAD_DECISION)
    elif d.decision == DECISION_NO_NEW_LESSON:
        if not (d.reason or "").strip():
            errors.append(_ERR_NO_REASON)
    else:  # absorb
        if not (d.class_id or "").strip():
            errors.append(_ERR_NO_CLASS)
        if not (d.lesson or "").strip():
            errors.append(_ERR_NO_LESSON)
        if (d.class_id or "").strip() and get_registry().get(d.class_id) is None:
            errors.append(
                f"unknown class '{d.class_id}' — registry is closed; "
                "carry the proposed lesson text for operator review instead"
            )

    if d.decided_at is not None:
        try:
            datetime.fromisoformat(d.decided_at)
        except ValueError:
            errors.append(_ERR_ISO)

    return GateVerdict(allowed=not errors, errors=errors, decision=d)


def gate_close(d: AbsorbDecision) -> GateVerdict:
    """Run the gate. Side effects: NONE (propose-not-write holds)."""
    return validate_close_decision(d)


def absorb_proposal(class_id: str, lesson: str, source: str | None = None) -> dict:
    """Build the concrete proposal payload an 'absorb' decision hands the operator.

    Calls ``lore.compiler.propose`` semantics (propose-not-write: the payload
    is data, nothing is written). Fail-safe: an unknown class returns
    ``{"error": "unknown class '<id>'"}`` instead of raising.

    ``source`` is the optional provenance marker (LORE-009: e.g.
    ``qa-dagger`` / ``dogfood-dagger`` closures flowing through the same
    absorb-gate as incidents). Omitted (None, the default) it is NOT added
    to the payload — the default shape stays byte-compatible.
    """
    try:
        payload = propose(class_id)
    except KeyError:
        return {"error": f"unknown class '{class_id}'"}
    payload["lesson"] = lesson
    if source is not None:
        payload["source"] = source
    return payload


# ------------------------------------------------------------- window sweep
# Duration tokens the sweep accepts for ``--window``: a bare integer (HOURS by
# default), or an explicit unit suffix (h/m/s). A duration is a SWEEP PARAMETER
# (the size of the evidence window to sweep), never an invented date: no
# timestamp is ever fabricated from it.
_DURATION_RE = re.compile(r"^(\d+)(h|m|s)?$", re.IGNORECASE)
_DURATION_DEFAULT_UNIT = "h"


def parse_duration(text: str) -> int:
    """Parse a sweep duration like ``2h``/``45m``/``90`` into seconds.

    A bare integer means hours (the ``--window`` flag's native unit in the
    PRD interface, e.g. ``lore absorb --window 2h``). Raises ``ValueError``
    on anything that is not a positive duration — never guessed, never
    defaulted to a silent nonzero.
    """
    m = _DURATION_RE.match((text or "").strip())
    if not m:
        raise ValueError(
            f"invalid --window duration {text!r} — expected forms: "
            "'<n>' (hours), '<n>h', '<n>m', '<n>s' (e.g. 2h, 45m, 90)"
        )
    value = int(m.group(1))
    if value <= 0:
        raise ValueError(f"--window must be positive, got {text!r}")
    unit = (m.group(2) or _DURATION_DEFAULT_UNIT).lower()
    return value * {"h": 3600, "m": 60, "s": 1}[unit]


def absorb_sweep(
    blocks: list[EvidenceBlock],
    *,
    window: str | None = None,
    ns: str | None = None,
    board: str | None = None,
) -> list[dict]:
    """Group parsed evidence blocks into per-class absorb PROPOSALS.

    LORE-010: the ``lore absorb --window`` sweep. Each block is classified by
    the existing keyword/signature classifier; blocks that land in
    ``unclassified`` are NOT dropped — they are reported under the
    ``unclassified`` bucket (absorbing into unclassified is always allowed),
    so a sweep shows its honest coverage instead of a confident zero.

    PROPOSE-NOT-WRITE (same hard law as the gate): this returns DATA ONLY —
    per-class proposal dicts in the existing ``absorb_proposal`` shape
    (``propose()`` payload + ``lesson``), plus sweep provenance. It never
    writes anything, never mutates the registry, and performs no
    filesystem/board/DuckBrain IO. ``window``/``ns``/``board`` are recorded
    in each proposal's provenance fields verbatim when provided — no live
    lookups, no invention.

    An empty or wholly-unclassifiable trail yields ``[]`` (the caller prints
    an explicit empty-result message and exits 0 — never a fabricated
    success).
    """
    if not blocks:
        return []

    grouped: dict[str, list[EvidenceBlock]] = {}
    for block in blocks:
        classification = classify(block.detail)
        grouped.setdefault(classification.class_id, []).append(block)

    provenance = {
        "kind": "absorb-sweep",
        "window": window,
        "ns": ns,
        "board": board,
    }
    proposals: list[dict] = []
    for class_id, members in grouped.items():
        proposal = absorb_proposal(class_id, "\n".join(b.detail for b in members))
        proposal["sweep"] = {
            "window": window,
            "ns": ns,
            "board": board,
            "blocks_total": len(blocks),
            "blocks_class": len(members),
            "evidence": [b.to_trail_entry() for b in members],
        }
        proposal["provenance"] = dict(provenance)
        proposals.append(proposal)
    return proposals
