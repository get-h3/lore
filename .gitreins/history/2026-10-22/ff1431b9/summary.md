# Verdict: README-6

**Task:** INSTALL.md unknown-class paste refresh to the live 14-class list
**Evaluated:** 2026-10-22T19:32:39.566169
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ docs/INSTALL.md unknown-class refusal block quotes the CURRENT compile output: the Known list carries all 14 registry classes (docs-count-drift, worktree-reap-data-loss, fast-forward-push-reject present) and ends at unclassified in registry tuple order, with the freshly executed CLI command output quoted verbatim beside the fence: docs/INSTALL.md:349 holds the CLI command `uv run python -m lore compile --class does-not-exist ; echo "exit=$?"` in a ```sh fence, with the output fence at 352-355 directly beside it. I re-ran that exact command: `uv run python -m lore compile --class does-not-exist` emitted a 368-byte line ending `... fast-forward-push-reject, unclassified` and `exit=2`; `diff /tmp/live.txt /tmp/doc.txt` (doc line 353) printed no differences and echoed BYTE-IDENTICAL (368 vs 368 bytes). Registry order verified programmatically: `from lore.classes import SEED_CLASSES, UNCLASSIFIED_CLASS` yields count: 14, ids in exactly the doc's order, last: unclassified, and docs-count-drift/worktree-reap-data-loss/fast-forward-push-reject all True. Test suite `uv run pytest -x --tb=short -q` exit_code 0: '560 passed in 6.09s'.
docs/INSTALL.md:353 is byte-identical to freshly executed `uv run python -m lore compile --class does-not-exist` output, listing all 14 registry classes in tuple order ending at unclassified, with the command quoted beside the fence and the full suite green (560 passed).

## Summary

Judge Result: README-6

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ docs/INSTALL.md unknown-class refusal block quotes the CURRENT compile output: the Known list carries all 14 registry classes (docs-count-drift, worktree-reap-data-loss, fast-forward-push-reject present) and ends at unclassified in registry tuple order, with the freshly executed CLI command output quoted verbatim beside the fence: docs/INSTALL.md:349 holds the CLI command `uv run python -m lore compile --class does-not-exist ; echo "exit=$?"` in a ```sh fence, with the output fence at 352-355 directly beside it. I re-ran that exact command: `uv run python -m lore compile --class does-not-exist` emitted a 368-byte line ending `... fast-forward-push-reject, unclassified` and `exit=2`; `diff /tmp/live.txt /tmp/doc.txt` (doc line 353) printed no differences and echoed BYTE-IDENTICAL (368 vs 368 bytes). Registry order verified programmatically: `from lore.classes import SEED_CLASSES, UNCLASSIFIED_CLASS` yields count: 14, ids in exactly the doc's order, last: unclassified, and docs-count-drift/worktree-reap-data-loss/fast-forward-push-reject all True. Test suite `uv run pytest -x --tb=short -q` exit_code 0: '560 passed in 6.09s'.
docs/INSTALL.md:353 is byte-identical to freshly executed `uv run python -m lore compile --class does-not-exist` output, listing all 14 registry classes in tuple order ending at unclassified, with the command quoted beside the fence and the full suite green (560 passed).

Overall: PASS ✓
