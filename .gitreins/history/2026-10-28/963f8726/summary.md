# Verdict: DOC-5-R2

**Task:** INSTALL --help fence refresh
**Evaluated:** 2026-10-28T20:45:37.145006
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  ✗ sed the fenced help block, diff against live lore --help output exits 0 empty; ch:trace row=DOC-5-R2 marker resolves in the committed row: First half PASSES: `sed -n "118,145p" docs/INSTALL.md > /tmp/f.txt && .venv/bin/python -m lore --help > /tmp/h.txt && diff /tmp/f.txt /tmp/h.txt` -> DIFF_EXIT=0 (28 lines each, byte-identical); same diff at the fix commit 67d1fad (`git show 67d1fad:docs/INSTALL.md | sed -n '118,145p'` vs live help) -> DIFF_EXIT=0. Full suite `uv run pytest -x --tb=short -q` -> exit_code 0, '566 passed in 3.83s'. Second half FAILS: the `ch:trace row=DOC-5-R2` marker exists once in .coding-hermes/board/tasks.jsonl but the row it lives in is still status="pending", worker_status="pending", commit_hash=null, guard_result=null, ci_result=null, completed_at=null, worker_summary=null, foreman_note=null — the marker was written by the pre-fix filing commit 6b96c49 and points at commit=9acf205df371996b27bfd640bf25ce88100c77ee (the row-filing commit, 2026-10-26), not at the fix commit 67d1fad. The fix commit 67d1fad touched only CONTRIBUTING.md, README.md, docs/INSTALL.md, scripts/test-count.txt, skills/lore-usage/SKILL.md — no board row update; the wave closeout 7ab218c closed only PERF-3, DOC-7, DOC-9, LORE-070, DOC-8, leaving DOC-5-R2 unclosed. The marker therefore does not resolve in a committed (closed, commit-bound) row.
The INSTALL --help fence is byte-identical to live `lore --help` (diff exit 0, 566 tests pass), but the ch:trace row=DOC-5-R2 marker still sits in a pending, uncommitted board row pointing at the pre-fix filing commit rather than the fix commit.

## Summary

Judge Result: DOC-5-R2

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: FAIL
  INCOMPLETE
  ✗ sed the fenced help block, diff against live lore --help output exits 0 empty; ch:trace row=DOC-5-R2 marker resolves in the committed row: First half PASSES: `sed -n "118,145p" docs/INSTALL.md > /tmp/f.txt && .venv/bin/python -m lore --help > /tmp/h.txt && diff /tmp/f.txt /tmp/h.txt` -> DIFF_EXIT=0 (28 lines each, byte-identical); same diff at the fix commit 67d1fad (`git show 67d1fad:docs/INSTALL.md | sed -n '118,145p'` vs live help) -> DIFF_EXIT=0. Full suite `uv run pytest -x --tb=short -q` -> exit_code 0, '566 passed in 3.83s'. Second half FAILS: the `ch:trace row=DOC-5-R2` marker exists once in .coding-hermes/board/tasks.jsonl but the row it lives in is still status="pending", worker_status="pending", commit_hash=null, guard_result=null, ci_result=null, completed_at=null, worker_summary=null, foreman_note=null — the marker was written by the pre-fix filing commit 6b96c49 and points at commit=9acf205df371996b27bfd640bf25ce88100c77ee (the row-filing commit, 2026-10-26), not at the fix commit 67d1fad. The fix commit 67d1fad touched only CONTRIBUTING.md, README.md, docs/INSTALL.md, scripts/test-count.txt, skills/lore-usage/SKILL.md — no board row update; the wave closeout 7ab218c closed only PERF-3, DOC-7, DOC-9, LORE-070, DOC-8, leaving DOC-5-R2 unclosed. The marker therefore does not resolve in a committed (closed, commit-bound) row.
The INSTALL --help fence is byte-identical to live `lore --help` (diff exit 0, 566 tests pass), but the ch:trace row=DOC-5-R2 marker still sits in a pending, uncommitted board row pointing at the pre-fix filing commit rather than the fix commit.

Overall: FAIL ✗
