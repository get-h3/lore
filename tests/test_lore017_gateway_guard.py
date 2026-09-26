"""Registry + classifier coverage for the gateway-guard-violation class (LORE-017)."""

from lore.classes import UNCLASSIFIED_ID, get_registry
from lore.classifier import classify

NEW_CLASS_ID = "gateway-guard-violation"


def test_gateway_guard_class_in_registry():
    reg = get_registry()
    cls = reg.get(NEW_CLASS_ID)
    assert cls is not None
    assert cls.name == "Gateway guard violation"
    assert "2026-09" in cls.provenance
    assert "2026-09-24" in cls.provenance
    assert 2 <= len(cls.signature_patterns) <= 4
    assert 4 <= len(cls.keywords) <= 8


def test_registry_total_count_derived():
    # LORE-032: derive the count from SEED_CLASSES (LORE-017 precedent) —
    # curated classes + unclassified, never a hardcoded literal.
    from lore.classes import SEED_CLASSES

    assert len(get_registry()) == len(SEED_CLASSES) + 1


def test_canonical_symptom_classifies_high_confidence():
    result = classify("banned command tripped the gateway guard")
    assert result.class_id == NEW_CLASS_ID
    assert result.confidence >= 0.9


def test_paraphrase_classifies_high_confidence():
    result = classify("git push blocked by the gateway guard hardline")
    assert result.class_id == NEW_CLASS_ID
    assert result.confidence >= 0.9


def test_repeated_guard_failure_paraphrase_classifies():
    result = classify("the same gateway guard block repeated across ticks")
    assert result.class_id == NEW_CLASS_ID
    assert result.confidence >= 0.9


def test_unrelated_text_still_unclassified():
    result = classify("nothing here matches anything at all")
    assert result.class_id == UNCLASSIFIED_ID


def test_signature_patterns_compile_and_match_finding():
    import re

    reg = get_registry()
    cls = reg.get(NEW_CLASS_ID)
    compiled = [re.compile(p) for p in cls.signature_patterns]
    for symptom in (
        "banned command tripped the gateway guard",
        "git push blocked by the gateway guard hardline",
        "denied command hit the hardline block again",
    ):
        assert any(rx.search(symptom) for rx in compiled), (
            f"no signature pattern matches {symptom!r}"
        )


def test_no_cross_class_regression_for_guard_symptoms():
    """The new symptom should not steal the top slot from an existing class's
    canonical symptom (near-neighbor: gateway-drain-window)."""
    drain = classify("drain 503s kill ticks while the gateway restarts")
    assert drain.class_id == "gateway-drain-window"
    assert drain.confidence >= 0.9
    guard = classify("banned command tripped the gateway guard")
    assert guard.class_id == NEW_CLASS_ID
