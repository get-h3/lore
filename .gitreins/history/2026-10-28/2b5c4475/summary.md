# Verdict: DOC-5-R2

**Task:** INSTALL --help fence refresh
**Evaluated:** 2026-10-28T20:48:29.805983
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ sed the fenced help block, diff against live lore --help output exits 0 empty; ch:trace row=DOC-5-R2 marker resolves in the committed row: Fence-vs-live diff empty: `sed -n '118,145p' docs/INSTALL.md > /tmp/fence.txt && uv run python -m lore --help > /tmp/live_help.txt && diff /tmp/fence.txt /tmp/live_help.txt` -> diff_exit=0, both files 28 lines; same check against the committed blob (`git show HEAD:docs/INSTALL.md | sed -n '118,145p'`) -> head_fence_diff_exit=0, working tree clean. Marker resolves in the committed row: `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -o 'ch:trace row=DOC-5-R2...'` returns the row's marker with spec=docs/INSTALL.md, doc=docs/INSTALL.md#L118, evidence=fence-diff-empty-vs-live-help, verdict=963f8726, commit=67d1fad6. Test suite fresh: `uv run pytest -x --tb=short -q` -> exit_code 0, "566 passed in 3.58s". Premise supersession disclosed in the row is corroborated: top-level help has 0 hits for events.jsonl/uncovered_classes/90-day, while `uv run python -m lore audit --help` (exit 0) has 1 hit each.
Fenced help block in docs/INSTALL.md is byte-identical to live `lore --help` (empty diff, exit 0), the ch:trace row=DOC-5-R2 marker resolves in the committed board row, and the suite is green (566 passed).

## Summary

Judge Result: DOC-5-R2

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ sed the fenced help block, diff against live lore --help output exits 0 empty; ch:trace row=DOC-5-R2 marker resolves in the committed row: Fence-vs-live diff empty: `sed -n '118,145p' docs/INSTALL.md > /tmp/fence.txt && uv run python -m lore --help > /tmp/live_help.txt && diff /tmp/fence.txt /tmp/live_help.txt` -> diff_exit=0, both files 28 lines; same check against the committed blob (`git show HEAD:docs/INSTALL.md | sed -n '118,145p'`) -> head_fence_diff_exit=0, working tree clean. Marker resolves in the committed row: `git show HEAD:.coding-hermes/board/tasks.jsonl | grep -o 'ch:trace row=DOC-5-R2...'` returns the row's marker with spec=docs/INSTALL.md, doc=docs/INSTALL.md#L118, evidence=fence-diff-empty-vs-live-help, verdict=963f8726, commit=67d1fad6. Test suite fresh: `uv run pytest -x --tb=short -q` -> exit_code 0, "566 passed in 3.58s". Premise supersession disclosed in the row is corroborated: top-level help has 0 hits for events.jsonl/uncovered_classes/90-day, while `uv run python -m lore audit --help` (exit 0) has 1 hit each.
Fenced help block in docs/INSTALL.md is byte-identical to live `lore --help` (empty diff, exit 0), the ch:trace row=DOC-5-R2 marker resolves in the committed board row, and the suite is green (566 passed).

Overall: PASS ✓
