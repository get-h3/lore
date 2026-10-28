# Verdict: README-7

**Task:** Refresh stale INSTALL compile JSON signature
**Evaluated:** 2026-10-28T21:34:40.531466
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ The docs INSTALL compile JSON signature must byte-match live uv run lore compile --class secret-env-clobber --format json output and include the non-capturing groups and negative-lookbehind alternative.: docs/INSTALL.md:298 now reads "signature": "(?:\\.env(?:\\.example)?|(?<!\\.)env)\\s+(?:twins?|clobber|overwrite)", which is byte-identical to line 5 of live `uv run lore compile --class secret-env-clobber --format json` output (programmatic comparison: 'sig equal: True'; the 13-line doc JSON prefix is byte-identical to the live output). The signature contains 3 non-capturing groups `(?:` and the negative-lookbehind alternative `(?<!\.)env`; it compiles and matches '.env clobber', '.env.example twins', 'env clobber', '.env overwrite'. It also matches the source registry lore/classes.py:134. Test suite: `uv run pytest -x --tb=short` exit_code 0, '566 passed in 4.52s'.
docs/INSTALL.md:298 signature byte-matches live compile JSON output and includes the non-capturing groups plus negative-lookbehind alternative; full suite passes (566 passed).

## Summary

Judge Result: README-7

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ The docs INSTALL compile JSON signature must byte-match live uv run lore compile --class secret-env-clobber --format json output and include the non-capturing groups and negative-lookbehind alternative.: docs/INSTALL.md:298 now reads "signature": "(?:\\.env(?:\\.example)?|(?<!\\.)env)\\s+(?:twins?|clobber|overwrite)", which is byte-identical to line 5 of live `uv run lore compile --class secret-env-clobber --format json` output (programmatic comparison: 'sig equal: True'; the 13-line doc JSON prefix is byte-identical to the live output). The signature contains 3 non-capturing groups `(?:` and the negative-lookbehind alternative `(?<!\.)env`; it compiles and matches '.env clobber', '.env.example twins', 'env clobber', '.env overwrite'. It also matches the source registry lore/classes.py:134. Test suite: `uv run pytest -x --tb=short` exit_code 0, '566 passed in 4.52s'.
docs/INSTALL.md:298 signature byte-matches live compile JSON output and includes the non-capturing groups plus negative-lookbehind alternative; full suite passes (566 passed).

Overall: PASS ✓
