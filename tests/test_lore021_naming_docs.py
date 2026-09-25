"""LORE-021: pin the documented naming contract so it cannot silently drift.

Two documented facts about :mod:`lore.classifier` are pinned mechanically:

1. ``NearMiss.raw_score`` is the RAW keyword fraction ``n_hits / n_keywords``,
   and the CLI ``match --explain`` prints that SAME raw fraction as
   ``score=``. The band-scaled value :func:`_keyword_confidence` computes is
   a DIFFERENT number (it is the ``confidence=`` the CLI prints for accepted
   matches, and is 0.0 by construction for near-misses).
2. ``Classification.evidence`` is a list of PLAIN DICTS with exactly the keys
   ``"kind"`` and ``"detail"`` (kinds: ``signature``, ``keyword``) — not
   dataclass objects.
"""

from lore.__main__ import main as cli_main
from lore.classifier import (
    NearMiss,
    _keyword_confidence,
    classify,
    near_misses,
)


# ------------------------------------------------------- raw_score vs score=
def test_near_miss_raw_score_is_the_raw_hit_fraction():
    nm = near_misses("two foremen committed to the same worktree checkout")[0]
    assert isinstance(nm, NearMiss)
    # Raw fraction, computed from the object's own fields — no scaling.
    assert nm.raw_score == nm.n_hits / nm.n_keywords
    assert nm.raw_score == len(nm.hit_keywords) / nm.n_keywords


def test_band_scaled_value_differs_from_raw_score_for_a_near_miss():
    # The module's OWN scaling function is the source of the band-scaled
    # number; for a below-threshold near-miss it returns 0.0 — never the raw
    # fraction. This is exactly the divergence the docstring names.
    nm = near_misses("two foremen committed to the same worktree checkout")[0]
    assert 0.0 < nm.raw_score < 1.0  # precondition: a real fraction
    assert _keyword_confidence(nm.n_keywords, nm.n_hits) == 0.0
    assert _keyword_confidence(nm.n_keywords, nm.n_hits) != nm.raw_score


def test_cli_explain_prints_the_raw_fraction_as_score(capsys):
    # The near-misses section's `score=` is raw_score formatted — the raw
    # fraction, NOT a band-scaled value.
    nm = near_misses("two foremen committed to the same worktree checkout")[0]
    code = cli_main(
        ["match", "--explain", "two foremen committed to the same worktree checkout"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert f"score={nm.raw_score:.2f}" in out
    # And the band-scaled number (0.00 for a near-miss, via the module's own
    # scaling) is a DIFFERENT string — it must not appear as this line's score.
    scaled = f"{_keyword_confidence(nm.n_keywords, nm.n_hits):.2f}"
    assert scaled != f"{nm.raw_score:.2f}"
    assert f"score={scaled}" not in out


def test_band_scaled_value_is_the_confidence_for_an_accepted_keyword_match():
    # Above threshold: the band-scaled value IS the labeled confidence (the
    # CLI prints it as `confidence=`), and it differs from the raw fraction.
    # Phrased so no signature regex fires (keyword-only acceptance).
    from lore.classes import get_registry

    text = "worktree checkout sibling collision reap"
    cls = classify(text)
    assert cls.matched_signature is None
    assert cls.class_id == "shared-checkout-collision"
    n_keywords = len(get_registry().get("shared-checkout-collision").keywords)
    assert len(cls.matched_keywords) == 5  # all but "index.lock"
    scaled = _keyword_confidence(n_keywords, len(cls.matched_keywords))
    assert scaled == cls.confidence
    assert scaled != len(cls.matched_keywords) / n_keywords  # scaling ≠ identity


# ------------------------------------------------------- evidence dict shape
def test_signature_hit_evidence_is_plain_dicts_with_exact_keys():
    cls = classify("drain 503s while requests drain during restart")
    assert cls.matched_signature is not None, "precondition: signature hit"
    assert cls.evidence, "precondition: evidence present"
    for item in cls.evidence:
        assert type(item) is dict, f"evidence items are plain dicts, got {type(item)}"
        assert set(item.keys()) == {"kind", "detail"}
    kinds = [e["kind"] for e in cls.evidence]
    assert kinds[0] == "signature"
    assert set(kinds[1:]) <= {"keyword"}
    assert cls.evidence[0]["detail"] == cls.matched_signature


def test_keyword_only_hit_evidence_is_plain_dicts_with_exact_keys():
    cls = classify("worktree checkout sibling collision reap")
    assert cls.matched_signature is None, "precondition: keyword-only hit"
    assert cls.evidence
    for item in cls.evidence:
        assert type(item) is dict
        assert set(item.keys()) == {"kind", "detail"}
        assert item["kind"] == "keyword"
        assert item["detail"] in cls.matched_keywords


def test_docstrings_state_both_names():
    # The documentation contract itself is pinned: the NearMiss docstring
    # names raw_score AND the CLI's score=; the Classification docstring
    # names the evidence dict shape.
    import inspect

    import lore.classifier as mod

    nm_doc = inspect.getdoc(mod.NearMiss)
    assert "raw_score" in nm_doc
    assert "score=" in nm_doc
    cls_doc = inspect.getdoc(mod.Classification)
    assert '"kind"' in cls_doc and '"detail"' in cls_doc
