# Dogfood run 18 — lore v0.3.0 new surfaces (2026-11-23)

Tick: `lore-dogfood-2026-11-23-14-15-27` · HEAD `23f800b` (== origin/main, parity 0 0)

## Promise

lore v0.3.0 (2026-11-21) claims three surfaces no earlier dogfood run exercised:

1. **LORE-EXPORT-1** — every `lore gate` verdict exports Prometheus textfile
   metrics (`lore_gate_runs_total`, `lore_gate_last_success`) atomically into
   the node_exporter textfile directory, default `/var/lib/node_exporter/textfile`.
2. **LORE-071** — a proposal-only absorb trigger: `BoardEventWatcher` turns a
   board's `events.jsonl` (read-only, byte-offset cursor, no replay on
   restart) and `AugerDecisionTableAdapter` turns an Auger Markdown export
   into evidence blocks that feed `absorb_sweep` → in-memory proposals.
3. **SUP-DEPS-LORE-20261121** — a weekly dependency-drift report
   (`scripts/dep-drift.sh`) shipped with systemd user units that are armed
   deliberately by the operator (both were armed on this host on 2026-11-20).

The standing promise (paste a symptom, get the class the fleet saw before,
close through the gate) is the regression floor, not the target.

## What a real run looked like (all commands verbatim at HEAD)

### The standing workflow still holds

- `uv run python -m lore match "drain 503"` → `gateway-drain-window
  confidence=0.90`, rc 0 — byte-identical to the README's pasted output.
- `match "secret .env clobber"` → `secret-env-clobber confidence=0.90`, rc 0.
- `lore consult "gateway drain 503 while restarting"` (positional title) →
  runbook + 7 checks + local lint history from last night's QA battery
  (`last lint-validated 2026-11-23T04:49:10+00:00 on this box`) — the
  per-box validation history survives across processes exactly as LORE-045's
  fix promised.
- `match "spawn 503"` → `unclassified 0.00` rc 0 while
  `consult --failure "spawn 503 while restarting"` returns the 7-check
  runbook — LORE-070's asymmetry, re-proven at HEAD (row complete; no new row).
- Suite: **586 passed in 6.29 s** (rc 0); `scripts/test-count.txt` = 586 and
  `count_sweep.py 586 .` rc 0; `ruff check .` and `ruff format --check .`
  clean. (CHANGELOG's 0.3.0 note says 579; the live canonical file is 586 —
  7 tests landed after the release note was written; the guard file is the
  synced one.)

### LORE-EXPORT-1: gate → Prometheus textfile

Driven as documented, on the host where node_exporter actually scrapes:

- First gate run (default dir, group-writable on this host): `GATE: ALLOW
  (absorb -> gateway-drain-window) source: lore-dogfood-run18`, rc 0.
- `h3_lore.prom` read back: `lore_gate_runs_total 6`,
  `lore_gate_last_success 1` (5 prior verdicts from the 11-22 QA battery +
  this one — the counter is durable, not per-invocation).
- DENY arm (`--class totally-unknown-class`): `GATE: DENY (1 errors)` with
  the registry-closed message, **rc 1**, and the textfile updated to
  `runs_total 7`, `last_success 0`. Both verdicts export, exactly as the
  README's Observability section states.
- Perf arm: 15 rapid gate invocations against a scratch textfile dir —
  counter ended at exactly 17 (2 warmup + 15 runs), i.e. no lost increments
  under the serialized atomic write path, corroborating the test-pinned
  concurrency story live.

### LORE-071: absorb trigger over the repo's OWN board

Consumer written per `docs/ABSORB-TRIGGER.md` (staged script, cursor in
scratch, board opened read-only):

- `BoardEventWatcher.consume()` over this repo's real `events.jsonl`
  (151 KB, 155-row board): **117 blocks**, classified into **4 proposals**
  (`unclassified`, `docs-count-drift`, `ingest-backfill-gap`,
  `secret-env-clobber`), each `action=update` with the proposal-only note
  "an operator must approve before this lands anywhere".
