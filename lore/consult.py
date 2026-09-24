"""lore.consult — tick-start consult: attach matching runbook refs to work context.

Integration A (LORE-007). Same spirit as the board_wake freshness reader:
a foreman calls this at tick start with the row's title/detail and gets back
"what we learned last time" WITHOUT asking — matched failure classes plus a
LIGHT reference to each class's runbook (refs, never full payloads).

Contract:

- FAIL-OPEN: a broken registry/compile can never crash the caller's
  tick-start. Compile errors simply omit that ref (the match is kept); a
  no-match returns an empty result with NO exception and NO side effects.
- CHEAP: one classify pass, tiny ref dicts, capped at
  :data:`MAX_MATCHED_CLASSES`. Measured honestly in ``elapsed_ms``.
- PROPOSE-NOT-WRITE compatible: this module reads the registry/compiler and
  writes nothing anywhere.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from lore.classifier import classify, classify_all

__all__ = [
    "MAX_MATCHED_CLASSES",
    "ConsultResult",
    "consult",
    "consult_task",
]

# Keep the context attach small: top-1 plus at most two additional matches.
MAX_MATCHED_CLASSES = 3


@dataclass(frozen=True)
class ConsultResult:
    """What a tick-start consult attached to the work context."""

    matched: bool = False
    matched_classes: list[str] = field(default_factory=list)
    runbook_refs: list[dict] = field(default_factory=list)
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        """JSON-safe dict (round-trips through json.loads)."""
        return {
            "matched": self.matched,
            "matched_classes": list(self.matched_classes),
            "runbook_refs": [dict(ref) for ref in self.runbook_refs],
            "elapsed_ms": self.elapsed_ms,
        }


def _runbook_ref(class_id: str) -> dict | None:
    """Build the LIGHT ref for one class; None on any compile failure (fail-open).

    Refs, not payloads: identity, status and size only — never the checks
    themselves (a foreman can compile_class() on demand if it wants the body).
    """
    # Imported inside the function so tests can monkeypatch
    # lore.compiler.compile_class (module-attribute level).
    from lore.compiler import compile_class

    try:
        rb = compile_class(class_id)
    except Exception:  # noqa: BLE001 — fail-open: ANY compile error omits the ref
        return None
    return {
        "class_id": rb.class_id,
        "name": rb.name,
        "status": rb.status,
        "last_validated": rb.last_validated,
        "check_count": len(rb.checks),
    }


def consult(text: str) -> ConsultResult:
    """Match symptom text against class signatures; attach runbook refs.

    Takes the classifier's match ONLY when it is a real match (confidence
    > 0.0 — signature or accepted keyword, never the unclassified fallback),
    plus any additional classes from :func:`classify_all` that also matched,
    best first, capped at :data:`MAX_MATCHED_CLASSES`. Fail-open throughout.
    """
    start = time.perf_counter()

    def _finish(matched_classes: list[str], refs: list[dict]) -> ConsultResult:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return ConsultResult(
            matched=bool(matched_classes),
            matched_classes=matched_classes,
            runbook_refs=refs,
            elapsed_ms=elapsed_ms,
        )

    text = text or ""
    top = classify(text)
    if top.confidence <= 0.0:
        # No match → no behaviour change: empty result, no exception.
        return _finish([], [])

    # Best-first union: the top-1 match, then any other class that ALSO
    # matched (confidence > 0.0), deduped, capped.
    matched_classes: list[str] = []
    refs: list[dict] = []
    candidates = [top]
    candidates.extend(
        c
        for c in classify_all(text)
        if c.confidence > 0.0 and c.class_id != top.class_id
    )
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    for cand in candidates[:MAX_MATCHED_CLASSES]:
        matched_classes.append(cand.class_id)
        ref = _runbook_ref(cand.class_id)
        if ref is not None:
            refs.append(ref)
    return _finish(matched_classes, refs)


def consult_task(title: str, detail: str = "") -> ConsultResult:
    """Tick-start convenience: consult over a board row's title + detail.

    ``detail`` is optional; the text classified is ``title + "\\n" + detail``
    (so a match reachable from the detail alone is found). Same fail-open
    contract as :func:`consult`.
    """
    return consult(f"{title}\n{detail}" if detail else title)
