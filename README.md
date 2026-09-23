# lore

### The cure that lived in one session transcript. Compiled into a runbook that proves it still runs.

Runbook compiler — **"how did we fix this last time, and does it still work?"**

*"How did we fix this last time — and does it still work?"*

---

## Why this exists

**Runbooks rot because they're written prose, and prose has no execution feedback.** The fleet's lived proof, three cases deep:

1. **The gateway restart doctrine** took four incidents and a compaction-boundary loss to formalize: batch config changes, pause-first under load, expect up-to-30-min drain 503s. The knowledge existed only in scattered session summaries and one memory note ("drain 503s kill ticks") — invisible to a fresh agent hitting the same wall.
2. **The scheduler cooldown authority model** (DB vs `fleet.toml` dual-store pins, `--verify` tripwire) was learned across SCHED-GAP-025 → SCHED-GAP-121 — the *same* class of drift bit twice, a year-class apart in fleet maturity, because the first lesson lived in an AGENTS.md paragraph nobody re-reads at incident time.
3. **The `.env`/`.env.example` clobber** had a one-line cure (container-env repair) that survived only inside one session's transcript. The next operator hits the same wall with no runbook — recovery took reading Docker env by hand and diffing four secret generations.

The pattern: **every incident generates world-class runbook material, and it evaporates into chat archives.** Bane's audit doctrine says findings must be *re-findable*; today they're re-findable only by whoever remembers the keywords.

## What it is

Per **failure class** (classified from the incident trail: drain-window, shared-checkout collision, secret clobber, disk-pressure corruption, cooldown drift, key-rotation, …):

- **Signature:** the log/logsey pattern that identifies the class (from B1's message-classes)
- **Checks in order,** each with: the exact command/query, expected healthy vs incident output, and *what decision it drives*
- **Recovery ladder** with guardrails (what NOT to run — the fleet's "never `--apply` on cooldown policy", "USR1-only restarts" class of law)
- **Evidence trail:** links to the DuckBrain rows, board events, and commits where each step was learned
- **Provenance + freshness:** which incidents fed it, last-validated timestamp

## Status

**Kicked off 2026-09-23.** Repo scaffolded, first task list built from the PRD and the
fleet's own incident history. See [`docs/PRD.md`](docs/PRD.md) for the full
product requirements and the acceptance replays this tool is judged against.

The task list lives on the project board at
`.coding-hermes/board/tasks.jsonl` and is driven by the fleet scheduler.

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

## Design laws this repo inherits

- **Evidence or it did not happen.** Every number links to the row, log line or
  commit that produced it. No summary without a drill-down.
- **Honesty labels are renderer-enforced.** Missing data renders as "no data",
  never as zero.
- **Absence is a first-class answer.** If the tool cannot see something, it says
  so loudly rather than reporting a confident zero.
- **Budget is the spec.** A tool that costs more than it answers gets uninstalled.

## License

MIT — see [LICENSE](LICENSE).
