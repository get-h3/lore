# Verdict: LORE-007

**Task:** Tick-start consult attaches matching runbook refs
**Evaluated:** 2026-09-24T15:54:03.801704
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Given a task title/detail, lore matches failure-class signatures and returns matching runbook refs cheaply and fail-open; no match means no behavior change: lore/consult.py: consult(text) runs one classify() pass (lore/classifier.py:111) and, when confidence>0.0, unions classify_all() matches best-first capped at MAX_MATCHED_CLASSES=3, attaching light refs built by _runbook_ref() (class_id/name/status/last_validated/check_count only, no payload). Fail-open: _runbook_ref wraps compile_class in `except Exception: return None` (lore/consult.py:67-69) so a broken compile omits the ref but keeps the match; no-match (confidence<=0.0) returns empty ConsultResult with no exception/side effects. consult_task(title, detail) classifies title+detail (lore/consult.py:118-125). CLI `lore consult` (lore/__main__.py:78-99) prints 'no matching runbook' and exits 0 on no-match. Cheap: elapsed_ms measured via perf_counter; manual runs gave 0.08-1.7ms. Evidence: `uv run pytest tests/test_consult.py -q` -> '13 passed in 0.02s'; full suite `uv run pytest -q` -> '187 passed in 0.13s'. Manual: consult('coffee machine broken') -> {'matched': False, 'matched_classes': [], 'runbook_refs': []}; consult_task('tick title','in-flight requests 503 while gateway restarts') -> matched True, ['gateway-drain-window'] with ref check_count=3; monkeypatched compile_class raising RuntimeError -> matched True, runbook_refs [], exit 0.
Tick-start consult matches failure-class signatures and returns light runbook refs cheaply and fail-open, with no behavior change on no-match; all 187 tests pass.

## Summary

Judge Result: LORE-007

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Given a task title/detail, lore matches failure-class signatures and returns matching runbook refs cheaply and fail-open; no match means no behavior change: lore/consult.py: consult(text) runs one classify() pass (lore/classifier.py:111) and, when confidence>0.0, unions classify_all() matches best-first capped at MAX_MATCHED_CLASSES=3, attaching light refs built by _runbook_ref() (class_id/name/status/last_validated/check_count only, no payload). Fail-open: _runbook_ref wraps compile_class in `except Exception: return None` (lore/consult.py:67-69) so a broken compile omits the ref but keeps the match; no-match (confidence<=0.0) returns empty ConsultResult with no exception/side effects. consult_task(title, detail) classifies title+detail (lore/consult.py:118-125). CLI `lore consult` (lore/__main__.py:78-99) prints 'no matching runbook' and exits 0 on no-match. Cheap: elapsed_ms measured via perf_counter; manual runs gave 0.08-1.7ms. Evidence: `uv run pytest tests/test_consult.py -q` -> '13 passed in 0.02s'; full suite `uv run pytest -q` -> '187 passed in 0.13s'. Manual: consult('coffee machine broken') -> {'matched': False, 'matched_classes': [], 'runbook_refs': []}; consult_task('tick title','in-flight requests 503 while gateway restarts') -> matched True, ['gateway-drain-window'] with ref check_count=3; monkeypatched compile_class raising RuntimeError -> matched True, runbook_refs [], exit 0.
Tick-start consult matches failure-class signatures and returns light runbook refs cheaply and fail-open, with no behavior change on no-match; all 187 tests pass.

Overall: PASS ✓
