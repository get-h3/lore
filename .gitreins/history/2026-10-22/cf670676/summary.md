# Verdict: LORE-060-R2

**Task:** scope logsey check claims with fresh-index precondition
**Evaluated:** 2026-10-22T17:03:12.739818
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ README.md:366-370 and CHANGELOG.md:12-13 claims scoped with fresh-index precondition; fresh validate run quotes orders 1,7 ok exit 0: README.md:372-378 (the `lore validate` bullet in the cited 366-370 region) now scopes the claim: "Executed checks grade the runbook against the live box's logsey index state: with a stale-or-missing logsey index, logsey's JSONL corpus-fallback engine rejects indexed SQL with exit 4 (`unsupported predicate`) and those orders record `error` (the class flips `stale` with reason `lint drift: check N (error)`); that signal is index drift, not runbook drift — `logsey index rebuild` (then re-run the lint) restores `ok`." CHANGELOG.md:35-47 LORE-060 entry carries the same precondition: "`validate --execute` now reports both checks `ok` (exit 0) ... — with a FRESH logsey index; on a stale-or-missing index logsey serves the JSONL corpus fallback, which rejects the indexed SQL with exit 4 (`unsupported predicate`) and the checks record `error` (LORE-060-R2: index drift, not runbook drift — `logsey index rebuild`, then re-run the lint, restores `ok`)" (the LORE-060 entry sits at 35-47, not the cited 12-13, but the required fresh-index scoping text is present). LIVE EVIDENCE for "fresh validate run quotes orders 1,7 ok exit 0": `uv run lore validate --execute` -> EXIT=0, gateway-drain-window executed_orders [1, 7], drifted_orders [], env_absent_orders [], stale_reason None, order 1 outcome ok exit 0, order 7 outcome ok exit 0. Direct logsey queries on the fresh index also exit 0 (order 1 -> 0 rows; order 7 -> rows). Stale-index half of the claim independently reproduced: `logsey --corpus-dir /tmp/staleidx query "<order 1 SQL>"` (corpus copied without index.duckdb) -> "error: unsupported predicate ... corpus JSONL fallback", REAL_EXIT=4, matching the doc text; `lint drift: check N (error)` format confirmed at lore/validate.py:1095. Test suite: `uv run pytest -x --tb=short -q` -> "560 passed in 11.70s", exit 0.
Both docs now scope the logsey check claims with the fresh-index precondition, and a live `lore validate --execute` reproduces orders 1 and 7 as ok exit 0 with empty drifted_orders, while the stale-index exit-4 fallback behavior is independently confirmed.

## Summary

Judge Result: LORE-060-R2

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ README.md:366-370 and CHANGELOG.md:12-13 claims scoped with fresh-index precondition; fresh validate run quotes orders 1,7 ok exit 0: README.md:372-378 (the `lore validate` bullet in the cited 366-370 region) now scopes the claim: "Executed checks grade the runbook against the live box's logsey index state: with a stale-or-missing logsey index, logsey's JSONL corpus-fallback engine rejects indexed SQL with exit 4 (`unsupported predicate`) and those orders record `error` (the class flips `stale` with reason `lint drift: check N (error)`); that signal is index drift, not runbook drift — `logsey index rebuild` (then re-run the lint) restores `ok`." CHANGELOG.md:35-47 LORE-060 entry carries the same precondition: "`validate --execute` now reports both checks `ok` (exit 0) ... — with a FRESH logsey index; on a stale-or-missing index logsey serves the JSONL corpus fallback, which rejects the indexed SQL with exit 4 (`unsupported predicate`) and the checks record `error` (LORE-060-R2: index drift, not runbook drift — `logsey index rebuild`, then re-run the lint, restores `ok`)" (the LORE-060 entry sits at 35-47, not the cited 12-13, but the required fresh-index scoping text is present). LIVE EVIDENCE for "fresh validate run quotes orders 1,7 ok exit 0": `uv run lore validate --execute` -> EXIT=0, gateway-drain-window executed_orders [1, 7], drifted_orders [], env_absent_orders [], stale_reason None, order 1 outcome ok exit 0, order 7 outcome ok exit 0. Direct logsey queries on the fresh index also exit 0 (order 1 -> 0 rows; order 7 -> rows). Stale-index half of the claim independently reproduced: `logsey --corpus-dir /tmp/staleidx query "<order 1 SQL>"` (corpus copied without index.duckdb) -> "error: unsupported predicate ... corpus JSONL fallback", REAL_EXIT=4, matching the doc text; `lint drift: check N (error)` format confirmed at lore/validate.py:1095. Test suite: `uv run pytest -x --tb=short -q` -> "560 passed in 11.70s", exit 0.
Both docs now scope the logsey check claims with the fresh-index precondition, and a live `lore validate --execute` reproduces orders 1 and 7 as ok exit 0 with empty drifted_orders, while the stale-index exit-4 fallback behavior is independently confirmed.

Overall: PASS ✓
