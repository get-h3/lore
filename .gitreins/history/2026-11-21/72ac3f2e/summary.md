# Verdict: RELEASE-LORE-010

**Task:** verify the v0.3.0 install channel
**Evaluated:** 2026-11-21T23:03:24.197732
**Result:** ✗ FAIL

## Criteria

- — **docs/qa/evidence/run-RELEASE-LORE-010/evidence.txt plus raw/{install,cli,metadata,negative}.txt record a COLD uv tool install of git+https://github.com/get-h3/lore@v0.3.0 exiting 0 with dist metadata and installed lore/__init__.py both at 0.3.0, the installed CLI run from a cwd outside any checkout exiting 0 and returning a classified match, and a nonexistent-tag negative arm exiting nonzero; the record names host, exact command, uv version and tag commit c769be4265e74a93b4706c6cc7971fe58a3f3dbd.**
  - Not examined — evaluation ended before this criterion was reached (no judgement was made about it)

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  — docs/qa/evidence/run-RELEASE-LORE-010/evidence.txt plus raw/{install,cli,metadata,negative}.txt record a COLD uv tool install of git+https://github.com/get-h3/lore@v0.3.0 exiting 0 with dist metadata and installed lore/__init__.py both at 0.3.0, the installed CLI run from a cwd outside any checkout exiting 0 and returning a classified match, and a nonexistent-tag negative arm exiting nonzero; the record names host, exact command, uv version and tag commit c769be4265e74a93b4706c6cc7971fe58a3f3dbd.: Not examined — evaluation ended before this criterion was reached (no judgement was made about it)
  ✗ Coverage FAILED — not passing: docs/qa/evidence/run-RELEASE-LORE-010/evidence.txt plus raw/{install,cli,metadata,negative}.txt record a COLD uv tool install of git+https://github.com/get-h3/lore@v0.3.0 exiting 0 with dist metadata and installed lore/__init__.py both at 0.3.0, the installed CLI run from a cwd outside any checkout exiting 0 and returning a classified match, and a nonexistent-tag negative arm exiting nonzero; the record names host, exact command, uv version and tag commit c769be4265e74a93b4706c6cc7971fe58a3f3dbd.
Cap exceeded: Iteration cap (100) reached (100.1 used). Increase max_iterations or split criteria. Partial verdict — 0 of 1 criteria graded, 1 ungraded. The run spent 3,703,101 in / 12,101 out over 100.1 iterations.

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: FAIL
  INCOMPLETE
  — docs/qa/evidence/run-RELEASE-LORE-010/evidence.txt plus raw/{install,cli,metadata,negative}.txt record a COLD uv tool install of git+https://github.com/get-h3/lore@v0.3.0 exiting 0 with dist metadata and installed lore/__init__.py both at 0.3.0, the installed CLI run from a cwd outside any checkout exiting 0 and returning a classified match, and a nonexistent-tag negative arm exiting nonzero; the record names host, exact command, uv version and tag commit c769be4265e74a93b4706c6cc7971fe58a3f3dbd.: Not examined — evaluation ended before this criterion was reached (no judgement was made about it)
  ✗ Coverage FAILED — not passing: docs/qa/evidence/run-RELEASE-LORE-010/evidence.txt plus raw/{install,cli,metadata,negative}.txt record a COLD uv tool install of git+https://github.com/get-h3/lore@v0.3.0 exiting 0 with dist metadata and installed lore/__init__.py both at 0.3.0, the installed CLI run from a cwd outside any checkout exiting 0 and returning a classified match, and a nonexistent-tag negative arm exiting nonzero; the record names host, exact command, uv version and tag commit c769be4265e74a93b4706c6cc7971fe58a3f3dbd.
Cap exceeded: Iteration cap (100) reached (100.1 used). Increase max_iterations or split criteria. Partial verdict — 0 of 1 criteria graded, 1 ungraded. The run spent 3,703,101 in / 12,101 out over 100.1 iterations.

Overall: FAIL ✗
