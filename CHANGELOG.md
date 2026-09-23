# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> Note: no git tag has been cut yet — there is no shipped release to point at.
> The package version in `pyproject.toml` is `0.1.0`; the entries below are the
> work landed to date, dated 2026-09-23 (see `git log`).

### Added (2026-09-23)

- Project kickoff: repository, PRD, and the rebuilt task list
  (`docs/PRD.md`, commit `43db84f`).
- Failure-class taxonomy + classifier: 9 curated failure classes plus an
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

### Documentation (2026-09-23, task `LORE-012`)

- `docs/INSTALL.md`: prerequisites, install, and first run for someone who has
  never seen the fleet — every command shown was run, every output pasted
  verbatim (45 tests, `match`/`compile`/`--help`), plus an explicit
  "what this tool is NOT" section.
- `docs/RUNBOOK-STORE.md`: the runbook-store design **decision** — central
  registry in the fleet's DuckBrain namespace + materialized per-repo
  git-tracked `runbooks/` dirs; read/write paths, propose-not-write, conflict
  and freshness rules, rejected alternatives. Design only; not implemented.
- README to the public-deliverable standard: hook headline, real numbers,
  PRD US-1..US-4 use-cases, and a Status section that separates shipped from
  planned/in-flight per task id (`LORE-005` evidence blocks and `LORE-006`
  re-validation are in flight, not shipped).