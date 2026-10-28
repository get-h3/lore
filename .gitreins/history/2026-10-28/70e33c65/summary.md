# Verdict: PERF-3

**Task:** absorb_sweep per-invocation classify memoization
**Evaluated:** 2026-10-28T20:30:00.578322
**Result:** ✗ FAIL

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✗ **tier2**
  - INCOMPLETE
  ✗ grep -n classification_cache lore/absorb.py shows the per-invocation memo inside absorb_sweep with no global cache; hyperfine A/B via /tmp/lore_absorb_perf.py exits 0 containing 'faster than'; JSON-semantic equality held; ch:trace row=PERF-3 resolves with test=tests/test_absorb_perf.py: Memo part PASSES: `grep -n classification_cache lore/absorb.py` -> 393 (dict literal), 398/399 (lookup), 402 (store), all inside `def absorb_sweep` at lore/absorb.py:353; repo-wide `grep -rn classification_cache --include=*.py` returns only those 4 lines, so no global/module-level cache. Hyperfine A/B PASSES: `hyperfine --warmup 1 --runs 3 'env LORE_PERF_CANDIDATE=0 .venv/bin/python -O /tmp/lore_absorb_perf.py --scale 100 --number 3 --repeats 3' '...CANDIDATE=1...'` exit_code 0, Summary: '1.18 ± 0.55 times faster than ...' (contains 'faster than'). JSON-semantic equality PASSES: /tmp/lore_absorb_perf.py asserts `json.dumps(baseline, sort_keys=True) == json.dumps(trial, sort_keys=True)` and the block-count sum, and the run exited 0. Tests PASS: `uv run pytest tests/test_absorb_perf.py -q` -> '2 passed in 0.06s' (exit 0). HOWEVER the ch:trace requirement FAILS: `grep -rn 'row=PERF-3'` matches only .gitreins/tasks.yaml:612 (the criteria text itself) and .gitreins/history/2026-10-28/c7eadca2/verdict.json:5 (criteria echo). There is no `ch:trace row=PERF-3 ... test=tests/test_absorb_perf.py` marker anywhere — not in tests/test_absorb_perf.py (which has no ch:trace line, unlike tests/test_count_guard.py:106 and tests/test_lore055_consult_missing_input.py:20), not in docs/CHANGELOG, and not in .coding-hermes/board/events.jsonl (the only PERF-3 event is audit id 386, which carries no ch:trace field; existing ch:trace rows there cover LORE-046/054/055/056/067-R2/QA-LORE-2/3/RELEASE-LORE-003 only). The trace row therefore does not resolve.
The memoization, hyperfine A/B ('faster than', exit 0), JSON-semantic equality, and tests/test_absorb_perf.py (2 passed) all hold, but the required ch:trace row=PERF-3 marker bound to test=tests/test_absorb_perf.py was never written anywhere in the repo.

## Summary

Judge Result: PERF-3

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: FAIL
  INCOMPLETE
  ✗ grep -n classification_cache lore/absorb.py shows the per-invocation memo inside absorb_sweep with no global cache; hyperfine A/B via /tmp/lore_absorb_perf.py exits 0 containing 'faster than'; JSON-semantic equality held; ch:trace row=PERF-3 resolves with test=tests/test_absorb_perf.py: Memo part PASSES: `grep -n classification_cache lore/absorb.py` -> 393 (dict literal), 398/399 (lookup), 402 (store), all inside `def absorb_sweep` at lore/absorb.py:353; repo-wide `grep -rn classification_cache --include=*.py` returns only those 4 lines, so no global/module-level cache. Hyperfine A/B PASSES: `hyperfine --warmup 1 --runs 3 'env LORE_PERF_CANDIDATE=0 .venv/bin/python -O /tmp/lore_absorb_perf.py --scale 100 --number 3 --repeats 3' '...CANDIDATE=1...'` exit_code 0, Summary: '1.18 ± 0.55 times faster than ...' (contains 'faster than'). JSON-semantic equality PASSES: /tmp/lore_absorb_perf.py asserts `json.dumps(baseline, sort_keys=True) == json.dumps(trial, sort_keys=True)` and the block-count sum, and the run exited 0. Tests PASS: `uv run pytest tests/test_absorb_perf.py -q` -> '2 passed in 0.06s' (exit 0). HOWEVER the ch:trace requirement FAILS: `grep -rn 'row=PERF-3'` matches only .gitreins/tasks.yaml:612 (the criteria text itself) and .gitreins/history/2026-10-28/c7eadca2/verdict.json:5 (criteria echo). There is no `ch:trace row=PERF-3 ... test=tests/test_absorb_perf.py` marker anywhere — not in tests/test_absorb_perf.py (which has no ch:trace line, unlike tests/test_count_guard.py:106 and tests/test_lore055_consult_missing_input.py:20), not in docs/CHANGELOG, and not in .coding-hermes/board/events.jsonl (the only PERF-3 event is audit id 386, which carries no ch:trace field; existing ch:trace rows there cover LORE-046/054/055/056/067-R2/QA-LORE-2/3/RELEASE-LORE-003 only). The trace row therefore does not resolve.
The memoization, hyperfine A/B ('faster than', exit 0), JSON-semantic equality, and tests/test_absorb_perf.py (2 passed) all hold, but the required ch:trace row=PERF-3 marker bound to test=tests/test_absorb_perf.py was never written anywhere in the repo.

Overall: FAIL ✗
