# lore — dogfood run 14 (2026-10-20)

**Target:** `get-h3/lore` @ HEAD `a6984b4` (main, == origin/main at run start)
**Lane:** lore-dogfood (skill-driven, no driver script), workdir
`~/.hermes/stand-in/dogfood/lore`
**Verdict:** ✅ **SHIPPABLE** on install + real use + fix verification; the run's
one real defect is a **scaling** defect in the audit read path (PERF-2), plus a
small ledger-hygiene defect (LORE-066). Nothing today is slow enough for a user
to feel; the measured trajectory is what makes PERF-2 worth a row.

---

## 1. The promise (null hypothesis)

> A user can paste a symptom line and get the failure class the fleet has seen
> before, with its evidence; compile that class's runbook proposal; lint the
> runbook's commands against the box; and see coverage + freshness in one
> audit — with the lint evidence surviving on the box.

Earlier runs already drove the responder (runs 1, 4), the scribe/gate/closure
surfaces (2, 6, 7), the machine JSON contract (8), the install envelope (9, 10),
the absorb error ladder (11), the teaching layer (12) and the PRD
success-criteria battery (13). Run 14 therefore takes three untouched angles:

1. **The cost of the freshness path as the local validate ledger grows** — the
   surface LORE-045/064 wired and nobody has measured (Step 2b).
2. **The documented quickstart from a genuinely fresh box**, driven as written
   (anonymous `git clone` + `uv sync --extra dev`), because the dep bump
   `cfc8f9c` and the LORE-064/051 code changes landed after run 10's leg.
3. **Fix verification for the four commits landed since run 13's HEAD**:
   `c1ac048` (LORE-051 bucket), `c63b82d`+`c9a0eb4` (LORE-064 audit freshness
   wiring), `f50478b`/`deb398a` (LORE-053/20261008 absorb error text),
   `cfc8f9c` (dep bump).

---

## 2. Real use at HEAD (control box)

Documented quickstart commands, verbatim, all rc=0:

```
$ .venv/bin/python -m lore match "drain 503"
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain
$ .venv/bin/python -m lore match "secret .env clobber"
secret-env-clobber	confidence=0.90	evidence: signature:.env clobber; keyword:.env; keyword:clobber
$ .venv/bin/python -m lore match "the coffee machine is making a weird noise"
unclassified	confidence=0.00	evidence: none
$ .venv/bin/python -m lore consult "gateway drain 503" | head -1
runbook: gateway-drain-window (Gateway drain window) status=proposal last_validated=never checks=7
```

`audit` renders 14 rows: 13 curated classes + the bucket row
(`[bucket] unclassified`, `bucket: true` in JSON) — the LORE-051 contract holds.
`absorb --window` on a non-export trail answers rc=0 with
`no classifiable evidence blocks in the trail (no blocks found — nothing
proposed, nothing written)`, and a mistyped window answers rc=2 with the
accepted-shape teaching line — the LORE-20261008 fix is visible to a user.

### Freshness wiring (LORE-064) — probed live, 4 arms

| arm | ledger for `gateway-drain-window` | audit status |
|---|---|---|
| A | no ledger | `proposal` |
| B | drifted record | `stale`, reason `lint drift: check 2 (error)` |
| C | clean record, then a drifted one | `stale` |
| D | drifted record, then a clean one | `proposal` |

So the wiring works **and** its semantics are "newest record wins by file
order" (not `max(timestamp)`). That matters for PERF-2's fix: an optimizer that
switches to a timestamp comparison would change behaviour. Evidence:
`docs/qa/evidence/run14/freshness-arms.txt`.

### Fresh box (bunker-mvp, agent `lore-df14`, destroyed)

The documented path, as written, on a fresh Debian agent (python 3.12.3):

```
git clone https://github.com/get-h3/lore   # anonymous https, rc=0, HEAD a6984b4
curl -LsSf https://astral.sh/uv/install.sh | sh        # rc=0 -> uv 0.13.3
uv sync --extra dev                        # rc=0, 34 packages, .venv created
python -m lore match "drain 503"           # 0.90, as documented
python -m lore validate --class gateway-drain-window --execute   # rc=0, 1 ledger row
```