- Restart semantics: second `consume()` with the same cursor returned
  **0 blocks** — no replay after a restart, as documented.
- `AugerDecisionTableAdapter(...).read()` on the shipped fixture: 4
  `duckbrain-row` blocks with the exact documented provenance shape
  (`source=auger:decisions:D-001`, `fields.table`, `fields.row_id`) →
  2 proposals.
- **Friction (filed, LORE-20261013):** the doc says
  "`AugerDecisionTableAdapter(path)` parses Auger's ... export" but never
  names the method; a consumer following the doc verbatim calls `.parse()`
  and gets `AttributeError` (this run did, before reading source — the
  method is `.read()`).

### SUP-DEPS: dependency drift — script vs. schedule

- `scripts/dep-drift.sh` run by hand: rc 0 in 1.45 s, honest current report —
  `4 of 34 locked packages behind PyPI latest` (certifi, charset-normalizer,
  filelock, platformdirs; two new pins drifted since the 11-20 report's
  "2 of 34"), `Not on PyPI (local or non-registry source): get-h3-lore 0.3.0`
  — the version stamp matches pyproject.
- **The scheduled leg did NOT run (filed, LORE-20261012).** Both lore user
  timers are enabled and active on this host, but this morning's Monday
  schedules produced nothing: `dep-drift.log` mtime is 2026-11-20 22:52
  (the foreman's manual run), `weekly-validate.log` mtime 2026-11-16 07:30.
  The dep-drift timer records `LastTriggerUSec=Mon 2026-11-23 07:56:59`
  while the bound service has **zero journal entries ever** and appended
  nothing. Corroborating host context: at 07:47:08 the box was at
  `mem avail 1.55%, swap 0.01%` with an earlyoom SIGKILL storm (hermes,
  bunker, gitlab-runner killed), journald dropped 226 messages, and the user
  manager restarted twice at 08:22:33/08:22:40. The armed schedule missed its
  first real run and nothing in lore's shipped arming path surfaces that —
  the timer's own state says "triggered", the log mtime is the only honest
  signal, and `deploy/systemd/README.md` does not document a check.

## Performance (Step 2b)

Host: 16 cores, loadavg 16.4–17.4 during measurement (saturated box —
numbers quoted at load, not on a quiet host).

| operation | warm | cold |
|---|---|---|
| `match "drain 503"` documented (`uv run`) | 102.3 ms ± 12.3 (n=20) | 0.05–0.07 s (n=3 one-shot, rc 0) |
| `match "drain 503"` raw venv | 98.6 ms ± 14.0 (n=20) | — |
| `gate` verdict + textfile export | 54.7 ms ± 5.6 (n=15) | — |

Everything sits at the interpreter floor (~50–100 ms); a user waits for
nothing. **No PERF row filed** — a win nobody can feel is not a finding
(runs 14–17 reached the same verdict at the same magnitudes).

## Verdict

**SHIPPABLE** on everything v0.3.0 added that this run drove: the gate
metrics export behaves exactly as its README section promises (both
verdicts, atomic counter, loud failure contract), the absorb trigger works
end-to-end over a real 117-event board with honest proposal-only output and
no replay, and dep-drift gives a correct current report in 1.5 s. The one
real defect is operational: **the armed weekly schedules silently missed
their first Monday run** under host memory pressure, and lore ships no way
to notice (LORE-20261012).

## Findings → rows

- LORE-20261012 (P2) — scheduled dep-drift/validate timers missed their first
  Monday run; timer state misleads; no shipped verification check.
- LORE-20261013 (P4) — `docs/ABSORB-TRIGGER.md` never names the adapter
  method (`.read()`); verbatim consumer hits AttributeError.

Left unverified this fire: none of the driven surfaces; the bunker battery's
lifecycle cells are graded in the board row from the collected ledger.
