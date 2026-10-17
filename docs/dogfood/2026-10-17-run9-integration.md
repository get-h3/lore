# Dogfood run 9 — fresh-machine + fix-verification at HEAD (2026-10-17)

**Target:** lore at HEAD `9b97fa2` (runs 8's HEAD was `25ddbb6`).
**Angle:** the delta — every surface the four foreman commits + PERF-1 touched since
run 8, driven first on the control host, then re-proved on a fresh bunker box.
**Verdict: SHIPPABLE.** All four landed fixes hold their documented contracts in real
use; the one fresh-box test failure is filed with a proven root cause (LORE-057).

## The promise, re-stated

*"A fresh user on a clean machine can install lore from the documented path, paste a
symptom line, get the failure class — and every fix the foremen landed since 10-13
actually works when a real user drives it."*

## What a real user does (and what actually happened)

### 1. The documented install path

Run 8's HEAD was 69 files behind (+9379 lines, runtime code included), so per the
delta rule the install leg re-ran rather than inheriting run 7/8's proofs. The fleet
QA battery (`bunker-qa.sh launch/collect`, get-h3/lore) ran on **bunker-mvp**
(las-01..04 all offline — tailscale "offline, last seen 4-15d ago"; host substitution
per the skill's sibling-host rule, `bunkerd` confirmed active before spawn).

Fresh box results (agent `e864c056`, QA HEAD 9b97fa2, 20 evidence rows,
`docs/qa/evidence/run9/battery-evidence.jsonl`):

| cell | verdict | note |
|---|---|---|
| fresh-install | OK | wheel install `get-h3-lore-0.1.2` + ruff 0.17.1 + pip-audit |
| ci-pass | OK | act: 1 job green, rc=0 |
| upgrade | OK | previous release v0.1.0 → HEAD reinstall clean |
| docker-deploy / ui-probe | N/A | no compose file / web UI |
| chaos-resource | PASS | suite survives 3G memory cap |
| chaos-errorpath | OK | clean error on missing config (rc=2) |
| chaos-disconnect | UNVERIFIED | filed as LORE-058 (vacuous since the wheel switch) |

### 2. The four landed fixes, driven as real use (control host, then the fresh box)

| fix | documented contract | local | fresh box |
|---|---|---|---|
| LORE-054 `match --class` | valid match 0.90 / valid-no-match 0.00 / unknown class exit 2 | A1-A4 ✓ | S0/S1 ✓ |
| LORE-055 `consult` missing input | no title + no --failure → exit 2 usage error; real no-match stays exit 0 | B1/B2 ✓ | S2 ✓ |
| LORE-049 round-2 signatures | bare finding list AND guard FAILED+secrets both → gateway-guard-violation 0.90 | C1/C2 ✓ | S3 ✓ |
| LORE-056 `gate --record` | missing parent → ALLOW, parent created, one JSONL record; DENY arms write nothing | D1 + F3/F4/F5 ✓ | S4 ✓ |

DENY arms re-proven exactly (absorb w/o class, unknown class, empty reason):
`GATE: DENY`, one error line, rc=1, zero filesystem writes — propose-not-write
held on the deny side while ALLOW-with-record still appends exactly one line.

### 3. Things I myself got wrong (operator errors, recorded so nobody files them)

- `info show --class X` → exits 2 with a usage error; `show`'s class is a
  **positional** argument. `match` and `consult` take flags (`--class`, `--failure` /
  positional title), `show` takes positional. See skill note.
- `consult --failure` wants **the text inline**, not a file path — the string I first
  passed ("[PATH]") classified miss for the text it didn't contain. Docstring says
  the text is parsed and guard-shaped.
- `gate absorb` needs no --reason, class+lesson only. DECISION validation is in
  lore/absorb.py.

### 4. The fresh-box test failure (filed: LORE-057)

Fresh box `pytest` at the same sha: **1 failed / 471 passed / 1 skipped** (vs `473
passed` on the control head). The failed test is
`tests/test_count_guard.py::test_shell_guard_flags_and_clears_stale_class_count`.
Root cause via controlled A/B on the fresh box (diag4.log):

```
env PATH=... /usr/bin:/bin ... bash scripts/check-test-count.sh → rc=2 (guard "misconfigured")
env PATH=$HOME/tools/venv/bin:... bash scripts/check-test-count.sh → rc=0 (PASS)
```

The guard (`scripts/check-test-count.sh:33`) runs `python3 -m pytest --collect-only` and
inherits the caller's PATH; on the fresh agent pytest was invoked via its absolute
venv path and `python3` stayed system python — no pytest, no collect count, guard
exits 2 honestly naming itself misconfigured, never drift. The **test** (not the
guard) assumes venv on PATH. This is a P3 (guard itself fails honest); fix in the
test's subprocess env or resolve pytest from `sys.executable`.

Side note: the fresh clone is a `qa-sync` auto-commit `4156dc4` from the battery's
snapshot process whose tree is content-identical to 9b97fa2 for lore/scripts/tests
(diag.log); treated as leg artifact, not a state divergence.

### 5. PERF-1 re-proof (the fix lives in real use)

`lore/scripts/bench.py` under equal load, same command, ~15 min apart, worktree A/B
(pre = 0bf0220 right before the dataclasses.replace commit; post = HEAD 9b97fa2):

| | compile_all_registry |
|---|---|
| pre | 158.63 µs/op |
| post | **81.94 µs/op** |

**1.94× faster.** Whole-run hyperfine also moved 320.7 ms → 258.8 ms at the same knob.
The foreman's "1.45–2.13×" claim holds at HEAD under real, repeatable conditions;
flake counts: pre = 200 full-registry compile per batch × 3 batches. Fixes have
closed PERF-1 — no new row.

### 6. What remains open (re-confirmed, not re-filed)

- **LORE-051** still shows the `unclassified` row as a 14th class in `lore audit`
  (`grep unclassified /tmp/lore-df/audit.json` hits line 121 of the current audit JSON;
  table row count still names `14 classes; 1 with zero real commands`). Row premise
  intact; not re-filed, at the stopping condition.
- **LORE-053** (absorb --window error text quality) is unchanged at HEAD; not re-proven
  this run (start-8 surface, contract unchanged by the delta).

## Evidence index

- `docs/qa/evidence/run9/battery-evidence.jsonl` — the fleet battery's own rows
- `docs/qa/evidence/run9/local-probes*.txt`, `validate-probe.txt`, `audit.json` — real-use records
- `docs/qa/evidence/run9/fresh-delta.log`, `diag*.log` — fresh-box smoke + A/B
- `docs/qa/evidence/run9/pre-bench.txt`, `post-bench.txt` — PERF-1 re-proof numbers
- `docs/qa/evidence/run9/notes.md` — raw run notes (scratch-grade)
- `docs/qa/evidence/run9/evidence.tgz` — the agent's own log tarball, preserved verbatim
