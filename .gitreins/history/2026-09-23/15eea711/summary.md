# Verdict: LORE-004

**Task:** Compiler — runbook generation per class
**Evaluated:** 2026-09-23T21:32:30.409727
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ tests: ============================= test session starts ==============================
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
- ✗ **tier2**
  - INCOMPLETE
  ✗ lore/compiler.py emits a Runbook per failure class: signature pattern, ordered checks (each with exact command/query, expected healthy vs incident output, and the decision it drives), recovery ladder with 'never X' guardrails, evidence trail (DuckBrain rows/board events/commits), and provenance + last_validated timestamp. Compiler output is a PROPOSAL, not a write (propose-not-write). Tests pass via pytest; ruff clean.: Tests: `uv run pytest -x --tb=short` -> 45 passed in 0.04s (exit 0). Ruff: `uv run ruff check .` -> "All checks passed!" exit 0.
Compiler: lore/compiler.py compile_class() builds Runbook with signature (signature_patterns[0]), checks (Check with order/command/expected_healthy/expected_incident/decision/read_only/evidence), recovery_ladder, guardrails ("Never X"), evidence_trail, provenance, last_validated (None unless attested), status=proposal. propose()/render_proposal_diff() are pure in-memory; test_no_publish_entrypoint asserts no open(/write_text/os.remove/shutil in module source; test_compile_does_not_touch_filesystem_writes_via_builtins monkeypatches builtins.open.

Partial verdict — evaluation hit resource cap before all criteria verified

## Summary

Judge Result: LORE-004

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ tests: ============================= test session starts ==============================
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)

Stage tier2: FAIL
  INCOMPLETE
  ✗ lore/compiler.py emits a Runbook per failure class: signature pattern, ordered checks (each with exact command/query, expected healthy vs incident output, and the decision it drives), recovery ladder with 'never X' guardrails, evidence trail (DuckBrain rows/board events/commits), and provenance + last_validated timestamp. Compiler output is a PROPOSAL, not a write (propose-not-write). Tests pass via pytest; ruff clean.: Tests: `uv run pytest -x --tb=short` -> 45 passed in 0.04s (exit 0). Ruff: `uv run ruff check .` -> "All checks passed!" exit 0.
Compiler: lore/compiler.py compile_class() builds Runbook with signature (signature_patterns[0]), checks (Check with order/command/expected_healthy/expected_incident/decision/read_only/evidence), recovery_ladder, guardrails ("Never X"), evidence_trail, provenance, last_validated (None unless attested), status=proposal. propose()/render_proposal_diff() are pure in-memory; test_no_publish_entrypoint asserts no open(/write_text/os.remove/shutil in module source; test_compile_does_not_touch_filesystem_writes_via_builtins monkeypatches builtins.open.

Partial verdict — evaluation hit resource cap before all criteria verified

Overall: FAIL ✗
