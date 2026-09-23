# lore

### Six greps across three archives to find what fixed it last time. One lookup that proves the fix still runs.

Runbook compiler — **"how did we fix this last time, and does it still work?"**

---

## The question lore answers

> **"How did we fix this last time — and does it still work?"**

Every incident generates world-class runbook material, and it evaporates into
chat archives. The gateway restart doctrine took **four incidents + a
compaction-boundary loss** to formalize; the scheduler cooldown authority model
was learned across **SCHED-GAP-025 → SCHED-GAP-121** — the same class of drift
bit twice; the `.env`/`.env.example` clobber's one-line cure survived only in
one session transcript. Six-grep investigations, again and again.

`lore` compiles a fleet's actual incident history into living, re-validated
runbooks per failure class — each carrying the real queries and commands that
diagnosed it last time — and turns the six greps into **one runbook lookup**.

## Quickstart

From a clean checkout, in under two minutes. Every command below was run and
its output pasted verbatim; the full walkthrough lives in
[docs/INSTALL.md](docs/INSTALL.md).

```sh
git clone https://github.com/get-h3/lore
cd lore
uv sync --extra dev
```

Ask lore to match a symptom against its failure-class registry:

```sh
uv run python -m lore match "drain 503"
```

Real output:

```
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain
unclassified	confidence=0.00	evidence: none
```

Another real symptom, a different class:

```sh
uv run python -m lore match "secret .env clobber"
```

```
secret-env-clobber	confidence=0.90	evidence: signature:.env clobber; keyword:.env; keyword:clobber
unclassified	confidence=0.00	evidence: none
```

And a symptom that matches nothing curated:

```sh
uv run python -m lore match "the coffee machine is making a weird noise"
```

```
unclassified	confidence=0.00	evidence: none
```

That is not a failure. **Absence is a first-class answer in this tool's own
doctrine**: an unknown symptom says `unclassified` loudly rather than
pretending to recognize it. Inventing classes without approval is not allowed;
absorbing into `unclassified` always is.

Now compile the runbook for the class you just matched:

```sh
uv run python -m lore compile --class gateway-drain-window --format md
```

Abridged real output (the `--format json` variant prints the same structure as
JSON):

````text
# Runbook: Gateway drain window (`gateway-drain-window`)

- **Status:** proposal
- **Last validated:** no data (never validated)
- **Provenance:** Compiled by lore.compiler from the curated class registry (lore.classes) and the fleet's incident history. Operator approval required to publish (propose-not-write).
- **Signature:** `drain\s+503`

## Checks (in order)

### Check 1 (read-only)

    logsey query --pattern 'drain 503' --since 30m

- Healthy: no rows
- Incident: 503s on in-flight requests while the gateway restarts/reloads
- Decision: confirm the class signature before touching anything
````

Note the two honesty fields: **Status: proposal** and **Last validated: no data
(never validated)**. The compiler emits a proposal and never writes a published
runbook to disk — publishing requires operator approval. A runbook that has
never been re-validated says so rather than carrying a confident-looking date.

An unknown class is refused rather than invented (the registry is closed):

```sh
uv run python -m lore compile --class does-not-exist ; echo "exit=$?"
# exit=2
```

Run the tests and lint that gate every change:

```sh
uv run pytest -q        # 148 passed
uv run ruff check .     # All checks passed!
```

### Or install it as a tool

Zero runtime dependencies, so installation is instant:

```sh
uv tool install git+https://github.com/get-h3/lore
lore match "key rotation expired"
```

```
key-rotation-expiry	confidence=0.90	evidence: signature:rotation expired; keyword:expired; keyword:rotation
unclassified	confidence=0.00	evidence: none
```

## What the classifier knows today

The curated registry holds **9 failure classes** plus an explicit
`unclassified` bucket:

`gateway-drain-window` · `shared-checkout-collision` · `secret-env-clobber` ·
`disk-pressure-corruption` · `cooldown-pin-drift` · `key-rotation-expiry` ·
`guard-degradation` · `spawn-hot-loop` · `ingest-backfill-gap`

Each class carries signature patterns and keyword evidence; matches print the
class id, a confidence, and the evidence that drove the match — never a naked
assertion.

## Who this is for

- **The 3 a.m. incident responder** (human on-call operator, PRD US-1): paste
  the symptom line you just saw and get the failure class the fleet has seen
  before — with the evidence that identifies it — instead of searching chat
  archives by memory.
- **The post-incident scribe** (PRD US-2): today's classifier is the taxonomy
  spine that the planned absorb/audit workflow will file updates into, so
  yesterday's fix becomes next time's runbook.
- **The runbook auditor / coverage reviewer** (PRD US-3): the same registry
  gives coverage reviewers a fixed vocabulary of failure classes — incidents
  that resolve to `unclassified` are gaps you can *see*, not a confident zero.
- **The cold-start agent on a new box** (PRD US-4): a first responder that
  starts with the fleet's scar tissue instead of zero. `lore match` finds the
  class; `lore compile` prints the compiled runbook as a proposal.

## Why this exists

**Runbooks rot because they're written prose, and prose has no execution feedback.** The fleet's lived proof, three cases deep:

