# Verdict: LORE-036

**Task:** Extend count-sync guard to class-count literals
**Evaluated:** 2026-09-26T07:43:37.542762
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ scripts/check-test-count.sh detects stale failure-class and curated-class count literals against len(lore.classes.SEED_CLASSES), with regression tests and docs synced; full pytest and ruff pass: scripts/check-test-count.sh delegates the sweep to scripts/count_sweep.py (SWEEP_OUT=$(python3 scripts/count_sweep.py "$CANONICAL" .); rc 2=misconfigured, 1=drift) and prints the derived class count in its banner. scripts/count_sweep.py defines CLASS_COUNT_RE = r"(?<![\w])(\d{1,4}) (failure classes|curated classes)(?![\w])" and derive_class_count() loads lore/classes.py via importlib and returns len(SEED_CLASSES) (never a second literal); _line_hits flags any class literal != derived count, skipping threshold phrasing and allowlisted dated records. Regression tests in tests/test_count_guard.py (12 tests): test_derived_class_count_matches_seed_registry:119, test_sweep_flags_stale_failure_class_literal:132, test_sweep_flags_stale_curated_class_literal:144, test_sweep_passes_current_class_counts:156, test_sweep_allowlists_dated_records:172, test_sweep_ignores_threshold_phrasing:202, test_sweep_flags_both_families_in_one_run:220, test_sweep_self_referencing_line_exempt:240, test_living_docs_carry_no_stale_count_literals:256, test_shell_guard_flags_and_clears_stale_class_count:279 (end-to-end rc=1 on stale '4 failure classes', rc=0 after restore). Docs synced: README.md:142 '13 failure classes', README.md:261 '13 curated classes', README.md:122/262 '319 passed'/'319 tests passing', docs/INSTALL.md '319 passed'/'319 tests', scripts/test-count.txt=319; len(SEED_CLASSES)=13 verified via python3. Command evidence: `sh scripts/check-test-count.sh` exit_code=0 -> 'PASS: test-count guard: canonical=319 matches live=319; class-count=13; no stale count literals in living docs'; `uv run pytest -q --tb=short` exit_code=0 -> '319 passed in 0.94s'; `uv run pytest tests/test_count_guard.py -q` exit_code=0 -> '12 passed'; `uv run ruff check .` exit_code=0 -> 'All checks passed!'; `uv run ruff format --check .` exit_code=0 -> '93 files already formatted'.
The count-sync guard now derives len(SEED_CLASSES) and flags stale failure-class/curated-class literals, with 12 passing regression tests, synced README/INSTALL docs, and green pytest (319 passed) and ruff.

## Summary

Judge Result: LORE-036

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ scripts/check-test-count.sh detects stale failure-class and curated-class count literals against len(lore.classes.SEED_CLASSES), with regression tests and docs synced; full pytest and ruff pass: scripts/check-test-count.sh delegates the sweep to scripts/count_sweep.py (SWEEP_OUT=$(python3 scripts/count_sweep.py "$CANONICAL" .); rc 2=misconfigured, 1=drift) and prints the derived class count in its banner. scripts/count_sweep.py defines CLASS_COUNT_RE = r"(?<![\w])(\d{1,4}) (failure classes|curated classes)(?![\w])" and derive_class_count() loads lore/classes.py via importlib and returns len(SEED_CLASSES) (never a second literal); _line_hits flags any class literal != derived count, skipping threshold phrasing and allowlisted dated records. Regression tests in tests/test_count_guard.py (12 tests): test_derived_class_count_matches_seed_registry:119, test_sweep_flags_stale_failure_class_literal:132, test_sweep_flags_stale_curated_class_literal:144, test_sweep_passes_current_class_counts:156, test_sweep_allowlists_dated_records:172, test_sweep_ignores_threshold_phrasing:202, test_sweep_flags_both_families_in_one_run:220, test_sweep_self_referencing_line_exempt:240, test_living_docs_carry_no_stale_count_literals:256, test_shell_guard_flags_and_clears_stale_class_count:279 (end-to-end rc=1 on stale '4 failure classes', rc=0 after restore). Docs synced: README.md:142 '13 failure classes', README.md:261 '13 curated classes', README.md:122/262 '319 passed'/'319 tests passing', docs/INSTALL.md '319 passed'/'319 tests', scripts/test-count.txt=319; len(SEED_CLASSES)=13 verified via python3. Command evidence: `sh scripts/check-test-count.sh` exit_code=0 -> 'PASS: test-count guard: canonical=319 matches live=319; class-count=13; no stale count literals in living docs'; `uv run pytest -q --tb=short` exit_code=0 -> '319 passed in 0.94s'; `uv run pytest tests/test_count_guard.py -q` exit_code=0 -> '12 passed'; `uv run ruff check .` exit_code=0 -> 'All checks passed!'; `uv run ruff format --check .` exit_code=0 -> '93 files already formatted'.
The count-sync guard now derives len(SEED_CLASSES) and flags stale failure-class/curated-class literals, with 12 passing regression tests, synced README/INSTALL docs, and green pytest (319 passed) and ruff.

Overall: PASS ✓
