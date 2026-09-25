# Verdict: LORE-023

**Task:** Classifier: real incident vocabulary misses seeded classes
**Evaluated:** 2026-09-25T18:44:58.905538
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Three probe phrases classify to expected existing classes; registry size unchanged; uv run pytest -q green: All three probes classify correctly: 'empty commit landed with my message but zero files' -> shared-checkout-collision (sig=empty commit, conf=0.90); 'core.bare got flipped on the main repo and pushes fail' -> shared-checkout-collision (sig=core.bare, conf=0.90); 'env clobber' -> secret-env-clobber (sig=env clobber, conf=0.90). Verified via `uv run python -c classify(...)` and CLI `uv run python -m lore match --explain` (each prints '<class>\tconfidence=0.90'). Registry size unchanged: pre-change a5cc091 has 10 ids, HEAD has the identical 10 ids (gateway-drain-window, shared-checkout-collision, secret-env-clobber, disk-pressure-corruption, cooldown-pin-drift, key-rotation-expiry, guard-degradation, spawn-hot-loop, ingest-backfill-gap, gateway-guard-violation); get_registry() len == 11 (10 seeds + unclassified), pinned by tests/test_classes.py::test_registry_size_is_pinned_closed. Tests: `uv run pytest -q` -> '280 passed in 0.26s', EXIT=0; LORE-023-specific tests (tests/test_near_miss.py + test_classes.py -k 'lore023 or registry_size') -> '6 passed'. No LSP diagnostics.
All three LORE-023 probe phrases classify to their expected existing classes, the registry size is unchanged (10 seed ids + unclassified = 11), and the full suite is green (280 passed, exit 0).

## Summary

Judge Result: LORE-023

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Three probe phrases classify to expected existing classes; registry size unchanged; uv run pytest -q green: All three probes classify correctly: 'empty commit landed with my message but zero files' -> shared-checkout-collision (sig=empty commit, conf=0.90); 'core.bare got flipped on the main repo and pushes fail' -> shared-checkout-collision (sig=core.bare, conf=0.90); 'env clobber' -> secret-env-clobber (sig=env clobber, conf=0.90). Verified via `uv run python -c classify(...)` and CLI `uv run python -m lore match --explain` (each prints '<class>\tconfidence=0.90'). Registry size unchanged: pre-change a5cc091 has 10 ids, HEAD has the identical 10 ids (gateway-drain-window, shared-checkout-collision, secret-env-clobber, disk-pressure-corruption, cooldown-pin-drift, key-rotation-expiry, guard-degradation, spawn-hot-loop, ingest-backfill-gap, gateway-guard-violation); get_registry() len == 11 (10 seeds + unclassified), pinned by tests/test_classes.py::test_registry_size_is_pinned_closed. Tests: `uv run pytest -q` -> '280 passed in 0.26s', EXIT=0; LORE-023-specific tests (tests/test_near_miss.py + test_classes.py -k 'lore023 or registry_size') -> '6 passed'. No LSP diagnostics.
All three LORE-023 probe phrases classify to their expected existing classes, the registry size is unchanged (10 seed ids + unclassified = 11), and the full suite is green (280 passed, exit 0).

Overall: PASS ✓
