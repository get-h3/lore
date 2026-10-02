# Verdict: LORE-044

**Task:** INSTALL.md: document how a fresh user obtains uv
**Evaluated:** 2026-10-01T12:22:49.623946
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ docs/INSTALL.md documents obtaining uv (installer command with note re: gated surfaces / curl-to-shell) and the bare-box unzip gap for self-update; docs-only, gates green: docs/INSTALL.md:15-35 adds '### Installing uv': installer command `curl -LsSf https://astral.sh/uv/install.sh | sh` (line 20) with explicit note it 'pipes a downloaded script straight into sh' and is 'unreachable on gated/blocked-network surfaces' (line 24); bare-box archive-tool gap documented (installer requires `tar`; Linux/macOS `.tar.gz` vs Windows-only `.zip` needing `unzip`, lines 26-27) plus manual standalone-release fallback (line 29); self-update gap covered — `uv self update` re-runs the same installer so it needs the archive tool and is standalone-installer-only (lines 32-35). Docs-only confirmed: commit 6dfe3b0 changed only docs/INSTALL.md (1 file, 22 insertions). Gates green: `uv run pytest -x --tb=short` => '364 passed in 8.90s' (exit 0); `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` => '142 files already formatted' exit 0; `bash scripts/check-test-count.sh` => 'PASS: test-count guard: canonical=364 matches live=364; class-count=13; no stale count literals in living docs' exit 0.
docs/INSTALL.md documents uv acquisition (curl-to-shell installer, gated-surface caveat, bare-box tar/unzip gap for self-update) as a docs-only change with all gates green.

## Summary

Judge Result: LORE-044

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ docs/INSTALL.md documents obtaining uv (installer command with note re: gated surfaces / curl-to-shell) and the bare-box unzip gap for self-update; docs-only, gates green: docs/INSTALL.md:15-35 adds '### Installing uv': installer command `curl -LsSf https://astral.sh/uv/install.sh | sh` (line 20) with explicit note it 'pipes a downloaded script straight into sh' and is 'unreachable on gated/blocked-network surfaces' (line 24); bare-box archive-tool gap documented (installer requires `tar`; Linux/macOS `.tar.gz` vs Windows-only `.zip` needing `unzip`, lines 26-27) plus manual standalone-release fallback (line 29); self-update gap covered — `uv self update` re-runs the same installer so it needs the archive tool and is standalone-installer-only (lines 32-35). Docs-only confirmed: commit 6dfe3b0 changed only docs/INSTALL.md (1 file, 22 insertions). Gates green: `uv run pytest -x --tb=short` => '364 passed in 8.90s' (exit 0); `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` => '142 files already formatted' exit 0; `bash scripts/check-test-count.sh` => 'PASS: test-count guard: canonical=364 matches live=364; class-count=13; no stale count literals in living docs' exit 0.
docs/INSTALL.md documents uv acquisition (curl-to-shell installer, gated-surface caveat, bare-box tar/unzip gap for self-update) as a docs-only change with all gates green.

Overall: PASS ✓
