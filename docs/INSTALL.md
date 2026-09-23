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
...................................................................      [100%]
67 passed in 0.07s
```

```
All checks passed!
```

The count to expect is **67 tests** (4 test files: taxonomy, classifier,
compiler, evidence). If your run says something else, you are on a different
revision — check `git log` before trusting this document.

## First run

### `--help` — the whole shipped surface

```sh
uv run python -m lore --help
```

```
usage: lore [-h] {match,compile} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,compile}
    match          classify a symptom text
    compile        compile runbook proposal(s) per failure class (stdout only)

options:
  -h, --help       show this help message and exit
```

That is the entire shipped CLI today: two subcommands, `match` and `compile`.
Anything else you may have heard of (`show`, `absorb`, `audit`, `validate`,
evidence blocks) is **planned or in flight** — see the README's Status section.

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
error: unknown class_id 'does-not-exist'; registry is closed. Known: gateway-drain-window, shared-checkout-clobber, ... (9 classes + unclassified)
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