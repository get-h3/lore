# Verdict: README-8

**Task:** Correct INSTALL shipped validate status
**Evaluated:** 2026-10-28T22:06:37.678830
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ PASS: docs/INSTALL.md no longer calls shipped lore validate lint in flight; grep -c LORE-006 is 1 and uv run lore validate --help exits 0; ch:trace row=README-8 resolves in committed board row.: All four sub-conditions verified. (1) No 'in flight' language remains: `git show HEAD:docs/INSTALL.md | grep -n -i "in flight"` returns no matches (exit 1); HEAD lines 416-418 now read 'The read-only command lint ships today as `lore validate`; what is absent is only the weekly *schedule*...'. Commit 01f3821 'docs: correct INSTALL validate status. Addresses README-8.' diff confirms removal of 'in flight (`LORE-006`)'. (2) `grep -c LORE-006 docs/INSTALL.md` -> 1 (and `git show HEAD:docs/INSTALL.md | grep -c LORE-006` -> 1); the sole survivor is line 129, the accurate --help block 'validate  read-only command lint (LORE-006). DEFAULT = plan/dry-'. (3) `uv run lore validate --help` -> EXIT_CODE=0, printing usage with --class/--format/--execute. (4) ch:trace row resolves in the committed board: `.coding-hermes/board/tasks.jsonl` is git-tracked, and `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -c "ch:trace row=README-8"` -> 2; the README-8 row's reasoning field contains 'ch:trace row=README-8 spec=docs/INSTALL.md wave=none:serial-doc-lane test=none:doc-status-claim doc=docs/INSTALL.md#L413 evidence=... verdict=none:not-judged commit=none:row-filed-before-fix memory=/project/lore/readme-sweep-2026-10-19'. Test suite per .gitreins/config.yaml test_command: `uv run pytest -x --tb=short -q` -> '566 passed in 10.99s', EXIT_CODE=0.
docs/INSTALL.md now correctly states the read-only lint ships as `lore validate` with only the weekly schedule absent, grep -c LORE-006 is 1, `uv run lore validate --help` exits 0, the ch:trace row=README-8 marker is present in the committed board row, and the full suite passes (566 passed, exit 0).

## Summary

Judge Result: README-8

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ PASS: docs/INSTALL.md no longer calls shipped lore validate lint in flight; grep -c LORE-006 is 1 and uv run lore validate --help exits 0; ch:trace row=README-8 resolves in committed board row.: All four sub-conditions verified. (1) No 'in flight' language remains: `git show HEAD:docs/INSTALL.md | grep -n -i "in flight"` returns no matches (exit 1); HEAD lines 416-418 now read 'The read-only command lint ships today as `lore validate`; what is absent is only the weekly *schedule*...'. Commit 01f3821 'docs: correct INSTALL validate status. Addresses README-8.' diff confirms removal of 'in flight (`LORE-006`)'. (2) `grep -c LORE-006 docs/INSTALL.md` -> 1 (and `git show HEAD:docs/INSTALL.md | grep -c LORE-006` -> 1); the sole survivor is line 129, the accurate --help block 'validate  read-only command lint (LORE-006). DEFAULT = plan/dry-'. (3) `uv run lore validate --help` -> EXIT_CODE=0, printing usage with --class/--format/--execute. (4) ch:trace row resolves in the committed board: `.coding-hermes/board/tasks.jsonl` is git-tracked, and `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -c "ch:trace row=README-8"` -> 2; the README-8 row's reasoning field contains 'ch:trace row=README-8 spec=docs/INSTALL.md wave=none:serial-doc-lane test=none:doc-status-claim doc=docs/INSTALL.md#L413 evidence=... verdict=none:not-judged commit=none:row-filed-before-fix memory=/project/lore/readme-sweep-2026-10-19'. Test suite per .gitreins/config.yaml test_command: `uv run pytest -x --tb=short -q` -> '566 passed in 10.99s', EXIT_CODE=0.
docs/INSTALL.md now correctly states the read-only lint ships as `lore validate` with only the weekly schedule absent, grep -c LORE-006 is 1, `uv run lore validate --help` exits 0, the ch:trace row=README-8 marker is present in the committed board row, and the full suite passes (566 passed, exit 0).

Overall: PASS ✓
