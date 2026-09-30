# Verdict: RELEASE-LORE-002

**Task:** PyPI distribution name decision + source-only install posture (verify-only close)
**Evaluated:** 2026-09-30T23:55:58.155499
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Re-verify at HEAD that the distribution name is a distinct unoccupied name ('get-h3-lore', PyPI HTTP 404) while the foreign 'lore' owner (instacart/lore 0.8.6) makes 'pip install lore' unusable; import package and console script remain 'lore'; README/INSTALL/RELEASE document the collision and source-only install posture; naming contract pinned by tests; suite + ruff + count guard green at the verified sha.: HEAD=4498a25aed3115b2958fb3c811cb2f66ed293e3c (clean tree). PyPI: `curl -o /dev/null -w %{http_code} https://pypi.org/pypi/get-h3-lore/json` -> 404 (unoccupied); `https://pypi.org/pypi/lore/json` -> 200 with author 'Montana Low and Jeremy Stanley' <montana@instacart.com> (instacart/lore), so bare `pip install lore` is unusable. pyproject.toml: name="get-h3-lore" v0.1.2, [project.scripts] lore="lore.__main__:main", packages.find include=["lore*"]. Runtime: `uv run python -c 'import lore'` -> 'import lore OK 0.1.2'; `uv run lore --help` -> 'usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit}'. Docs: README.md:156-159 ('Never `pip install lore`', instacart/lore, dist name get-h3-lore, not published); docs/INSTALL.md:38-42 and 330-333 (same + 'source-only install'); docs/RELEASE.md:9-13 (dist name get-h3-lore, 'PyPI publishing is NOT enabled', foreign instacart/lore). Contract pinned: tests/test_dist_name.py (name==get-h3-lore and !=lore, console script lore, import lore version, README+INSTALL warning) and tests/test_cli_surface.py:316-329 (importlib.metadata.version("get-h3-lore") + uv.lock entry). Green at sha: `uv run pytest -q -p no:cacheprovider` -> '353 passed in 2.63s', exit 0; `uv run ruff check .` -> 'All checks passed!', exit 0; `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=353 matches live=353; class-count=13; no stale count literals in living docs', exit 0.
Verified at HEAD 4498a25: get-h3-lore is unoccupied on PyPI (404) while instacart/lore owns bare 'lore' (200), import package/console script remain 'lore', README/INSTALL/RELEASE document the collision and source-only posture, the naming contract is pinned by tests, and pytest (353 passed), ruff, and the count guard are all green.

## Summary

Judge Result: RELEASE-LORE-002

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Re-verify at HEAD that the distribution name is a distinct unoccupied name ('get-h3-lore', PyPI HTTP 404) while the foreign 'lore' owner (instacart/lore 0.8.6) makes 'pip install lore' unusable; import package and console script remain 'lore'; README/INSTALL/RELEASE document the collision and source-only install posture; naming contract pinned by tests; suite + ruff + count guard green at the verified sha.: HEAD=4498a25aed3115b2958fb3c811cb2f66ed293e3c (clean tree). PyPI: `curl -o /dev/null -w %{http_code} https://pypi.org/pypi/get-h3-lore/json` -> 404 (unoccupied); `https://pypi.org/pypi/lore/json` -> 200 with author 'Montana Low and Jeremy Stanley' <montana@instacart.com> (instacart/lore), so bare `pip install lore` is unusable. pyproject.toml: name="get-h3-lore" v0.1.2, [project.scripts] lore="lore.__main__:main", packages.find include=["lore*"]. Runtime: `uv run python -c 'import lore'` -> 'import lore OK 0.1.2'; `uv run lore --help` -> 'usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit}'. Docs: README.md:156-159 ('Never `pip install lore`', instacart/lore, dist name get-h3-lore, not published); docs/INSTALL.md:38-42 and 330-333 (same + 'source-only install'); docs/RELEASE.md:9-13 (dist name get-h3-lore, 'PyPI publishing is NOT enabled', foreign instacart/lore). Contract pinned: tests/test_dist_name.py (name==get-h3-lore and !=lore, console script lore, import lore version, README+INSTALL warning) and tests/test_cli_surface.py:316-329 (importlib.metadata.version("get-h3-lore") + uv.lock entry). Green at sha: `uv run pytest -q -p no:cacheprovider` -> '353 passed in 2.63s', exit 0; `uv run ruff check .` -> 'All checks passed!', exit 0; `bash scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=353 matches live=353; class-count=13; no stale count literals in living docs', exit 0.
Verified at HEAD 4498a25: get-h3-lore is unoccupied on PyPI (404) while instacart/lore owns bare 'lore' (200), import package/console script remain 'lore', README/INSTALL/RELEASE document the collision and source-only posture, the naming contract is pinned by tests, and pytest (353 passed), ruff, and the count guard are all green.

Overall: PASS ✓
