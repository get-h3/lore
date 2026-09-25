# Verdict: LORE-003

**Task:** Failure-class taxonomy + classifier for lore
**Evaluated:** 2026-09-23T09:25:56.976785
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Python package lore/ with curated failure-class registry (drain-window, shared-checkout collision, secret clobber, disk-pressure corruption, cooldown drift, key-rotation, guard degradation, spawn hot-loop, ingest/backfill gap) plus explicit unclassified bucket; classifier maps a trail/message to a class by signature + keyword match with low-confidence falling back to unclassified; tests pass via pytest: lore/ package present (__init__.py, classes.py, classifier.py, __main__.py). lore/classes.py SEED_CLASSES contains all 9 curated classes: gateway-drain-window (L40), shared-checkout-collision (L57), secret-env-clobber (L74), disk-pressure-corruption (L98), cooldown-pin-drift (L121), key-rotation-expiry (L138), guard-degradation (L161), spawn-hot-loop (L185), ingest-backfill-gap (L202), plus explicit UNCLASSIFIED_CLASS (L227, id='unclassified', no-op pattern r'(?!)' so it never matches). lore/classifier.py classify() does signature regex match first (SIGNATURE_CONFIDENCE=0.9), then keyword score gated by KEYWORD_THRESHOLD=0.6 with keyword-only confidence capped at 0.5, else returns UNCLASSIFIED_ID with 0.0 confidence; _keyword_confidence returns 0.0 below threshold so weak matches fall back to unclassified. Tests: `uv run pytest -x --tb=short` exit_code 0, output 'collected 16 items ... 16 passed in 0.02s' (tests/test_classes.py 8 tests incl. test_unclassified_exists/test_all_seed_classes_present; tests/test_classifier.py 8 tests incl. test_total_miss_is_unclassified, test_signature_beats_keyword, test_keyword_only_weak_match_falls_back_to_unclassified, test_every_seed_class_matched_by_own_signature).


## Summary

Judge Result: LORE-003

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Python package lore/ with curated failure-class registry (drain-window, shared-checkout collision, secret clobber, disk-pressure corruption, cooldown drift, key-rotation, guard degradation, spawn hot-loop, ingest/backfill gap) plus explicit unclassified bucket; classifier maps a trail/message to a class by signature + keyword match with low-confidence falling back to unclassified; tests pass via pytest: lore/ package present (__init__.py, classes.py, classifier.py, __main__.py). lore/classes.py SEED_CLASSES contains all 9 curated classes: gateway-drain-window (L40), shared-checkout-collision (L57), secret-env-clobber (L74), disk-pressure-corruption (L98), cooldown-pin-drift (L121), key-rotation-expiry (L138), guard-degradation (L161), spawn-hot-loop (L185), ingest-backfill-gap (L202), plus explicit UNCLASSIFIED_CLASS (L227, id='unclassified', no-op pattern r'(?!)' so it never matches). lore/classifier.py classify() does signature regex match first (SIGNATURE_CONFIDENCE=0.9), then keyword score gated by KEYWORD_THRESHOLD=0.6 with keyword-only confidence capped at 0.5, else returns UNCLASSIFIED_ID with 0.0 confidence; _keyword_confidence returns 0.0 below threshold so weak matches fall back to unclassified. Tests: `uv run pytest -x --tb=short` exit_code 0, output 'collected 16 items ... 16 passed in 0.02s' (tests/test_classes.py 8 tests incl. test_unclassified_exists/test_all_seed_classes_present; tests/test_classifier.py 8 tests incl. test_total_miss_is_unclassified, test_signature_beats_keyword, test_keyword_only_weak_match_falls_back_to_unclassified, test_every_seed_class_matched_by_own_signature).


Overall: PASS ✓
