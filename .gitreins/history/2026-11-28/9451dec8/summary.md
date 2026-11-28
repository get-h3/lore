# Verdict: DOC-10-R2

**Task:** Refresh v0.3.0 version claims in README and release docs
**Evaluated:** 2026-11-28T11:05:57.729869
**Result:** ✓ PASS

## Criteria

- ✓ **PROOF: README Status names version 0.3.0, tags v0.1.0/v0.2.0/v0.3.0, and only uses git rev-list --count v0.3.0..HEAD for the live commit count; docs/RELEASE.md enumerates the same tags; scripts/check-test-count.sh, pytest -x -q, and pyproject version agreement pass. FAILIF: any stale 0.2.0-only tag list, any README Status count based on v0.2.0, missing 0.3.0 in either doc, test/count failure, or version mismatch.**
  - README.md:381-387 Status reads "Development version stamp **0.3.0**, released **2026-11-21** as tag **v0.3.0** (commit `c769be4`)" and enumerates "**v0.1.0** (2026-09-24, commit `c655666`), **v0.2.0** (2026-11-16, commit `165cc8f`), and **v0.3.0** (2026-11-21, commit `c769be4`)"; the only live-count command is README.md:386 `git rev-list --count v0.3.0..HEAD`. docs/RELEASE.md:7-10 enumerates the identical three tags with identical dates/commits. Tag objects verified: `git rev-parse v0.1.0^{commit}`=c655666 (2026-09-24), v0.2.0=165cc8f (2026-11-16), v0.3.0=c769be4 (2026-11-21) — all match the docs. `sh scripts/check-test-count.sh` exit_code=0, output "PASS: test-count guard: canonical=588 matches live=588; class-count=13; no stale count literals in living docs". `uv run pytest -x -q` exit_code=0, output "588 passed in 11.36s". Version agreement: pyproject.toml:7 `version = "0.3.0"` == lore/__init__.py:3 `__version__ = "0.3.0"`. No stale 0.2.0-only tag list remains (grep for "Two tags exist"/"7 commits"/"counted 2026-11-17" in living docs returns nothing).
