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

from dataclasses import dataclass, field
from datetime import datetime

from lore.classes import get_registry
from lore.compiler import propose

__all__ = [
    "DECISION_ABSORB",
    "DECISION_NO_NEW_LESSON",
    "AbsorbDecision",
    "GateVerdict",
    "absorb_proposal",
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
