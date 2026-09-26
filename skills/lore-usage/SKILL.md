# SKILL.md — lore usage (for agents landing in this repo)

## What lore is

Runbook compiler for a fleet of agents. You paste a symptom; it names the
failure class the fleet has seen before (with the evidence that identified it);
it compiles a runbook proposal per class (ordered read-only checks, expected
healthy-vs-incident outputs, recovery guardrails, evidence citations). It never
writes a published runbook: everything is a proposal until an operator
approves. Zero runtime dependencies, Python 3.11+.

## Install / run

```sh
uv tool install git+https://github.com/get-h3/lore   # standalone `lore` binary
# or, from a checkout:
uv sync --extra dev && uv run lore match "<symptoms>"
```

The repo is PUBLIC (flipped 2026-09-25 per LORE-018's decision; anonymous
clone works). **A `uv tool install` tracks the HEAD you installed, not the
repo** — a pre-LORE-007 install exposes only 3 of 8 subcommands and errors
with "invalid choice" on the rest. If a documented subcommand "doesn't
exist", run `uv tool upgrade lore` before filing a bug.

## The eight subcommands (all implemented, verified 2026-09-25)

- `match "<symptom|log lines>" [--explain]` — classify. `--explain` adds a
  `near-misses:` section: top-3 below-threshold classes with raw keyword
  scores (nothing auto-labeled; registry stays closed).
- `consult --failure "<guard/failure output>"` — guard-failure suggestion:
  prints matching runbook id + ordered checks; fail-open (`no matching
  runbook`, exit 0) so pipelines can append unconditionally.
- `compile [--class X] [--format json|md]` — runbook proposal(s) to stdout.
  Unknown class → exit 2 (closed registry).
- `validate [--class X] [--execute]` — read-only command lint. DEFAULT IS
  PLAN-ONLY: lists what WOULD run, executes nothing. `--execute` runs only
  gate-approved read-only commands; a missing tool reports `error (exit 127)`
  and flips the runbook `stale` — the anti-rot signal working, not a crash.
  Two live-run truths (2026-09-25, LORE-022/024): `--execute` NEVER sets
  `last_validated` (operator attestation only, propose-not-write) — the
  `stale` flag, not the freshness field, is today's freshness signal; and a
  check carrying a `<placeholder>` path shell-errors as input redirection,
  staling its class — `--class shared-checkout-collision` is the one class
  that lints green as authored. Run it where the fleet actually runs: on a
  bare box everything stales (exit 128 "not a git repository" is the
  machine, not the runbook).
- `gate --decision absorb|no-new-lesson ...` — closure absorb-gate machine
  check. `absorb` needs `--class` + `--lesson` (class must exist); ack needs
  `--reason`. ALLOW → exit 0, DENY → exit 1 with all violations listed.
  `--source qa-dagger|dogfood-dagger` records provenance on the verdict line.
- `absorb --class X --lesson "..." [--source ...]` — the runbook-update
  PROPOSAL payload (stdout only, propose-not-write).
- `absorb --window 2h [--trail-file P|--ns N|--source ...]` — sweep a PRIOR
  evidence trail into per-class absorb proposals (stdout only). The trail
  must be a logsey-export payload: a line matching `logsey export`, a fenced
  block, then one evidence line per row starting with a BARE ISO timestamp
  (`2026-09-25T06:12:00Z unit=gateway <detail>` — bracketed `[date]` prefixes
  do NOT parse). Unparseable-but-claimed exports raise; non-claimed input is
  an explicit empty result (exit 0).
- `show <class> [--evidence] [--format json|md]` — one compiled runbook,
  human-markdown default, with per-check evidence when asked.
- `audit [--format table|json|md]` — coverage + freshness matrix over all
  registry classes; honest `no data` freshness (never fabricated — but note
  it does not reflect lint runs either: `last_validated` is never stamped in
  v0.1.x, see LORE-022; read the `stale` status column as the live signal).

## The right-way patterns

- `lore match` prints an `unclassified confidence=0.00` row ALWAYS last —
  that is by design (absence is a first-class answer), not an error. When you
  get it, rerun with `--explain` and rephrase the symptom with the near-miss
  class's own vocabulary (LORE-016 fix, verified live).
- Multi-line pastes are fine; leading-dash symptoms (`-Q log stuck`) work —
  argparse does not eat them.
- Close a QA/dogfood run through the same gate as an incident: `lore absorb
  --class <id> --lesson "<text>" --source dogfood-dagger` for the proposal,
  then `lore gate --decision absorb ... --source dogfood-dagger` (or
  `--decision no-new-lesson --reason "..."`) for the verdict line.
- Library use (all verified from an external script):
  `from lore.classifier import classify, classify_all, near_misses`;
  `from lore.consult import consult_failure`;
  `from lore.compiler import compile_class, compile_all`.
  Pitfalls: `NearMiss` exposes `raw_score` (the CLI prints it as `score=`),
  plus `n_hits/n_keywords/hit_keywords`; `Classification.evidence` is a list
  of DICTS (`e["kind"]`, `e["detail"]`), not objects.

## Dev loop

```sh
uv run pytest -q    # expect: 320 passed in <1s (count synced to scripts/test-count.txt, LORE-029)
uv run ruff check . # expect: All checks passed!
```

Board: `.coding-hermes/board/tasks.jsonl` (JSONL, last row per id wins,
`LORE-*` ids). Commits: `type: description. Addresses <task-id>.`; GitReins
Tier-1 guard runs pre-commit; never commit `.gitreins/` runtime artifacts.
