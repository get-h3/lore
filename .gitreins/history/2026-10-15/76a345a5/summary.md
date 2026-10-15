# Verdict: LORE-054

**Task:** Implement match --class filter
**Evaluated:** 2026-10-15T01:10:54.398414
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ lore match <symptoms> --class <id> accepts documented flag, validates class exists, filters results, exits 2 on unknown class, 4 tests pass, guard green: Flag documented (README.md:409 `lore match "<symptoms|log line>" [--class ...]`; `lore match --help` lists `--class CLASS_ID  filter results to only the named class (must be a valid registry class)`). Parser adds it at lore/__main__.py:623-627 (dest=class_id). Validation at lore/__main__.py:77-84 rejects ids not in get_registry().all_classes(), printing "error: unknown class '<id>'" to stderr and returning 2. Filtering at lore/__main__.py:90-96 keeps only c.class_id == args.class_id, emitting "<id>\tconfidence=0.00\tevidence: none" when the class exists but doesn't match. Live CLI: `match "drain 503" --class gateway-drain-window` -> exit 0 with `gateway-drain-window\tconfidence=0.90\tevidence: signature:drain 503; keyword:503; keyword:drain`; `--class nonexistent-class` -> exit 2 + stderr "error: unknown class 'nonexistent-class'"; `match "completely unrelated" --class gateway-drain-window` -> exit 0 with `confidence=0.00`. Tests: `uv run pytest tests/test_lore054_match_class_filter.py -v` -> "4 passed in 0.20s" (all four PASSED). Full suite `uv run pytest -q` -> "435 passed in 2.17s" (exit 0). Guard: `gitreins guard` with files staged -> "Tier 1: DEGRADED PASS", "✓ tests (full)", guard log shows "435 passed in 1.85s", exit 0; lint lane skipped only for "no staged files", verified directly: `uv run ruff check .` -> "All checks passed!" (exit 0), `ruff format --check .` -> "167 files already formatted", `scripts/check-test-count.sh` -> "PASS: test-count guard: canonical=435 matches live=435".
The --class filter is implemented, documented, validated (exit 2 on unknown class), filters results correctly, all 4 new tests pass, the full 435-test suite is green, and the guard passes.

## Summary

Judge Result: LORE-054

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ lore match <symptoms> --class <id> accepts documented flag, validates class exists, filters results, exits 2 on unknown class, 4 tests pass, guard green: Flag documented (README.md:409 `lore match "<symptoms|log line>" [--class ...]`; `lore match --help` lists `--class CLASS_ID  filter results to only the named class (must be a valid registry class)`). Parser adds it at lore/__main__.py:623-627 (dest=class_id). Validation at lore/__main__.py:77-84 rejects ids not in get_registry().all_classes(), printing "error: unknown class '<id>'" to stderr and returning 2. Filtering at lore/__main__.py:90-96 keeps only c.class_id == args.class_id, emitting "<id>\tconfidence=0.00\tevidence: none" when the class exists but doesn't match. Live CLI: `match "drain 503" --class gateway-drain-window` -> exit 0 with `gateway-drain-window\tconfidence=0.90\tevidence: signature:drain 503; keyword:503; keyword:drain`; `--class nonexistent-class` -> exit 2 + stderr "error: unknown class 'nonexistent-class'"; `match "completely unrelated" --class gateway-drain-window` -> exit 0 with `confidence=0.00`. Tests: `uv run pytest tests/test_lore054_match_class_filter.py -v` -> "4 passed in 0.20s" (all four PASSED). Full suite `uv run pytest -q` -> "435 passed in 2.17s" (exit 0). Guard: `gitreins guard` with files staged -> "Tier 1: DEGRADED PASS", "✓ tests (full)", guard log shows "435 passed in 1.85s", exit 0; lint lane skipped only for "no staged files", verified directly: `uv run ruff check .` -> "All checks passed!" (exit 0), `ruff format --check .` -> "167 files already formatted", `scripts/check-test-count.sh` -> "PASS: test-count guard: canonical=435 matches live=435".
The --class filter is implemented, documented, validated (exit 2 on unknown class), filters results correctly, all 4 new tests pass, the full 435-test suite is green, and the guard passes.

Overall: PASS ✓
