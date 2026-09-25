# Verdict: LORE-019

**Task:** Docs truth sweep: repo PUBLIC + live test/class counts
**Evaluated:** 2026-09-25T09:03:00.879566
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ README quickstart works on the now-public repo; no stale 238/10-curated claims; live counts verified: (A) PUBLIC+quickstart: anonymous `git ls-remote https://github.com/get-h3/lore` exit=0 and `curl https://github.com/get-h3/lore` => HTTP 200 (public); README quickstart commands run verbatim: `uv run python -m lore match "drain 503"` => 'gateway-drain-window confidence=0.90 evidence: signature:drain 503; keyword:503; keyword:drain' (matches README:44-46), `lore compile --class does-not-exist` => exit=2 (matches README:113-114), `uv run ruff check .` => 'All checks passed!' exit=0. (B) no stale 238/10-curated: `grep -rn "238" README.md docs/ CHANGELOG.md AGENTS.md SECURITY.md` => no hits; '10 curated classes' is factually accurate (lore/classes.py has 10 FailureClass( entries at lines 39,56,73,97,120,137,160,184,201,225 + UNCLASSIFIED_CLASS at 256; live registry lists 10 curated + unclassified), so README:138/256 and CHANGELOG:19/45 are correct, not stale. (C) live counts verified: `uv run pytest -q` => '269 passed in 0.30s' exit=0 and guard command `uv run pytest -x --tb=short` => '269 passed in 0.24s' exit=0; `ls tests/test_*.py | wc -l` => 14; README.md:118 '# 269 passed', README.md:257 '**269 tests passing**', docs/INSTALL.md:52 '269 passed in 0.74s', docs/INSTALL.md:59 '**269 tests** (14 test files...)' all match live. Commit 971a1a6 corrected the prior 259/12 staleness (which a prior eval in .gitreins/history flagged) to 269/14.
All three sub-claims pass: repo is public with a working verbatim quickstart, no stale 238/10-curated claims (10 curated is accurate), and live counts (269 tests / 14 files) match the docs exactly.

## Summary

Judge Result: LORE-019

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ README quickstart works on the now-public repo; no stale 238/10-curated claims; live counts verified: (A) PUBLIC+quickstart: anonymous `git ls-remote https://github.com/get-h3/lore` exit=0 and `curl https://github.com/get-h3/lore` => HTTP 200 (public); README quickstart commands run verbatim: `uv run python -m lore match "drain 503"` => 'gateway-drain-window confidence=0.90 evidence: signature:drain 503; keyword:503; keyword:drain' (matches README:44-46), `lore compile --class does-not-exist` => exit=2 (matches README:113-114), `uv run ruff check .` => 'All checks passed!' exit=0. (B) no stale 238/10-curated: `grep -rn "238" README.md docs/ CHANGELOG.md AGENTS.md SECURITY.md` => no hits; '10 curated classes' is factually accurate (lore/classes.py has 10 FailureClass( entries at lines 39,56,73,97,120,137,160,184,201,225 + UNCLASSIFIED_CLASS at 256; live registry lists 10 curated + unclassified), so README:138/256 and CHANGELOG:19/45 are correct, not stale. (C) live counts verified: `uv run pytest -q` => '269 passed in 0.30s' exit=0 and guard command `uv run pytest -x --tb=short` => '269 passed in 0.24s' exit=0; `ls tests/test_*.py | wc -l` => 14; README.md:118 '# 269 passed', README.md:257 '**269 tests passing**', docs/INSTALL.md:52 '269 passed in 0.74s', docs/INSTALL.md:59 '**269 tests** (14 test files...)' all match live. Commit 971a1a6 corrected the prior 259/12 staleness (which a prior eval in .gitreins/history flagged) to 269/14.
All three sub-claims pass: repo is public with a working verbatim quickstart, no stale 238/10-curated claims (10 curated is accurate), and live counts (269 tests / 14 files) match the docs exactly.

Overall: PASS ✓
