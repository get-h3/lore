# lore dogfood run 15 — 2026-10-23 (HEAD `da91c1e`)

**Angle:** the auditor's coverage question — PRD `US-3` / `SC-2` ("every failure class seen in the last 90 days",
"classes with incidents but no runbook") — now that the `LORE-067` fix has wired an incident data path into
`lore audit`. Runs 14 (ledger cost + install), 14b (coverage had *no* incident path), 14c (US-2 scribe) and 14d (US-1
responder) covered the adjacent surfaces; this run drives the fix that was filed against 14b's finding, at the HEAD
where it shipped, in real use — from the repo, from an empty directory, from a foreign fleet repo, and from a fresh
machine.

**Verdict: PROMISING-BUT-ROUGH on the coverage surface; SHIPPABLE everywhere else (install, responder, machine contract, speed).**

---

## 1. The promise (null hypothesis)

> "Run `lore audit` and you see whether the fleet's recent incidents are covered: per class, is a runbook compiled,
> how many checks does it carry, how many of those are real commands, and when was it last validated — and you can
> see the classes that have incidents but no runbook."
> (`README.md:399-400` Shipped bullet for `lore audit`; `docs/PRD.md` US-3 / SC-2.)

## 2. What a user actually gets

### 2a. In this repo (the maintainer's own checkout)

```
$ .venv/bin/lore audit --format json | jq -r '.classes[]|"\(.class_id)\tcompiled=\(.runbook_compiled)\tchecks=\(.check_count)"'
gateway-drain-window       compiled=true   checks=7
shared-checkout-collision  compiled=true   checks=3
secret-env-clobber         compiled=true   checks=2
disk-pressure-corruption   compiled=true   checks=3
cooldown-pin-drift         compiled=false  checks=3     <-- "not compiled", three checks printed
key-rotation-expiry        compiled=true   checks=2
guard-degradation          compiled=true   checks=2
spawn-hot-loop             compiled=true   checks=3
ingest-backfill-gap        compiled=true   checks=2
gateway-guard-violation    compiled=true   checks=2
docs-count-drift           compiled=false  checks=2     <-- same shape
worktree-reap-data-loss    compiled=false  checks=2     <-- same shape
fast-forward-push-reject   compiled=true   checks=2
unclassified               compiled=false  checks=0
```

The markdown view the operator reads is the same contradiction in a table: header `compiled`, value `False`, and
`checks 7` two columns later.

### 2b. Anywhere else (the normal user case)

| Where | `incident_seen` | `runbook_compiled` |
|---|---|---|
| this repo's root (board events present) | 10 of 14 classes | 11 true / 3 false |
| fresh clone on a clean bunker box (same HEAD) | same | 10 true / 4 false |
| an empty scratch directory | none | **0 true / 14 false** |
| a foreign fleet repo (`get-h3/shim`, 430 events) | none | **0 true / 14 false** |

`lore audit` resolves its incident source against the **current working directory**
(`lore/incidents.py:47-74`), silently, with `rc=0` when it finds nothing. So a user who installs lore into their own
repo is told, by the column whose job is "is a runbook compiled", that no runbook is compiled — for all fourteen
classes, whose check counts are printed beside it.

### 2c. The two questions the story actually asks

1. **"Which classes has the fleet seen in the last 90 days?"** — answerable only for classes that are already in the
   registry: the scanner's regex is built from `SEED_CLASSES` (`lore/incidents.py:88-96`). Control/treatment probe
   with a fresh fixture board:

   ```
   control   events.jsonl detail {"class_id":"gateway-drain-window"}   -> rows=14, incident_seen=['gateway-drain-window']
   treatment events.jsonl detail {"class_id":"postgres-deadlock-storm"} -> rows=14, incident_seen=[], novel class in output: 0
   ```

   A genuinely new failure class — the reason to want a coverage matrix — is dropped without a word.

2. **"Which classes have incidents but no runbook?"** — unrepresentable: rows come from `compile_all()`, so the
   output universe is the set of classes that already have runbooks. `incident_count()` is computed at
   `lore/__main__.py:611` and discarded ("side-effect call for future use"); the JSON summary carries no incident
   number at all.

### 2d. The incident signal is prose, with no window

The secondary signal joins a task's `detail`/`foreman_note`/`title` and regex-matches class ids, with **no timestamp
filter** (`lore/incidents.py:141-171`; only the events file is windowed). Probe: one generic in-window event plus two
tasks dated **2024** whose titles merely say "mention gateway-drain-window in passing" and "rename
worktree-reap-data-loss doc heading":

```
incident_seen=["gateway-drain-window","worktree-reap-data-loss"]     (zero incidents in the record)
control, same fixture with those two tasks removed: incident_seen=[]
```

Documentation edits mutate the coverage report. Combined with 2a, they also mutate the `compiled` column.

## 3. Fresh machine (install leg, not skipped)

