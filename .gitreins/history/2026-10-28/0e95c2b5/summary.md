# Verdict: README-9-R2

**Task:** Document shipped match and validate flags
**Evaluated:** 2026-10-28T21:55:53.005949
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE

(auto-parsed from non-JSON response — JSON parse failed: Expecting property name enclosed in double quotes: line 11 column 70 (char 604)) All four sub-checks of the single criterion are verified with live command output.

**Summary of evidence:**

| Sub-check | Result | Evidence |
|---|---|---|
| README names `match --class` | PASS | `grep -Fn "match [--class" README.md` → `376:` (rc=0) |
| README names `validate --format` | PASS | `g

## Summary

Judge Result: README-9-R2

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE

(auto-parsed from non-JSON response — JSON parse failed: Expecting property name enclosed in double quotes: line 11 column 70 (char 604)) All four sub-checks of the single criterion are verified with live command output.

**Summary of evidence:**

| Sub-check | Result | Evidence |
|---|---|---|
| README names `match --class` | PASS | `grep -Fn "match [--class" README.md` → `376:` (rc=0) |
| README names `validate --format` | PASS | `g

Overall: PASS ✓
