# Verdict: LORE-20261008

**Task:** absorb --window error teaches accepted trail shape
**Evaluated:** 2026-10-19T12:27:10.644454
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ Error text for rc=2 absorb --window input names the upstream gap instead of the accepted contract (fenced block + bare-ISO lines); identical text for unrelated noise vs real export missing fence; no-export-marker case should exit 0 like non-claimed input: lore/evidence.py:67-71 defines LOGSEY_EXPORT_SHAPE_HINT = 'accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z kind=incident detail=...)' — the accepted contract, with no internal tooling state (LOGSEY_EXPORT_CONTRACT_STATUS is never interpolated). evidence.py:231-235 raises LogseyExportParseError('found export marker but no fenced block; <hint>') and evidence.py:271-275 raises 'fenced block present but no parseable evidence lines; <hint>'; lore/__main__.py:461-466 prints 'error: {exc}' to stderr and returns 2. Empirical CLI runs (uv run python -m lore absorb --window 2h --trail-file ...): marker+unrelated noise -> rc=2 'error: found export marker but no fenced block; accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z ...)'; marker+fence with no ISO lines -> rc=2 'error: fenced block present but no parseable evidence lines; accepted shape: ...' (same hint text, distinguishable what-went-wrong clause); no export marker -> rc=0 'no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)'. Tests: tests/test_lore053_absorb_window_error.py (4 tests) pins all three behaviors incl. asserting the 'unfrozen' internal status never leaks. Full suite: `uv run pytest -x --tb=short` -> exit_code 0, '523 passed in 3.94s'.
absorb --window rc=2 errors now teach the accepted fenced-block/bare-ISO trail shape (identical hint for both failure modes), no-marker input exits 0, and the full suite passes (523 passed).

## Summary

Judge Result: LORE-20261008

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ Error text for rc=2 absorb --window input names the upstream gap instead of the accepted contract (fenced block + bare-ISO lines); identical text for unrelated noise vs real export missing fence; no-export-marker case should exit 0 like non-claimed input: lore/evidence.py:67-71 defines LOGSEY_EXPORT_SHAPE_HINT = 'accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z kind=incident detail=...)' — the accepted contract, with no internal tooling state (LOGSEY_EXPORT_CONTRACT_STATUS is never interpolated). evidence.py:231-235 raises LogseyExportParseError('found export marker but no fenced block; <hint>') and evidence.py:271-275 raises 'fenced block present but no parseable evidence lines; <hint>'; lore/__main__.py:461-466 prints 'error: {exc}' to stderr and returns 2. Empirical CLI runs (uv run python -m lore absorb --window 2h --trail-file ...): marker+unrelated noise -> rc=2 'error: found export marker but no fenced block; accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z ...)'; marker+fence with no ISO lines -> rc=2 'error: fenced block present but no parseable evidence lines; accepted shape: ...' (same hint text, distinguishable what-went-wrong clause); no export marker -> rc=0 'no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)'. Tests: tests/test_lore053_absorb_window_error.py (4 tests) pins all three behaviors incl. asserting the 'unfrozen' internal status never leaks. Full suite: `uv run pytest -x --tb=short` -> exit_code 0, '523 passed in 3.94s'.
absorb --window rc=2 errors now teach the accepted fenced-block/bare-ISO trail shape (identical hint for both failure modes), no-marker input exits 0, and the full suite passes (523 passed).

Overall: PASS ✓
