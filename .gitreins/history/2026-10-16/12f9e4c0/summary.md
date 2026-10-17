# Verdict: PERF-1

**Task:** compiler: replace to_dict/from_dict clone with dataclasses.replace
**Evaluated:** 2026-10-16T19:10:05.261189
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ The compiler's compile_all clones Check instances via Check.from_dict(c.to_dict()) on lore/compiler.py:939. Measured to be 114 us/op. Candidate: dataclasses.replace(c, evidence=[dict(e) for e in c.evidence]) measured at 71.87 us/op (1.59x faster). Acceptance: the candidate change is integrated, benchmark confirms >=1.5x speedup on the path, and full suite passes (ruff check+format clean, pytest green, count guard PASS). Output of compile_all is functionally identical.: Integrated: commit b52efca modifies lore/compiler.py:945-948 to `dataclasses.replace(c, evidence=[dict(e) for e in c.evidence])` (with `import dataclasses` at line 34), replacing the old `Check.from_dict(c.to_dict())` clone. Speedup: isolated timeit (N=20000, min of 7 repeats) old=3.22 us/op vs new=1.51 us/op = 2.13x (>=1.5x); `uv run python scripts/bench.py` exits 0 with 'PASS: 7 operations measured' (compile_all_registry 78.89 us/op). Functional identity: scripted comparison over every entry in lore/compiler.py `_CHECKS` found 0 mismatches (old==new, evidence lists equal, evidence list/dicts are fresh copies); compile_all() returns 14 runbooks / 35 checks and from_dict(to_dict(rb))==rb for all. Tests: `uv run pytest -x --tb=short` -> '473 passed in 2.39s', exit 0. Lint: `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` -> '179 files already formatted', exit 0. Count guard: `sh scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=473 matches live=473; class-count=13; no stale count literals in living docs', exit 0. LSP diagnostics: 0 findings.
dataclasses.replace clone is integrated in lore/compiler.py, measured 2.13x faster on the path, functionally identical output, with pytest (473 passed), ruff check+format, and the count guard all green.

## Summary

Judge Result: PERF-1

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ The compiler's compile_all clones Check instances via Check.from_dict(c.to_dict()) on lore/compiler.py:939. Measured to be 114 us/op. Candidate: dataclasses.replace(c, evidence=[dict(e) for e in c.evidence]) measured at 71.87 us/op (1.59x faster). Acceptance: the candidate change is integrated, benchmark confirms >=1.5x speedup on the path, and full suite passes (ruff check+format clean, pytest green, count guard PASS). Output of compile_all is functionally identical.: Integrated: commit b52efca modifies lore/compiler.py:945-948 to `dataclasses.replace(c, evidence=[dict(e) for e in c.evidence])` (with `import dataclasses` at line 34), replacing the old `Check.from_dict(c.to_dict())` clone. Speedup: isolated timeit (N=20000, min of 7 repeats) old=3.22 us/op vs new=1.51 us/op = 2.13x (>=1.5x); `uv run python scripts/bench.py` exits 0 with 'PASS: 7 operations measured' (compile_all_registry 78.89 us/op). Functional identity: scripted comparison over every entry in lore/compiler.py `_CHECKS` found 0 mismatches (old==new, evidence lists equal, evidence list/dicts are fresh copies); compile_all() returns 14 runbooks / 35 checks and from_dict(to_dict(rb))==rb for all. Tests: `uv run pytest -x --tb=short` -> '473 passed in 2.39s', exit 0. Lint: `uv run ruff check . --quiet` exit 0; `uv run ruff format --check .` -> '179 files already formatted', exit 0. Count guard: `sh scripts/check-test-count.sh` -> 'PASS: test-count guard: canonical=473 matches live=473; class-count=13; no stale count literals in living docs', exit 0. LSP diagnostics: 0 findings.
dataclasses.replace clone is integrated in lore/compiler.py, measured 2.13x faster on the path, functionally identical output, with pytest (473 passed), ruff check+format, and the count guard all green.

Overall: PASS ✓
