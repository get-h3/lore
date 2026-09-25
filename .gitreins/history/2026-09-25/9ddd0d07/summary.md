# Verdict: LORE-027

**Task:** INSTALL scope note: validate --execute reports environment, not runbook health
**Evaluated:** 2026-09-25T18:21:48.441864
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ INSTALL.md documents what validate --execute assumes; uv run pytest -q green: docs/INSTALL.md:110-125 adds a '### What `validate --execute` assumes' section stating --execute runs gate-approved read-only commands on whatever box you invoke it from, requires real commands on PATH and a real checkout, and lists outcome classes (exit 127 = command not on box/environment, exit 128 = not a git repo, shell syntax errors naming a `<token>` = unfilled placeholders, everything else = genuine drift). This matches the implementation at lore/__main__.py:207-221 (explicit --execute runs gate-approved read-only commands and prints per-check exit codes). Tests: `uv run pytest -q` => '274 passed in 0.22s', exit_code 0.
INSTALL.md documents validate --execute's environment assumptions and outcome classes, and the full test suite passes (274 passed).

## Summary

Judge Result: LORE-027

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ INSTALL.md documents what validate --execute assumes; uv run pytest -q green: docs/INSTALL.md:110-125 adds a '### What `validate --execute` assumes' section stating --execute runs gate-approved read-only commands on whatever box you invoke it from, requires real commands on PATH and a real checkout, and lists outcome classes (exit 127 = command not on box/environment, exit 128 = not a git repo, shell syntax errors naming a `<token>` = unfilled placeholders, everything else = genuine drift). This matches the implementation at lore/__main__.py:207-221 (explicit --execute runs gate-approved read-only commands and prints per-check exit codes). Tests: `uv run pytest -q` => '274 passed in 0.22s', exit_code 0.
INSTALL.md documents validate --execute's environment assumptions and outcome classes, and the full test suite passes (274 passed).

Overall: PASS ✓
