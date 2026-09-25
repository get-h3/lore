# Verdict: QA-LORE-1

**Task:** Upgrade-path cell: install v0.1.0 then upgrade to main
**Evaluated:** 2026-09-25T10:33:29.208679
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Fresh install of lore@v0.1.0 from the public GitHub repo succeeds and CLI works; in-place upgrade to main succeeds and pytest+CLI smoke pass on the upgraded install: Reproduced end-to-end in a clean venv. (1) Fresh install: `pip install "git+https://github.com/get-h3/lore.git@v0.1.0"` -> exit 0, resolved to commit 1713ab81 (tag v0.1.0), `pip show lore` -> Version: 0.1.0; CLI works: `lore --help` exit 0 listing {match,consult,compile,validate,gate,absorb,show,audit}. (2) In-place upgrade: `pip install --upgrade "git+https://github.com/get-h3/lore.git@main"` -> exit 0 with log 'Found existing installation: lore 0.1.0 / Uninstalling lore-0.1.0 / Successfully installed lore-0.1.1' (a real reinstall, not a silent no-op — the exact failure the 0.1.0->0.1.1 bump in pyproject.toml:6 and uv.lock fixes); `pip show lore` -> Version: 0.1.1. (3) CLI smoke on upgraded install: `lore --help` exit 0, `lore match "disk full on node"` exit 0, `lore compile --help` exit 0, `lore gate --help` exit 0; installed package resolves to venv site-packages/lore/__init__.py with lore.__main__.main present. (4) pytest on upgraded install: `python -m pytest -q --tb=short` -> exit 0, '269 passed in 0.44s'; repo guard command `uv run pytest -x --tb=short` -> exit 0, '269 passed in 0.44s'.
Fresh v0.1.0 install from the public GitHub repo and in-place upgrade to main both succeed, with CLI smoke and 269 passing pytest tests on the upgraded 0.1.1 install.

## Summary

Judge Result: QA-LORE-1

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Fresh install of lore@v0.1.0 from the public GitHub repo succeeds and CLI works; in-place upgrade to main succeeds and pytest+CLI smoke pass on the upgraded install: Reproduced end-to-end in a clean venv. (1) Fresh install: `pip install "git+https://github.com/get-h3/lore.git@v0.1.0"` -> exit 0, resolved to commit 1713ab81 (tag v0.1.0), `pip show lore` -> Version: 0.1.0; CLI works: `lore --help` exit 0 listing {match,consult,compile,validate,gate,absorb,show,audit}. (2) In-place upgrade: `pip install --upgrade "git+https://github.com/get-h3/lore.git@main"` -> exit 0 with log 'Found existing installation: lore 0.1.0 / Uninstalling lore-0.1.0 / Successfully installed lore-0.1.1' (a real reinstall, not a silent no-op — the exact failure the 0.1.0->0.1.1 bump in pyproject.toml:6 and uv.lock fixes); `pip show lore` -> Version: 0.1.1. (3) CLI smoke on upgraded install: `lore --help` exit 0, `lore match "disk full on node"` exit 0, `lore compile --help` exit 0, `lore gate --help` exit 0; installed package resolves to venv site-packages/lore/__init__.py with lore.__main__.main present. (4) pytest on upgraded install: `python -m pytest -q --tb=short` -> exit 0, '269 passed in 0.44s'; repo guard command `uv run pytest -x --tb=short` -> exit 0, '269 passed in 0.44s'.
Fresh v0.1.0 install from the public GitHub repo and in-place upgrade to main both succeed, with CLI smoke and 269 passing pytest tests on the upgraded 0.1.1 install.

Overall: PASS ✓
