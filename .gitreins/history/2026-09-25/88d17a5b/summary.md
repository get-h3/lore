# Verdict: LORE-020

**Task:** absorb --window trail contract + --source plumbing
**Evaluated:** 2026-09-25T09:00:30.481258
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ --source flows into sweep proposals (omit = no source key); trail contract documented; regression tests RED-proven: Plumbing: lore/__main__.py:296-298 passes source=args.source into absorb_sweep; lore/absorb.py absorb_sweep(source=...) threads it to absorb_proposal(class_id, ..., source=source) and into proposal['sweep']['source'] + provenance['source']; absorb_proposal (lore/absorb.py:132-155) enforces the None-rule `if source is not None: payload['source'] = source`. Omit-rule: tests/test_lore020_absorb_window.py::test_cli_absorb_window_no_source_keeps_payload_shape asserts 'source' not in p — PASSED. Docs: docs/INSTALL.md:243 '### The `absorb` trail contract' (4-point contract + worked example) and README.md:283-291 ([--source S] + None-rule). RED-proof: reverting the __main__.py source= plumbing made test_cli_absorb_window_source_recorded_per_class FAIL with KeyError: 'source' at tests/test_lore020_absorb_window.py:41 (1 failed, 2 passed); restored -> `uv run pytest tests/test_lore020_absorb_window.py -v` = 3 passed. Full suite `uv run pytest -x --tb=short` = 269 passed in 0.24s (exit 0); working tree clean after restore.
--source is plumbed into every sweep proposal with the documented omit-None rule, the trail contract is documented in docs/INSTALL.md and README.md, and the regression tests are RED-proven and green (269 passed).

## Summary

Judge Result: LORE-020

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ --source flows into sweep proposals (omit = no source key); trail contract documented; regression tests RED-proven: Plumbing: lore/__main__.py:296-298 passes source=args.source into absorb_sweep; lore/absorb.py absorb_sweep(source=...) threads it to absorb_proposal(class_id, ..., source=source) and into proposal['sweep']['source'] + provenance['source']; absorb_proposal (lore/absorb.py:132-155) enforces the None-rule `if source is not None: payload['source'] = source`. Omit-rule: tests/test_lore020_absorb_window.py::test_cli_absorb_window_no_source_keeps_payload_shape asserts 'source' not in p — PASSED. Docs: docs/INSTALL.md:243 '### The `absorb` trail contract' (4-point contract + worked example) and README.md:283-291 ([--source S] + None-rule). RED-proof: reverting the __main__.py source= plumbing made test_cli_absorb_window_source_recorded_per_class FAIL with KeyError: 'source' at tests/test_lore020_absorb_window.py:41 (1 failed, 2 passed); restored -> `uv run pytest tests/test_lore020_absorb_window.py -v` = 3 passed. Full suite `uv run pytest -x --tb=short` = 269 passed in 0.24s (exit 0); working tree clean after restore.
--source is plumbed into every sweep proposal with the documented omit-None rule, the trail contract is documented in docs/INSTALL.md and README.md, and the regression tests are RED-proven and green (269 passed).

Overall: PASS ✓
