"""Registry integrity tests for the lore failure-class taxonomy."""

import pytest

from lore.classes import UNCLASSIFIED_ID, get_registry

SEED_CLASS_IDS = [
    "gateway-drain-window",
    "shared-checkout-collision",
    "secret-env-clobber",
    "disk-pressure-corruption",
    "cooldown-pin-drift",
    "key-rotation-expiry",
    "guard-degradation",
    "spawn-hot-loop",
    "ingest-backfill-gap",
]


def test_unclassified_exists():
    reg = get_registry()
    uc = reg.get(UNCLASSIFIED_ID)
    assert uc is not None
    assert uc.id == UNCLASSIFIED_ID


def test_all_seed_classes_present():
    reg = get_registry()
    ids = {c.id for c in reg.all_classes()}
    for cid in SEED_CLASS_IDS:
        assert cid in ids, f"missing seed class: {cid}"


def test_no_duplicate_ids():
    reg = get_registry()
    ids = [c.id for c in reg.all_classes()]
    assert len(ids) == len(set(ids))


def test_every_class_has_signature_and_keywords():
    reg = get_registry()
    for cls in reg.all_classes():
        assert cls.id, "class id must be non-empty"
        assert cls.name, f"{cls.id}: name must be non-empty"
        assert cls.description, f"{cls.id}: description must be non-empty"
        assert cls.signature_patterns, f"{cls.id}: no signature patterns"
        assert cls.keywords, f"{cls.id}: no keywords"
        assert "2026-09" in cls.provenance, (
            f"{cls.id}: provenance missing fleet history note"
        )


def test_signature_patterns_compile():
    import re

    reg = get_registry()
    for cls in reg.all_classes():
        for pat in cls.signature_patterns:
            try:
                re.compile(pat)
            except re.error as e:
                pytest.fail(f"{cls.id}: bad regex {pat!r}: {e}")


def test_runtime_class_invention_refused():
    reg = get_registry()
    with pytest.raises(RuntimeError):
        reg.register(
            id="made-up-class",
            name="Made Up",
            description="should not be allowed",
            signature_patterns=["x"],
            keywords=["x"],
            provenance="runtime invention",
        )


def test_registry_size_is_pinned_closed():
    # LORE-023: the registry is a CLOSED curated list; its size is pinned so
    # class sprawl cannot arrive quietly. Vocabulary growth goes into the
    # EXISTING classes' patterns/keywords, never into new ids.
    # 10 curated seed classes + unclassified (grep -c 'id="' lore/classes.py).
    assert len(get_registry()) == 11


def test_registry_lookup_unknown_returns_none():
    reg = get_registry()
    assert reg.get("does-not-exist") is None


def test_classifier_returns_classification_dataclass():
    from lore.classifier import Classification, classify

    result = classify("nothing here matches anything at all")
    assert isinstance(result, Classification)
    assert result.class_id == UNCLASSIFIED_ID
