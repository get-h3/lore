# Verdict: LORE-019

**Task:** Docs truth sweep: repo PUBLIC + live test/class counts
**Evaluated:** 2026-09-25T09:00:01.525644
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✗ **tier2**
  - INCOMPLETE
  ✗ README quickstart works on the now-public repo; no stale 238/10-curated claims; live counts verified: Two of three sub-claims PASS, one FAILS. (A) PUBLIC + quickstart: PASS — `gh repo view get-h3/lore --json visibility,isPrivate` => {"isPrivate":false,"visibility":"PUBLIC"}; fresh public clone `git clone https://github.com/get-h3/lore /tmp/lore-qs-test` exit=0; `uv sync --extra dev` exit=0; `uv run python -m lore match "drain 503"` => 'gateway-drain-window confidence=0.90 evidence: signature:drain 503; keyword:503; keyword:drain' (matches README verbatim); `uv run ruff check .` => 'All checks passed!'; grep for private/invite/internal-only in README/INSTALL/CHANGELOG => exit=1 (none). (B) no stale 238/10-curated: PASS — `grep -rn "238" README.md docs/ CHANGELOG.md AGENTS.md SECURITY.md .github/` => exit=1 (no hits; only historical .gitreins/history + .coding-hermes/waves records mention 238). '10 curated' is factually ACCURATE: live `SEED_CLASSES` len=10, registry `all_classes()` len=11, curated (non-unclassified)=10; README.md:138/256 and CHANGELOG.md:19/45 correctly say '10 curated classes + unclassified', and README.md:139-143 lists all 10 including gateway-guard-violation. (C) live counts verified: FAIL — README.md:118 says `uv run pytest -q  # 259 passed`, README.md:257 says '**259 tests passing**', docs/INSTALL.md:52 says '259 passed in 0.74s', docs/INSTALL.md:59 says 'The count to expect is **259 tests** (12 test files...)'. Live at merged HEAD c7a7c2c: `uv run pytest -q` => '269 passed in 0.42s' and `ls tests/*.py | wc -l` => 14. Root cause: 259/12 was accurate at LORE-019's base 75e5c73 (verified: `git checkout 75e5c73 && uv run pytest -q` => '259 passed', 12 test files), but same-wave siblings LORE-020 (cdb8499, tests/test_lore020_absorb_window.py) and LORE-021 (718b9e6, tests/test_lore021_naming_docs.py) added 2 test files / +10 tests that landed AFTER the docs sweep, and the docs were never re-synced. The docs are therefore stale by 10 tests and 2 test files at the tree the criterion is judged against, so 'live counts verified' is not satisfied.
Repo is genuinely PUBLIC and the README quickstart works end-to-end on a fresh clone with no stale 238 or 10-curated claims, but the pinned test counts (259 tests / 12 test files in README.md:118,257 and docs/INSTALL.md:52,59) are stale against the live tree (269 tests / 14 test files), so the 'live counts verified' requirement fails.

## Summary

Judge Result: LORE-019

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: FAIL
  INCOMPLETE
  ✗ README quickstart works on the now-public repo; no stale 238/10-curated claims; live counts verified: Two of three sub-claims PASS, one FAILS. (A) PUBLIC + quickstart: PASS — `gh repo view get-h3/lore --json visibility,isPrivate` => {"isPrivate":false,"visibility":"PUBLIC"}; fresh public clone `git clone https://github.com/get-h3/lore /tmp/lore-qs-test` exit=0; `uv sync --extra dev` exit=0; `uv run python -m lore match "drain 503"` => 'gateway-drain-window confidence=0.90 evidence: signature:drain 503; keyword:503; keyword:drain' (matches README verbatim); `uv run ruff check .` => 'All checks passed!'; grep for private/invite/internal-only in README/INSTALL/CHANGELOG => exit=1 (none). (B) no stale 238/10-curated: PASS — `grep -rn "238" README.md docs/ CHANGELOG.md AGENTS.md SECURITY.md .github/` => exit=1 (no hits; only historical .gitreins/history + .coding-hermes/waves records mention 238). '10 curated' is factually ACCURATE: live `SEED_CLASSES` len=10, registry `all_classes()` len=11, curated (non-unclassified)=10; README.md:138/256 and CHANGELOG.md:19/45 correctly say '10 curated classes + unclassified', and README.md:139-143 lists all 10 including gateway-guard-violation. (C) live counts verified: FAIL — README.md:118 says `uv run pytest -q  # 259 passed`, README.md:257 says '**259 tests passing**', docs/INSTALL.md:52 says '259 passed in 0.74s', docs/INSTALL.md:59 says 'The count to expect is **259 tests** (12 test files...)'. Live at merged HEAD c7a7c2c: `uv run pytest -q` => '269 passed in 0.42s' and `ls tests/*.py | wc -l` => 14. Root cause: 259/12 was accurate at LORE-019's base 75e5c73 (verified: `git checkout 75e5c73 && uv run pytest -q` => '259 passed', 12 test files), but same-wave siblings LORE-020 (cdb8499, tests/test_lore020_absorb_window.py) and LORE-021 (718b9e6, tests/test_lore021_naming_docs.py) added 2 test files / +10 tests that landed AFTER the docs sweep, and the docs were never re-synced. The docs are therefore stale by 10 tests and 2 test files at the tree the criterion is judged against, so 'live counts verified' is not satisfied.
Repo is genuinely PUBLIC and the README quickstart works end-to-end on a fresh clone with no stale 238 or 10-curated claims, but the pinned test counts (259 tests / 12 test files in README.md:118,257 and docs/INSTALL.md:52,59) are stale against the live tree (269 tests / 14 test files), so the 'live counts verified' requirement fails.

Overall: FAIL ✗
