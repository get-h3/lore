# Verdict: QA-LORE-8

**Task:** Exclude failure-branch-only CI cell ci-act from owed-cell NOT-COLLECTED accounting
**Evaluated:** 2026-11-26T17:04:39.555245
**Result:** ✗ FAIL (DEGRADED — skipped checks)

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  ✗ Coverage FAILED — ungraded: The QA harness owed-cell roster (derive_owed_cells) no longer lists ci-act as an owed cell when absent, because the battery emits ci-act only from act-failure branches of the ci-pass cell (a green or skipped CI simulation never emits it, so the NOT-COLLECTED row was spurious on every green fire, per lore-qa-2026-11-22-20-12-17 ledger). Verify: replaying the roster derivation over the harvested lore-qa-2026-11-22 battery script no longer yields ci-act; ci-pass remains owed; bash -n passes; evidence recorded in docs/qa/evidence/run-QA-LORE-8. Failure condition: a genuinely dropped cell still yields no NOT-COLLECTED row (e.g. ci-pass absent with roster derived). Proof: before/after replay output plus md5 before/after of the harness.
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
  ✗ Coverage FAILED — ungraded: The QA harness owed-cell roster (derive_owed_cells) no longer lists ci-act as an owed cell when absent, because the battery emits ci-act only from act-failure branches of the ci-pass cell (a green or skipped CI simulation never emits it, so the NOT-COLLECTED row was spurious on every green fire, per lore-qa-2026-11-22-20-12-17 ledger). Verify: replaying the roster derivation over the harvested lore-qa-2026-11-22 battery script no longer yields ci-act; ci-pass remains owed; bash -n passes; evidence recorded in docs/qa/evidence/run-QA-LORE-8. Failure condition: a genuinely dropped cell still yields no NOT-COLLECTED row (e.g. ci-pass absent with roster derived). Proof: before/after replay output plus md5 before/after of the harness.
Evaluator error: LLM call failed: LLM request failed after 3 attempts (provider=openai model=glm-5.3-flash url=https://api.z.ai/api/coding/paas/v4/chat/completions key=<GITREINS_LLM_API_KEY>) — last error: 429 Client Error: Too Many Requests for url: https://api.z.ai/api/coding/paas/v4/chat/completions

Stage fix_verification: PASS
  fix_verification: 0 finding(s) verified

Overall: FAIL ✗
