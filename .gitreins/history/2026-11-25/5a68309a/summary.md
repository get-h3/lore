# Verdict: QA-LORE-7

**Task:** Stop .gitignore *.log from shadowing tracked docs/qa/evidence log files
**Evaluated:** 2026-11-25T05:46:32.344895
**Result:** ✓ PASS

## Criteria

- ✓ **Tracked evidence logs under docs/qa/evidence/ are never shadowed by the .gitignore local-scratch *.log rule: a negation pattern re-includes docs/qa/evidence log files so git check-ignore admits none of the 10 tracked .log files, a regression test proves no tracked file is ignored (git check-ignore over git ls-files is empty), and the file count guard plus pytest plus ruff stay green. Failure condition: git check-ignore lists any tracked path, or the new test fails. Proof: test output on the merged tree plus check-ignore run over the full tracked set.**
  - Negation present at .gitignore:23 '!docs/qa/evidence/**/*.log' directly after the scratch rule at .gitignore:22 '*.log'. Fresh commands on clean tree 39b95cd: (a) `git ls-files | git check-ignore --stdin` -> exit code 1, empty stdout = zero tracked paths ignored; (b) `git ls-files 'docs/qa/evidence/*.log' | wc -l` = 10 (run14 x4, run9 x6); (c) regression test tests/test_qalore7_gitignore_evidence.py::test_no_tracked_file_is_gitignored PASSED and ::test_qa_evidence_logs_tracked_and_not_ignored PASSED (fresh run, '15 passed'); (d) file count guard tests/test_count_guard.py 13/13 PASSED; (e) exact guard test_command `uv run pytest -x --tb=short -q` -> '586 passed in 7.84s', exit_code 0; (f) `uv run ruff check . --quiet` rc=0 and `uv run ruff format --check .` rc=0.
- ✓ **The negation is correctly scoped: the local-scratch *.log rule still ignores scratch .log files outside docs/qa/evidence/, so the fix does not globally unignore logs.**
  - Command `git check-ignore -v scratch_probe_qalore7.log docs/qa/evidence/run9/diag.log docs/qa/evidence/run14/fresh-box-clone.log` (probe file created then removed; tree clean afterwards) returned exactly one line `.gitignore:22:*.log scratch_probe_qalore7.log` with rc=0 — the scratch rule still fires at repo root while neither evidence log was reported ignored, proving scope, not a blanket unignore.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ Tracked evidence logs under docs/qa/evidence/ are never shadowed by the .gitignore local-scratch *.log rule: a negation pattern re-includes docs/qa/evidence log files so git check-ignore admits none of the 10 tracked .log files, a regression test proves no tracked file is ignored (git check-ignore over git ls-files is empty), and the file count guard plus pytest plus ruff stay green. Failure condition: git check-ignore lists any tracked path, or the new test fails. Proof: test output on the merged tree plus check-ignore run over the full tracked set.: Negation present at .gitignore:23 '!docs/qa/evidence/**/*.log' directly after the scratch rule at .gitignore:22 '*.log'. Fresh commands on clean tree 39b95cd: (a) `git ls-files | git check-ignore --stdin` -> exit code 1, empty stdout = zero tracked paths ignored; (b) `git ls-files 'docs/qa/evidence/*.log' | wc -l` = 10 (run14 x4, run9 x6); (c) regression test tests/test_qalore7_gitignore_evidence.py::test_no_tracked_file_is_gitignored PASSED and ::test_qa_evidence_logs_tracked_and_not_ignored PASSED (fresh run, '15 passed'); (d) file count guard tests/test_count_guard.py 13/13 PASSED; (e) exact guard test_command `uv run pytest -x --tb=short -q` -> '586 passed in 7.84s', exit_code 0; (f) `uv run ruff check . --quiet` rc=0 and `uv run ruff format --check .` rc=0.
  ✓ The negation is correctly scoped: the local-scratch *.log rule still ignores scratch .log files outside docs/qa/evidence/, so the fix does not globally unignore logs.: Command `git check-ignore -v scratch_probe_qalore7.log docs/qa/evidence/run9/diag.log docs/qa/evidence/run14/fresh-box-clone.log` (probe file created then removed; tree clean afterwards) returned exactly one line `.gitignore:22:*.log scratch_probe_qalore7.log` with rc=0 — the scratch rule still fires at repo root while neither evidence log was reported ignored, proving scope, not a blanket unignore.
QA-LORE-7 verified on the clean merged tree: the .gitignore negation re-includes evidence logs, check-ignore over the full tracked set admits nothing (rc=1), exactly 10 tracked evidence .log files exist, the new regression test, file count guard, full 586-test pytest run, and ruff (check + format) are all green, and the scratch *.log rule still functions outside docs/qa/evidence/.
- ✓ **fix_verification**
  - fix_verification: 0 finding(s) verified

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ Tracked evidence logs under docs/qa/evidence/ are never shadowed by the .gitignore local-scratch *.log rule: a negation pattern re-includes docs/qa/evidence log files so git check-ignore admits none of the 10 tracked .log files, a regression test proves no tracked file is ignored (git check-ignore over git ls-files is empty), and the file count guard plus pytest plus ruff stay green. Failure condition: git check-ignore lists any tracked path, or the new test fails. Proof: test output on the merged tree plus check-ignore run over the full tracked set.: Negation present at .gitignore:23 '!docs/qa/evidence/**/*.log' directly after the scratch rule at .gitignore:22 '*.log'. Fresh commands on clean tree 39b95cd: (a) `git ls-files | git check-ignore --stdin` -> exit code 1, empty stdout = zero tracked paths ignored; (b) `git ls-files 'docs/qa/evidence/*.log' | wc -l` = 10 (run14 x4, run9 x6); (c) regression test tests/test_qalore7_gitignore_evidence.py::test_no_tracked_file_is_gitignored PASSED and ::test_qa_evidence_logs_tracked_and_not_ignored PASSED (fresh run, '15 passed'); (d) file count guard tests/test_count_guard.py 13/13 PASSED; (e) exact guard test_command `uv run pytest -x --tb=short -q` -> '586 passed in 7.84s', exit_code 0; (f) `uv run ruff check . --quiet` rc=0 and `uv run ruff format --check .` rc=0.
  ✓ The negation is correctly scoped: the local-scratch *.log rule still ignores scratch .log files outside docs/qa/evidence/, so the fix does not globally unignore logs.: Command `git check-ignore -v scratch_probe_qalore7.log docs/qa/evidence/run9/diag.log docs/qa/evidence/run14/fresh-box-clone.log` (probe file created then removed; tree clean afterwards) returned exactly one line `.gitignore:22:*.log scratch_probe_qalore7.log` with rc=0 — the scratch rule still fires at repo root while neither evidence log was reported ignored, proving scope, not a blanket unignore.
QA-LORE-7 verified on the clean merged tree: the .gitignore negation re-includes evidence logs, check-ignore over the full tracked set admits nothing (rc=1), exactly 10 tracked evidence .log files exist, the new regression test, file count guard, full 586-test pytest run, and ruff (check + format) are all green, and the scratch *.log rule still functions outside docs/qa/evidence/.

Stage fix_verification: PASS
  fix_verification: 0 finding(s) verified

Overall: PASS ✓
