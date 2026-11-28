# Verdict: DOC-10-R2

**Task:** Refresh v0.3.0 version claims in README and release docs
**Evaluated:** 2026-11-28T10:59:14.096209
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  ✗ Coverage FAILED — ungraded: PROOF: README Status names version 0.3.0, tags v0.1.0/v0.2.0/v0.3.0, and only uses git rev-list --count v0.3.0..HEAD for the live commit count; docs/RELEASE.md enumerates the same tags; scripts/check-test-count.sh, pytest -x -q, and pyproject version agreement pass. FAILIF: any stale 0.2.0-only tag list, any README Status count based on v0.2.0, missing 0.3.0 in either doc, test/count failure, or version mismatch.
Evaluator error: LLM call failed: LLM request failed after 3 attempts (provider=openai model=glm-5.3-flash url=https://api.z.ai/api/coding/paas/v4/chat/completions key=<GITREINS_LLM_API_KEY>) — last error: 429 Client Error: Too Many Requests for url: https://api.z.ai/api/coding/paas/v4/chat/completions
- ✓ **fix_verification**
  - fix_verification: 0 finding(s) verified

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: FAIL
  INCOMPLETE
  ✗ Coverage FAILED — ungraded: PROOF: README Status names version 0.3.0, tags v0.1.0/v0.2.0/v0.3.0, and only uses git rev-list --count v0.3.0..HEAD for the live commit count; docs/RELEASE.md enumerates the same tags; scripts/check-test-count.sh, pytest -x -q, and pyproject version agreement pass. FAILIF: any stale 0.2.0-only tag list, any README Status count based on v0.2.0, missing 0.3.0 in either doc, test/count failure, or version mismatch.
Evaluator error: LLM call failed: LLM request failed after 3 attempts (provider=openai model=glm-5.3-flash url=https://api.z.ai/api/coding/paas/v4/chat/completions key=<GITREINS_LLM_API_KEY>) — last error: 429 Client Error: Too Many Requests for url: https://api.z.ai/api/coding/paas/v4/chat/completions

Stage fix_verification: PASS
  fix_verification: 0 finding(s) verified

Overall: FAIL ✗
