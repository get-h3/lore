# Verdict: LORE-017

**Task:** Gateway-guard-violation failure class
**Evaluated:** 2026-09-25T08:49:29.906961
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Closed-registry seed edit in lore/classes.py + stale-count sweep + classify tests + live match/compile proof: All four sub-elements verified. (1) Closed-registry seed edit: commit 198f2b0 adds FailureClass id='gateway-guard-violation' to SEED_CLASSES in lore/classes.py (4 signature patterns, 8 keywords, provenance citing 2026-09-24 dogfood); ClassRegistry.register still raises RuntimeError — live check printed 'REFUSED: the failure-class registry is closed and curated...' and len(get_registry())==11. (2) Stale-count sweep: README.md:138/256 (10 curated classes, 238 tests), CHANGELOG.md:18/42 (10 curated, 238), docs/INSTALL.md:50/57 (238 passed, 10 test files); verified 238 passed at commit 198f2b0 in worktree lore-LORE-017 (uv run pytest -q => '238 passed in 0.30s'). Remaining '148'/'9 failure classes' strings live only in docs/dogfood/* historical reports that document the LORE-019 staleness finding, not live claims. (3) Classify tests: tests/test_lore017_gateway_guard.py has 8 tests (registry membership, total count 11, canonical symptom + 2 paraphrases at >=0.9, signature-regex match, cross-class drain-vs-guard regression, unclassified negative) — 'uv run pytest -q tests/test_lore017_gateway_guard.py' => '8 passed'. (4) Live match/compile proof: 'uv run lore match "banned command tripped the gateway guard"' => 'gateway-guard-violation confidence=0.90'; 'uv run lore compile --class gateway-guard-violation --format md' renders the runbook (2 read-only checks, 4-step recovery ladder, 3 guardrails, evidence trail). Full suite on current tree: 'uv run pytest -q' => '259 passed in 0.21s' (259 = 238 + LORE-016 additions); 'uv run ruff check .' => 'All checks passed!'.
LORE-017 fully satisfies its criterion: the gateway-guard-violation class is seeded into the closed registry, stale counts were swept, 8 classify tests pass, and live match/compile both prove the class end-to-end.

## Summary

Judge Result: LORE-017

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Closed-registry seed edit in lore/classes.py + stale-count sweep + classify tests + live match/compile proof: All four sub-elements verified. (1) Closed-registry seed edit: commit 198f2b0 adds FailureClass id='gateway-guard-violation' to SEED_CLASSES in lore/classes.py (4 signature patterns, 8 keywords, provenance citing 2026-09-24 dogfood); ClassRegistry.register still raises RuntimeError — live check printed 'REFUSED: the failure-class registry is closed and curated...' and len(get_registry())==11. (2) Stale-count sweep: README.md:138/256 (10 curated classes, 238 tests), CHANGELOG.md:18/42 (10 curated, 238), docs/INSTALL.md:50/57 (238 passed, 10 test files); verified 238 passed at commit 198f2b0 in worktree lore-LORE-017 (uv run pytest -q => '238 passed in 0.30s'). Remaining '148'/'9 failure classes' strings live only in docs/dogfood/* historical reports that document the LORE-019 staleness finding, not live claims. (3) Classify tests: tests/test_lore017_gateway_guard.py has 8 tests (registry membership, total count 11, canonical symptom + 2 paraphrases at >=0.9, signature-regex match, cross-class drain-vs-guard regression, unclassified negative) — 'uv run pytest -q tests/test_lore017_gateway_guard.py' => '8 passed'. (4) Live match/compile proof: 'uv run lore match "banned command tripped the gateway guard"' => 'gateway-guard-violation confidence=0.90'; 'uv run lore compile --class gateway-guard-violation --format md' renders the runbook (2 read-only checks, 4-step recovery ladder, 3 guardrails, evidence trail). Full suite on current tree: 'uv run pytest -q' => '259 passed in 0.21s' (259 = 238 + LORE-016 additions); 'uv run ruff check .' => 'All checks passed!'.
LORE-017 fully satisfies its criterion: the gateway-guard-violation class is seeded into the closed registry, stale counts were swept, 8 classify tests pass, and live match/compile both prove the class end-to-end.

Overall: PASS ✓
