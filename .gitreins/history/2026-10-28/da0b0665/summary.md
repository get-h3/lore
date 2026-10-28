# Verdict: README-11

**Task:** Document collision-safe uv tool installation
**Evaluated:** 2026-10-28T21:35:46.760934
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ README must retain the original uv tool install recipe and document uv tool upgrade or uv tool install --force for an existing lore executable, including when --force is appropriate.: README.md (lines ~148-170) still contains the original recipe `uv tool install git+https://github.com/get-h3/lore` followed by `lore match "key rotation expired"`; it then documents `uv tool upgrade lore` for upgrading an installed lore tool in place, and `uv tool install --force git+https://github.com/get-h3/lore` for overwriting an existing tool that owns the `lore` executable name, with explicit guidance: "`--force` is appropriate only for that deliberate overwrite; otherwise, keep the existing installed version rather than clobbering its executable." Diff a390fe1..f9be8c4 shows only README.md changed (16 insertions, 7 deletions). Docs-only change; no test suite applies to this criterion.
README retains the original uv tool install recipe and clearly documents both `uv tool upgrade lore` and `uv tool install --force`, including when --force is appropriate.

## Summary

Judge Result: README-11

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ README must retain the original uv tool install recipe and document uv tool upgrade or uv tool install --force for an existing lore executable, including when --force is appropriate.: README.md (lines ~148-170) still contains the original recipe `uv tool install git+https://github.com/get-h3/lore` followed by `lore match "key rotation expired"`; it then documents `uv tool upgrade lore` for upgrading an installed lore tool in place, and `uv tool install --force git+https://github.com/get-h3/lore` for overwriting an existing tool that owns the `lore` executable name, with explicit guidance: "`--force` is appropriate only for that deliberate overwrite; otherwise, keep the existing installed version rather than clobbering its executable." Diff a390fe1..f9be8c4 shows only README.md changed (16 insertions, 7 deletions). Docs-only change; no test suite applies to this criterion.
README retains the original uv tool install recipe and clearly documents both `uv tool upgrade lore` and `uv tool install --force`, including when --force is appropriate.

Overall: PASS ✓
