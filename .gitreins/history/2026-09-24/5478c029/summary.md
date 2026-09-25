# Verdict: LORE-008

**Task:** Absorb-gate on close requires lesson decision
**Evaluated:** 2026-09-24T15:54:23.647115
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Closure flow enforces a machine-checked choice: lore absorb proposal OR explicit no-new-lesson ack with reason; both machine-checkable: lore/absorb.py:88-113 validate_close_decision enforces the two-branch choice: decision must be in {absorb,no-new-lesson}; 'absorb' requires non-empty class_id + lesson AND class_id present in the closed registry (get_registry().get(class_id) is None -> error), yielding a proposal payload via absorb_proposal (lore/absorb.py:118-132, propose-not-write/stdout only); 'no-new-lesson' requires a non-empty reason (_ERR_NO_REASON). Returns GateVerdict(allowed=not errors) — a machine-checkable boolean + error list. lore/__main__.py:184-201 _cmd_gate maps allowed->exit 0, denied->exit 1, and argparse choices=(DECISION_ABSORB,DECISION_NO_NEW_LESSON) rejects invalid words. Live CLI evidence: `lore gate --decision absorb --class gateway-drain-window --lesson 'drain first'` -> 'GATE: ALLOW (absorb -> gateway-drain-window)' exit=0; `--decision no-new-lesson` (no reason) -> 'GATE: DENY (1 errors) / error: no-new-lesson requires a reason' exit=1; `--decision no-new-lesson --reason 'routine redeploy'` -> ALLOW exit=0; `--decision absorb --class nope --lesson x` -> DENY unknown class exit=1; `--decision absorb --class gateway-drain-window` (no lesson) -> DENY 'absorb requires a lesson' exit=1; `--decision bogus` -> argparse invalid choice. Tests: `uv run pytest -x --tb=short` -> 187 passed in 0.23s (tests/test_absorb.py 17 tests covering CLI exit codes, closed-registry refusal, missing reason/lesson, multi-violation verdicts, and the propose-not-write guard). LSP diagnostics: 0.
The closure gate enforces a machine-checked absorb-or-no-new-lesson decision with exit-code/boolean verdicts, verified by passing tests and live CLI runs.

## Summary

Judge Result: LORE-008

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Closure flow enforces a machine-checked choice: lore absorb proposal OR explicit no-new-lesson ack with reason; both machine-checkable: lore/absorb.py:88-113 validate_close_decision enforces the two-branch choice: decision must be in {absorb,no-new-lesson}; 'absorb' requires non-empty class_id + lesson AND class_id present in the closed registry (get_registry().get(class_id) is None -> error), yielding a proposal payload via absorb_proposal (lore/absorb.py:118-132, propose-not-write/stdout only); 'no-new-lesson' requires a non-empty reason (_ERR_NO_REASON). Returns GateVerdict(allowed=not errors) — a machine-checkable boolean + error list. lore/__main__.py:184-201 _cmd_gate maps allowed->exit 0, denied->exit 1, and argparse choices=(DECISION_ABSORB,DECISION_NO_NEW_LESSON) rejects invalid words. Live CLI evidence: `lore gate --decision absorb --class gateway-drain-window --lesson 'drain first'` -> 'GATE: ALLOW (absorb -> gateway-drain-window)' exit=0; `--decision no-new-lesson` (no reason) -> 'GATE: DENY (1 errors) / error: no-new-lesson requires a reason' exit=1; `--decision no-new-lesson --reason 'routine redeploy'` -> ALLOW exit=0; `--decision absorb --class nope --lesson x` -> DENY unknown class exit=1; `--decision absorb --class gateway-drain-window` (no lesson) -> DENY 'absorb requires a lesson' exit=1; `--decision bogus` -> argparse invalid choice. Tests: `uv run pytest -x --tb=short` -> 187 passed in 0.23s (tests/test_absorb.py 17 tests covering CLI exit codes, closed-registry refusal, missing reason/lesson, multi-violation verdicts, and the propose-not-write guard). LSP diagnostics: 0.
The closure gate enforces a machine-checked absorb-or-no-new-lesson decision with exit-code/boolean verdicts, verified by passing tests and live CLI runs.

Overall: PASS ✓
