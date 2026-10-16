# Verdict: LORE-055

**Task:** consult with no title or failure input silently succeeds as a no-match
**Evaluated:** 2026-10-16T04:16:04.906822
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ lore consult with no title and no --failure must exit 2 with a concise required-input error; valid no-match (unrelated symptom) must remain exit 0; tests pin both contracts.: lore/__main__.py _cmd_consult now guards at the top: `failure = getattr(args, "failure", None); if not failure and not args.title:` prints `error: consult requires a title argument unless --failure is given (usage: lore consult <title> [--detail ...] | consult --failure <text>)` to stderr and `return 2`. Live CLI verification: `uv run lore consult` -> EXIT=2 with that stderr message; `uv run lore consult --failure ""` -> EXIT=2 (empty string treated as missing); valid no-match `uv run lore consult "totally unrelated symptom xyzzy plugh"` -> EXIT=0 + `no matching runbook`; `uv run lore consult --failure "totally unrelated symptom xyzzy plugh"` -> EXIT=0 + `no matching runbook`. Tests pin both contracts: tests/test_lore055_consult_missing_input.py (new, subprocess-level) asserts returncode==2, `error:`/`title`/`--failure` in stderr, no `no matching runbook` on stdout, plus exit-0 no-match for both title and --failure modes and an unchanged match path; tests/test_lore016_qa_audit.py's old fail-open-exit-0 test was revised to the exit-2 contract. Command evidence: `uv run pytest tests/test_lore055_consult_missing_input.py tests/test_lore016_qa_audit.py -q --tb=short` -> `27 passed in 0.65s` (exit 0); full suite `uv run pytest -q --tb=short` -> `469 passed in 2.87s` (exit 0); `bash scripts/check-test-count.sh` -> `PASS: test-count guard: canonical=469 matches live=469` (exit 0).
consult with no title and no --failure now exits 2 with a concise stderr required-input error while valid no-match input still exits 0, with both contracts pinned by passing subprocess-level tests (469 passed).

## Summary

Judge Result: LORE-055

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ lore consult with no title and no --failure must exit 2 with a concise required-input error; valid no-match (unrelated symptom) must remain exit 0; tests pin both contracts.: lore/__main__.py _cmd_consult now guards at the top: `failure = getattr(args, "failure", None); if not failure and not args.title:` prints `error: consult requires a title argument unless --failure is given (usage: lore consult <title> [--detail ...] | consult --failure <text>)` to stderr and `return 2`. Live CLI verification: `uv run lore consult` -> EXIT=2 with that stderr message; `uv run lore consult --failure ""` -> EXIT=2 (empty string treated as missing); valid no-match `uv run lore consult "totally unrelated symptom xyzzy plugh"` -> EXIT=0 + `no matching runbook`; `uv run lore consult --failure "totally unrelated symptom xyzzy plugh"` -> EXIT=0 + `no matching runbook`. Tests pin both contracts: tests/test_lore055_consult_missing_input.py (new, subprocess-level) asserts returncode==2, `error:`/`title`/`--failure` in stderr, no `no matching runbook` on stdout, plus exit-0 no-match for both title and --failure modes and an unchanged match path; tests/test_lore016_qa_audit.py's old fail-open-exit-0 test was revised to the exit-2 contract. Command evidence: `uv run pytest tests/test_lore055_consult_missing_input.py tests/test_lore016_qa_audit.py -q --tb=short` -> `27 passed in 0.65s` (exit 0); full suite `uv run pytest -q --tb=short` -> `469 passed in 2.87s` (exit 0); `bash scripts/check-test-count.sh` -> `PASS: test-count guard: canonical=469 matches live=469` (exit 0).
consult with no title and no --failure now exits 2 with a concise stderr required-input error while valid no-match input still exits 0, with both contracts pinned by passing subprocess-level tests (469 passed).

Overall: PASS ✓
