# Verdict: LORE-036

**Task:** Extend count-sync guard to class-count literals
**Evaluated:** 2026-09-26T07:42:55.095701
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ scripts/check-test-count.sh detects stale failure-class and curated-class count literals against len(lore.classes.SEED_CLASSES), with regression tests and docs synced; full pytest and ruff pass: scripts/check-test-count.sh delegates to scripts/count_sweep.py (SWEEP_OUT=$(python3 scripts/count_sweep.py "$CANONICAL" .), rc2=misconfigured, rc!=0=drift rc1) and prints the derived class count via `count_sweep.py --class-count .`. scripts/count_sweep.py:50 CLASS_COUNT_RE = r"(?<![\w])(\d{1,4}) (failure classes|curated classes)(?![\w])"; derive_class_count() loads lore/classes.py from repo root and returns len(SEED_CLASSES) (no second hand literal); _line_hits() flags mismatches, skipping threshold phrasing (>=, at least) and self-reference lines. Live mutation proof: sed README.md 13->12 failure classes => guard rc=1 with 'README.md:142: The curated registry holds **12 failure classes**'; restored => rc=0 'PASS: test-count guard: canonical=319 matches live=319; class-count=13; no stale count literals in living docs'. Regression tests: tests/test_count_guard.py (12 tests) incl. test_derived_class_count_matches_seed_registry, test_sweep_flags_stale_class_count_literal, test_sweep_allows_current_class_count, test_sweep_allowlists_dated_records, test_sweep_ignores_threshold_phrasing, test_sweep_flags_both_families_in_one_run, test_living_docs_carry_no_stale_count_literals, and end-to-end test_shell_guard_flags_and_clears_stale_class_count (scratch git repo, rc1 then rc0). Docs synced: README.md:142 '**13 failure classes**' equals len(SEED_CLASSES)=13 (verified by loading lore/classes.py), README/INSTALL test counts bumped 309->319 matching scripts/test-count.txt=319. Tests: `uv run pytest -x --tb=short` => '319 passed in 0.99s', exit 0. Lint: `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` => '92 files already formatted', exit 0. LSP diagnostics: 0 findings.
The count-sync guard now derives the class count from lore/classes.py SEED_CLASSES and flags stale 'N failure classes'/'N curated classes' literals (proven by live mutation rc=1/rc=0), with 12 regression tests, synced README/INSTALL docs, and green pytest (319 passed) and ruff.

## Summary

Judge Result: LORE-036

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ scripts/check-test-count.sh detects stale failure-class and curated-class count literals against len(lore.classes.SEED_CLASSES), with regression tests and docs synced; full pytest and ruff pass: scripts/check-test-count.sh delegates to scripts/count_sweep.py (SWEEP_OUT=$(python3 scripts/count_sweep.py "$CANONICAL" .), rc2=misconfigured, rc!=0=drift rc1) and prints the derived class count via `count_sweep.py --class-count .`. scripts/count_sweep.py:50 CLASS_COUNT_RE = r"(?<![\w])(\d{1,4}) (failure classes|curated classes)(?![\w])"; derive_class_count() loads lore/classes.py from repo root and returns len(SEED_CLASSES) (no second hand literal); _line_hits() flags mismatches, skipping threshold phrasing (>=, at least) and self-reference lines. Live mutation proof: sed README.md 13->12 failure classes => guard rc=1 with 'README.md:142: The curated registry holds **12 failure classes**'; restored => rc=0 'PASS: test-count guard: canonical=319 matches live=319; class-count=13; no stale count literals in living docs'. Regression tests: tests/test_count_guard.py (12 tests) incl. test_derived_class_count_matches_seed_registry, test_sweep_flags_stale_class_count_literal, test_sweep_allows_current_class_count, test_sweep_allowlists_dated_records, test_sweep_ignores_threshold_phrasing, test_sweep_flags_both_families_in_one_run, test_living_docs_carry_no_stale_count_literals, and end-to-end test_shell_guard_flags_and_clears_stale_class_count (scratch git repo, rc1 then rc0). Docs synced: README.md:142 '**13 failure classes**' equals len(SEED_CLASSES)=13 (verified by loading lore/classes.py), README/INSTALL test counts bumped 309->319 matching scripts/test-count.txt=319. Tests: `uv run pytest -x --tb=short` => '319 passed in 0.99s', exit 0. Lint: `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` => '92 files already formatted', exit 0. LSP diagnostics: 0 findings.
The count-sync guard now derives the class count from lore/classes.py SEED_CLASSES and flags stale 'N failure classes'/'N curated classes' literals (proven by live mutation rc=1/rc=0), with 12 regression tests, synced README/INSTALL docs, and green pytest (319 passed) and ruff.

Overall: PASS ✓
