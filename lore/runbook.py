"""Runbook data model for the lore compiler.

A :class:`Runbook` is a first-class, serialisable object — one per failure
class — carrying the PRD §"What it compiles" sections: signature, ordered
checks, recovery ladder with guardrails, evidence trail, provenance and
freshness. Serialization is lossless: ``from_dict(to_dict(rb)) == rb``
(round-trip asserted in tests).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

# Status vocabulary. A freshly compiled runbook is ALWAYS a proposal until an
# operator publishes it (propose-not-write); "validated" is set only when a
# caller explicitly passes a last_validated timestamp (operator attestation),
# and "stale" is owned by the later re-validation loop task.
STATUS_PROPOSAL = "proposal"
STATUS_STALE = "stale"
STATUS_VALIDATED = "validated"


@dataclass(frozen=True)
class Check:
    """One ordered diagnostic step in a runbook."""

    order: int
    command: str  # the EXACT command/query to run
    expected_healthy: str  # what healthy output looks like
    expected_incident: str  # what incident output looks like
    decision: str  # what decision this check drives
    read_only: bool  # True for verify/dry-run/SELECT-only probes
    evidence: list[dict] = field(default_factory=list)  # {"kind","detail"}

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Check:
        return cls(
            order=int(d["order"]),
            command=d["command"],
            expected_healthy=d["expected_healthy"],
            expected_incident=d["expected_incident"],
            decision=d["decision"],
            read_only=bool(d["read_only"]),
            evidence=[dict(e) for e in d.get("evidence", [])],
        )


@dataclass(frozen=True)
class Runbook:
    """A compiled runbook for one failure class (always a proposal)."""

    class_id: str
    name: str
    signature: str  # the log/logsey pattern identifying the class
    checks: list[Check] = field(default_factory=list)  # ordered by Check.order
    recovery_ladder: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)  # the "never X" laws
    evidence_trail: list[dict] = field(default_factory=list)  # {"kind","detail"}
    provenance: str = ""
    last_validated: str | None = None  # ISO-8601, None = NEVER validated
    status: str = STATUS_PROPOSAL

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "name": self.name,
            "signature": self.signature,
            "checks": [c.to_dict() for c in self.checks],
            "recovery_ladder": list(self.recovery_ladder),
            "guardrails": list(self.guardrails),
            "evidence_trail": [dict(e) for e in self.evidence_trail],
            "provenance": self.provenance,
            "last_validated": self.last_validated,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Runbook:
        return cls(
            class_id=d["class_id"],
            name=d["name"],
            signature=d["signature"],
            checks=[Check.from_dict(c) for c in d.get("checks", [])],
            recovery_ladder=list(d.get("recovery_ladder", [])),
            guardrails=list(d.get("guardrails", [])),
            evidence_trail=[dict(e) for e in d.get("evidence_trail", [])],
            provenance=d.get("provenance", ""),
            last_validated=d.get("last_validated"),
            status=d.get("status", STATUS_PROPOSAL),
        )

    def to_markdown(self) -> str:
        """Render this runbook as markdown.

        Honesty rule: absent sections render as ``no data`` — never as zero,
        an empty success, or an invented value.
        """
        lines: list[str] = []
        lines.append(f"# Runbook: {self.name} (`{self.class_id}`)")
        lines.append("")
        lines.append(f"- **Status:** {self.status}")
        lines.append(
            "- **Last validated:** "
            + (
                self.last_validated
                if self.last_validated
                else "no data (never validated)"
            )
        )
        lines.append(f"- **Provenance:** {self.provenance or 'no data'}")
        lines.append(f"- **Signature:** `{self.signature}`")
        lines.append("")
        lines.append("## Checks (in order)")
        lines.append("")
        if not self.checks:
            lines.append("no data")
        else:
            for c in sorted(self.checks, key=lambda x: x.order):
                mode = "read-only" if c.read_only else "MUTATING"
                lines.append(f"### Check {c.order} ({mode})")
                lines.append("")
                lines.append("```sh")
                lines.append(c.command)
                lines.append("```")
                lines.append(f"- Healthy: {c.expected_healthy}")
                lines.append(f"- Incident: {c.expected_incident}")
                lines.append(f"- Decision: {c.decision}")
                if c.evidence:
                    for ev in c.evidence:
                        lines.append(f"- Evidence: {ev['kind']}: {ev['detail']}")
                else:
                    lines.append("- Evidence: no data")
                lines.append("")
        lines.append("## Recovery ladder")
        lines.append("")
        if not self.recovery_ladder:
            lines.append("no data")
        else:
            for i, step in enumerate(self.recovery_ladder, 1):
                lines.append(f"{i}. {step}")
        lines.append("")
        lines.append("## Guardrails (never X)")
        lines.append("")
        if not self.guardrails:
            lines.append("no data")
        else:
            for g in self.guardrails:
                lines.append(f"- {g}")
        lines.append("")
        lines.append("## Evidence trail")
        lines.append("")
        if not self.evidence_trail:
            lines.append("no data")
        else:
            for ev in self.evidence_trail:
                lines.append(f"- {ev['kind']}: {ev['detail']}")
        lines.append("")
        return "\n".join(lines)
