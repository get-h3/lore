# Verdict: LORE-024

**Task:** Template outcome for placeholder checks in validate --execute
**Evaluated:** 2026-09-25T19:10:21.938687
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Placeholder checks report template outcome without executing; template alone never flips a class stale; uv run pytest -q green: lore/validate.py:151 defines OUTCOME_TEMPLATE='template', added to OUTCOME_VOCABULARY (:133-141) but NOT to DRIFT_OUTCOMES (:144). lint_runbook (:750-755) sets outcome=OUTCOME_TEMPLATE with a fill-me stderr message and never calls the runner for such checks. _unfilled_placeholder_token (:659-661) is quote-aware via _unquoted (:216) — verified '<key-name>' inside quotes returns None while bare <main-tree> is detected. Runtime check on gateway-drain-window: 5 template results, all exit_code None, runner invoked only for the 2 real checks; apply_lint returned status 'proposal' with stale_reason None (template alone never flips stale). tests/test_validate.py:325 (test_apply_lint_template_outcome_never_flips_stale) and :343 (template + real error still flips stale) cover both directions. `uv run pytest -q` -> exit_code 0, '282 passed in 0.24s'.
Placeholder checks are reported as a non-drift 'template' outcome without execution, template alone never flips a class stale, and the full suite passes (282 passed).

## Summary

Judge Result: LORE-024

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Placeholder checks report template outcome without executing; template alone never flips a class stale; uv run pytest -q green: lore/validate.py:151 defines OUTCOME_TEMPLATE='template', added to OUTCOME_VOCABULARY (:133-141) but NOT to DRIFT_OUTCOMES (:144). lint_runbook (:750-755) sets outcome=OUTCOME_TEMPLATE with a fill-me stderr message and never calls the runner for such checks. _unfilled_placeholder_token (:659-661) is quote-aware via _unquoted (:216) — verified '<key-name>' inside quotes returns None while bare <main-tree> is detected. Runtime check on gateway-drain-window: 5 template results, all exit_code None, runner invoked only for the 2 real checks; apply_lint returned status 'proposal' with stale_reason None (template alone never flips stale). tests/test_validate.py:325 (test_apply_lint_template_outcome_never_flips_stale) and :343 (template + real error still flips stale) cover both directions. `uv run pytest -q` -> exit_code 0, '282 passed in 0.24s'.
Placeholder checks are reported as a non-drift 'template' outcome without execution, template alone never flips a class stale, and the full suite passes (282 passed).

Overall: PASS ✓
