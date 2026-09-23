# The runbook store: design decision

**Decision: two homes, one truth — a central registry in the fleet's DuckBrain
namespace, materialized into per-repo, git-tracked `runbooks/` directories.
Nothing lands in either without an operator-approved proposal.**

Status: decided (this document), not implemented. Today `lore compile` prints
to stdout only.

---

## The problem the store solves

`lore compile` can already produce a correct runbook proposal — but a proposal
that evaporates with the terminal scrollback is exactly the disease this tool
exists to cure. The knowledge needs to (a) be reachable fleet-wide, from any
box, by an agent that has never cloned the repo where the incident happened,
and (b) travel with the code it heals, so that a repo's next reader — human or
agent — sees its runbooks without asking a registry.

Either home alone fails:

- **Registry-only** fails at PR review. A runbook for `shared-checkout-collision`
  that lives only in a central namespace never crosses the desk of the person
  reviewing a change to the checkout code. Runbooks rot precisely when their
  review path decouples from the code's review path.
- **Dirs-only** fails at cold-start. A brand-new node (PRD US-4) has no clones
  yet; an agent mid-fire on an unfamiliar box cannot be asked to know *which*
  repo to look in — classification is fleet-level, not repo-level.

## The two homes

### 1. Central registry — DuckBrain namespace

A `lore` namespace in the fleet's persistent memory holds the canonical copy of
every runbook: class registry index, current runbook bodies, provenance, and
`last_validated` state. Any agent on the fleet can read it before a single
clone exists. This is the read-entry-point for PRD US-4 (new-box onboarding)
and the authority `lore match` and a future `lore show` consult.

### 2. Materialized per-repo `runbooks/` directories

Each repo that a class's runbook touches gets a git-tracked `runbooks/`
directory holding the materialized copy of its runbooks (rendered markdown,
the same shape `compile --format md` emits). Because they are git-tracked:

- updates travel with the code and land through the repo's normal PR review —
  a human reviewer approving a change to the cooldown code sees the runbook
  delta that change causes, in the same diff;
- the fleet's doctrine of "git-backed, review-gated" applies unchanged;
- history and blame work for free.

## The shape of a stored runbook

A stored runbook is exactly what `lore/runbook.py` defines — serialization is
already lossless (the `Runbook`/`Check` dataclasses, `to_dict`/`from_dict`
round-trip asserted in tests):

- `class_id`, `name`, `signature` — identity and the pattern that matches it;
- `checks` — ordered list, each with `order`, `command` (the exact command),
  `expected_healthy`, `expected_incident`, `decision`, `read_only`,
  `evidence`;
- `recovery_ladder` — the ordered recovery steps;
- `guardrails` — the "never X" laws;
- `evidence_trail` — links to the incident rows, board events, and commits
  where each step was learned;
- `provenance` — what compiled this and from where;
- `last_validated` — ISO-8601 or None = never validated;
- `status` — `proposal` | `validated` | `stale`.

The registry stores the JSON form; materialized dirs store the rendered
markdown form (`compile --format md`). Both are generated from the same
object, so neither can drift into a different structure.

## Read path

```
agent needs a runbook
  -> DuckBrain lore namespace (canonical, fleet-wide, no clone needed)
  -> materialized per-repo runbooks/ dir (context at the point of work,
     travels with git clone, reviewable in-PR)
  -> human PR review (any change to a materialized dir is a normal PR)
```

`lore match` and `lore show` read the registry. The materialized dir is the
same content rendered for humans at the point where the failure happens —
so the runbook is discoverable both by search (registry) and by proximity
(the repo).

## Write path — propose-not-write, end to end

1. **Compile proposes.** `lore compile` (and the planned `lore absorb`,
   LORE-005's evidence blocks feeding it) emits a runbook with
   `status: proposal` to stdout. It never writes to the registry or to any
   `runbooks/` dir.
2. **An operator approves.** A human (or an explicitly authorized operator
   flow) reviews the proposal — checks, commands, guardrails, evidence trail.
3. **Only then does anything land.** Approval writes the runbook to the
   central registry, then (or via the next materialization pass) updates the
   affected repos' `runbooks/` dirs — which land as normal PRs and pass human
   review there too.

No automatic write path exists anywhere in this design. A wrong runbook is
worse than none (PRD §Risks); approval is the only gate between a proposal
and a stored runbook.

## Conflict / dedupe between registry and dirs

- **The DuckBrain registry is canonical.** A materialized dir is a rendered
  projection of the registry entry; if they disagree, the registry wins and
  the dir is regenerated.
- **Materialization is deterministic** — the markdown renderer
  (`Runbook.to_markdown()`) is pure, so re-materializing the same registry
  entry produces the same bytes; git diffs therefore show only real changes.
- **Dedupe is by `class_id`,** one runbook per class, both sides. Two repos
  both touched by one class share one runbook (it materializes into each
  affected repo, identical); a runbook never forks into repo-specific
  variants without becoming a new, separately-approved proposal.
- **Drift repair:** a materialization pass compares each dir against the
  registry and opens the diff as a PR; it never silently force-pushes a dir.

## Freshness / staleness contract

- `last_validated` is the only freshness signal, and None renders as
  "no data (never validated)" — never as zero or a fake date.
- The re-validation loop — a weekly read-only command lint
  (`--verify`/`--dry-run`/SELECT-only) that flips drifted runbooks to
  `status: stale` — is **planned, in flight under LORE-006**. It is named here
  as a contract the store must accommodate (`status: stale` already exists in
  the data model), not as a shipped capability. Nothing re-validates today.
- A stale runbook is not deleted: it stays in the registry and dirs with its
  honesty label, because a stale map is still evidence of the terrain.

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| **Registry-only** (DuckBrain alone) | Runbooks never pass human PR review; repo reviewers never see runbook deltas; cold-box agents win but code authors lose. |
| **Dirs-only** (per-repo alone) | Cold-start fails — a fresh node has no clones and no way to know which repo holds the runbook; no fleet-wide index for `match`/`audit`. |
| **DB-only** (SQL/SQLite store, no git) | Loses PR review entirely, adds a database to a zero-dependency tool, and contradicts the fleet's JSONL/git-backed-configuration doctrine: stores that travel in git get reviewed; opaque DB rows do not. |
| **Git-only central repo** (no DuckBrain) | Adds a clone step to every cold-start and duplicates what the fleet's persistent memory already provides; DuckBrain is the established read path for fleet knowledge. |

## Status of this decision

Decided in this document (LORE-012). Implementation is **planned, not
shipped**: today nothing writes anywhere, `compile` prints proposals to
stdout, and the re-validation loop is in flight under LORE-006. When the
store lands, this document's write path becomes the implementation spec.