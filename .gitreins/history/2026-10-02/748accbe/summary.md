# Verdict: QA-LORE-2

**Task:** PyPI name squat: lore distribution occupied by instacart; distinct dist name + source-install docs required before any publish
**Evaluated:** 2026-10-02T05:00:45.724846
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Remedy at HEAD: pyproject name=get-h3-lore; README never-install-lore notice; tests/test_dist_name.py green; 384 tests pass: pyproject.toml:6 `name = "get-h3-lore"` (not the squatted bare `lore`); README.md:156-163 carries the notice '> **Never `pip install lore`.** That distribution name on PyPI belongs to an unrelated third-party package (instacart/lore) ... The PyPI *distribution* name reserved for us is `get-h3-lore`' (mirrored in docs/INSTALL.md:60,352); `uv run pytest tests/test_dist_name.py -v` => '4 passed in 0.01s' (all four: distribution_name_is_not_the_squatted_bare_name, console_script_still_named_lore, import_package_still_lore_with_version, never_pip_install_lore_warning_in_docs); full suite `uv run pytest -x --tb=short` => '384 passed in 10.36s', exit_code 0.
All remedy elements verified at HEAD: dist name get-h3-lore, README/INSTALL never-install-lore notices, test_dist_name.py green, and the full 384-test suite passes.

## Summary

Judge Result: QA-LORE-2

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Remedy at HEAD: pyproject name=get-h3-lore; README never-install-lore notice; tests/test_dist_name.py green; 384 tests pass: pyproject.toml:6 `name = "get-h3-lore"` (not the squatted bare `lore`); README.md:156-163 carries the notice '> **Never `pip install lore`.** That distribution name on PyPI belongs to an unrelated third-party package (instacart/lore) ... The PyPI *distribution* name reserved for us is `get-h3-lore`' (mirrored in docs/INSTALL.md:60,352); `uv run pytest tests/test_dist_name.py -v` => '4 passed in 0.01s' (all four: distribution_name_is_not_the_squatted_bare_name, console_script_still_named_lore, import_package_still_lore_with_version, never_pip_install_lore_warning_in_docs); full suite `uv run pytest -x --tb=short` => '384 passed in 10.36s', exit_code 0.
All remedy elements verified at HEAD: dist name get-h3-lore, README/INSTALL never-install-lore notices, test_dist_name.py green, and the full 384-test suite passes.

Overall: PASS ✓
