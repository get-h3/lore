# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **LORE-069** — `lore absorb` can now emit a real runbook UPDATE. Its only
  production call site (`absorb_proposal`, lore/absorb.py) previously called
  `propose(class_id)` with no `existing` argument, so EVERY payload said
  `"action": "new"` with `added` byte-identical to the runbook the class
  already has — the tested diff engine (compiler.py) was unreachable from any
  user-facing path, and PRD US-2's "drafts the runbook update ... evidence
  blocks, dead ends marked dead" was unmet. `absorb_proposal` now compiles the
  class's existing runbook, folds the trail evidence into the fresh side (swept
  blocks passed through faithfully from `absorb_sweep`, or the lesson text
  parsed with the exact `parse_text_line` tolerance the `--window` sweep uses;
  folded via `attach_evidence`), and calls
  `propose(class_id, existing=..., fresh=...)` — `propose` gained an additive
  keyword-only `fresh` parameter (default unchanged). Curated classes with a
  trail that adds evidence get `"action": "update"` with a NON-EMPTY
  `added.evidence_trail` naming the trail-derived content; a trail that adds
  nothing is an explicitly empty update (never a fake `"new"`); every folded
  block also lands in the payload's `blocks` list as
  `{kind, detail, source, observed_at, outcome}` with `outcome` the closed
  vocabulary `"dead-end"`/`"observed"` (US-2's dead-end marking, structured).
  Propose-not-write holds — nothing is written. 13 regression tests at the
  `absorb_proposal` seam pin both the update and the no-change case; the
  run-14c usage-skill caveat section is updated to describe the fixed surface.

- **LORE-060** — gateway-drain-window's logsey checks (orders 1 and 7) now
  speak logsey's REAL CLI contract: ONE quoted SQL string over the indexed
  DuckDB engine (`logs` table, `message`/`ts` columns, `now() - INTERVAL <n>
  MINUTE` windows), not the unshipped `--pattern/--since` flags that exit 2
  ("unexpected second argument") on the actual binary (dogfood run 10,
  verified live on HEAD 9b97fa2). `validate --execute` now reports both
  checks `ok` (exit 0) instead of env-absent-looking exits; the read-only
  gate, the 127-classification fixtures, the README/INSTALL rendered check,
  and the test-count literal were all synced. New
  `tests/test_lore060_logsey_sql_contract.py` pins the single-arg SQL shape
  so the fiction cannot re-enter the compiled runbook unnoticed.

- **LORE-050** — two honesty gaps from dogfood run 7's scratch-dir
  `validate --execute` (1/7 checks executed, 6/7 template-skipped, the
  history record grading the class `drifted_orders: []`). GAP A: every
  surface that renders a check command (runbook markdown, `validate`
  plan/`--execute`, `consult --failure`) now prints a `fill-in:` hint per
  unfilled `<placeholder>` slot from a per-slot-name table
  (`lore/placeholders.py`) describing WHERE the value comes from —
  deployment-neutral, never a host path or a secret's value. GAP B: the
  history record carries derived `executed_count`/`total_checks` and
  consult's lint line appends `; executed X/Y checks`, so "not drifted" can
  never again silently mean "almost nothing was exercised". Counts derived
  from the seeded outcomes everywhere, including tests.

- **LORE-043** — the tick-start consult (LORE-007) no longer goes silent on
  short board-row TITLES. Keyword acceptance is now length-scoped: a text of
  at most 8 words (the board census' title 25th percentile; the 10-word
  paraphrase pinned as refused stays on the long path) accepts keyword
  evidence at a 0.3 gate (was 0.6 for every length), so the 4-word title
  `worker worktree checkout collision` (3/8 keywords = 0.375) labels
  `shared-checkout-collision` at capped keyword confidence instead of
  returning `matched:false`. The confidence cap (0.5), the keyword-only
  evidence kind, the honesty refusal below the gate with its near-miss
  echo, and the long-text 0.6 gate are all unchanged; the registry is
  untouched (13 curated classes).

## [0.1.2] — 2026-09-26

Version refresh only — no code changes. Bumped from `0.1.1` after a stale-version
audit (`uv pip list --outdated` flagged the editable install; the published
"0.8.6 latest" on the index belongs to a different `lore` package, not this
repo). Also syncs the module-level `lore.__version__`, which had drifted to
`0.1.0` while `pyproject.toml` carried `0.1.1`. Not released: no tag, no
publish — the bump keeps the upgrade path live for installed `v0.1.x`
tool installs (same rationale as the 0.1.1 bump).

## [0.1.1] — 2026-09-25

Post-release development version. Bumped from `0.1.0` so that
`pip install --upgrade` from an installed `v0.1.0` actually reinstalls —
during the QA-LORE-1 upgrade-path cell, upgrading from the tag to `main`
was a silent no-op while both carried version `0.1.0`.

## [0.1.0] — 2026-09-24

> Tagged `v0.1.0` (annotated tag on commit `c655666`) and the repository is
> **public** as of 2026-09-25, executing LORE-001's recorded decision: flip to
> public at the first release. The entries below describe work landed to date
> (see `git log`).

### Added (2026-09-23)

- Project kickoff: repository, PRD, and the rebuilt task list
  (`docs/PRD.md`, commit `43db84f`).
- Failure-class taxonomy + classifier: 10 curated failure classes plus an
  explicit `unclassified` bucket, and the `lore match "<symptoms>"` CLI
  (commits `f883cae`, merge `6a93e7d`).
- GitHub Actions CI: build + pytest + ruff on push/PR (commits `d176e63`,
  merge `53ceea3`).
- GitReins co-harness + `AGENTS.md` conventions (commits `0859d51`, `e4b071c`,
  `ea8fbd6`, `aa7690a`).
- Documentation to the fleet's public-deliverable standard: this changelog,
  `SECURITY.md`, and a README rewrite with a runnable walkthrough
  (`LORE-015`).
- Runbook compiler: `lore/compiler.py` + `lore/runbook.py` emit a Runbook per
  curated failure class (signature, ordered checks with healthy-vs-incident
  expectations and the decision each drives, recovery ladder, `never X`
  guardrails, evidence trail, provenance + `last_validated`). Compilation is
  **propose-not-write** — no published runbook is written to disk. Adds the
  `lore compile [--class X] [--format json|md]` subcommand (commits `7cbdb70`,
  merge `d969b81`).
- QA cycle finding `QA-LORE-1` (upgrade-path finding) appended to the board
  (commit `209fb2c`).

### Added (2026-09-24)

- `lore consult` (LORE-007), `lore gate` (LORE-008), the `lore absorb
  --window` evidence-trail sweep, `lore show` and `lore audit` (LORE-010):
  the shipped CLI surface is **eight subcommands** (`lore --help`).
- Failure class `gateway-guard-violation` added to the closed registry
  (LORE-017, commit `198f2b0`) — 10 curated classes + `unclassified`.
- QA audit coverage for the v0.1.0 CLI + API surface (LORE-016,
  commit `2d8f3dd`).

### Documentation (2026-09-23, task `LORE-012`)

- `docs/INSTALL.md`: prerequisites, install, and first run for someone who has
  never seen the fleet — every command shown was run, every output pasted
  verbatim (`match`/`compile`/`validate`/`--help`; the expected test count is
  stated on the current tree in that document), plus an explicit "what this
  tool is NOT" section.
- `docs/RUNBOOK-STORE.md`: the runbook-store design **decision** — central
  registry in the fleet's DuckBrain namespace + materialized per-repo
  git-tracked `runbooks/` dirs; read/write paths, propose-not-write, conflict
  and freshness rules, rejected alternatives. Design only; not implemented.
- README to the public-deliverable standard: hook headline, real numbers,
  PRD US-1..US-4 use-cases, and a Status section that separates shipped from
  planned/in-flight per task id (`LORE-005` evidence blocks and `LORE-006`
  re-validation are in flight, not shipped).