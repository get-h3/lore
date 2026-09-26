# Verdict: LORE-030

**Task:** Fresh-clone UX: fail fast with clear message when pytest runs without --extra dev
**Evaluated:** 2026-09-26T01:04:19.617634
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ bare uv sync in a fresh public clone then uv run pytest fails FAST with a clear message naming uv sync --extra dev; documented quickstart (uv sync --extra dev && uv run pytest) stays green; uv run pytest -q green on main and ruff clean: Fresh clone (git clone /home/kara/lore /tmp/lore_fresh @4f67b60) + bare `uv sync` (installs only lore==0.1.1, no pytest) + `uv run pytest` in a clean env (env -i, PATH excluding host dev venv): EXIT=4 (pytest.ExitCode.USAGE_ERROR), output is exactly 2 lines — 'ERROR: pytest could not import the lore package from this checkout... Fix: run uv sync --extra dev, then uv run pytest. See docs/INSTALL.md.' — with grep -c ModuleNotFoundError = 0 (no traceback flood) and wall time 0.66s (fails FAST). Guard is tests/conftest.py pytest_configure() raising pytest.UsageError(_FIX_MESSAGE) when `import lore` raises ModuleNotFoundError. Documented quickstart in the same fresh clone: `uv sync --extra dev` (installs pytest==9.1.1, ruff==0.16.8) then `uv run pytest -q` => EXIT=0, '293 passed in 0.47s'. Main tree: `uv run pytest -q` => '293 passed in 0.54s' (exit 0); `uv run ruff check .` => 'All checks passed!' (exit 0); LORE-030 regression file `uv run pytest tests/test_lore030_ux_guard.py -q` => '4 passed'. Docs name the fix: README.md:33/36 and docs/INSTALL.md:20/23.
Verified end-to-end: bare uv sync + uv run pytest fails fast with exit 4 and one clear message naming 'uv sync --extra dev', while the documented quickstart and main tree stay green (293 passed, ruff clean).

## Summary

Judge Result: LORE-030

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ bare uv sync in a fresh public clone then uv run pytest fails FAST with a clear message naming uv sync --extra dev; documented quickstart (uv sync --extra dev && uv run pytest) stays green; uv run pytest -q green on main and ruff clean: Fresh clone (git clone /home/kara/lore /tmp/lore_fresh @4f67b60) + bare `uv sync` (installs only lore==0.1.1, no pytest) + `uv run pytest` in a clean env (env -i, PATH excluding host dev venv): EXIT=4 (pytest.ExitCode.USAGE_ERROR), output is exactly 2 lines — 'ERROR: pytest could not import the lore package from this checkout... Fix: run uv sync --extra dev, then uv run pytest. See docs/INSTALL.md.' — with grep -c ModuleNotFoundError = 0 (no traceback flood) and wall time 0.66s (fails FAST). Guard is tests/conftest.py pytest_configure() raising pytest.UsageError(_FIX_MESSAGE) when `import lore` raises ModuleNotFoundError. Documented quickstart in the same fresh clone: `uv sync --extra dev` (installs pytest==9.1.1, ruff==0.16.8) then `uv run pytest -q` => EXIT=0, '293 passed in 0.47s'. Main tree: `uv run pytest -q` => '293 passed in 0.54s' (exit 0); `uv run ruff check .` => 'All checks passed!' (exit 0); LORE-030 regression file `uv run pytest tests/test_lore030_ux_guard.py -q` => '4 passed'. Docs name the fix: README.md:33/36 and docs/INSTALL.md:20/23.
Verified end-to-end: bare uv sync + uv run pytest fails fast with exit 4 and one clear message naming 'uv sync --extra dev', while the documented quickstart and main tree stay green (293 passed, ruff clean).

Overall: PASS ✓
