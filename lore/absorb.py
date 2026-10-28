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
from datetime import UTC, datetime

import lore
from lore.classes import get_registry
from lore.classifier import classify
from lore.compiler import compile_class, propose
from lore.evidence import EvidenceBlock, attach_evidence, parse_text_line

__all__ = [
    "DECISION_ABSORB",
    "DECISION_NO_NEW_LESSON",
    "AbsorbDecision",
    "GateVerdict",
    "absorb_proposal",
    "absorb_sweep",
    "block_outcome",
    "fold_lesson_blocks",
    "gate_close",
    "validate_close_decision",
    "verdict_record",
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


def verdict_record(
    v: GateVerdict,
    *,
    decided_at: str | None = None,
    tool_version: str = lore.__version__,
) -> dict:
    """Build one durable, grep-stable audit record (REVIEW-LORE-001).

    Pure data — nothing is written here; the CALLER (the CLI, only under the
    explicit opt-in ``--record PATH`` flag) appends it as one JSONL line.
    ``decided_at`` is the operator's ``--decided-at`` when given, otherwise
    the current UTC time stamped at record-build time (a durable audit
    record must be able to answer "when"; the CLI's printed verdict itself
    never invents timestamps).
    """
    d = v.decision
    return {
        "decided_at": decided_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": d.decision if d else None,
        "class_id": d.class_id if d else None,
        "lesson": d.lesson if d else "",
        "reason": d.reason if d else "",
        "ack_ref": d.ack_ref if d else None,
        "source": d.source if d else None,
        "allowed": v.allowed,
        "errors": list(v.errors),
        "tool_version": tool_version,
    }


# ------------------------------------------------------- lesson folding (LORE-069)
# Outcome vocabulary for one evidence block, as PRD US-2's scribe names it:
# a dead end is a command/approach that was tried and FAILED in the swept
# window; everything else is an observed fact (working or neutral). The
# vocabulary is closed: anything that does not match a dead-end pattern is
# "observed" — never guessed into a stronger claim.
OUTCOME_DEAD_END = "dead-end"
OUTCOME_OBSERVED = "observed"

# Dead-end markers, word-bounded so "undead", "deadline", "dealedge" etc.
# never trigger. Kept deliberately small and honest: these are the phrases
# an operator (or a sweep line) uses to record that something did NOT work.
_DEAD_END_RE = re.compile(
    r"\b(dead end|dead-end|unsuccessfully|failed to|did not work|didn't work"
    r"|does not work|doesn't work|no avail|nothing worked)\b",
    re.IGNORECASE,
)

# The proposal carries, per block, its parsed identity: kind + first line of
# detail (truncated for payload brevity) + the outcome label.
_DETAIL_SNIPPET_LEN = 160


def block_outcome(detail: str) -> str:
    """Closed-vocabulary outcome for one evidence detail (US-2)."""
    return OUTCOME_DEAD_END if _DEAD_END_RE.search(detail or "") else OUTCOME_OBSERVED


def _blocks_from_lesson(lesson: str) -> list[EvidenceBlock]:
    """Parse a lesson text with the SAME tolerance the --window sweep uses.

    The lesson arrives as either swept-block details (already evidence) or
    operator prose. Each line is offered to :func:`parse_text_line` — a
    leading ISO-8601 timestamp makes it a logsey-export block, plain prose
    lines stay prose. Nothing is fabricated: a lesson of pure prose yields
    no blocks (honest, and the proposal still says ``update``).
    """
    blocks: list[EvidenceBlock] = []
    for line in (lesson or "").splitlines():
        b = parse_text_line(line.strip())
        if b is not None:
            blocks.append(b)
    return blocks


def block_proposal_entry(b: EvidenceBlock) -> dict:
    """One per-block entry for the proposal's ``blocks`` field (US-2)."""
    first_line = b.detail.splitlines()[0] if b.detail else ""
    if len(first_line) > _DETAIL_SNIPPET_LEN:
        first_line = first_line[: _DETAIL_SNIPPET_LEN - 3] + "..."
    return {
        "kind": b.kind,
        "detail": first_line,
        "source": b.source,
        "observed_at": b.observed_at,
        "outcome": block_outcome(b.detail),
    }


def _entry_to_block(e: dict) -> EvidenceBlock:
    """One trail-entry dict -> EvidenceBlock (fold + rendering share this)."""
    return EvidenceBlock(
        kind=e["kind"],
        detail=e["detail"],
        source=e.get("source"),
        observed_at=e.get("observed_at"),
        window=e.get("window"),
    )


def fold_lesson_blocks(fresh, blocks: list[dict]) -> object:
    """Return a NEW runbook with trail-derived evidence folded in (LORE-069).

    ``fresh`` is the registry-compiled runbook; ``blocks`` are trail entries
    (``{"kind","detail"}``, optionally ``observed_at``/``window``/``source``)
    from a swept window or a parsed lesson. Each entry is appended to the
    runbook's evidence_trail via :func:`lore.evidence.attach_evidence`, so
    the diff between ``fresh-with-evidence`` and the existing runbook NAMES
    the trail-derived content (PRD US-2's "evidence blocks, dead ends
    marked dead" — the outcome labels ride the per-block entries). The
    attach is frozen-safe and attaches NOTHING to checks (no per_check
    mapping is invented); propose-not-write holds — nothing is written.
    """
    evidence_blocks = [
        EvidenceBlock(
            kind=e["kind"],
            detail=e["detail"],
            source=e.get("source"),
            observed_at=e.get("observed_at"),
            window=e.get("window"),
        )
        for e in blocks
        if isinstance(e, dict) and e.get("kind") and e.get("detail")
    ]
    if not evidence_blocks:
        return fresh
    return attach_evidence(fresh, evidence_blocks)


def absorb_proposal(
    class_id: str, lesson: str, source: str | None = None, *, blocks=None
) -> dict:
    """Build the concrete proposal payload an 'absorb' decision hands the operator.

    LORE-069: the proposal now diffs against the class's EXISTING runbook
    with the trail evidence folded into the fresh side, so a curated class
    with a runbook gets ``"action": "update"`` and a payload that NAMES the
    delta (``changed``/``removed``/``added`` carry the trail-derived
    content) instead of a byte-copy of the runbook the class already has
    labelled ``"new"``. A trail that adds nothing yields an explicitly
    empty update — honest absence, never a fake "new".

    Per-block US-2 rendering: every folded block also lands in the
    proposal's ``blocks`` list as ``{kind, detail, source, observed_at,
    outcome}``, ``outcome`` being the closed vocabulary
    ``"dead-end"``/``"observed"`` (see :func:`block_outcome`) — dead ends
    are marked dead in structured form, not prose.

    ``blocks`` (keyword-only, caller-supplied): already-parsed evidence
    entries (from the sweep's classified blocks) folded into the fresh
    side; when omitted the ``lesson`` text is parsed with the SAME
    tolerance the ``--window`` sweep uses (:func:`lore.evidence.parse_text_line`).

    Calls ``lore.compiler.propose`` semantics (propose-not-write: the payload
    is data, nothing is written). Fail-safe: an unknown class returns
    ``{"error": "unknown class '<id>'"}`` instead of raising.

    ``source`` is the optional provenance marker (LORE-009: e.g.
    ``qa-dagger`` / ``dogfood-dagger`` closures flowing through the same
    absorb-gate as incidents). Omitted (None, the default) it is NOT added
    to the payload — the default shape stays byte-compatible.
    """
    try:
        existing = compile_class(class_id)
    except KeyError:
        return {"error": f"unknown class '{class_id}'"}

    folded = list(blocks or [])
    if not folded:
        folded = [
            {
                "kind": b.kind,
                "detail": b.detail,
                "observed_at": b.observed_at,
                "source": b.source,
                "window": b.window,
            }
            for b in _blocks_from_lesson(lesson)
        ]

    fresh = fold_lesson_blocks(compile_class(class_id), [dict(e) for e in folded])
    payload = propose(class_id, existing=existing, fresh=fresh)
    payload["blocks"] = [block_proposal_entry(_entry_to_block(e)) for e in folded]
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
    source: str | None = None,
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

    ``source`` (LORE-020) is the provenance marker threaded through to every
    per-class proposal via :func:`absorb_proposal`'s None-rule: omitted
    (None) the payloads keep their original shape with no top-level
    ``source`` key; given, every proposal carries ``source`` verbatim.

    An empty or wholly-unclassifiable trail yields ``[]`` (the caller prints
    an explicit empty-result message and exits 0 — never a fabricated
    success).
    """
    if not blocks:
        return []

    # PERF-3: memoize the classifier per invocation — sweeps over repeated
    # evidence (the normal logsey-export case) classify each unique detail
    # text once instead of once per block. Function-local, so nothing leaks
    # across sweeps; grouping order and output values are unchanged.
    classification_cache: dict[str, object] = {}

    grouped: dict[str, list[EvidenceBlock]] = {}
    for block in blocks:
        detail = block.detail
        if detail in classification_cache:
            classification = classification_cache[detail]
        else:
            classification = classify(detail)
            classification_cache[detail] = classification
        grouped.setdefault(classification.class_id, []).append(block)

    provenance = {
        "kind": "absorb-sweep",
        "window": window,
        "ns": ns,
        "board": board,
        "source": source,
    }
    proposals: list[dict] = []
    for class_id, members in grouped.items():
        proposal = absorb_proposal(
            class_id,
            "\n".join(b.detail for b in members),
            source=source,
            blocks=[
                {
                    "kind": b.kind,
                    "detail": b.detail,
                    "observed_at": b.observed_at,
                    "source": b.source,
                }
                for b in members
            ],
        )
        proposal["sweep"] = {
            "window": window,
            "ns": ns,
            "board": board,
            "source": source,
            "blocks_total": len(blocks),
            "blocks_class": len(members),
            "evidence": [b.to_trail_entry() for b in members],
        }
        proposal["provenance"] = dict(provenance)
        proposals.append(proposal)
    return proposals
