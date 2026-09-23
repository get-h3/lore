"""Classifier behaviour tests: signature beats keyword, honesty rule on weak matches."""

from lore.classes import UNCLASSIFIED_ID
from lore.classifier import Classification, classify, classify_all

# ---------------------------------------------------------------- fixtures
# Realistic log-line / symptom fixtures, one per seed class, each containing
# at least one string that the class's own signature patterns match.

SIGNATURE_FIXTURES = {
    "gateway-drain-window": (
        "hermes gateway restart: batch config change applied, expect up to 30 min "
        "of drain 503s while in-flight requests finish"
    ),
    "shared-checkout-collision": (
        "worktree reap --all deleted the fresh worker checkout; git index.lock held "
        "by a sibling worker on the same branch"
    ),
    "secret-env-clobber": (
        "container .env overwritten by .env.example twins: central login 401 on every "
        "key, secrets clobbered by the example file"
    ),
    "disk-pressure-corruption": (
        "sqlite header wiped after ENOSPC: disk pressure on the volume corrupted the "
        "database pages mid-write"
    ),
    "cooldown-pin-drift": (
        "fleet.toml says paused but the DB pin still says enabled: cooldown authority "
        "drift between the two stores"
    ),
    "key-rotation-expiry": (
        "all provider keys return 401 Unauthorized after rotation; expired key never "
        "re-issued, calls failing auth across lanes"
    ),
    "guard-degradation": (
        "tier-1 guard passes in the worktree but the main-tree gate fails at the same "
        "commit: guard result not gate-equivalent, degraded verification"
    ),
    "spawn-hot-loop": (
        "scheduler respawns the same tick over and over, worker spin: -Q log stuck at "
        "0 bytes with rising CPU and no repo writes"
    ),
    "ingest-backfill-gap": (
        "chat archive shows a hole for 08-29/30: ingest pipeline reported success but "
        "the destination is missing rows, backfill needed"
    ),
}

KEYWORD_FIXTURES = {
    "gateway-drain-window": "503s while requests drain during restart",
    "secret-env-clobber": "env file secrets got clobbered",
    "disk-pressure-corruption": "enospic volume corruption risk",  # deliberately odd form
    "key-rotation-expiry": "expired credentials, auth fails",
    "spawn-hot-loop": "worker keeps respawning endlessly",
}

MISS_FIXTURE = "the quarterly report covers widget sales and marketing spend"


# ---------------------------------------------------------------- tests
def test_total_miss_is_unclassified():
    result = classify(MISS_FIXTURE)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0
    assert result.evidence == []


def test_signature_beats_keyword():
    # Text carrying both a gateway-drain-window signature AND secret-clobber
    # keywords must land on the signature class, not the keyword one.
    text = (
        "the env secrets got clobbered and meanwhile we expect drain 503s "
        "while in-flight requests finish during the gateway restart"
    )
    result = classify(text)
    assert result.class_id == "gateway-drain-window"
    assert result.confidence >= 0.8


def test_keyword_only_weak_match_falls_back_to_unclassified():
    # A keyword-only match must never be labeled as the specific class unless
    # it clears the keyword threshold. "expired credentials, auth fails" is
    # keyword-ish but the fixture asserts the honesty rule: below-threshold
    # keyword scores return unclassified, never a specific class.
    result = classify("expired credentials, auth fails")
    if result.class_id != UNCLASSIFIED_ID:
        # If it IS labeled, it must be because the keyword score cleared the
        # threshold — high confidence is forbidden for keyword-only evidence.
        assert result.confidence < 0.8
        assert all(ev["kind"] == "keyword" for ev in result.evidence), (
            "keyword-only classification must carry keyword evidence only"
        )


def test_every_seed_class_matched_by_own_signature():
    for cid, fixture in SIGNATURE_FIXTURES.items():
        result = classify(fixture)
        assert result.class_id == cid, (
            f"{cid}: fixture classified as {result.class_id} "
            f"(evidence={result.evidence})"
        )
        assert result.confidence >= 0.8


def test_keyword_fixtures_either_classified_or_honest_unclassified():
    # Keyword fixtures may land on their class (above threshold) or fall back
    # to unclassified — but a strong (signature-level) label without signature
    # evidence is forbidden.
    for cid, fixture in KEYWORD_FIXTURES.items():
        result = classify(fixture)
        assert result.confidence < 0.8, (
            f"{cid}: keyword-only fixture must never get signature-level confidence"
        )
        if result.class_id == cid:
            assert all(ev["kind"] == "keyword" for ev in result.evidence)


def test_classify_all_orders_best_first():
    text = (
        "drain 503s during gateway restart; also the env secrets clobbered the "
        "container login"
    )
    results = classify_all(text)
    assert results, "classify_all must return candidates"
    assert results[0].class_id == "gateway-drain-window"
    confs = [r.confidence for r in results]
    assert confs == sorted(confs, reverse=True), "candidates must be best-first"
    assert results[-1].class_id == UNCLASSIFIED_ID, "fallback must be present"
    # best candidate appears once; fallback appears exactly once
    ids = [r.class_id for r in results]
    assert len(ids) == len(set(ids)), "no duplicate class ids in candidates"


def test_classification_is_dataclass_with_expected_fields():
    result = classify(SIGNATURE_FIXTURES["gateway-drain-window"])
    assert isinstance(result, Classification)
    assert result.class_id
    assert isinstance(result.confidence, float)
    assert isinstance(result.evidence, list)
    for ev in result.evidence:
        assert set(ev.keys()) >= {"kind", "detail"}


def test_empty_input_is_unclassified():
    result = classify("")
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0
