# Verdict: PERF-3

**Task:** absorb_sweep per-invocation classify memoization
**Evaluated:** 2026-10-28T20:36:29.998570
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ grep -n classification_cache lore/absorb.py shows the per-invocation memo inside absorb_sweep with no global cache; hyperfine A/B via /tmp/lore_absorb_perf.py exits 0 containing 'faster than'; JSON-semantic equality held; ch:trace row=PERF-3 resolves with test=tests/test_absorb_perf.py: Memo: `grep -n classification_cache lore/absorb.py` -> 393 (`classification_cache: dict[str, object] = {}`), 398/399 (lookup), 402 (store), all inside `def absorb_sweep` (lore/absorb.py:353); repo-wide `grep -rn classification_cache --include=*.py` returns only those 4 lines, so no module-level/global cache. Hyperfine A/B: `hyperfine --warmup 2 -r 5 -L cand 0,1 'LORE_PERF_CANDIDATE={cand} uv run python /tmp/lore_absorb_perf.py --scale 200 --number 20 --repeats 3'` exit_code=0, Summary line: 'LORE_PERF_CANDIDATE=1 ... ran 1.01 ± 0.20 times faster than LORE_PERF_CANDIDATE=0 ...' (contains 'faster than'). JSON-semantic equality: /tmp/lore_absorb_perf.py asserts `json.dumps(baseline, sort_keys=True) == json.dumps(trial, sort_keys=True)` and the run exited 0; tests/test_absorb_perf.py additionally asserts equality against a naive per-block-classify reference. ch:trace: .coding-hermes/board/tasks.jsonl:120 (PERF-3, committed in 7ab218c) worker_summary begins `ch:trace row=PERF-3 spec=none:no-spec-anchor-perf-row wave=... test=tests/test_absorb_perf.py doc=none:perf-code-not-doc evidence=hyperfine-A-B-faster-than...` — row resolves with the required test binding. Tests: `uv run pytest tests/test_absorb_perf.py -q` -> '2 passed in 0.07s', exit_code=0.
Per-invocation memo is function-local in absorb_sweep with no global cache, hyperfine A/B exits 0 reporting 'faster than' with JSON-semantic equality, the ch:trace row=PERF-3 marker binds test=tests/test_absorb_perf.py, and that test file passes (2 passed).

## Summary

Judge Result: PERF-3

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ grep -n classification_cache lore/absorb.py shows the per-invocation memo inside absorb_sweep with no global cache; hyperfine A/B via /tmp/lore_absorb_perf.py exits 0 containing 'faster than'; JSON-semantic equality held; ch:trace row=PERF-3 resolves with test=tests/test_absorb_perf.py: Memo: `grep -n classification_cache lore/absorb.py` -> 393 (`classification_cache: dict[str, object] = {}`), 398/399 (lookup), 402 (store), all inside `def absorb_sweep` (lore/absorb.py:353); repo-wide `grep -rn classification_cache --include=*.py` returns only those 4 lines, so no module-level/global cache. Hyperfine A/B: `hyperfine --warmup 2 -r 5 -L cand 0,1 'LORE_PERF_CANDIDATE={cand} uv run python /tmp/lore_absorb_perf.py --scale 200 --number 20 --repeats 3'` exit_code=0, Summary line: 'LORE_PERF_CANDIDATE=1 ... ran 1.01 ± 0.20 times faster than LORE_PERF_CANDIDATE=0 ...' (contains 'faster than'). JSON-semantic equality: /tmp/lore_absorb_perf.py asserts `json.dumps(baseline, sort_keys=True) == json.dumps(trial, sort_keys=True)` and the run exited 0; tests/test_absorb_perf.py additionally asserts equality against a naive per-block-classify reference. ch:trace: .coding-hermes/board/tasks.jsonl:120 (PERF-3, committed in 7ab218c) worker_summary begins `ch:trace row=PERF-3 spec=none:no-spec-anchor-perf-row wave=... test=tests/test_absorb_perf.py doc=none:perf-code-not-doc evidence=hyperfine-A-B-faster-than...` — row resolves with the required test binding. Tests: `uv run pytest tests/test_absorb_perf.py -q` -> '2 passed in 0.07s', exit_code=0.
Per-invocation memo is function-local in absorb_sweep with no global cache, hyperfine A/B exits 0 reporting 'faster than' with JSON-semantic equality, the ch:trace row=PERF-3 marker binds test=tests/test_absorb_perf.py, and that test file passes (2 passed).

Overall: PASS ✓
