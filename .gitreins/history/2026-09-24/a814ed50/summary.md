# Verdict: LORE-016

**Task:** Classifier near-miss evidence echo
**Evaluated:** 2026-09-24T15:53:05.034638
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ tests: ============================= test session starts ==============================
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
- ✓ **tier2**
  - COMPLETE
  ✓ Given a symptom text that produces no accepted match, lore exposes the top-3 below-threshold candidate classes with scores; registry stays closed; nothing auto-labeled: lore/classifier.py:228 defines near_misses(text, limit=3) returning NearMiss(class_id, raw_score=n_hits/n_keywords, n_hits, n_keywords, hit_keywords), sorted desc and capped at limit — verified empirically: a text hitting 8 classes returned exactly 3 (guard-degradation 0.333, shared-checkout-collision 0.167, secret-env-clobber 0.167). CLI: lore/__main__.py:45-55 prints a 'near-misses:' section under --explain; `uv run python -m lore match --explain "two foremen committed to the same worktree checkout"` output 'unclassified confidence=0.00' then 'shared-checkout-collision score=0.33 (2/6 keywords: worktree, checkout)'. Registry stays closed: lore/classes.py:272 register() raises RuntimeError ('the failure-class registry is closed and curated'); verified registry list unchanged (10 classes) after near_misses. Nothing auto-labeled: classify() returns unclassified 0.0 both before and after near_misses; near_misses only reports classes with conf==0.0 and hits>0 and skips signature-accepted classes (classifier.py:249-253). Tests: `uv run pytest -x --tb=short` -> exit 0, '187 passed in 0.57s' (9 in tests/test_near_miss.py). LSP diagnostics: 0 findings.
LORE-016 fully implemented: near_misses exposes top-3 below-threshold candidates with raw scores via library API and --explain CLI, registry remains closed, and nothing is auto-labeled — all 187 tests pass.

## Summary

Judge Result: LORE-016

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ tests: ============================= test session starts ==============================
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)

Stage tier2: PASS
  COMPLETE
  ✓ Given a symptom text that produces no accepted match, lore exposes the top-3 below-threshold candidate classes with scores; registry stays closed; nothing auto-labeled: lore/classifier.py:228 defines near_misses(text, limit=3) returning NearMiss(class_id, raw_score=n_hits/n_keywords, n_hits, n_keywords, hit_keywords), sorted desc and capped at limit — verified empirically: a text hitting 8 classes returned exactly 3 (guard-degradation 0.333, shared-checkout-collision 0.167, secret-env-clobber 0.167). CLI: lore/__main__.py:45-55 prints a 'near-misses:' section under --explain; `uv run python -m lore match --explain "two foremen committed to the same worktree checkout"` output 'unclassified confidence=0.00' then 'shared-checkout-collision score=0.33 (2/6 keywords: worktree, checkout)'. Registry stays closed: lore/classes.py:272 register() raises RuntimeError ('the failure-class registry is closed and curated'); verified registry list unchanged (10 classes) after near_misses. Nothing auto-labeled: classify() returns unclassified 0.0 both before and after near_misses; near_misses only reports classes with conf==0.0 and hits>0 and skips signature-accepted classes (classifier.py:249-253). Tests: `uv run pytest -x --tb=short` -> exit 0, '187 passed in 0.57s' (9 in tests/test_near_miss.py). LSP diagnostics: 0 findings.
LORE-016 fully implemented: near_misses exposes top-3 below-threshold candidates with raw scores via library API and --explain CLI, registry remains closed, and nothing is auto-labeled — all 187 tests pass.

Overall: PASS ✓