Per-stage stamps (`docs/qa/evidence/run14/fresh-box-leg2-stamps.txt`): clone
1 s, uv installer 1 s, `uv sync` 2 s — ~4 s of box time from nothing to a
working CLI (the box's network is fast; the uv release download dominates).
Delta smoke on that box: a persisted drifted record flips the audit row to
`stale` with the reason rendered (`freshness-arms` equivalent — the
`leg2.log` DELTA block), and the bucket row reports `bucket=True`. Both the
LORE-064 and LORE-051 contracts hold on a machine that never ran lore.

**One leg artifact, stated plainly:** the first leg script failed at the uv
provisioning step because it hard-coded a uv release tag (`0.36.0`) that does
not exist — `curl` 404, everything after it cascaded to rc=127. That is my
script's bug, not the product's; the documented installer path was then driven
and passed. Full trail (including the failure) is kept in
`docs/qa/evidence/run14/fresh-box-leg1.log`.

---

## 3. What it costs in time (Step 2b)

`lore audit` is the headline operation that reads the local validate ledger
(`.lore/validate-history.jsonl`, one record per class per `validate --execute`
run). This repo's ledger is **3,161 rows / 878,746 bytes, written over 18 days
(~176 rows/day)** by the product's own lint runs.

```
# warm, hyperfine --warmup 3 --runs 12; cwd holds ./.lore/validate-history.jsonl
ledger rows      lore audit            lore consult
0 (floor)         48.3 ms ±  2.5 ms     53.9 ms ± 5.5 ms
3,161 (today)    144.2 ms ± 15.7 ms     59.4 ms ± 3.1 ms
31,610 (10x)       1.056 s ± 0.151 s   116.8 ms ± 4.9 ms
316,100 (100x)     9.564 s ± 0.388 s   (not measured, --runs 3)

# cold (sync + drop_caches each run, 3,161-row ledger)
audit real 0.23 / 0.24 s   vs warm 0.13 s
consult cold 0.15 s        vs warm 0.05 s
control cold `cat` of the ledger: 0.03 s
```

**Where the time goes** (`cProfile -s tottime`, 3,161 rows): `_audit_rows`
(`lore/__main__.py:560`) = 0.200 s cumulative, and it calls
`last_local_validation` (`lore/validate.py:1194`) **14 times** — once per
registry class — each call doing `readlines()` over the whole file and
`json.loads` on every non-blank line: **44,254 loads** at 3,161 rows,
**442,540** at 31,610. The parse *is* the cost, and it is repeated once per
class.

**Equivalent work, measured:** replacing 14 passes with one
(`/tmp/lore-df14/passbench.py`) gives 38.0 ± 3.5 ms vs 145.3 ± 28.1 ms at 3,161
rows (**3.8x**), and 88.2 ± 4.7 ms vs 1.010 ± 0.062 s at 31,610 rows
(**11.5x**).

**Honest framing:** 144 ms is *not* something a user feels today. The reason
this is filed (PERF-2) is that the cost is linear in a file the product writes
~176 rows/day, with no rotation, compaction or cap anywhere in the docs — the
same usage reaches ~1 s per `audit` in about five months, and ~9.5 s in about
four and a half years. `consult`/`compile` pay the same mechanism at 1x (they
read the ledger once) and only become visible at 10x (53.9 → 116.8 ms).

---

## 4. Findings

| row | priority | what |
|---|---|---|
| **PERF-2** | P3 | `lore audit` re-reads and re-parses the entire ledger once per registry class (14x). Commands, warm+cold numbers, profile, hot path (`__main__.py:604` → `validate.py:1208-1226`), equivalent-work bench, growth trajectory, fix direction and acceptance criteria all in the row. |
| **LORE-066** | P4 | `validate --execute` persists a 0-check "lint-verified" ledger record for the `unclassified` **bucket** on every run — 225 of 3,161 rows (7.1%) carry `total_checks: 0`, `outcomes: []`, yet the label claims commands answered. No functional harm (the bucket never flips stale); it is weight + an overstated label. |
| **LORE-063-R2** | P3 | recurrence of a closed row: `skills/lore-usage/SKILL.md:123` read `expect: 510 passed` while canonical is 523, **and `python3 scripts/count_sweep.py 523 .` still exits 0** — the self-reference exemption (`count_sweep.py:102-103`) exempts the one line whose whole job is to state the count, which is why the fix to LORE-063 (number-sync only, `615fda1`) did not hold. Run 14 corrected the literal in-run; the row is scoped to the guard half. |

All three rows were appended with self-verifying scripts (snapshot, id-absence
assertion, line-delta = 2 then 1, per-id occurrence = 1). `boardctl validate` reads
**3 errors / 42 warnings before and 3 errors / 42 warnings after** — the 3
errors and 42 warnings are pre-existing (two rows carry the out-of-vocabulary
status `closed`, one events id descends) and are **not** mine; the new rows add
zero errors and zero warnings.

Re-confirmed, not re-filed: LORE-061 (env-absent vs drifted rendering) still
reads `stale` in the table view while the JSON carries `env_absent_orders`
separately; LORE-065 (no sync verb) unchanged; LORE-060's logsey runbook text
still the older CLI contract (`LORE-060-R2` covers the recurrence).

---

## 5. What this run leaves behind

- `docs/qa/evidence/run14/` — every measurement as a re-runnable artifact:
  hyperfine JSON+text at 0 / 3,161 / 31,610 / 316,100 rows, cold-vs-warm `/usr/bin/time`
  captures, both cProfile dumps, the single-pass-vs-14-pass bench, the ledger
  census, the freshness 4-arm probe, the bucket record, and the fresh box's
  leg logs + stage stamps.
- `docs/dogfood/diagnostics.md` — a run-14 section explaining the mechanism
  (why 14x, where the ledger comes from, and the two leg lessons).
- `skills/lore-usage/SKILL.md` — the ledger is now documented as a *cost*:
  what it is, how it grows, that `audit` reads it per class, and that any
  change to the read path must preserve file-order-newest semantics.
- `.coding-hermes/dogfood-log.md` — the run-14 entry with verdict and angle.
- Board rows `PERF-2`, `LORE-066`.

**Foreman:** not woken and no scheduler state touched — this lane is read-only
on scheduling, per the skill. The rows are on the board for the next tick.