Documented quickstart driven **as written** on `bunker-mvp` agent `df-lore-1023` (spawned for this tick, TTL 2h,
destroyed after read-back), box with no `uv` and no checkout:

| step | command (from README/INSTALL) | rc | wall |
|---|---|---|---|
| clone | `git clone https://github.com/get-h3/lore` | 0 | 1 s |
| toolchain | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | 0 | 1 s (uv 0.13.5) |
| provision | `uv sync --extra dev` | 0 | 2 s |
| first command | `uv run python -m lore match "drain 503"` | 0 | ~0 s → `gateway-drain-window confidence=0.90` |
| suite | `uv run pytest -q` | 0 | 10 s → **560 passed** |
| lint | `uv run ruff check .` | 0 | → All checks passed |

Read-back at the end of the tick: the agent's checkout is `da91c1e`, the same commit the controller drove. The
coverage defect reproduced identically on the fresh clone (`compiled_false=4`, `checks_but_uncompiled=3`), i.e. it
ships.

Evidence: `docs/qa/evidence/run15/fresh-box-leg.txt`, `audit-fresh-box.json`.

## 4. Speed (Step 2b)

| operation | measurement |
|---|---|
| `lore audit --format json`, no ledger (interpreter floor) | 60.6 ms ± 5.8 (hyperfine ×5) |
| `lore audit --format json`, repo's 5,127-row / 1.4 MB ledger | **68.0 ms ± 14.6** |
| same, 10× rows (51,270) | 146.2 ms ± 4.3 |
| same, 100× rows (512,700) | 1,170.6 ms ± 39.0 |
| `lore match "drain 503"` warm | 76.4 ms ± 8.5 |
| `lore match` first run (`/usr/bin/time -p`) | real 0.06 s |

`PERF-2`'s claim re-proved numerically: the ledger is opened **once** per invocation at 1× and 10× (strace:
`openat` hits on `validate-history.jsonl` = 1), not fourteen times. **No PERF row filed** — nothing here is slow
enough for a user to feel (7 ms of ledger cost on the repo's own file), and a win nobody can feel devalues the real
findings. Evidence: `docs/qa/evidence/run15/perf-step2b.txt`, `hf-*.json`.

## 5. What works (re-verified, no rows)

- Documented responder examples byte-exact on the fresh box: `drain 503` → 0.90, `secret .env clobber` → 0.90,
  the deliberate `unclassified` → 0.00, all `rc=0`.
- Install path as written: clone → uv installer → sync → first match, ~5 s of in-box time, 560 tests + ruff clean.
- Test count prose in sync (`scripts/test-count.txt` = 560 = `pytest -q` on the fresh box; `count_sweep.py` exits 0).
- The lint/freshness half of audit is untouched by the incidents work and still honest (`last_validated` = `no data`
  until attestation, `summary.note` says so).

## 6. Findings filed (board `.coding-hermes/board/tasks.jsonl`)

| row | sev | one line |
|---|---|---|
| `LORE-067-R2` | P2 | `runbook_compiled` was redefined as "class seen in incidents", so it prints `false` for classes whose checks it prints on the same row — and for all 14 anywhere without a board. Tests were weakened to `isinstance(..., bool)` so CI stayed green. |
| `LORE-067-R3` | P3 | The incident path cannot answer US-3: a novel class_id in `events.jsonl` yields no row/number, and any old board task that merely names a class id counts as an in-window incident (no timestamp filter on that signal). |
| `DOC-8` | P4 | The incident source path is undocumented on every reader-facing surface (0 mentions of `events.jsonl`/`incident_seen`/`coverage_note` in README, docs, usage skill; `lore audit --help` silent), and the usage skill still asserted the retired "literal True — can never print False" contract. Prose corrected in-run; row asks for the docs + a claim-check. |
| `LORE-068-R2` | P3 | Found while validating after filing: the board still fails its own gate — `tasks.jsonl` line 105 (`DOC-6`) carries a duplicate `foreman_note` key, so `boardctl validate` = FAIL (1 error) and every JSON reader silently drops the first note (an operator question). |

Pre-existing board state (not caused by this run): `boardctl validate` = 1 error / 94 warnings **before** the appends
and 1 error / 94 warnings **after** (verified against a pre-append copy) — +0 errors, +0 warnings.

## 7. Left behind

- `docs/dogfood/2026-10-23-run15-integration.md` (this file)
- `docs/dogfood/diagnostics.md` — run-15 section (how the incident path is built, the two probes, the `--script`
  upload pitfall)
- `docs/qa/evidence/run15/` — audit JSON from four cwds, novel-class control/treatment, board-prose window probe,
  perf JSON + summary, fresh-box leg log, board-validate output
- `skills/lore-usage/SKILL.md` — audit-coverage section rewritten to the shipped truth (the stale "literal True"
  claim removed in place, not annotated)
- `.coding-hermes/dogfood-log.md` — run-15 entry
