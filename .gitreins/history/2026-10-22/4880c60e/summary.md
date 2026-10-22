# Verdict: PERF-2

**Task:** single-pass ledger read for lore audit
**Evaluated:** 2026-10-22T06:55:39.988667
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ lore audit completes <100ms CLI / ~50ms in-process budget at a 3161-row synthetic ledger with results identical to the multi-pass baseline; full suite+lint+format+count-guard green: PERF (independently measured at a 3165-row synthetic ledger, 14 classes x 226 batches + 1 arm): in-process _audit_rows mean=6.07ms max=6.48ms (budget ~50ms); real CLI subprocess `python -m lore audit --format json` mean=56.6ms median=56.1ms max=61.9ms (budget <100ms); warm main() mean=7.14ms. BASELINE EQUIVALENCE: loaded HEAD~1 lore/__main__.py + lore/validate.py (pre-change multi-pass) under aliases and diffed _audit_rows() output on a 3165-row ledger that also contained a torn line, a blank line and a non-dict line -> 'row count new/old: 14 14', 'rows identical: True'; batch==multipass per class True, 14 keys == 14 classes. IMPLEMENTATION: lore/validate.py:1230 last_local_validation_batch() scans once, keeps LAST record per class_id (newest by FILE ORDER, not max(timestamp)), skips blank/torn/non-dict/non-str-class_id, OSError->{}; lore/__main__.py:597 hoists `history = last_local_validation_batch(path=history_path)` out of the per-class loop and line 620 uses `history.get(rb.class_id)`; last_local_validation still used at __main__.py:76 (not dead). GATES (actual output): `uv run pytest -x --tb=short -q` exit 0 '544 passed in 4.59s'; `uv run pytest tests/test_perf2_audit_single_pass.py -v` exit 0 '8 passed in 0.23s' (incl. test_audit_cli_under_budget, test_audit_matches_multipass_rows, test_audit_cli_json_unchanged_vs_baseline); `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` exit 0 '213 files already formatted'; `bash scripts/check-test-count.sh` exit 0 'PASS: test-count guard: canonical=544 matches live=544; class-count=13; no stale count literals in living docs'. LSP diagnostics: 0. Docs count synced 536->544 across README/INSTALL/CONTRIBUTING/SKILL.md/scripts/test-count.txt; LORE-061 tests re-seamed to patch last_local_validation_batch.
Single-pass ledger read verified: 6.07ms in-process and 56.6ms CLI at a 3165-row ledger, output byte-identical to the pre-change multi-pass baseline, with 544 tests, ruff check/format and the count guard all green.

## Summary

Judge Result: PERF-2

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ lore audit completes <100ms CLI / ~50ms in-process budget at a 3161-row synthetic ledger with results identical to the multi-pass baseline; full suite+lint+format+count-guard green: PERF (independently measured at a 3165-row synthetic ledger, 14 classes x 226 batches + 1 arm): in-process _audit_rows mean=6.07ms max=6.48ms (budget ~50ms); real CLI subprocess `python -m lore audit --format json` mean=56.6ms median=56.1ms max=61.9ms (budget <100ms); warm main() mean=7.14ms. BASELINE EQUIVALENCE: loaded HEAD~1 lore/__main__.py + lore/validate.py (pre-change multi-pass) under aliases and diffed _audit_rows() output on a 3165-row ledger that also contained a torn line, a blank line and a non-dict line -> 'row count new/old: 14 14', 'rows identical: True'; batch==multipass per class True, 14 keys == 14 classes. IMPLEMENTATION: lore/validate.py:1230 last_local_validation_batch() scans once, keeps LAST record per class_id (newest by FILE ORDER, not max(timestamp)), skips blank/torn/non-dict/non-str-class_id, OSError->{}; lore/__main__.py:597 hoists `history = last_local_validation_batch(path=history_path)` out of the per-class loop and line 620 uses `history.get(rb.class_id)`; last_local_validation still used at __main__.py:76 (not dead). GATES (actual output): `uv run pytest -x --tb=short -q` exit 0 '544 passed in 4.59s'; `uv run pytest tests/test_perf2_audit_single_pass.py -v` exit 0 '8 passed in 0.23s' (incl. test_audit_cli_under_budget, test_audit_matches_multipass_rows, test_audit_cli_json_unchanged_vs_baseline); `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` exit 0 '213 files already formatted'; `bash scripts/check-test-count.sh` exit 0 'PASS: test-count guard: canonical=544 matches live=544; class-count=13; no stale count literals in living docs'. LSP diagnostics: 0. Docs count synced 536->544 across README/INSTALL/CONTRIBUTING/SKILL.md/scripts/test-count.txt; LORE-061 tests re-seamed to patch last_local_validation_batch.
Single-pass ledger read verified: 6.07ms in-process and 56.6ms CLI at a 3165-row ledger, output byte-identical to the pre-change multi-pass baseline, with 544 tests, ruff check/format and the count guard all green.

Overall: PASS ✓
