# Verdict: LORE-067

**Task:** Wire incident data path into lore audit coverage matrix
**Evaluated:** 2026-10-22T15:18:03.689039
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  ✗ PRD US-3: every failure class seen in last 90 days. PRD SC-2: runs on fleet's last 90 days of incidents. Current coverage = registry size (literal True, SEED_CLASSES tuple). Must wire a real incident data source (logsey board events, or similar) so runbook_compiled is computed from actual incident data, not a constant. acceptance: lore audit --format json reports computed runbook_compiled per class based on incident data, not literal True; at least one integration test proves the coverage matrix reads from an incident source; docs/PRD.md US-3 and SC-2 claims are met: The literal True was replaced by `is_seen = rb.class_id in seen_classes` (lore/__main__.py:619,623), but the data path is non-functional and untested. (a) NO INTEGRATION TEST: `grep -rn 'incident_classes|incident_count|events_path' tests/*.py` returns zero matches; no tests/test_lore067*.py exists; the only test changes are weakened assertions (tests/test_cli_surface.py:88 `assert isinstance(r['runbook_compiled'], bool)`, tests/test_lore051_audit_bucket.py:132 `'| False |' or '| True |'`, tests/test_lore064_audit_wiring.py:329 just adds key names). (b) PRODUCTION PATH IS DEAD: `.coding-hermes/board/events.jsonl` exists with 221 lines / 177 in-window events, yet `uv run python -c 'from lore.incidents import incident_classes; print(incident_classes())'` -> `set()`. Cause: lore/incidents.py `_classify_task_ids` calls `classify(task_id)` on IDs like 'LORE-003', which returns class_id='unclassified', confidence=0.0 (classifier matches symptom text, not task IDs), and `_parse_absorb_class_ids` finds nothing because events.jsonl contains 0 occurrences of 'class_id'. (c) OUTPUT IS STILL A CONSTANT: `uv run python -m lore audit --format json` prints `"runbook_compiled": false` plus `"coverage_note": "incident source unavailable — coverage based on registry, not incidents"` for all 14 classes — a hardcoded constant in the opposite direction, not computed coverage. (d) `incident_count(events_path=events_path)` at lore/__main__.py:611 is called and its return value discarded ('side-effect call for future use'). (e) DOCS NOT UPDATED: docs/PRD.md:28 (US-3) and docs/PRD.md:63 (SC-2) are unchanged, and skills/lore-usage/SKILL.md:280 still states '`runbook_compiled` is the literal `True`' and that the US-3/SC-2 gap 'is filed as LORE-067'. Test suite run: `uv run pytest -x --tb=short -q` -> exit_code 0, '557 passed in 3.48s' — green, but no test exercises the incident source, so the acceptance clause 'at least one integration test proves the coverage matrix reads from an incident source' is unmet.
The literal True was swapped for a lookup, but the incident source resolves to an empty set in production (task-ID classification never matches), audit still emits a constant false for every class, no integration test covers the path, and PRD US-3/SC-2 docs remain unchanged.

## Summary

Judge Result: LORE-067

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: FAIL
  INCOMPLETE
  ✗ PRD US-3: every failure class seen in last 90 days. PRD SC-2: runs on fleet's last 90 days of incidents. Current coverage = registry size (literal True, SEED_CLASSES tuple). Must wire a real incident data source (logsey board events, or similar) so runbook_compiled is computed from actual incident data, not a constant. acceptance: lore audit --format json reports computed runbook_compiled per class based on incident data, not literal True; at least one integration test proves the coverage matrix reads from an incident source; docs/PRD.md US-3 and SC-2 claims are met: The literal True was replaced by `is_seen = rb.class_id in seen_classes` (lore/__main__.py:619,623), but the data path is non-functional and untested. (a) NO INTEGRATION TEST: `grep -rn 'incident_classes|incident_count|events_path' tests/*.py` returns zero matches; no tests/test_lore067*.py exists; the only test changes are weakened assertions (tests/test_cli_surface.py:88 `assert isinstance(r['runbook_compiled'], bool)`, tests/test_lore051_audit_bucket.py:132 `'| False |' or '| True |'`, tests/test_lore064_audit_wiring.py:329 just adds key names). (b) PRODUCTION PATH IS DEAD: `.coding-hermes/board/events.jsonl` exists with 221 lines / 177 in-window events, yet `uv run python -c 'from lore.incidents import incident_classes; print(incident_classes())'` -> `set()`. Cause: lore/incidents.py `_classify_task_ids` calls `classify(task_id)` on IDs like 'LORE-003', which returns class_id='unclassified', confidence=0.0 (classifier matches symptom text, not task IDs), and `_parse_absorb_class_ids` finds nothing because events.jsonl contains 0 occurrences of 'class_id'. (c) OUTPUT IS STILL A CONSTANT: `uv run python -m lore audit --format json` prints `"runbook_compiled": false` plus `"coverage_note": "incident source unavailable — coverage based on registry, not incidents"` for all 14 classes — a hardcoded constant in the opposite direction, not computed coverage. (d) `incident_count(events_path=events_path)` at lore/__main__.py:611 is called and its return value discarded ('side-effect call for future use'). (e) DOCS NOT UPDATED: docs/PRD.md:28 (US-3) and docs/PRD.md:63 (SC-2) are unchanged, and skills/lore-usage/SKILL.md:280 still states '`runbook_compiled` is the literal `True`' and that the US-3/SC-2 gap 'is filed as LORE-067'. Test suite run: `uv run pytest -x --tb=short -q` -> exit_code 0, '557 passed in 3.48s' — green, but no test exercises the incident source, so the acceptance clause 'at least one integration test proves the coverage matrix reads from an incident source' is unmet.
The literal True was swapped for a lookup, but the incident source resolves to an empty set in production (task-ID classification never matches), audit still emits a constant false for every class, no integration test covers the path, and PRD US-3/SC-2 docs remain unchanged.

Overall: FAIL ✗
