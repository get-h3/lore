# PRD: `h3-lore` — Runbook Compiler

**Project:** get-h3 · agent-ops line · **Item:** B3 · **Author:** Kara-agent · **Date:** 2026-09-17
**Status:** proposed · **Effort:** M–L (~3 weeks) · **Depends on:** B1 (logsey) for evidence blocks; DuckBrain + boards as inputs · **Feeds:** every responder, human or agent

---

## The one-liner

Compiles the fleet's *actual* incident history — DuckBrain namespaces, board events, post-mortem docs — into living runbooks per failure class, each carrying the **real queries and commands that diagnosed it last time**, re-validated against the current system on a schedule.

## The problem, measured

**Runbooks rot because they're written prose, and prose has no execution feedback.** The fleet's lived proof, three cases deep:

1. **The gateway restart doctrine** took four incidents and a compaction-boundary loss to formalize: batch config changes, pause-first under load, expect up-to-30-min drain 503s. The knowledge existed only in scattered session summaries and one memory note ("drain 503s kill ticks") — invisible to a fresh agent hitting the same wall.
2. **The scheduler cooldown authority model** (DB vs `fleet.toml` dual-store pins, `--verify` tripwire) was learned across SCHED-GAP-025 → SCHED-GAP-121 — the *same* class of drift bit twice, a year-class apart in fleet maturity, because the first lesson lived in an AGENTS.md paragraph nobody re-reads at incident time.
3. **The `.env`/`.env.example` clobber** had a one-line cure (container-env repair) that survived only inside one session's transcript. The next operator hits the same wall with no runbook — recovery took reading Docker env by hand and diffing four secret generations.

The pattern: **every incident generates world-class runbook material, and it evaporates into chat archives.** Bane's audit doctrine says findings must be *re-findable*; today they're re-findable only by whoever remembers the keywords.

## User stories

**US-1 (incident responder, mid-fire):** As an agent at 3 a.m. facing "scheduler spawns 503-ing at spawn time," I ask `lore match "spawn 503"` and get the drain-window runbook — checks in order, the exact logsey query, the known-good command sequence — compiled from the last three times this happened.

**US-2 (post-incident scribe):** As the agent that just closed an incident, I run `lore absorb --window 2h --ns coding-hermes` and it drafts the runbook update from what actually happened — evidence blocks, working commands, dead ends marked dead — filed as a *proposal* the operator approves.

**US-3 (runbook auditor):** As Bane reviewing coverage, I run `lore audit` and see: every failure class seen in the last 90 days, whether a runbook exists, whether its commands *still work* (last-validated date), and the classes with incidents but no runbook — coverage as a number, not a feeling.

**US-4 (new-box onboarding):** As an agent landing on a fresh fleet node, `lore` syncs the class runbooks; the box's first responder starts with four incidents' worth of scar tissue instead of zero.

## What it compiles

Per **failure class** (classified from the incident trail: drain-window, shared-checkout collision, secret clobber, disk-pressure corruption, cooldown drift, key-rotation, …):

- **Signature:** the log/logsey pattern that identifies the class (from B1's message-classes)
- **Checks in order,** each with: the exact command/query, expected healthy vs incident output, and *what decision it drives*
- **Recovery ladder** with guardrails (what NOT to run — the fleet's "never `--apply` on cooldown policy", "USR1-only restarts" class of law)
- **Evidence trail:** links to the DuckBrain rows, board events, and commits where each step was learned
- **Provenance + freshness:** which incidents fed it, last-validated timestamp

## The re-validation loop (what makes it living)

Dead runbooks are the disease; this is the cure:

- **Command lint on schedule:** every command in every runbook re-runs in read-only/verify mode (`--verify` flags, `--dry-run`, SELECT-only queries) against the live system on a weekly cron; any drift flips the runbook to `stale` in `lore audit`.
- **Absorb-on-close:** incident closure without an `lore absorb` leaves a visible gap in `lore audit` — the process enforces itself.
- **Human-in-the-loop on write:** compile proposes, operator approves (the fleet's board-review model); nothing auto-writes doctrine.

## Interface

```
lore match "<symptoms|log line>" [--class ...]
lore show <class> [--evidence]
lore absorb --window ... [--ns ...] [--board ...]   # propose updates from an incident trail
lore audit [--format table|json|md]                 # coverage + freshness matrix
lore validate [--class ...]                         # run the read-only command lint now
```

## Success criteria

1. Compile-from-history proof: the **gateway drain-window runbook**, compiled purely from the 09-16 incident trail, contains the correct checks and ≥90% of the commands the humans eventually figured out by hand — before the next drain incident occurs.
2. `lore audit` runs on the fleet's last 90 days of incidents and produces an honest coverage matrix (≥8 failure classes, gaps named, not hidden).
3. Re-validation catches reality: after a deliberate breaking change (e.g. rename a flag the runbooks reference), the weekly lint flips the affected runbooks to `stale` within one cycle.
4. Responder test: a fresh agent, given only `lore match`, handles a scripted recurrence of a known incident in ≤3 steps without consulting chat history.

## Why get-h3 / why open

Every ops team's runbooks rot; every agent fleet re-learns the same incidents. The hard 20% — incident classification from messy trails, evidence-block extraction, the re-validation harness — is exactly what a fleet with DuckBrain + boards + logsey already has the raw material for, and nobody else has. This is Bane's audit doctrine ("findings must be re-findable") compiled into a tool.

## Risks

- **Garbage compounding:** a wrong runbook is worse than none → proposals-not-writes, operator approval, provenance on every line.
- Classification sprawl → curated class list with an explicit `unclassified` bucket; absorbing into `unclassified` is always allowed, inventing classes is not (without approval).
- Validation false-confidence → read-only lint proves commands *parse and answer*, not that recovery *succeeds*; runbooks carry that honesty label too (the verify-harness honesty law, applied to ops).
