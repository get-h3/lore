# Install & first run

Everything here was run and its output pasted verbatim. If a command below does
not work for you as written, that is a bug in this document — please open an
issue.

## Prerequisites

- **Python 3.11+** (`python3 --version`). That is the only hard requirement —
  `lore` has **zero runtime dependencies**.
- [uv](https://docs.astral.sh/uv/) is recommended (it provisions the virtualenv
  and dev tools). Plain `pip` works too, but bare `pytest` exits 127 before a
  venv exists — see the AGENTS.md note.

## Install from source

```sh
git clone https://github.com/get-h3/lore
cd lore
uv sync --extra dev
```

`uv sync --extra dev` provisions `.venv` plus pytest and ruff. Real output
(versions will drift; the shape will not):

```
 + packaging==26.3
 + pluggy==1.6.0
 + pygments==2.21.0
 + pytest==9.1.1
 + ruff==0.16.8
```

pip-only alternative: `python3 -m venv .venv && .venv/bin/pip install -e .[dev]`.

## Verify the install

Run the test suite and the linter — the same gates every change to this repo passes:

```sh
uv run pytest -q
uv run ruff check .
```

Real output on the current tree:

```
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
269 passed in 0.74s
```

```
All checks passed!
```

The count to expect is **269 tests** (14 test files: taxonomy, classifier,
compiler, evidence, validate, and the CLI/QA-coverage suites added since). If
your run says something else, you are on a different revision — check
`git log` before trusting this document.

## First run

### `--help` — the whole shipped surface

```sh
uv run python -m lore --help
```

```
usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit
```

That is the entire shipped CLI today: eight subcommands — `match`, `consult`,
`compile`, `validate`, `gate`, `absorb`, `show` and `audit`. Anything else you
may have heard of (runbook-store materialization, the scheduled weekly lint) is
**planned** — see the README's Status section. `lore validate` runs the lint;
the weekly *schedule* that would run it for you is not installed (that is a
separate task).

### `match` — classify a symptom

```sh
uv run python -m lore match "drain 503"
```

```
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain
unclassified	confidence=0.00	evidence: none
```

More real symptoms:

```sh
uv run python -m lore match "secret .env clobber"
```

```
secret-env-clobber	confidence=0.90	evidence: signature:.env clobber; keyword:.env; keyword:clobber
unclassified	confidence=0.00	evidence: none
```

```sh
uv run python -m lore match "key rotation expired"
```

```
key-rotation-expiry	confidence=0.90	evidence: signature:rotation expired; keyword:expired; keyword:rotation
unclassified	confidence=0.00	evidence: none
```

A symptom that matches nothing curated:

```sh
uv run python -m lore match "coffee machine"
```

```
unclassified	confidence=0.00	evidence: none
```

That is not a failure — absence is a first-class answer here. An unknown
symptom says `unclassified` loudly; inventing classes without approval is not
allowed.

### `compile` — emit the runbook proposal

```sh
uv run python -m lore compile --class secret-env-clobber --format json | head -20
```

```
[
  {
    "class_id": "secret-env-clobber",
    "name": "Secret / .env clobber",
    "signature": "\\.env(\\.example)?\\s+(twins?|clobber|overwrite)",
    "checks": [
      {
        "order": 1,
        "command": "docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | head -20",
        "expected_healthy": "live secret-bearing values present",
        "expected_incident": "example/placeholder values (key 401s downstream)",
        "decision": "confirm the clobber before any rewrite",
        "read_only": true,
```

The human-readable form of a full runbook (`gateway-drain-window`, abridged —
the recovery ladder and guardrails sections continue below what is shown):

```sh
uv run python -m lore compile --class gateway-drain-window --format md
```

````text
# Runbook: Gateway drain window (`gateway-drain-window`)

- **Status:** proposal
- **Last validated:** no data (never validated)
- **Provenance:** Compiled by lore.compiler from the curated class registry (lore.classes) and the fleet's incident history. Operator approval required to publish (propose-not-write).
- **Signature:** `drain\s+503`

## Checks (in order)

### Check 1 (read-only)

```sh
logsey query --pattern 'drain 503' --since 30m
```
- Healthy: no rows
- Incident: 503s on in-flight requests while the gateway restarts/reloads
- Decision: confirm the class signature before touching anything
- Evidence: incident: PRD §The problem, measured case 1

## Recovery ladder

1. Stop config changes: batch them instead of trickling under load.
2. Pause-first under load: hold the rollout until in-flight requests finish.
...

## Guardrails (never X)

- Never restart the gateway with in-flight requests still draining from the previous restart.
...
````

Note the honesty fields: **Status: proposal** and **Last validated: no data
(never validated)**. The compiler is propose-not-write — it prints to stdout
and never writes a published runbook to disk.

An unknown class is refused (the registry is closed):

```sh
uv run python -m lore compile --class does-not-exist ; echo "exit=$?"
```

```
error: unknown class_id 'does-not-exist'; registry is closed. Known: gateway-drain-window, shared-checkout-collision, secret-env-clobber, disk-pressure-corruption, cooldown-pin-drift, key-rotation-expiry, guard-degradation, spawn-hot-loop, ingest-backfill-gap, gateway-guard-violation, unclassified
exit=2
```

### Install as a standalone tool (optional)

```sh
uv tool install git+https://github.com/get-h3/lore
lore match "key rotation expired"
```

```
key-rotation-expiry	confidence=0.90	evidence: signature:rotation expired; keyword:expired; keyword:rotation
unclassified	confidence=0.00	evidence: none
```

### The `absorb` trail contract

`lore absorb --window <dur>` reads a **prior evidence trail** from stdin (or
`--trail-file PATH`) in logsey export format (see `lore/evidence.py
parse_logsey_export` — a header line plus a fenced block of log lines), then:

1. classifies every parseable block into per-class absorb **proposals**,
   printed on stdout;
2. with `--source <marker>`, every per-class proposal carries that provenance
   marker (omitted, the payloads keep their shape with no `source` key);
3. an empty trail is an explicit empty result — exit 0, not an error; and
4. **propose-not-write**: nothing is ever written, stdout is the only side
   effect.

````sh
printf 'logsey export --window 2h\n```\n2026-09-24T10:00:00 unit=loreforge gateway drain 503 while restart\n```\n' \
  | uv run python -m lore absorb --window 2h --source dogfood-dagger
````

```
[
  {
    "class_id": "gateway-drain-window",
    ...
    "source": "dogfood-dagger",
    ...
```

## What this tool is NOT

- **No published runbook store yet.** Compile output goes to stdout only;
  nothing lands in a registry or on disk. The runbook-store design (central
  registry + materialized per-repo dirs) is decided in
  [RUNBOOK-STORE.md](RUNBOOK-STORE.md) but not implemented.
- **No scheduled lint / re-validation yet.** The weekly read-only command lint
  that would flip stale runbooks is in flight (`LORE-006`); nothing runs on a
  schedule today.
- **Propose-not-write.** The compiler never writes to disk. Publishing anything
  requires an operator's explicit approval, by design.
- **Not a monitor.** lore classifies and compiles; it does not watch logs,
  alert, or run your recovery ladder.

## Next

- [README](../README.md) — the tool, its use-cases, and its design laws.
- [RUNBOOK-STORE.md](RUNBOOK-STORE.md) — where compiled runbooks will live,
  and why.
- [PRD](PRD.md) — full product requirements and the design authority.