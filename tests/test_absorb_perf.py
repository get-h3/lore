"""PERF-3 regression test: absorb_sweep memoizes classify per invocation.

A sweep over repeated evidence (the normal logsey-export case — every sweep
interval re-reports the same lines) reclassified identical detail text once
per block. Now each unique detail text classifies at most once per
absorb_sweep call. Guards:
  - output is JSON-semantic-equal to the naive per-block-classify result;
  - classify is invoked at most once per unique detail text.
Block construction follows /tmp/lore_absorb_perf.py: parse the run14c
trail fixture (6 blocks) via parse_logsey_export and repeat it to 600.
"""

from __future__ import annotations

import json
from pathlib import Path

from lore import absorb
from lore.absorb import absorb_proposal
from lore.classifier import classify as _real_classify
from lore.evidence import EvidenceBlock, parse_logsey_export

_TRAIL_PATH = (
    Path(__file__).resolve().parents[1] / "docs/qa/evidence/run14c/trail-real.txt"
)
_BLOCKS_PER_FIXTURE = 6
_REPEATS = 100  # 6 x 100 = 600 blocks, all detail text repeated
_WINDOW = "2h"
_SOURCE = "perf-test"


def _repeated_blocks() -> list[EvidenceBlock]:
    blocks = parse_logsey_export(_TRAIL_PATH.read_text())
    assert len(blocks) == _BLOCKS_PER_FIXTURE, len(blocks)
    return blocks * _REPEATS


def _absorb_with_classifier(blocks: list[EvidenceBlock], classify_impl) -> list[dict]:
    """Run absorb_sweep with ``classify_impl`` standing in for the classifier."""
    original = absorb.classify
    absorb.classify = classify_impl
    try:
        return absorb.absorb_sweep(blocks, window=_WINDOW, source=_SOURCE)
    finally:
        absorb.classify = original


def _naive_no_memo_sweep(blocks: list[EvidenceBlock], classify_impl) -> list[dict]:
    """Faithful pre-fix reference: classify once per block, group in
    first-seen order, build proposals exactly as absorb_sweep does. Deliberately
    duplicates the grouping so a future memo regression flips this comparison,
    not hides inside it."""
    grouped: dict[str, list[EvidenceBlock]] = {}
    for block in blocks:
        classification = classify_impl(block.detail)  # per-block, no memo
        grouped.setdefault(classification.class_id, []).append(block)

    provenance = {
        "kind": "absorb-sweep",
        "window": _WINDOW,
        "ns": None,
        "board": None,
        "source": _SOURCE,
    }
    proposals: list[dict] = []
    for class_id, members in grouped.items():
        proposal = absorb_proposal(
            class_id,
            "\n".join(b.detail for b in members),
            source=_SOURCE,
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
            "window": _WINDOW,
            "ns": None,
            "board": None,
            "source": _SOURCE,
            "blocks_total": len(blocks),
            "blocks_class": len(members),
            "evidence": [b.to_trail_entry() for b in members],
        }
        proposal["provenance"] = dict(provenance)
        proposals.append(proposal)
    return proposals


def test_absorb_sweep_memoizes_classify_per_invocation():
    blocks = _repeated_blocks()
    unique_texts = len({b.detail for b in blocks})

    # Naive reference: classify per block via the faithful no-memo sweep.
    naive_calls: list[str] = []

    def naive_classify(text: str):
        naive_calls.append(text)
        return _real_classify(text)

    naive_out = _naive_no_memo_sweep(blocks, naive_classify)
    assert len(naive_calls) == len(blocks)  # reference classifies once per block

    # Counting wrapper over the real classifier, with a per-invocation memo
    # (the same pattern absorb_sweep now implements internally).
    real_calls: list[str] = []
    memo: dict[str, object] = {}

    def memoizing_classify(text: str):
        real_calls.append(text)
        if text not in memo:
            memo[text] = _real_classify(text)
        return memo[text]

    memo_out = _absorb_with_classifier(blocks, memoizing_classify)
    assert len(real_calls) <= unique_texts  # (b) at most 1 classify per unique text

    # (a) JSON-semantic equality with the naive result: identical per-class
    # block counts, first-seen ordering, and every value byte-identical.
    assert json.dumps(memo_out, sort_keys=True) == json.dumps(naive_out, sort_keys=True)


def test_absorb_sweep_real_code_bounds_classify_calls():
    """The memo lives in absorb_sweep itself, not just in this test's harness:
    swap in a bare counting wrapper (no test-side memo) over 600 repeated
    blocks and the real code must invoke classify no more than once per
    unique detail text."""
    blocks = _repeated_blocks()
    unique_texts = len({b.detail for b in blocks})

    calls: list[str] = []

    def counting_classify(text: str):
        calls.append(text)
        return _real_classify(text)

    out = _absorb_with_classifier(blocks, counting_classify)
    assert len(calls) <= unique_texts
    # And the sweep output is still complete: every block accounted for.
    assert sum(p["sweep"]["blocks_class"] for p in out) == len(blocks)
