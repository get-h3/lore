"""Symptom classifier over the curated failure-class registry.

Match strategy (in order):

1. **Signature regex** match against the text = HIGH confidence (0.9).
2. **Keyword score** (share of the class's keywords present, case-insensitive)
   = LOWER confidence, accepted only when the score clears the keyword gate:
   :data:`KEYWORD_THRESHOLD` (0.6) for LONG texts, or the lower
   :data:`SHORT_KEYWORD_THRESHOLD` (0.3) when the text is SHORT (at most
   :data:`SHORT_TEXT_WORD_LIMIT` words). Keyword-only confidence is capped
   at 0.5 so a keyword match can never be mistaken for signature strength.
   The short band exists for the tick-start consult (LORE-007), whose input
   is a board row's TITLE (LORE-043): titles are short, so demanding 60% of
   a class's vocabulary from ~4 words starved the classifier of real
   evidence — the band lowers only the acceptance GATE for keyword
   evidence, never the confidence scaling and never the honesty rule.
3. Otherwise → :data:`UNCLASSIFIED_ID` with 0.0 confidence.

Honesty rule: a weak (below-gate) match is NEVER labeled as a specific
class — it returns unclassified. A specific label always carries its
evidence (kind: ``signature`` or ``keyword``) so callers can audit why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from lore.classes import UNCLASSIFIED_ID, FailureClass, get_registry

# Confidence levels.
SIGNATURE_CONFIDENCE = 0.9
KEYWORD_CONFIDENCE_MAX = 0.5  # keyword-only matches never reach signature strength
KEYWORD_THRESHOLD = (
    0.6  # fraction of a class's keywords required to accept (long texts)
)
UNCLASSIFIED_CONFIDENCE = 0.0

# LORE-043 (dogfood 2026-10-01 run 4): the tick-start consult classifies a
# board row's TITLE, which is short — a realistic 4-word title carrying 3 of
# 8 collision keywords (raw score 0.375) sat below the 0.6 long-text gate and
# the consult returned ``matched:false`` for the fleet's most recurring
# collision class. SHORT texts therefore accept keyword evidence at a lower
# gate. Both constants are principled, and the pins in
# tests/test_lore043_short_text_threshold.py hold them in place:
#
# - SHORT_TEXT_WORD_LIMIT = 8: the board census (65 historical rows,
#   measured by the filing run) shows a median title of 14 words with a
#   25th percentile of 8 — task titles cluster at or below 8 words. The
#   threshold is deliberately BELOW the longest paraphrase the near-miss
#   tests refuse ("container env lost the API key after .env got
#   clobbered", 10 words — must stay on the long path), so 9 would flip a
#   pinned refusal and 12 (a naive "titles are short" read) would flip two.
# - SHORT_KEYWORD_THRESHOLD = 0.3: the brief's "2-3 keyword hits on a short
#   title" shape (exact multiples of 8 and 6-keyword classes land at 0.25/
#   0.333, so a fraction-of-3 gate keeps those two classes behaving the
#   same while the LORE-043 title's 3/8 = 0.375 clears it).
SHORT_TEXT_WORD_LIMIT = 8
SHORT_KEYWORD_THRESHOLD = 0.3

_FALLBACK_SIGNATURE = r"$^"  # never matches (empty pattern guard for unclassified)


@dataclass
class Classification:
    """One candidate classification for a symptom text.

    :attr:`evidence` is a list of PLAIN DICTS (``type(e) is dict``), not
    dataclass objects: each item has exactly the keys ``"kind"`` and
    ``"detail"``. Kinds: ``"signature"`` (first item only, when a signature
    regex matched — ``detail`` is the matched text) and ``"keyword"`` (one
    item per keyword hit — ``detail`` is the keyword string).
    """

    class_id: str
    confidence: float
    matched_signature: str | None = None
    matched_keywords: tuple[str, ...] = ()
    evidence: list[dict] = field(default_factory=list)

    @property
    def is_unclassified(self) -> bool:
        return self.class_id == UNCLASSIFIED_ID


@dataclass(frozen=True)
class NearMiss:
    """A below-threshold class that *almost* matched a symptom text.

    Evidence echo only — never an auto-label. :attr:`raw_score` is the raw
    keyword fraction ``n_hits / n_keywords`` (not the threshold-gated
    confidence ``classify`` returns), so callers see how close the class was.

    Naming clarity (both names, so the two numbers are never conflated):

    - ``raw_score`` = the raw fraction. The CLI ``match --explain`` prints
      this SAME raw fraction as ``score=`` in the near-misses section.
    - The band-scaled value computed by :func:`_keyword_confidence` is a
      DIFFERENT number: it is what ``classify`` returns as ``confidence``
      and what the CLI prints as ``confidence=`` for accepted matches. For
      a near-miss it is always 0.0 by construction (below threshold, so
      the band scaling never applies).
    """

    class_id: str
    raw_score: float
    n_hits: int
    n_keywords: int
    hit_keywords: tuple[str, ...]


@dataclass(frozen=True)
class _CompiledClass:
    cls: FailureClass
    signature_res: tuple[re.Pattern[str], ...]


def _compile_all() -> dict[str, _CompiledClass]:
    compiled: dict[str, _CompiledClass] = {}
    for cls in get_registry().all_classes():
        sigs = tuple(
            re.compile(pat, re.IGNORECASE)
            for pat in (cls.signature_patterns or (_FALLBACK_SIGNATURE,))
        )
        compiled[cls.id] = _CompiledClass(cls=cls, signature_res=sigs)
    return compiled


_COMPILED: dict[str, _CompiledClass] | None = None


def _compiled() -> dict[str, _CompiledClass]:
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = _compile_all()
    return _COMPILED


def _keyword_hits(cls: FailureClass, lower_text: str) -> tuple[str, ...]:
    hits = []
    for kw in cls.keywords:
        if kw.lower() in lower_text:
            hits.append(kw)
    return tuple(hits)


def _keyword_gate(lower_text: str) -> float:
    """Acceptance gate for keyword evidence, scoped by the text's length.

    LORE-043: the tick-start consult (LORE-007) is fed board-row TITLES,
    which are short — demanding :data:`KEYWORD_THRESHOLD` of a class's
    vocabulary from ~4 words starved the classifier of real evidence and
    left the fleet's most recurring collision class silent at tick start.
    A text at most :data:`SHORT_TEXT_WORD_LIMIT` words long accepts
    keyword evidence at the lower :data:`SHORT_KEYWORD_THRESHOLD`; every
    longer text keeps the strict long-text gate.
    """
    if len(lower_text.split()) <= SHORT_TEXT_WORD_LIMIT:
        return SHORT_KEYWORD_THRESHOLD
    return KEYWORD_THRESHOLD


def _keyword_confidence(
    n_keywords: int, n_hits: int, gate: float = KEYWORD_THRESHOLD
) -> float:
    """Band-scaled keyword confidence, or 0.0 when the gate refuses.

    ``gate`` is the acceptance threshold for THIS text (callers pass the
    length-scoped gate from :func:`_keyword_gate`; the default keeps the
    long-text gate for arithmetic-only callers). Below the gate the raw
    score is refused as evidence for any label (0.0); at or above it the
    score scales within the keyword band ``[gate, 1.0]`` so keyword
    evidence stays visibly weaker than a signature match. Naming: this
    band-scaled return value is the ``confidence`` classify labels
    accepted matches with (CLI prints it as ``confidence=``); it is NOT
    ``NearMiss.raw_score``, and the CLI's near-misses section prints
    ``score=`` for that RAW fraction instead.
    """
    if n_keywords == 0 or n_hits == 0:
        return 0.0
    score = n_hits / n_keywords
    if score < gate:
        return 0.0  # below gate: refused as evidence for any label
    # Scale within the keyword band so keyword evidence stays visibly weaker
    # than a signature match.
    span = 1.0 - gate
    return round(KEYWORD_CONFIDENCE_MAX * (gate + span * score), 3)


def classify(text: str) -> Classification:
    """Classify a symptom text into exactly one class.

    Signature matches win; otherwise a keyword score above threshold; otherwise
    unclassified. Weak keyword evidence never labels a specific class.
    """
    text = text or ""
    lower_text = text.lower()

    # (1) Signature regex match — high confidence, first class wins.
    for compiled in _compiled().values():
        if compiled.cls.id == UNCLASSIFIED_ID:
            continue
        for sig in compiled.signature_res:
            m = sig.search(text)
            if m:
                hits = _keyword_hits(compiled.cls, lower_text)
                evidence = [{"kind": "signature", "detail": m.group(0)}]
                evidence.extend({"kind": "keyword", "detail": kw} for kw in hits)
                return Classification(
                    class_id=compiled.cls.id,
                    confidence=SIGNATURE_CONFIDENCE,
                    matched_signature=m.group(0),
                    matched_keywords=hits,
                    evidence=evidence,
                )

    # (2) Keyword score — lower confidence, length-scoped gate (LORE-043).
    gate = _keyword_gate(lower_text)
    best_id: str | None = None
    best_conf = 0.0
    best_hits: tuple[str, ...] = ()
    for compiled in _compiled().values():
        if compiled.cls.id == UNCLASSIFIED_ID:
            continue
        hits = _keyword_hits(compiled.cls, lower_text)
        conf = _keyword_confidence(len(compiled.cls.keywords), len(hits), gate)
        if conf > best_conf:
            best_id, best_conf, best_hits = compiled.cls.id, conf, hits

    if best_id is not None and best_conf > 0.0:
        return Classification(
            class_id=best_id,
            confidence=best_conf,
            matched_signature=None,
            matched_keywords=best_hits,
            evidence=[{"kind": "keyword", "detail": kw} for kw in best_hits],
        )

    # (3) Total miss — unclassified, zero confidence. Honest fallback.
    return Classification(
        class_id=UNCLASSIFIED_ID,
        confidence=UNCLASSIFIED_CONFIDENCE,
        matched_signature=None,
        matched_keywords=(),
        evidence=[],
    )


def classify_all(text: str) -> list[Classification]:
    """All candidate classes for the text, best first, fallback included once.

    The unclassified fallback is appended only when no class matched, so
    callers can distinguish "nothing matched" from ranked candidates; when a
    class did match, the list is the ranked non-empty candidates only.
    """
    text = text or ""
    lower_text = text.lower()
    candidates: list[Classification] = []

    for compiled in _compiled().values():
        if compiled.cls.id == UNCLASSIFIED_ID:
            continue
        # Signature first within this class.
        for sig in compiled.signature_res:
            m = sig.search(text)
            if m:
                hits = _keyword_hits(compiled.cls, lower_text)
                evidence = [{"kind": "signature", "detail": m.group(0)}]
                evidence.extend({"kind": "keyword", "detail": kw} for kw in hits)
                candidates.append(
                    Classification(
                        class_id=compiled.cls.id,
                        confidence=SIGNATURE_CONFIDENCE,
                        matched_signature=m.group(0),
                        matched_keywords=hits,
                        evidence=evidence,
                    )
                )
                break
        else:
            hits = _keyword_hits(compiled.cls, lower_text)
            conf = _keyword_confidence(
                len(compiled.cls.keywords),
                len(hits),
                _keyword_gate(lower_text),
            )
            if conf > 0.0:
                candidates.append(
                    Classification(
                        class_id=compiled.cls.id,
                        confidence=conf,
                        matched_signature=None,
                        matched_keywords=hits,
                        evidence=[{"kind": "keyword", "detail": kw} for kw in hits],
                    )
                )

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    # Explicit unclassified fallback, always last (never duplicates a match).
    candidates.append(
        Classification(
            class_id=UNCLASSIFIED_ID,
            confidence=UNCLASSIFIED_CONFIDENCE,
            matched_signature=None,
            matched_keywords=(),
            evidence=[],
        )
    )
    return candidates


def near_misses(text: str, limit: int = 3) -> list[NearMiss]:
    """Below-threshold classes that partially matched, best first, top ``limit``.

    The evidence echo for the honesty rule: ``classify``/``classify_all``
    refuse to label weak keyword evidence (below :data:`KEYWORD_THRESHOLD`),
    which is doctrine — but the raw score already computed and discarded is
    real graded signal. ``near_misses`` returns it instead of throwing it
    away. Registry stays read-only over :meth:`get_registry().all_classes()`;
    a near-miss is NEVER a classification and nothing here auto-labels.

    Only classes with hits > 0 and keyword confidence 0.0 (i.e. score strictly
    below threshold, no signature match) are reported — a class the text
    already matched by signature or above-threshold keywords never appears
    here.
    """
    text = text or ""
    lower_text = text.lower()
    misses: list[NearMiss] = []
    for compiled in _compiled().values():
        if compiled.cls.id == UNCLASSIFIED_ID:
            continue
        if any(sig.search(text) for sig in compiled.signature_res):
            continue  # signature-accepted: classify already labels this class
        hits = _keyword_hits(compiled.cls, lower_text)
        conf = _keyword_confidence(
            len(compiled.cls.keywords),
            len(hits),
            _keyword_gate(lower_text),
        )
        if conf == 0.0 and hits:
            misses.append(
                NearMiss(
                    class_id=compiled.cls.id,
                    raw_score=len(hits) / len(compiled.cls.keywords),
                    n_hits=len(hits),
                    n_keywords=len(compiled.cls.keywords),
                    hit_keywords=hits,
                )
            )
    misses.sort(key=lambda nm: nm.raw_score, reverse=True)
    return misses[:limit]
