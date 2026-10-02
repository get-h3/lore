# Verdict: LORE-041

**Task:** Classifier: absorb git checkout-collision canonical error text into shared-checkout-collision
**Evaluated:** 2026-10-01T12:23:11.059120
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ lore match on git's canonical collision error ('error: Your local changes to the following files would be overwritten by checkout / Please commit your changes or stash them') classifies shared-checkout-collision, and secret-env-clobber no longer outranks it on that text; near-miss echo corrected; all existing tests + new regression tests pass, ruff clean, count guard green: Canonical text now classifies shared-checkout-collision at conf 0.9 with matched_signature 'would be overwritten by checkout' (pre-fix worktree HEAD^1 returned unclassified 0.0). secret-env-clobber no longer outranks it: pre-fix near_misses(CANON)=[('secret-env-clobber',0.167),('shared-checkout-collision',0.125)]; post-fix near_misses(CANON)=[] (class is signature-accepted, no echo). Fix in lore/classes.py: shared-checkout-collision absorbs token-exact patterns r'would\s+be\s+overwritten\s+by\s+checkout' and r'please\s+commit\s+your\s+changes\s+or\s+stash'; secret-env-clobber keyword 'overwritten' swapped for class-owning 'twins' (count held at 6). No collateral damage: near_misses('gateway drain 503')=[('guard-degradation',0.167)] unchanged, and clobber true positives still classify 0.9 ('container .env overwritten by .env.example twins: central login 401', 'env file got clobbered', 'env clobber', 'the .env.example twins overwrote the live secrets'). Tests: `uv run pytest -q` -> '364 passed in 5.70s' exit 0; new tests/test_lore041_collision_canonical.py 11 passed, RED-proven (4 failed, 7 passed against pre-fix classes.py). ruff: `uv run ruff check . --quiet` exit 0; `ruff format --check .` -> '142 files already formatted' exit 0. Count guard: `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=364 matches live=364; class-count=13; no stale count literals in living docs' exit 0 (scripts/test-count.txt 353->364, docs synced).
LORE-041 verified: canonical git checkout-collision text now classifies shared-checkout-collision at 0.9 with secret-env-clobber no longer outranking it, near-miss echo corrected without collateral damage, 364 tests pass, ruff clean, count guard green.

## Summary

Judge Result: LORE-041

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ lore match on git's canonical collision error ('error: Your local changes to the following files would be overwritten by checkout / Please commit your changes or stash them') classifies shared-checkout-collision, and secret-env-clobber no longer outranks it on that text; near-miss echo corrected; all existing tests + new regression tests pass, ruff clean, count guard green: Canonical text now classifies shared-checkout-collision at conf 0.9 with matched_signature 'would be overwritten by checkout' (pre-fix worktree HEAD^1 returned unclassified 0.0). secret-env-clobber no longer outranks it: pre-fix near_misses(CANON)=[('secret-env-clobber',0.167),('shared-checkout-collision',0.125)]; post-fix near_misses(CANON)=[] (class is signature-accepted, no echo). Fix in lore/classes.py: shared-checkout-collision absorbs token-exact patterns r'would\s+be\s+overwritten\s+by\s+checkout' and r'please\s+commit\s+your\s+changes\s+or\s+stash'; secret-env-clobber keyword 'overwritten' swapped for class-owning 'twins' (count held at 6). No collateral damage: near_misses('gateway drain 503')=[('guard-degradation',0.167)] unchanged, and clobber true positives still classify 0.9 ('container .env overwritten by .env.example twins: central login 401', 'env file got clobbered', 'env clobber', 'the .env.example twins overwrote the live secrets'). Tests: `uv run pytest -q` -> '364 passed in 5.70s' exit 0; new tests/test_lore041_collision_canonical.py 11 passed, RED-proven (4 failed, 7 passed against pre-fix classes.py). ruff: `uv run ruff check . --quiet` exit 0; `ruff format --check .` -> '142 files already formatted' exit 0. Count guard: `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=364 matches live=364; class-count=13; no stale count literals in living docs' exit 0 (scripts/test-count.txt 353->364, docs synced).
LORE-041 verified: canonical git checkout-collision text now classifies shared-checkout-collision at 0.9 with secret-env-clobber no longer outranking it, near-miss echo corrected without collateral damage, 364 tests pass, ruff clean, count guard green.

Overall: PASS ✓
