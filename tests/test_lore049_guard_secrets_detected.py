"""LORE-049: guard-failure secrets-detected phrasing must reach a curated class."""

from lore.classes import get_registry
from lore.classifier import classify

CLASS_ID = "gateway-guard-violation"

# The canonical guard-failure text measured `unclassified 0.00` before the
# seed-table fix (LORE-049).
GUARD_SECRETS_TEXTS = (
    "guard FAILED: secrets detected in diff",
    "guard failure: secrets detected in the diff",
    "secrets detected in diff — guard FAILED, fix and re-run",
)


def test_canonical_guard_secrets_text_classifies():
    result = classify("guard FAILED: secrets detected in diff")
    assert result.class_id == CLASS_ID
    assert result.confidence >= 0.9


def test_variant_phrasings_classify():
    for text in GUARD_SECRETS_TEXTS[1:]:
        result = classify(text)
        assert result.class_id == CLASS_ID, text
        assert result.confidence >= 0.9, text


def test_matched_signature_is_token_exact():
    result = classify("guard FAILED: secrets detected in diff")
    # matched_signature is the full regex match ("guard FAILED: secrets
    # detected"); the load-bearing part is the token-exact secrets-detected
    # phrase inside it.
    assert "secrets detected" in result.matched_signature


def test_bare_half_phrasings_stay_unguarded_class():
    # Co-occurrence rule: a bare "secrets detected" with no guard language
    # must not fire the guard class; a bare guard failure with no secrets
    # neither (existing LORE-017 coverage keeps those on banned/denied).
    result = classify("secrets detected somewhere in the repo")
    assert result.class_id != CLASS_ID


def test_patterns_registered_on_curated_class():
    cls = get_registry().get(CLASS_ID)
    assert any("secrets?\\s+detected" in p for p in cls.signature_patterns)
