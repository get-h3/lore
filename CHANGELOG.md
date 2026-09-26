# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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