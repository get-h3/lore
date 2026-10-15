# Verdict: LORE-052

**Task:** validate --execute: process substitution + missing files flip classes stale
**Evaluated:** 2026-10-14T00:18:50.458308
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ In /home/kara/get-h3/lore: (1) validate --execute no longer hard-fails on process substitution: runbook checks invoking bash-specific syntax execute under a bash-capable shell or classify honestly (not /bin/sh syntax error); (2) a check whose target FILE is missing classifies env-absent (or an explicit env-missing outcome), NOT error, and does not flip the class stale on the author's own box; (3) env_absent_orders is populated for those checks; (4) uv run pytest -q green, uv run ruff check . clean, guard passes: (1) lore/validate.py:246-289 _default_runner now resolves _bash_path() (/bin/bash) and runs [bash,'-c',command], falling back to shell=True only when bash is absent. Real execution: `_default_runner('diff <(echo a) <(echo a) && echo IDENTICAL')` -> rc=0, stdout 'IDENTICAL'; the old path `/bin/sh -c 'diff <(echo a) <(echo a)'` -> exit 2 'Syntax error: "(" unexpected'. Curated class secret-env-clobber check 2 (`diff <(grep -o '^[A-Z_]*' .env | sort) <(grep -o '^[A-Z_]*' .env.example | sort)`) now classifies 'ok' (was a shell syntax error). (2) lore/validate.py:814-870 _missing_target_file (conjunction: rc!=0, stderr file-not-found signal, command references the missing name/path) + _classify:863 routes to OUTCOME_ENV_ABSENT. End-to-end on curated class cooldown-pin-drift from a cwd without fleet.toml: check 2 outcome='env-absent', stale_reason=None, apply_lint(report, rb).status == rb.status ('proposal', no stale flip). (3) Same run: report.env_absent_orders == [2]; synthetic missing-file test yields env_absent_orders == [1]. (4) `uv run pytest -q` -> '426 passed in 1.94s' (exit 0); `uv run ruff check .` -> 'All checks passed!' (exit 0); `gitreins guard --full` -> 'Tier 1 Guards: PASS' (secrets clean, lint ok, tests full); `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=426 matches live=426'. LSP diagnostics: 0 findings.


## Summary

Judge Result: LORE-052

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ In /home/kara/get-h3/lore: (1) validate --execute no longer hard-fails on process substitution: runbook checks invoking bash-specific syntax execute under a bash-capable shell or classify honestly (not /bin/sh syntax error); (2) a check whose target FILE is missing classifies env-absent (or an explicit env-missing outcome), NOT error, and does not flip the class stale on the author's own box; (3) env_absent_orders is populated for those checks; (4) uv run pytest -q green, uv run ruff check . clean, guard passes: (1) lore/validate.py:246-289 _default_runner now resolves _bash_path() (/bin/bash) and runs [bash,'-c',command], falling back to shell=True only when bash is absent. Real execution: `_default_runner('diff <(echo a) <(echo a) && echo IDENTICAL')` -> rc=0, stdout 'IDENTICAL'; the old path `/bin/sh -c 'diff <(echo a) <(echo a)'` -> exit 2 'Syntax error: "(" unexpected'. Curated class secret-env-clobber check 2 (`diff <(grep -o '^[A-Z_]*' .env | sort) <(grep -o '^[A-Z_]*' .env.example | sort)`) now classifies 'ok' (was a shell syntax error). (2) lore/validate.py:814-870 _missing_target_file (conjunction: rc!=0, stderr file-not-found signal, command references the missing name/path) + _classify:863 routes to OUTCOME_ENV_ABSENT. End-to-end on curated class cooldown-pin-drift from a cwd without fleet.toml: check 2 outcome='env-absent', stale_reason=None, apply_lint(report, rb).status == rb.status ('proposal', no stale flip). (3) Same run: report.env_absent_orders == [2]; synthetic missing-file test yields env_absent_orders == [1]. (4) `uv run pytest -q` -> '426 passed in 1.94s' (exit 0); `uv run ruff check .` -> 'All checks passed!' (exit 0); `gitreins guard --full` -> 'Tier 1 Guards: PASS' (secrets clean, lint ok, tests full); `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=426 matches live=426'. LSP diagnostics: 0 findings.


Overall: PASS ✓
