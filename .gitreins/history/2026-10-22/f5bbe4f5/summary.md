# Verdict: DOC-5

**Task:** Fix INSTALL.md help fence to match real binary output
**Evaluated:** 2026-10-22T15:33:48.481341
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ INSTALL.md:116-147 fenced usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit block must match usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit output exactly; diff EMPTY: docs/INSTALL.md fence content at lines 116-143 (closing fence line 144) is byte-identical to real binary output. Ran `uv run python -m lore --help` (exit_code=0) -> /tmp/real_help.txt (1563 bytes); extracted `awk 'NR>=116 && NR<=143' docs/INSTALL.md` -> /tmp/fence.txt (1563 bytes). `diff /tmp/fence.txt /tmp/real_help.txt` returned diff_exit=0 with EMPTY output; `cmp` reported IDENTICAL. Exact Python string comparison against the criterion text: fence==criterion True, real==criterion True, fence==real True. Em-dashes (U+2014) preserved in 'stdout only — propose-not-write' (line 134) and 'freshness — never fabricated dates' (line 139). Commit 420dd45 touched only docs/INSTALL.md (2 insertions, 6 deletions), removing two stale fragments that no longer exist in the binary: the `gate` '--record PATH appends one JSONL audit record per ALLOWED verdict' text and the `audit` '`unclassified` catch-all bucket is marked (bucket: true / [bucket])' text. Test suite: `uv run pytest -x --tb=short -q` -> exit_code=0, '557 passed in 4.20s'.
INSTALL.md:116-143 is byte-for-byte identical to the real `lore --help` output (empty diff, cmp IDENTICAL, 1563 bytes each) and the full suite passes with 557 tests.

## Summary

Judge Result: DOC-5

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ INSTALL.md:116-147 fenced usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit block must match usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit output exactly; diff EMPTY: docs/INSTALL.md fence content at lines 116-143 (closing fence line 144) is byte-identical to real binary output. Ran `uv run python -m lore --help` (exit_code=0) -> /tmp/real_help.txt (1563 bytes); extracted `awk 'NR>=116 && NR<=143' docs/INSTALL.md` -> /tmp/fence.txt (1563 bytes). `diff /tmp/fence.txt /tmp/real_help.txt` returned diff_exit=0 with EMPTY output; `cmp` reported IDENTICAL. Exact Python string comparison against the criterion text: fence==criterion True, real==criterion True, fence==real True. Em-dashes (U+2014) preserved in 'stdout only — propose-not-write' (line 134) and 'freshness — never fabricated dates' (line 139). Commit 420dd45 touched only docs/INSTALL.md (2 insertions, 6 deletions), removing two stale fragments that no longer exist in the binary: the `gate` '--record PATH appends one JSONL audit record per ALLOWED verdict' text and the `audit` '`unclassified` catch-all bucket is marked (bucket: true / [bucket])' text. Test suite: `uv run pytest -x --tb=short -q` -> exit_code=0, '557 passed in 4.20s'.
INSTALL.md:116-143 is byte-for-byte identical to the real `lore --help` output (empty diff, cmp IDENTICAL, 1563 bytes each) and the full suite passes with 557 tests.

Overall: PASS ✓
