# lore run-9 (dogfood, 2026-10-17) working notes — HEAD 9b97fa2

## Angle / delta (run 8 HEAD 25ddbb6 vs current 9b97fa2)
- 69 files, +9379: LORE-049 round-2 guard-vocab, LORE-050 placeholder hints + executed-ratio
  honesty, LORE-052 bash-runner/env-absent, LORE-054 match --class NEW FLAG, LORE-055 consult
  exit-2 missing-input, LORE-056 gate --record parent creation, PERF-1 compiler clone swap.
- Uncovered-by-prior-runs surfaces = exactly these delta verbs + re-proof of each at HEAD.

## Local real-use results (control host; evidence /tmp/lore-df/local-probes*.txt)

### All four landed fixes hold their documented contracts:
- LORE-054: A1 match --class valid-matching → gateway-drain-window 0.90 rc0;
  A2 class present, no match → confidence=0.00 rc0 (documented); A3 unknown class
  → rc2 "error: unknown class 'does-not-exist'"; A4 flagless control unchanged.
- LORE-055: B1 bare consult → rc2 "error: consult requires a title argument unless
  --failure is given (usage: lore consult <title> [--detail ...] | consult --failure
  <text>)"; B2 title-only no-match keeps rc0 + "no matching runbook" (fail-open contract
  intact per the docstring).
- LORE-049 round-2: C1 bare finding list → gateway-guard-violation 0.90
  (signature:secrets detected in diff); C2 guard FAILED + secrets co-occur → 0.90
  (signature:guard FAILED secrets detected); C4/C5 git canonical collision phrases →
  shared-checkout-collision 0.90 (LORE-041 re-proof intact under round-2 signatures).
- LORE-056: D1 rm -rf parent → gate ALLOW rc0, parent dir CREATED, one valid JSONL record
  written ({"allowed": true, "decision": "no-new-lesson", ...}); F3/F4/F5 all DENY arms
  (missing class / unknown class / empty reason) → rc1 "GATE: DENY" + error line, ZERO
  filesystem writes (no dir created) — propose-not-write honored on the deny side; D1/D4
  ALLOW arms write exactly one record.

### Operator-error captures (my misses, recorded so nobody re-files them):
- E3 `show --class X --format json` → rc2 unrecognized args: show takes POSITIONAL class_id
  (E4 `show gateway-drain-window --format json` rc0 — full JSON contract output). My assumed
  form, verified from --help after the miss. NOT a product finding — but note match/consult
  take --class/--failure FLAGS while show/compile take POSITIONAL class args: mixed forms
  across the verb family is at most a P3 docs polish note, run-8 already covered exit ladders.
- F1 consult --failure with a PATH → fail-open "no matching runbook": --failure takes TEXT
  (usage says `--failure <text>`). My miss, not a defect.
- D3 gate absorb with no --reason → ALLOW: --reason is only REQUIRED for no-new-lesson
  (source lore/absorb.py:98-116). Correct per source; my assumption was wrong.

### Perf (Step 2b; box loadavg 25-31 during measurements — fleet loaded, numbers are
self-consistent same-gate comparisons):
- Headline match, documented path: uv run match warm 111.1 ms ± 10.2, "cold" (--prepare
  sync) 119.4 ms ± 9.9; match --class 138.2 ms ± 27.4 (uv overhead dominates);
  .venv/bin/python -m lore match 62.9 ms ± 2.1 (raw interpreter path).
- Pattern: uv-run wrapper adds ~48 ms vs raw .venv path on this box. NOT filed:
  0.06-0.14 s for a one-shot CLI lookup is not a wait a user feels (hooky-satisfying
  doctrine — no PERF row for sub-half-second ops).
- PERF-1 re-proof under equal load: scripts/bench.py compile_all_registry
  pre-fix worktree (0bf0220) 158.63 µs/op vs HEAD (9b97fa2) 81.94 µs/op = 1.94x,
  same command (--number 200 --repeats 3), same box, ~15 min apart. Also directly:
  hyperfine bench.py whole-run pre 320.7 ms ± 27.5 vs post 258.8 ms ± 27.4 (1.24x).
  Foreman's claimed 1.45-2.13x HOLDS at HEAD. Fixes already closed PERF-1 — no new row.
- full `lore compile` (all 14 runbooks, docs path): 85.7 ms ± 5.6 warm via uv run.
- installed scripts/bench.py at the repo's documented perf entry (LORE-042) ran clean.

## Bunker battery leg (bunker-qa.sh, server bunker-mvp, host-agonistic substitute
after las-01..04 offline): launched agent=e864c056, QA HEAD 9b97fa2, evidence
/tmp/bunker-qa-evidence-20261017T041033Z-49866.jsonl. Cells: fresh-install, upgrade-prep,
ci-pass, chaos-*. Waiting on collect (background proc_c4cc56970ab5).

## Findings so far
1. (LORE-051Family) audit unclassified-bucket row still pending — NOT re-proven this run
   (not a delta surface; pending row stands, stopping condition).
2. (potential NEW) LORE-051-class: audit table counts 14 classes (13+unclassified shown as
   a class) — pending row; re-check what run 7 actually filed vs what's still open.
3. consult --failure check-count honesty: gateway-guard-violation runbook shows checks=2
   but the counts swept the registry last run with 7 checks; verify whether 2 is correct
   for this class (it is — that class has 2 checks authored; E5 crash is the concerning bit).
4. (potential NEW) `lore show --evidence` + `lore audit` interplay at HEAD — run-7's
   audit-bucket row LORE-051 still pending; skip, covered above.
5. (potential NEW) E5: `lore show <unknown-class>` rc/exit + error wording — check: does
   show name the closed registry (like compile does: "Known: ...") or leave bare? If bare,
   file a parity row.
