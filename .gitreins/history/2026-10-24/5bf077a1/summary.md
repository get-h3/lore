# Verdict: LORE-20261011

**Task:** Fix absorb unknown-class exit code
**Evaluated:** 2026-10-24T23:25:36.122702
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ Unknown absorb class exits 2 while valid class exits 0 and preserves error output: lore/__main__.py:442-443 now does `payload = absorb_proposal(...); print(json.dumps(payload, indent=2)); return 2 if "error" in payload else 0`; lore/absorb.py:296-299 returns {"error": "unknown class '<id>'"} on KeyError. Live CLI verification: `uv run python -m lore absorb --class nope-class --lesson x` printed {"error": "unknown class 'nope-class'"} and EXIT_UNKNOWN=2; `uv run python -m lore absorb --class gateway-drain-window --lesson x` gave EXIT_VALID=0 with payload class_id=gateway-drain-window and empty stderr — error output is preserved (still emitted as the stdout JSON payload, matching the propose-not-write contract). Tests: `uv run pytest tests/test_lore016_qa_audit.py -x --tb=short` -> 21 passed in 0.24s; full suite `uv run pytest -x --tb=short` -> 562 passed in 4.78s (exit_code 0). New test tests/test_lore016_qa_audit.py:130-149 asserts unknown==2, valid==0, and match unknown==2 with stderr message. Behavior also matches documented convention in docs/dogfood/diagnostics.md:12 ('unknown class is a KeyError -> exit 2').
The absorb CLI now returns exit 2 for an unknown class and 0 for a valid class while still printing the error payload, verified by direct CLI runs and a fully green 562-test suite.

## Summary

Judge Result: LORE-20261011

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ Unknown absorb class exits 2 while valid class exits 0 and preserves error output: lore/__main__.py:442-443 now does `payload = absorb_proposal(...); print(json.dumps(payload, indent=2)); return 2 if "error" in payload else 0`; lore/absorb.py:296-299 returns {"error": "unknown class '<id>'"} on KeyError. Live CLI verification: `uv run python -m lore absorb --class nope-class --lesson x` printed {"error": "unknown class 'nope-class'"} and EXIT_UNKNOWN=2; `uv run python -m lore absorb --class gateway-drain-window --lesson x` gave EXIT_VALID=0 with payload class_id=gateway-drain-window and empty stderr — error output is preserved (still emitted as the stdout JSON payload, matching the propose-not-write contract). Tests: `uv run pytest tests/test_lore016_qa_audit.py -x --tb=short` -> 21 passed in 0.24s; full suite `uv run pytest -x --tb=short` -> 562 passed in 4.78s (exit_code 0). New test tests/test_lore016_qa_audit.py:130-149 asserts unknown==2, valid==0, and match unknown==2 with stderr message. Behavior also matches documented convention in docs/dogfood/diagnostics.md:12 ('unknown class is a KeyError -> exit 2').
The absorb CLI now returns exit 2 for an unknown class and 0 for a valid class while still printing the error payload, verified by direct CLI runs and a fully green 562-test suite.

Overall: PASS ✓
