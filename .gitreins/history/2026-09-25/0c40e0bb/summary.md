# Verdict: LORE-029

**Task:** Count-sync guard: automate test-count claims in docs
**Evaluated:** 2026-09-25T23:27:32.823238
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ scripts/test-count.txt holds the single canonical test count; scripts/check-test-count.sh sweeps *.md for stale '<N> passed'/'<N> tests' literals (exit 1 + file:line on drift; exit 2 on missing/non-numeric canonical; dated-record allowlist; exit 0 on clean tree); a pytest test asserts the canonical count equals the live collected count; README.md and docs/INSTALL.md carry no stale count literals; uv run pytest -q green and uv run ruff check . clean: scripts/test-count.txt contains exactly '289'. check-test-count.sh verified live: clean tree -> 'PASS: test-count guard: canonical=289 matches live=289' EXIT=0; missing canonical -> 'ERROR: canonical count file ... not found' EXIT=2; non-numeric ('abc') -> 'ERROR: ... is not a single number' EXIT=2; drift literal (README '999 passed') -> '330:999 passed' + 'FAIL: stale test-count literal(s)' EXIT=1; canonical mismatch (123 vs live 289) -> 'FAIL: test-count drift' EXIT=1. Allowlist verified: CHANGELOG.md/docs/dogfood/*/docs/acceptance/* with 999/888/777 literals -> EXIT=0. tests/test_count_guard.py::test_canonical_count_matches_live_collected_count asserts canonical == live collected count and PASSED (2 passed in 0.27s). README.md:118,257 and docs/INSTALL.md:52,59 carry 289 (current, not stale). uv run pytest -q -> '289 passed in 0.62s'; uv run ruff check . -> 'All checks passed!' (exit 0).


## Summary

Judge Result: LORE-029

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ scripts/test-count.txt holds the single canonical test count; scripts/check-test-count.sh sweeps *.md for stale '<N> passed'/'<N> tests' literals (exit 1 + file:line on drift; exit 2 on missing/non-numeric canonical; dated-record allowlist; exit 0 on clean tree); a pytest test asserts the canonical count equals the live collected count; README.md and docs/INSTALL.md carry no stale count literals; uv run pytest -q green and uv run ruff check . clean: scripts/test-count.txt contains exactly '289'. check-test-count.sh verified live: clean tree -> 'PASS: test-count guard: canonical=289 matches live=289' EXIT=0; missing canonical -> 'ERROR: canonical count file ... not found' EXIT=2; non-numeric ('abc') -> 'ERROR: ... is not a single number' EXIT=2; drift literal (README '999 passed') -> '330:999 passed' + 'FAIL: stale test-count literal(s)' EXIT=1; canonical mismatch (123 vs live 289) -> 'FAIL: test-count drift' EXIT=1. Allowlist verified: CHANGELOG.md/docs/dogfood/*/docs/acceptance/* with 999/888/777 literals -> EXIT=0. tests/test_count_guard.py::test_canonical_count_matches_live_collected_count asserts canonical == live collected count and PASSED (2 passed in 0.27s). README.md:118,257 and docs/INSTALL.md:52,59 carry 289 (current, not stale). uv run pytest -q -> '289 passed in 0.62s'; uv run ruff check . -> 'All checks passed!' (exit 0).


Overall: PASS ✓
