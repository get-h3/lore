# Verdict: LORE-053

**Task:** absorb --window fail-closed error teaches nothing: identical text for unrelated noise and a real export missing its fence; contract (fenced block + bare-ISO lines) appears nowhere in the error
**Evaluated:** 2026-10-18T14:51:44.204587
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ Error text for rc=2 absorb --window teaches the accepted shape (fenced block + bare-ISO lines) with an example, and distinguishes 'no export marker at all' (exit 0 empty result) from 'export marker present but no fenced block' (exit 2 with teaching error). Tests pin both contracts.: lore/evidence.py adds LOGSEY_EXPORT_SHAPE_HINT = "accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z kind=incident detail='gateway drain 503')"; parse_logsey_export raises "found export marker but no fenced block; {hint}" (no fence) vs "fenced block present but no parseable evidence lines; {hint}" (fence, bad lines), and returns [] when no marker (evidence.py:231-236, 273-278). lore/__main__.py:463-466 now prints f"error: {exc}" and returns 2, dropping the internal 'trail claims to be an export' wording. Live CLI verification: `printf 'random noise\n' | python -m lore absorb --window 2h` -> rc=0, stdout 'no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)'; `printf 'logsey export --window 1h\n'` -> rc=2, stderr 'error: found export marker but no fenced block; accepted shape: a fenced code block (``` or ```jsonl) ... (e.g. 2026-10-18T14:30:00Z kind=incident detail=...)' ; fence-with-bad-lines -> rc=2 with the distinct 'no parseable evidence lines' clause. Tests: tests/test_lore053_absorb_window_error.py pins both contracts at the subprocess boundary (test_no_export_marker_is_unclaimed_input_exit0_not_error asserts rc=0 + empty stderr; test_marker_without_fence_exit2_teaching_error and test_marker_with_fence_but_no_valid_lines_exit2_teaching_error assert rc=2 + shape/example text and no LOGSEY_EXPORT_CONTRACT_STATUS leak; test_both_teaching_errors_are_distinguishable asserts differing stderr), plus tests/test_cli_surface.py updated. Test run: `uv run pytest -q` -> exit_code 0, '514 passed in 2.77s'; targeted run of the two files -> '26 passed in 0.56s'.
absorb --window now emits a teaching error naming the fenced-block + bare-ISO shape with an example, distinguishes no-marker (exit 0) from marker-without-fence (exit 2), and both contracts are pinned by passing subprocess-level tests (514 passed).

## Summary

Judge Result: LORE-053

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ Error text for rc=2 absorb --window teaches the accepted shape (fenced block + bare-ISO lines) with an example, and distinguishes 'no export marker at all' (exit 0 empty result) from 'export marker present but no fenced block' (exit 2 with teaching error). Tests pin both contracts.: lore/evidence.py adds LOGSEY_EXPORT_SHAPE_HINT = "accepted shape: a fenced code block (``` or ```jsonl) containing lines that start with a bare ISO-8601 timestamp (e.g. 2026-10-18T14:30:00Z kind=incident detail='gateway drain 503')"; parse_logsey_export raises "found export marker but no fenced block; {hint}" (no fence) vs "fenced block present but no parseable evidence lines; {hint}" (fence, bad lines), and returns [] when no marker (evidence.py:231-236, 273-278). lore/__main__.py:463-466 now prints f"error: {exc}" and returns 2, dropping the internal 'trail claims to be an export' wording. Live CLI verification: `printf 'random noise\n' | python -m lore absorb --window 2h` -> rc=0, stdout 'no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)'; `printf 'logsey export --window 1h\n'` -> rc=2, stderr 'error: found export marker but no fenced block; accepted shape: a fenced code block (``` or ```jsonl) ... (e.g. 2026-10-18T14:30:00Z kind=incident detail=...)' ; fence-with-bad-lines -> rc=2 with the distinct 'no parseable evidence lines' clause. Tests: tests/test_lore053_absorb_window_error.py pins both contracts at the subprocess boundary (test_no_export_marker_is_unclaimed_input_exit0_not_error asserts rc=0 + empty stderr; test_marker_without_fence_exit2_teaching_error and test_marker_with_fence_but_no_valid_lines_exit2_teaching_error assert rc=2 + shape/example text and no LOGSEY_EXPORT_CONTRACT_STATUS leak; test_both_teaching_errors_are_distinguishable asserts differing stderr), plus tests/test_cli_surface.py updated. Test run: `uv run pytest -q` -> exit_code 0, '514 passed in 2.77s'; targeted run of the two files -> '26 passed in 0.56s'.
absorb --window now emits a teaching error naming the fenced-block + bare-ISO shape with an example, distinguishes no-marker (exit 0) from marker-without-fence (exit 2), and both contracts are pinned by passing subprocess-level tests (514 passed).

Overall: PASS ✓
