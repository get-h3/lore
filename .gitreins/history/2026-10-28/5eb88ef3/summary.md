# Verdict: README-8

**Task:** Correct INSTALL shipped validate status
**Evaluated:** 2026-10-28T21:55:26.730619
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ PASS: docs/INSTALL.md no longer calls shipped lore validate lint in flight; grep -c LORE-006 is 1 and uv run lore validate --help exits 0; ch:trace row=README-8 resolves in committed board row.: All four sub-checks verified. (1) Commit 01f3821 diff at docs/INSTALL.md:417-419 replaced 'The weekly read-only command lint that would flip stale runbooks is in flight (`LORE-006`)' with 'The read-only command lint ships today as `lore validate`; what is absent is only the weekly *schedule* that would run it on a calendar — nothing runs on a schedule.'; `grep -i 'in flight' docs/INSTALL.md` returns no match. (2) `grep -c LORE-006 docs/INSTALL.md` -> 1 (exit 0), the sole survivor being the accurate help-text mention at line 129 'validate read-only command lint (LORE-006). DEFAULT = plan/dry-'. (3) `uv run lore validate --help` -> EXIT=0, output 'usage: lore validate [-h] [--class CLASS_ID] [--format {json,md}] [--execute]'. (4) ch:trace row=README-8 resolves in the committed board row: .coding-hermes/board/tasks.jsonl line 102 (id=README-8) reasoning contains 'ch:trace row=README-8 spec=docs/INSTALL.md ... doc=docs/INSTALL.md#L413'; the file is tracked and clean (`git status --porcelain` empty) and `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -c 'ch:trace row=README-8 '` -> 1, proving the marker is in the committed blob. Test suite also green: `uv run pytest -x --tb=short -q` -> EXIT=0, '566 passed in 5.02s'.
docs/INSTALL.md now correctly states the read-only lint ships as `lore validate` with only the weekly schedule absent, grep -c LORE-006 is 1, `uv run lore validate --help` exits 0, the ch:trace row=README-8 marker is present in the committed board row, and the full suite passes (566 passed, exit 0).

## Summary

Judge Result: README-8

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ PASS: docs/INSTALL.md no longer calls shipped lore validate lint in flight; grep -c LORE-006 is 1 and uv run lore validate --help exits 0; ch:trace row=README-8 resolves in committed board row.: All four sub-checks verified. (1) Commit 01f3821 diff at docs/INSTALL.md:417-419 replaced 'The weekly read-only command lint that would flip stale runbooks is in flight (`LORE-006`)' with 'The read-only command lint ships today as `lore validate`; what is absent is only the weekly *schedule* that would run it on a calendar — nothing runs on a schedule.'; `grep -i 'in flight' docs/INSTALL.md` returns no match. (2) `grep -c LORE-006 docs/INSTALL.md` -> 1 (exit 0), the sole survivor being the accurate help-text mention at line 129 'validate read-only command lint (LORE-006). DEFAULT = plan/dry-'. (3) `uv run lore validate --help` -> EXIT=0, output 'usage: lore validate [-h] [--class CLASS_ID] [--format {json,md}] [--execute]'. (4) ch:trace row=README-8 resolves in the committed board row: .coding-hermes/board/tasks.jsonl line 102 (id=README-8) reasoning contains 'ch:trace row=README-8 spec=docs/INSTALL.md ... doc=docs/INSTALL.md#L413'; the file is tracked and clean (`git status --porcelain` empty) and `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -c 'ch:trace row=README-8 '` -> 1, proving the marker is in the committed blob. Test suite also green: `uv run pytest -x --tb=short -q` -> EXIT=0, '566 passed in 5.02s'.
docs/INSTALL.md now correctly states the read-only lint ships as `lore validate` with only the weekly schedule absent, grep -c LORE-006 is 1, `uv run lore validate --help` exits 0, the ch:trace row=README-8 marker is present in the committed board row, and the full suite passes (566 passed, exit 0).

Overall: PASS ✓
