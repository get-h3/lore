# Verdict: DOC-1

**Task:** match --explain undocumented
**Evaluated:** 2026-09-29T03:15:39.026513
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ README.md and docs/INSTALL.md each document --explain with verbatim near-misses example: README.md:79-93 ('### Near-misses (evidence echo)') and docs/INSTALL.md:185-201 ('#### `--explain` — echo the near-misses') both document --explain with the identical near-misses example. Ran `uv run python -m lore match "gateway drain 503" --explain` (exit_code 0); actual output is byte-for-byte identical to the documented block: 'gateway-drain-window\tconfidence=0.90\tevidence: signature:drain 503; keyword:503; keyword:drain; keyword:gateway' / 'unclassified\tconfidence=0.00\tevidence: none' / 'near-misses:' / '  guard-degradation  score=0.17  (1/6 keywords: gate)'.
Both README.md and docs/INSTALL.md document --explain with a near-misses example that matches the real CLI output verbatim.

## Summary

Judge Result: DOC-1

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ README.md and docs/INSTALL.md each document --explain with verbatim near-misses example: README.md:79-93 ('### Near-misses (evidence echo)') and docs/INSTALL.md:185-201 ('#### `--explain` — echo the near-misses') both document --explain with the identical near-misses example. Ran `uv run python -m lore match "gateway drain 503" --explain` (exit_code 0); actual output is byte-for-byte identical to the documented block: 'gateway-drain-window\tconfidence=0.90\tevidence: signature:drain 503; keyword:503; keyword:drain; keyword:gateway' / 'unclassified\tconfidence=0.00\tevidence: none' / 'near-misses:' / '  guard-degradation  score=0.17  (1/6 keywords: gate)'.
Both README.md and docs/INSTALL.md document --explain with a near-misses example that matches the real CLI output verbatim.

Overall: PASS ✓