- ✓ **The README Status CHANGELOG anchor link (CHANGELOG.md#030--2026-11-21) resolves to an actual heading in CHANGELOG.md.**
  - CHANGELOG.md:10 contains the heading `## [0.3.0] — 2026-11-21`, which GitHub slugs to `#030--2026-11-21` — exactly the anchor used at README.md:383. Regex extraction of all `## [X.Y.Z] — date` headings confirms 0.3.0 is present alongside 0.2.0/0.1.2/0.1.1/0.1.0.
- ✓ **The commit SHAs and dates cited for each tag in README.md and docs/RELEASE.md match the actual git tag objects.**
  - `git rev-parse <tag>^{commit}` + `git log -1 --date=short` gives v0.1.0=c6556662c93b (2026-09-24), v0.2.0=165cc8f6d354 (2026-11-16), v0.3.0=c769be4265e7 (2026-11-21). All three match the SHAs/dates written at README.md:381-386 and docs/RELEASE.md:9-10 — no fabricated commit references.
- ✓ **No living doc still asserts the superseded "Two tags exist" / "7 commits past v0.2.0" / "counted 2026-11-17" claims; surviving v0.2.0..HEAD references are confined to allowlisted historical evidence.**
  - grep for "Two tags exist|7 commits|counted 2026-11-17" across README.md docs/*.md CONTRIBUTING.md returned no matches. Repo-wide grep for "v0.2.0..HEAD" hits only docs/qa/evidence/run-README-12/README.md:45, docs/qa/evidence/run-README-12/2026-11-24-sweep.txt:19, and docs/qa/evidence/run-DOC-10/README.md:28,41 — all under docs/qa/evidence/*, which scripts/count_sweep.py:39 lists in ALLOWLISTED_PATTERNS as dated historical evidence. check-test-count.sh exit_code=0 independently confirms no stale literals in living docs.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ PROOF: README Status names version 0.3.0, tags v0.1.0/v0.2.0/v0.3.0, and only uses git rev-list --count v0.3.0..HEAD for the live commit count; docs/RELEASE.md enumerates the same tags; scripts/check-test-count.sh, pytest -x -q, and pyproject version agreement pass. FAILIF: any stale 0.2.0-only tag list, any README Status count based on v0.2.0, missing 0.3.0 in either doc, test/count failure, or version mismatch.: README.md:381-387 Status reads "Development version stamp **0.3.0**, released **2026-11-21** as tag **v0.3.0** (commit `c769be4`)" and enumerates "**v0.1.0** (2026-09-24, commit `c655666`), **v0.2.0** (2026-11-16, commit `165cc8f`), and **v0.3.0** (2026-11-21, commit `c769be4`)"; the only live-count command is README.md:386 `git rev-list --count v0.3.0..HEAD`. docs/RELEASE.md:7-10 enumerates the identical three tags with identical dates/commits. Tag objects verified: `git rev-parse v0.1.0^{commit}`=c655666 (2026-09-24), v0.2.0=165cc8f (2026-11-16), v0.3.0=c769be4 (2026-11-21) — all match the docs. `sh scripts/check-test-count.sh` exit_code=0, output "PASS: test-count guard: canonical=588 matches live=588; class-count=13; no stale count literals in living docs". `uv run pytest -x -q` exit_code=0, output "588 passed in 11.36s". Version agreement: pyproject.toml:7 `version = "0.3.0"` == lore/__init__.py:3 `__version__ = "0.3.0"`. No stale 0.2.0-only tag list remains (grep for "Two tags exist"/"7 commits"/"counted 2026-11-17" in living docs returns nothing).
  ✓ The README Status CHANGELOG anchor link (CHANGELOG.md#030--2026-11-21) resolves to an actual heading in CHANGELOG.md.: CHANGELOG.md:10 contains the heading `## [0.3.0] — 2026-11-21`, which GitHub slugs to `#030--2026-11-21` — exactly the anchor used at README.md:383. Regex extraction of all `## [X.Y.Z] — date` headings confirms 0.3.0 is present alongside 0.2.0/0.1.2/0.1.1/0.1.0.
  ✓ The commit SHAs and dates cited for each tag in README.md and docs/RELEASE.md match the actual git tag objects.: `git rev-parse <tag>^{commit}` + `git log -1 --date=short` gives v0.1.0=c6556662c93b (2026-09-24), v0.2.0=165cc8f6d354 (2026-11-16), v0.3.0=c769be4265e7 (2026-11-21). All three match the SHAs/dates written at README.md:381-386 and docs/RELEASE.md:9-10 — no fabricated commit references.
  ✓ No living doc still asserts the superseded "Two tags exist" / "7 commits past v0.2.0" / "counted 2026-11-17" claims; surviving v0.2.0..HEAD references are confined to allowlisted historical evidence.: grep for "Two tags exist|7 commits|counted 2026-11-17" across README.md docs/*.md CONTRIBUTING.md returned no matches. Repo-wide grep for "v0.2.0..HEAD" hits only docs/qa/evidence/run-README-12/README.md:45, docs/qa/evidence/run-README-12/2026-11-24-sweep.txt:19, and docs/qa/evidence/run-DOC-10/README.md:28,41 — all under docs/qa/evidence/*, which scripts/count_sweep.py:39 lists in ALLOWLISTED_PATTERNS as dated historical evidence. check-test-count.sh exit_code=0 independently confirms no stale literals in living docs.
README Status and docs/RELEASE.md both correctly name v0.3.0 with the full v0.1.0/v0.2.0/v0.3.0 tag list, the live count uses only v0.3.0..HEAD, and the count guard, pytest -x -q (588 passed), and pyproject/__init__ version agreement all pass.
- ✓ **fix_verification**
  - fix_verification: 0 finding(s) verified

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ PROOF: README Status names version 0.3.0, tags v0.1.0/v0.2.0/v0.3.0, and only uses git rev-list --count v0.3.0..HEAD for the live commit count; docs/RELEASE.md enumerates the same tags; scripts/check-test-count.sh, pytest -x -q, and pyproject version agreement pass. FAILIF: any stale 0.2.0-only tag list, any README Status count based on v0.2.0, missing 0.3.0 in either doc, test/count failure, or version mismatch.: README.md:381-387 Status reads "Development version stamp **0.3.0**, released **2026-11-21** as tag **v0.3.0** (commit `c769be4`)" and enumerates "**v0.1.0** (2026-09-24, commit `c655666`), **v0.2.0** (2026-11-16, commit `165cc8f`), and **v0.3.0** (2026-11-21, commit `c769be4`)"; the only live-count command is README.md:386 `git rev-list --count v0.3.0..HEAD`. docs/RELEASE.md:7-10 enumerates the identical three tags with identical dates/commits. Tag objects verified: `git rev-parse v0.1.0^{commit}`=c655666 (2026-09-24), v0.2.0=165cc8f (2026-11-16), v0.3.0=c769be4 (2026-11-21) — all match the docs. `sh scripts/check-test-count.sh` exit_code=0, output "PASS: test-count guard: canonical=588 matches live=588; class-count=13; no stale count literals in living docs". `uv run pytest -x -q` exit_code=0, output "588 passed in 11.36s". Version agreement: pyproject.toml:7 `version = "0.3.0"` == lore/__init__.py:3 `__version__ = "0.3.0"`. No stale 0.2.0-only tag list remains (grep for "Two tags exist"/"7 commits"/"counted 2026-11-17" in living docs returns nothing).
  ✓ The README Status CHANGELOG anchor link (CHANGELOG.md#030--2026-11-21) resolves to an actual heading in CHANGELOG.md.: CHANGELOG.md:10 contains the heading `## [0.3.0] — 2026-11-21`, which GitHub slugs to `#030--2026-11-21` — exactly the anchor used at README.md:383. Regex extraction of all `## [X.Y.Z] — date` headings confirms 0.3.0 is present alongside 0.2.0/0.1.2/0.1.1/0.1.0.
  ✓ The commit SHAs and dates cited for each tag in README.md and docs/RELEASE.md match the actual git tag objects.: `git rev-parse <tag>^{commit}` + `git log -1 --date=short` gives v0.1.0=c6556662c93b (2026-09-24), v0.2.0=165cc8f6d354 (2026-11-16), v0.3.0=c769be4265e7 (2026-11-21). All three match the SHAs/dates written at README.md:381-386 and docs/RELEASE.md:9-10 — no fabricated commit references.
  ✓ No living doc still asserts the superseded "Two tags exist" / "7 commits past v0.2.0" / "counted 2026-11-17" claims; surviving v0.2.0..HEAD references are confined to allowlisted historical evidence.: grep for "Two tags exist|7 commits|counted 2026-11-17" across README.md docs/*.md CONTRIBUTING.md returned no matches. Repo-wide grep for "v0.2.0..HEAD" hits only docs/qa/evidence/run-README-12/README.md:45, docs/qa/evidence/run-README-12/2026-11-24-sweep.txt:19, and docs/qa/evidence/run-DOC-10/README.md:28,41 — all under docs/qa/evidence/*, which scripts/count_sweep.py:39 lists in ALLOWLISTED_PATTERNS as dated historical evidence. check-test-count.sh exit_code=0 independently confirms no stale literals in living docs.
README Status and docs/RELEASE.md both correctly name v0.3.0 with the full v0.1.0/v0.2.0/v0.3.0 tag list, the live count uses only v0.3.0..HEAD, and the count guard, pytest -x -q (588 passed), and pyproject/__init__ version agreement all pass.

Stage fix_verification: PASS
  fix_verification: 0 finding(s) verified

Overall: PASS ✓
