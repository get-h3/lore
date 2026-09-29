# Verdict: DOC-3

**Task:** gate flags --decided-at and --ref undocumented
**Evaluated:** 2026-09-29T03:15:51.316606
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ README.md documents both flags with semantics and example shows --ref: README.md:229-233 documents both flags with semantics: '--ref <board-row-or-incident-id> carries the row/incident id the decision closes, and --decided-at <ISO-8601> records when it was decided — never invented when omitted.' The example at line 232-233 shows --ref: `lore gate --decision no-new-lesson --reason "covered by v0.1 docs" --ref QA-LORE-2`. Semantics match the code (lore/__main__.py:605 --ref help='board row / incident id'; :607-612 --decided-at help='optional ISO-8601 timestamp (never invented when omitted)'). Example verified runnable: `uv run python -m lore gate --decision no-new-lesson --reason "covered by v0.1 docs" --ref QA-LORE-2` -> 'GATE: ALLOW (no-new-lesson)'. Test suite: `uv run pytest -x --tb=short` -> 325 passed in 1.71s (exit 0).
README.md documents both gate provenance flags with correct semantics and a runnable example that shows --ref; all 325 tests pass.

## Summary

Judge Result: DOC-3

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ README.md documents both flags with semantics and example shows --ref: README.md:229-233 documents both flags with semantics: '--ref <board-row-or-incident-id> carries the row/incident id the decision closes, and --decided-at <ISO-8601> records when it was decided — never invented when omitted.' The example at line 232-233 shows --ref: `lore gate --decision no-new-lesson --reason "covered by v0.1 docs" --ref QA-LORE-2`. Semantics match the code (lore/__main__.py:605 --ref help='board row / incident id'; :607-612 --decided-at help='optional ISO-8601 timestamp (never invented when omitted)'). Example verified runnable: `uv run python -m lore gate --decision no-new-lesson --reason "covered by v0.1 docs" --ref QA-LORE-2` -> 'GATE: ALLOW (no-new-lesson)'. Test suite: `uv run pytest -x --tb=short` -> 325 passed in 1.71s (exit 0).
README.md documents both gate provenance flags with correct semantics and a runnable example that shows --ref; all 325 tests pass.

Overall: PASS ✓