1. **The gateway restart doctrine** took four incidents and a compaction-boundary loss to formalize: batch config changes, pause-first under load, expect up-to-30-min drain 503s. The knowledge existed only in scattered session summaries and one memory note ("drain 503s kill ticks") — invisible to a fresh agent hitting the same wall.
2. **The scheduler cooldown authority model** (DB vs `fleet.toml` dual-store pins, `--verify` tripwire) was learned across SCHED-GAP-025 → SCHED-GAP-121 — the *same* class of drift bit twice, a year-class apart in fleet maturity, because the first lesson lived in an AGENTS.md paragraph nobody re-reads at incident time.
3. **The `.env`/`.env.example` clobber** had a one-line cure (container-env repair) that survived only inside one session's transcript. The next operator hits the same wall with no runbook — recovery took reading Docker env by hand and diffing four secret generations.

The pattern: **every incident generates world-class runbook material, and it evaporates into chat archives.** Bane's audit doctrine says findings must be *re-findable*; today they're re-findable only by whoever remembers the keywords.

## What a runbook carries

Per **failure class** (classified from the incident trail: drain-window, shared-checkout collision, secret clobber, disk-pressure corruption, cooldown drift, key-rotation, …):

- **Signature:** the log/logsey pattern that identifies the class (from B1's message-classes)
- **Checks in order,** each with: the exact command/query, expected healthy vs incident output, and *what decision it drives*
- **Recovery ladder** with guardrails (what NOT to run — the fleet's "never `--apply` on cooldown policy", "USR1-only restarts" class of law)
- **Evidence trail:** links to the DuckBrain rows, board events, and commits where each step was learned
- **Provenance + freshness:** which incidents fed it, last-validated timestamp

Where compiled runbooks will be stored — a central registry in the fleet's
DuckBrain namespace plus materialized per-repo `runbooks/` directories,
git-tracked so updates travel with code and pass human PR review — is decided
in [docs/RUNBOOK-STORE.md](docs/RUNBOOK-STORE.md) (design, not yet implemented).

## Design laws this repo inherits

- **Evidence or it did not happen.** Every number links to the row, log line or
  commit that produced it. No summary without a drill-down.
- **Honesty labels are renderer-enforced.** Missing data renders as "no data",
  never as zero.
- **Absence is a first-class answer.** If the tool cannot see something, it says
  so loudly rather than reporting a confident zero.
- **Budget is the spec.** A tool that costs more than it answers gets uninstalled.

## The agent-ops line

Four tools that turn a fleet's operational exhaust into queryable, provable
truth. Same spine: evidence-first, honesty-labeled, pocket-scale.

| Tool | The question it answers |
|---|---|
| [logsey](https://github.com/get-h3/logsey) | What happened on this box? |
| [pulse](https://github.com/get-h3/pulse) | What was the machine doing when it failed? |
| [lore](https://github.com/get-h3/lore) | How did we fix this last time — and does it still work? |
| [digest](https://github.com/get-h3/digest) | What needs me today? |

Standalone tools; pairs compound — pulse joins logsey, digest cites everything.

## Status

**v0.1.0 — early.** Kicked off 2026-09-23. Split honestly into what runs today
and what does not:

### Shipped — runs today, verified on `main`

- The failure-class taxonomy + classifier (9 curated classes + `unclassified`),
  with **148 tests passing** and a clean `ruff check`.
- The `lore match "<symptoms>"` command — the responder's entry point.
- The runbook compiler (`lore compile [--class X] [--format json|md]`): emits a
  Runbook per curated class, as a **proposal** — it never writes a published
  runbook to disk. See "What a runbook carries" above for the shape.
- Evidence blocks (`lore/evidence.py`): the curated evidence-kind vocabulary,
  the logsey-export contract parser, and the honest degradation path
  (`degrade_to_command_output`) for as long as logsey's `export` subcommand is
  unimplemented. Attaching evidence never sets `last_validated`.
- Zero runtime dependencies; MIT licensed; CI (build + pytest + ruff) green on
  `main`.
- The read-only command lint (`lore validate`): re-runs each runbook's checks and
  flips a drifted runbook to `stale`, carrying the reason. **Default is plan
  mode** — it lists what *would* run and executes nothing; `--execute` opts in.
  The report carries a machine-checkable honesty label: the lint proves commands
  *parse and answer*, **not** that recovery *succeeds*. No schedule is installed
  yet (a separate task owns the weekly timer).
- Install guide: [docs/INSTALL.md](docs/INSTALL.md). Runbook-store design
  decision: [docs/RUNBOOK-STORE.md](docs/RUNBOOK-STORE.md).

### Planned / in flight — named, not promised as runnable

- **Runbook store** (central registry + materialized per-repo dirs) — design
  decided in [RUNBOOK-STORE.md](docs/RUNBOOK-STORE.md), not implemented.
- **Runbook viewing (`lore show`), absorbing incident trails into proposals
  (`lore absorb`), coverage audit (`lore audit`)** — planned; no code exists.
- The PRD's planned interface is:

```text
lore match "<symptoms|log line>" [--class ...]
lore show <class> [--evidence]
lore absorb --window ... [--ns ...] [--board ...]   # propose updates from an incident trail
lore audit [--format table|json|md]                 # coverage + freshness matrix
lore validate [--class ...]                         # run the read-only command lint now
```

`lore match` and `lore compile` run today. See [`docs/PRD.md`](docs/PRD.md) for the full
product requirements, the design authority this repo is judged against. The
task list lives on the project board at `.coding-hermes/board/tasks.jsonl`.

## Security

Runbooks carry **operational commands**. Commands embedded in a runbook must be
reviewed before execution, must be read-only/verify-mode by design intent, and
must never embed a secret. See [SECURITY.md](SECURITY.md) for reporting
vulnerabilities and the full threat notes.

## License

MIT — see [LICENSE](LICENSE).