# Verdict: INFRA-LORE-044

**Task:** Guard hook budget vs effective test timeout gap closed in config
**Evaluated:** 2026-11-21T04:06:57.926797
**Result:** ✓ PASS

## Criteria

- ✓ **A commit in the repo prints no guard budget warning (neither the hook_timeout<=test_timeout WARN nor the evaluator.test_timeout unknown-key WARN); .gitreins/config.yaml is valid under gitreins 0.21.0 with a declared hook budget above the effective test budget; tier-1 guard PASS on the fixed tree; RED-proven on real commits.**
  - (1) No warnings: ran validate_config() from the installed gitreins 0.21.1 (engine/config_schema.py) on .gitreins/config.yaml — 'issue count: 0'; grep for WARN across all .gitreins/logs/*.log finds none, including the post-merge guard log guard-20261121T035229.151341Z.log (run_utc 03:52:29Z = 22:52:29 -0500, 7s after merge commit 75c094b at 22:52:22) with 'overall: PASS'. (2) Valid + budget: config_schema.py:120-121 accepts guards.test_timeout/hook_timeout as int; the evaluator key list (config_schema.py:139-157) has no test_timeout and the fix removed it (verified: 'evaluator has test_timeout: False'); declared hook_timeout 1320 > test_timeout 1200, both int (verified via venv python). (3) Tier-1 PASS: prior stage tier1 lint/secrets/tests all exit_code 0, plus fresh run of the configured test_command 'uv run pytest -x --tb=short -q' => '572 passed in 4.35s' exit 0. (4) RED-proven: commit a556d76 records RED probe 8faab64 (pre-fix real commit printed 'WARN: evaluator.test_timeout: unknown key — this key is ignored') and GREEN probe a95845c (post-fix, no warning); both probe commits exist in git history.
- ✓ **Removing evaluator.test_timeout does not silently reduce the effective test budget below the previously intended 600s**
  - The removed evaluator.test_timeout: 600 was already ignored by gitreins 0.21 (unknown-key WARN; absent from the evaluator key list at config_schema.py:139-157), so its removal loses no effective behavior; the effective budget is preserved explicitly at guards.test_timeout: 1200 (>= 600) with guards.hook_timeout: 1320 = 1200+120, matching the guard's own derivation at guard_manager.py:1828; evaluator.max_time '30m' retained for LORE-037 (.gitreins/config.yaml:46).

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ A commit in the repo prints no guard budget warning (neither the hook_timeout<=test_timeout WARN nor the evaluator.test_timeout unknown-key WARN); .gitreins/config.yaml is valid under gitreins 0.21.0 with a declared hook budget above the effective test budget; tier-1 guard PASS on the fixed tree; RED-proven on real commits.: (1) No warnings: ran validate_config() from the installed gitreins 0.21.1 (engine/config_schema.py) on .gitreins/config.yaml — 'issue count: 0'; grep for WARN across all .gitreins/logs/*.log finds none, including the post-merge guard log guard-20261121T035229.151341Z.log (run_utc 03:52:29Z = 22:52:29 -0500, 7s after merge commit 75c094b at 22:52:22) with 'overall: PASS'. (2) Valid + budget: config_schema.py:120-121 accepts guards.test_timeout/hook_timeout as int; the evaluator key list (config_schema.py:139-157) has no test_timeout and the fix removed it (verified: 'evaluator has test_timeout: False'); declared hook_timeout 1320 > test_timeout 1200, both int (verified via venv python). (3) Tier-1 PASS: prior stage tier1 lint/secrets/tests all exit_code 0, plus fresh run of the configured test_command 'uv run pytest -x --tb=short -q' => '572 passed in 4.35s' exit 0. (4) RED-proven: commit a556d76 records RED probe 8faab64 (pre-fix real commit printed 'WARN: evaluator.test_timeout: unknown key — this key is ignored') and GREEN probe a95845c (post-fix, no warning); both probe commits exist in git history.
  ✓ Removing evaluator.test_timeout does not silently reduce the effective test budget below the previously intended 600s: The removed evaluator.test_timeout: 600 was already ignored by gitreins 0.21 (unknown-key WARN; absent from the evaluator key list at config_schema.py:139-157), so its removal loses no effective behavior; the effective budget is preserved explicitly at guards.test_timeout: 1200 (>= 600) with guards.hook_timeout: 1320 = 1200+120, matching the guard's own derivation at guard_manager.py:1828; evaluator.max_time '30m' retained for LORE-037 (.gitreins/config.yaml:46).
The fix declares guards.test_timeout: 1200 and guards.hook_timeout: 1320 (hook > test) and removes the ignored evaluator.test_timeout key; the installed gitreins 0.21.1 schema validator reports zero issues, no WARN appears in any guard log including the post-merge run, the fresh test run passes 572/572, and RED/GREEN probes on real commits are recorded in commit a556d76.

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ A commit in the repo prints no guard budget warning (neither the hook_timeout<=test_timeout WARN nor the evaluator.test_timeout unknown-key WARN); .gitreins/config.yaml is valid under gitreins 0.21.0 with a declared hook budget above the effective test budget; tier-1 guard PASS on the fixed tree; RED-proven on real commits.: (1) No warnings: ran validate_config() from the installed gitreins 0.21.1 (engine/config_schema.py) on .gitreins/config.yaml — 'issue count: 0'; grep for WARN across all .gitreins/logs/*.log finds none, including the post-merge guard log guard-20261121T035229.151341Z.log (run_utc 03:52:29Z = 22:52:29 -0500, 7s after merge commit 75c094b at 22:52:22) with 'overall: PASS'. (2) Valid + budget: config_schema.py:120-121 accepts guards.test_timeout/hook_timeout as int; the evaluator key list (config_schema.py:139-157) has no test_timeout and the fix removed it (verified: 'evaluator has test_timeout: False'); declared hook_timeout 1320 > test_timeout 1200, both int (verified via venv python). (3) Tier-1 PASS: prior stage tier1 lint/secrets/tests all exit_code 0, plus fresh run of the configured test_command 'uv run pytest -x --tb=short -q' => '572 passed in 4.35s' exit 0. (4) RED-proven: commit a556d76 records RED probe 8faab64 (pre-fix real commit printed 'WARN: evaluator.test_timeout: unknown key — this key is ignored') and GREEN probe a95845c (post-fix, no warning); both probe commits exist in git history.
  ✓ Removing evaluator.test_timeout does not silently reduce the effective test budget below the previously intended 600s: The removed evaluator.test_timeout: 600 was already ignored by gitreins 0.21 (unknown-key WARN; absent from the evaluator key list at config_schema.py:139-157), so its removal loses no effective behavior; the effective budget is preserved explicitly at guards.test_timeout: 1200 (>= 600) with guards.hook_timeout: 1320 = 1200+120, matching the guard's own derivation at guard_manager.py:1828; evaluator.max_time '30m' retained for LORE-037 (.gitreins/config.yaml:46).
The fix declares guards.test_timeout: 1200 and guards.hook_timeout: 1320 (hook > test) and removes the ignored evaluator.test_timeout key; the installed gitreins 0.21.1 schema validator reports zero issues, no WARN appears in any guard log including the post-merge run, the fresh test run passes 572/572, and RED/GREEN probes on real commits are recorded in commit a556d76.

Overall: PASS ✓
