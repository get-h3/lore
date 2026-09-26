"""LORE-034/035: worktree-reap-data-loss + fast-forward-push-reject classes
and the docs-count-drift signature widening.

Covers the 2026-09-26 discovery stress test that returned unclassified for
both new failure modes plus the most common natural drift-report phrasing,
with near-miss guards pinning the neighboring classes (registry stays a
closed curated list; counts are DERIVED from SEED_CLASSES, never hardcoded).
"""

from lore.classes import (
    SEED_CLASSES,
    UNCLASSIFIED_ID,
    get_registry,
)
from lore.classifier import classify

REAP_CLASS = "worktree-reap-data-loss"
PUSH_CLASS = "fast-forward-push-reject"
DOCS_CLASS = "docs-count-drift"

# ---------------------------------------------------------------- input 1
REAP_INPUT = (
    "watchdog reaped the worktree, branch classified merged though it had no commits"
)
REAP_VARIANTS = [
    "reap deleted the fresh zero-commit worktree",
    "worktree deleted though it had no commits",
    "the reaper removed the worktree mid-dispatch; its work was never committed",
]

# ---------------------------------------------------------------- input 2
PUSH_INPUT = "git push rejected non-fast-forward, origin has diverged"
PUSH_VARIANTS = [
    "push rejected non-fast-forward",
    "push was rejected because the remote advanced",
    "origin advanced while the worker held a stale HEAD: push rejected",
]

# ---------------------------------------------------------------- input 3
DOCS_INPUT = "docs say 230 tests, actual count on HEAD is 297"
DOCS_VARIANTS = [
    "documentation lists 200 tests but the real count is 301",
    "README says 148 tests, actual count on main is 202",
]

# ---------------------------------------------------------------- near miss
NEAR_MISS_REAP_HEALTHY = "worktree merged and removed after merge confirmation"
NEAR_MISS_PUSH_AUTH = "push rejected: permission denied (publickey)"
DOCS_REGRESSION_PIN = "README claims 148 tests but the suite shows 297"

OUT_OF_VOCABULARY = "the quarterly report covers widget sales and marketing spend"


def test_canonical_reap_phrase_classifies():
    result = classify(REAP_INPUT)
    assert result.class_id == REAP_CLASS
    assert result.confidence >= 0.9


def test_canonical_push_phrase_classifies():
    result = classify(PUSH_INPUT)
    assert result.class_id == PUSH_CLASS
    assert result.confidence >= 0.9


def test_canonical_docs_phrase_classifies():
    result = classify(DOCS_INPUT)
    assert result.class_id == DOCS_CLASS
    assert result.confidence >= 0.9


def test_reap_variants_classify():
    for text in REAP_VARIANTS:
        result = classify(text)
        assert result.class_id == REAP_CLASS, text
        assert result.confidence >= 0.9, text


def test_push_variants_classify():
    for text in PUSH_VARIANTS:
        result = classify(text)
        assert result.class_id == PUSH_CLASS, text
        assert result.confidence >= 0.9, text


def test_docs_variants_classify():
    for text in DOCS_VARIANTS:
        result = classify(text)
        assert result.class_id == DOCS_CLASS, text
        assert result.confidence >= 0.9, text


def test_healthy_post_merge_reap_is_NOT_reap_data_loss():
    # Negative space: a worktree merged AND removed after merge
    # confirmation is a healthy end-of-tick reap — no un-committed-work
    # marker, so the new class must not fire.
    result = classify(NEAR_MISS_REAP_HEALTHY)
    assert result.class_id != REAP_CLASS


def test_permission_denied_push_is_NOT_fast_forward_reject():
    # Negative space: an auth-shaped refusal is a DIFFERENT failure
    # class — every signature pattern requires a divergence marker
    # (non-fast-forward / diverged / advanced), never a bare refusal.
    result = classify(NEAR_MISS_PUSH_AUTH)
    assert result.class_id != PUSH_CLASS


def test_existing_docs_pattern_regression_pin():
    # The pre-existing "claims N tests but the suite shows M" pattern must
    # keep working after the signature widening (LORE-035 added shapes, it
    # did not touch this one).
    result = classify(DOCS_REGRESSION_PIN)
    assert result.class_id == DOCS_CLASS
    assert result.confidence >= 0.9


def test_out_of_vocabulary_stays_unclassified():
    result = classify(OUT_OF_VOCABULARY)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0


def test_registry_counts_derived_from_seeds():
    # LORE-017/LORE-032 precedent: the pin is DERIVED — base = the seed
    # table minus the two new ids, registry = curated ids + unclassified.
    base = [c for c in SEED_CLASSES if c.id not in (REAP_CLASS, PUSH_CLASS)]
    assert len(SEED_CLASSES) == len(base) + 2
    assert len(get_registry()) == len(SEED_CLASSES) + 1


def test_new_seed_ids_are_in_the_registry():
    curated = {c.id for c in get_registry().all_classes()} - {UNCLASSIFIED_ID}
    assert REAP_CLASS in curated
    assert PUSH_CLASS in curated
