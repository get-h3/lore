"""lore.evidence — evidence-block extraction (LORE-005).

Canonical evidence-block model shared by every runbook check. Each block is
one re-findable claim: what kind of source it came from, the human-readable
evidence line, and (when known) where and when it was observed. The
``{"kind","detail"}`` trail-entry shape is the compatibility seam with
``lore.runbook.Check.evidence`` and ``Runbook.evidence_trail`` — those fields
keep working unchanged.

Logsey export contract — HONESTY LABEL:

    LOGSEY_EXPORT_CONTRACT_STATUS (below) names the truth: logsey's ``export``
    subcommand is PLANNED AND NOT IMPLEMENTED (logsey internal/cli/cli.go
    ``planned`` slice; README: "not implemented"), so there is NO frozen
    on-disk format to parse against today. :func:`parse_logsey_export` accepts
    the documented PRD-level contract shapes, tolerantly, and labels itself
    unfrozen. When logsey's export lands and freezes a wire format, tighten
    the parser here — nothing else in the model has to move.

Accepted shapes (documented, tolerant, UNFROZEN):

- An export header line naming the invocation, e.g. ``logsey export --window
  18:30-19:10``. Its presence claims "this is a logsey export"; a header with
  NO parseable evidence block after it is an explicit parse failure, not an
  empty success.
- A fenced code block (``` or ```jsonl) whose lines are either JSON objects
  (logsey's structured-JSONL passthrough: native fields preserved verbatim in
  ``fields``) or "timestamped, source-attributed" text lines: a leading
  ISO-8601 timestamp, then ``key=value`` attributes (``unit=`` / ``source=`` /
  ``component=`` name the source; severity/level/pid/session-id and friends
  land in ``fields``), then the human-readable message. Field names follow
  logsey's indexed vocabulary (journald: ts/unit/severity/pid; app logs:
  level/component/session-id) — no invented vocabulary.
- Text with no export header and no fenced block is NOT claimed to be an
  export: it yields an explicit empty list ("no blocks found"), never a
  fabricated block.
- A line that claims to be JSON but does not parse raises
  :class:`LogseyExportParseError` — the caller can always tell "no blocks
  found" from "unparseable input", and neither is reported as a bare success.

Graceful degradation (the task row's "degrade gracefully" clause): until the
logsey export exists, callers capture raw command output via
:func:`degrade_to_command_output`, which produces a ``command-output`` block —
never a ``logsey-export`` block, so a degraded capture can never be mistaken
for a real export.
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

# Honesty label for the upstream contract this parser targets. Referenced by
# every parser docstring — do not soften it.
LOGSEY_EXPORT_CONTRACT_STATUS = (
    "unfrozen — logsey export subcommand not yet implemented "
    "(internal/cli/cli.go planned list)"
)

# Curated, closed evidence-kind vocabulary. The first group is what the
# compiler's curated tables already use (lore.compiler evidence/trail
# comments); the second group is what the logsey export contract and this
# module add. An unknown kind is REFUSED — never silently accepted (same
# closed-registry discipline as lore.classes).
KINDS: tuple[str, ...] = (
    # kinds already in use by the curated runbook tables
    "board",
    "incident",
    "gap",
    "memory",
    "commit",
    # kinds the logsey export contract and the degradation path add
    "logsey-export",
    "command-output",
    "board-event",
    "duckbrain-row",
)


def is_known_kind(kind: str) -> bool:
    """Membership check for the curated evidence-kind vocabulary."""
    return kind in KINDS


class LogseyExportParseError(ValueError):
    """Raised when input CLAIMS to be a logsey export but cannot be parsed.

    Distinct from "no blocks found" (an explicit empty list): the caller must
    be able to tell the two apart, and neither may be reported as a fabricated
    success.
    """


@dataclass(frozen=True)
class EvidenceBlock:
    """One re-findable evidence claim attached to a runbook or a check."""

    kind: str  # from the curated KINDS vocabulary
    detail: str  # the human-readable evidence line
    source: str | None = None  # where it came from (unit/file/table/key)
    observed_at: str | None = None  # ISO-8601 when known, else None
    window: str | None = None  # e.g. "18:30-19:10" when the block is windowed
    fields: dict = field(default_factory=dict)  # native passthrough (JSONL case)

    def __post_init__(self) -> None:
        if not is_known_kind(self.kind):
            raise ValueError(
                f"unknown evidence kind {self.kind!r}; the vocabulary is "
                f"closed. Known: {', '.join(KINDS)}"
            )
        if not self.detail:
            raise ValueError("evidence detail must be non-empty (no empty claims)")

    def to_trail_entry(self) -> dict:
        """The exact {"kind","detail"} shape Check.evidence / evidence_trail use."""
        return {"kind": self.kind, "detail": self.detail}

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "detail": self.detail,
            "source": self.source,
            "observed_at": self.observed_at,
            "window": self.window,
            "fields": dict(self.fields),
        }

    @classmethod
    def from_dict(cls, d: dict) -> EvidenceBlock:
        return cls(
            kind=d["kind"],
            detail=d["detail"],
            source=d.get("source"),
            observed_at=d.get("observed_at"),
            window=d.get("window"),
            fields=dict(d.get("fields") or {}),
        )


# ---------------------------------------------------------- logsey export parse
_EXPORT_HEADER_RE = re.compile(r"logsey\s+export\b")
_FENCE_RE = re.compile(r"^```(\w*)\s*$")
_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?)\s+")
_KV_RE = re.compile(r"(\w[\w.-]*)=(\S+)")
_SOURCE_KEYS = ("unit", "source", "component")

# journald/app-log vocabulary the export contract names, promoted to
# first-class block attributes when present in a line's key=value attributes.
_PROMOTED_KEYS = ("severity", "level", "pid", "session-id")


def _block_from_json_obj(obj: dict, *, window: str | None) -> EvidenceBlock:
    """Build a block from one native JSONL row (passthrough, no invention)."""
    detail = obj.get("message") or obj.get("msg") or json.dumps(obj, sort_keys=True)
    source = obj.get("unit") or obj.get("source") or obj.get("component")
    return EvidenceBlock(
        kind="logsey-export",
        detail=str(detail),
        source=source if isinstance(source, str) else None,
        observed_at=obj.get("ts") if isinstance(obj.get("ts"), str) else None,
        window=window,
        fields=dict(obj),  # native fields, verbatim
    )


def _block_from_text_line(line: str, *, window: str | None) -> EvidenceBlock | None:
    """Parse one "timestamped, source-attributed" text line, tolerantly."""
    m = _TS_RE.match(line)
    if not m:
        return None
    observed_at, rest = m.group(1), line[m.end() :]
    fields: dict = {}
    source = None
    for key, value in _KV_RE.findall(rest):
        fields[key] = value
        if key in _SOURCE_KEYS and source is None:
            source = value
    return EvidenceBlock(
        kind="logsey-export",
        detail=rest.strip(),
        source=source,
        observed_at=observed_at,
        window=window,
        fields=fields,
    )


def parse_logsey_export(text: str) -> list[EvidenceBlock]:
    """Parse a documented logsey export payload into evidence blocks.

    Contract status: {status}. Accepted shapes are documented at module
    level; the format is treated as UNFROZEN and parsing is tolerant.

    Return contract:
    - ``[]`` means "no blocks found" — the input did not claim to be an
      export (no export header, no fenced block) or was empty.
    - :class:`LogseyExportParseError` means "unparseable input" — the input
      CLAIMED to be an export (header present, or a JSON-looking line failed
      to parse) but no block could be extracted.
    Neither case is ever reported as a fabricated success.
    """
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    has_header = any(_EXPORT_HEADER_RE.search(ln) for ln in lines)

    # locate the (first) fenced block
    fence_start = None
    fence_lang = ""
    for i, ln in enumerate(lines):
        m = _FENCE_RE.match(ln.strip())
        if m:
            fence_start = i
            fence_lang = m.group(1).lower()
            break

    if fence_start is None:
        if has_header:
            raise LogseyExportParseError(
                f"input claims a logsey export ({LOGSEY_EXPORT_CONTRACT_STATUS}) but carries no "
                "fenced evidence block"
            )
        return []  # did not claim to be an export: no blocks found

    # extract the fence body up to the closing fence
    body: list[str] = []
    for ln in lines[fence_start + 1 :]:
        if _FENCE_RE.match(ln.strip()):
            break
        body.append(ln)

    window = None
    wm = re.search(r"--window\s+(\S+)", " ".join(lines[: fence_start + 1]))
    if wm:
        window = wm.group(1)

    blocks: list[EvidenceBlock] = []
    for raw in body:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("{") or fence_lang == "jsonl":
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LogseyExportParseError(
                    f"export line claims JSON but does not parse: {exc}"
                ) from exc
            if not isinstance(obj, dict):
                raise LogseyExportParseError(
                    "export JSON line is not an object; refusing to guess shape"
                )
            blocks.append(_block_from_json_obj(obj, window=window))
            continue
        b = _block_from_text_line(line, window=window)
        if b is not None:
            blocks.append(b)
        # a non-timestamped prose line inside the fence is tolerated (UNFROZEN
        # format) but never converted into a block — no fabricated attribution.

    if not blocks and has_header:
        raise LogseyExportParseError(
            f"input claims a logsey export ({LOGSEY_EXPORT_CONTRACT_STATUS}) but its fenced block "
            "yielded no parseable evidence lines"
        )
    return blocks


# ------------------------------------------------------- graceful degradation
def degrade_to_command_output(
    command: str, stdout: str, *, returncode: int = 0
) -> EvidenceBlock:
    """Capture raw command output as evidence — the until-logsey-lands path.

    The block kind is ``command-output``, NEVER ``logsey-export``: a degraded
    capture must be impossible to mistake for a real export. The EXACT
    command, its raw stdout and the returncode are preserved verbatim; no
    timestamp is invented (the caller does not source one).
    """
    detail = f"$ {command} (returncode={returncode})\n{stdout}"
    return EvidenceBlock(
        kind="command-output",
        detail=detail,
        source=None,
        observed_at=None,
        window=None,
        fields={"command": command, "stdout": stdout, "returncode": returncode},
    )


# ----------------------------------------------------------------- attachment
def attach_evidence(
    runbook,  # Runbook (imported lazily to avoid a cycle at module load)
    blocks=(),  # Sequence[EvidenceBlock] -> appended to evidence_trail, in order
    *,
    per_check: Mapping[int, list[EvidenceBlock]] | None = None,
):
    """Return a NEW Runbook with evidence blocks attached (frozen-safe).

    Documented placement rule:
    - ``blocks`` (positional sequence) are appended, IN GIVEN ORDER, to the
      runbook's ``evidence_trail`` as ``{"kind","detail"}`` trail entries.
    - ``per_check`` maps Check.order -> blocks; each mapped check gets the
      blocks appended to its own ``Check.evidence`` list, in given order. A
      mapping keyed by an order that no check carries raises ``ValueError``
      (refused, never silently dropped).
    - Attaching evidence is NOT operator attestation: ``last_validated`` is
      never set and ``status`` is never changed to "validated".
    - Deterministic: same input -> byte-identical ``to_dict()`` output.
    """
    known_orders = {c.order for c in runbook.checks}
    if per_check:
        unknown = sorted(set(per_check) - known_orders)
        if unknown:
            raise ValueError(
                f"per_check references check order(s) {unknown} that this "
                f"runbook does not carry (known orders: {sorted(known_orders)})"
            )

    trail_extra = [b.to_trail_entry() for b in blocks]
    new_checks = []
    for c in runbook.checks:
        extra = [b.to_trail_entry() for b in (per_check or {}).get(c.order, [])]
        new_checks.append(dataclasses.replace(c, evidence=[*c.evidence, *extra]))

    return dataclasses.replace(
        runbook,
        checks=new_checks,
        evidence_trail=[*runbook.evidence_trail, *trail_extra],
    )


# Attaching takes the Runbook structurally (duck-typed frozen dataclass with
# checks/evidence_trail — exactly what dataclasses.replace needs), so there is
# no import cycle with lore.runbook at module load.
