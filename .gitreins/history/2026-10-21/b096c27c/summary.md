# Verdict: LORE-061

**Task:** env_absent orders surfaced in validate output and audit table/json/md
**Evaluated:** 2026-10-21T17:01:47.421716
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ Tier 1: uv run pytest -q passes with new tests, ruff check/format clean, check-test-count.sh PASS. Tier 2: (1) uv run python -m lore validate --class gateway-drain-window --execute plain-text output includes an env_absent: checks N,M line for any checks that classified as env-absent. (2) uv run python -m lore audit --format json includes an env_absent_orders field on any class whose history record carries env_absent orders. (3) uv run python -m lore audit --format table and --format md each render the env_absent column. (4) When env_absent_orders is empty, the field does not appear in JSON output.: Tier 1: `uv run pytest -q` -> "531 passed in 5.44s" (exit 0), including new tests/test_lore061_env_absent_rendering.py; `uv run ruff check .` -> "All checks passed!" (exit 0); `uv run ruff format --check .` -> "208 files already formatted" (exit 0); `bash scripts/check-test-count.sh` -> "PASS: test-count guard: canonical=531 matches live=531; class-count=13" (exit 0). Tier 2 (1): lore/__main__.py:358-362 prints `  env_absent: checks {', '.join(orders)} did not run (tool or file absent on this box — not drift)` in the plain-text branch of _cmd_validate; direct invocation with a mocked report containing an env-absent check produced "env_absent: checks 3 did not run (tool or file absent on this box — not drift)" (the live gateway-drain-window run shows no such line only because that class has env_absent_orders: []). (2): lore/__main__.py:617-622 attaches row["env_absent_orders"] from the history record; mocked `_cmd_audit(format='json')` emitted "env_absent_orders": [1, 3]. (3): table header "env_absent" at lore/__main__.py:704 with value at :717, md header "| env_absent |" at :671 with value at :678; mocked runs rendered "t T - True 3 3 no data proposal [1, 3]" (table) and "| t | T | True | 3 | 3 | no data | proposal | [1, 3] |  |" (md), and live `audit --format table`/`--format md` both show the env_absent column. (4): with env_absent_orders=[] the JSON output omits the field (verified 'env_absent_orders' in output == False), guarded by `if env_absent:` at lore/__main__.py:620 and covered by test_audit_json_without_env_absent_no_field.
All Tier 1 gates pass (531 tests, ruff check/format clean, test-count guard PASS) and all four Tier 2 behaviors are implemented and verified by direct invocation.

## Summary

Judge Result: LORE-061

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ Tier 1: uv run pytest -q passes with new tests, ruff check/format clean, check-test-count.sh PASS. Tier 2: (1) uv run python -m lore validate --class gateway-drain-window --execute plain-text output includes an env_absent: checks N,M line for any checks that classified as env-absent. (2) uv run python -m lore audit --format json includes an env_absent_orders field on any class whose history record carries env_absent orders. (3) uv run python -m lore audit --format table and --format md each render the env_absent column. (4) When env_absent_orders is empty, the field does not appear in JSON output.: Tier 1: `uv run pytest -q` -> "531 passed in 5.44s" (exit 0), including new tests/test_lore061_env_absent_rendering.py; `uv run ruff check .` -> "All checks passed!" (exit 0); `uv run ruff format --check .` -> "208 files already formatted" (exit 0); `bash scripts/check-test-count.sh` -> "PASS: test-count guard: canonical=531 matches live=531; class-count=13" (exit 0). Tier 2 (1): lore/__main__.py:358-362 prints `  env_absent: checks {', '.join(orders)} did not run (tool or file absent on this box — not drift)` in the plain-text branch of _cmd_validate; direct invocation with a mocked report containing an env-absent check produced "env_absent: checks 3 did not run (tool or file absent on this box — not drift)" (the live gateway-drain-window run shows no such line only because that class has env_absent_orders: []). (2): lore/__main__.py:617-622 attaches row["env_absent_orders"] from the history record; mocked `_cmd_audit(format='json')` emitted "env_absent_orders": [1, 3]. (3): table header "env_absent" at lore/__main__.py:704 with value at :717, md header "| env_absent |" at :671 with value at :678; mocked runs rendered "t T - True 3 3 no data proposal [1, 3]" (table) and "| t | T | True | 3 | 3 | no data | proposal | [1, 3] |  |" (md), and live `audit --format table`/`--format md` both show the env_absent column. (4): with env_absent_orders=[] the JSON output omits the field (verified 'env_absent_orders' in output == False), guarded by `if env_absent:` at lore/__main__.py:620 and covered by test_audit_json_without_env_absent_no_field.
All Tier 1 gates pass (531 tests, ruff check/format clean, test-count guard PASS) and all four Tier 2 behaviors are implemented and verified by direct invocation.

Overall: PASS ✓
