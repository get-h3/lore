# ADDENDUM-delivery4 — lore-docs audit, tick lore-ops-2026-11-24-21-03-06, pass 4

Pass 4 (re-fire) advanced the verification tier this lane has not reached before:
live-boundary T4 probes of the gate/metrics/record path documented in README.md
"QA/dogfood findings close through the absorb-gate" and "Observability", plus a
re-measure of the README-12 premise (delivery 3's carried-unverified queue).
Tip at probe time: 0e0f0504a18d05859f0a9a94616480cfd50cdd66 (HEAD == origin/main,
rev-list origin/main..HEAD = 0, no tip advance mid-pass). README.md sha256
c40222d1a0df7206bcd9c169970bd8a912b47ada8b16b48640727c6cb97494bd — byte-identical
to the sha README-12 was filed against, so its line numbers stand. Full command
transcript (exact commands + outputs): stand-in
`audit-lore-docs-2026-11-24-2103` probe-pass4-20261124.out, published below under
"Probe record".

## 1. README-12 premise re-measured — STILL TRUE at tip (no new row; evidence for the open row)

- `uv run python -m lore compile --class gateway-drain-window --format md` (rc=0)
  renders Check 1's command between literal ```sh / ``` fence lines
  (7 `^```sh$` lines across the full compile output).
- README.md quickstart compile sample (lines 103-127) holds the command as ONE
  4-space-indented line, ZERO fence lines in the sample region. The fence-form
  premise README-12 filed (`lore/runbook.py:128` behavior vs the sample) is
  unchanged; row stays open for its worker.

## 2. T4 gate + observability: every documented claim verified live (scratch textfile dir)

All probes used `H3_LORE_TEXTFILE_DIR=<run-unique scratch dir>` (README.md:284-285
documents the override to an existing writable directory). Effects read back from
WHERE THEY LANDED, not from stdout (T4):

1. ALLOW (absorb -> gateway-drain-window, --ref, --record): rc=0, verdict line
   `GATE: ALLOW (absorb -> gateway-drain-window)`. `h3_lore.prom` landed in the
   scratch textfile dir with `lore_gate_runs_total 1`, `lore_gate_last_success 1`.
   `--record PATH` appended exactly one JSONL line with exactly the fields
   README.md:273-276 documents (ack_ref, allowed, class_id, decided_at, decision,
   errors, lesson, reason, source, tool_version; tool_version 0.3.0).
2. ALLOW (no-new-lesson ack): rc=0, `GATE: ALLOW (no-new-lesson)`, record count
   UNCHANGED (1 → 1), `lore_gate_runs_total 1 → 2`. Matches the ac-ack semantics.
3. TRUE DENIAL (absorb with no class/lesson): rc=1, `GATE: DENY (2 errors)` +
   "error: absorb requires a class_id/lesson", NO record appended (1 → 1),
   `lore_gate_runs_total 2 → 3`, `lore_gate_last_success 0`. Matches
   README.md:272-277 ("Denials do not write audit records, but both verdicts
   export metrics") and README.md:283-286 ("Every gate verdict updates
   h3_lore.prom... 1 for ALLOW and 0 for DENY") — all verified live.

## 3. validate plan / --execute: documented behavior reproduced (T3 on the CLI, T4 on the persisted side-effect)

- Plan mode: rc=0, JSON plan listing `would_refuse: []`, executes nothing.
- `--execute`: rc=0. gateway-drain-window checks 1/7 record `error` against the
  ship's logsey 0.2.1 fallback engine (unsupported OR-predicate) and the class
  flips `stale` with `drifted_orders: [1, 7]`,
  `stale_reason: "lint drift: check 1 (error), check 7 (error)"` — behavior
  EXACTLY as documented at README.md:415-419 (index drift, not runbook drift;
  `logsey index rebuild` restores `ok`). NOT a docs gap: the stale flip and its
  reason string were quoted in the docs before this probe.
- Side-effect readback: `.lore/validate-history.jsonl` appended one record with
  the documented honesty_label + `executed_count`/`total_checks`
  (README.md:421-433); `git check-ignore .lore/validate-history.jsonl` →
  .gitignore:41 `.lore/` (the "git-ignored, per-box" claim at README.md:422
  verified). Checkout stayed clean except the pre-existing untracked
  .coding-hermes/evidence/ QA residue (row LORE-HYGIENE-20261122 owns that).

## 4. Coverage and boundaries this pass

Audited live: gate allow/ack/deny exits + verdict lines, metrics export +
override, audit-record write/denial semantics, validate plan vs --execute,
persisted lint-history record, README-12 sample-vs-binary render.
Findings filed: ZERO (no doc claim broke at T4; README-12's premise re-verified
as still true — its row remains the owner). Re-triage: no open pre-2026-09-30
P1-P3 doc rows on this board (all open doc rows already P4/P5).
UNVERIFIED (left for later passes / workers):
- `logsey index rebuild` claim (README.md:419) not exercised — touching the real
  logsey index state on this box is outside a docs lane's write budget.
- `lore validate --format md` render not re-run this pass (JSON arm covered).
- consult modes already T3-verified in delivery 2; consult --json not re-run.
- README-12's fix (render sample or drop the verbatim promise) remains with
  their worker; this pass only re-proved the premise.

## Probe record (frozen transcript of the exact commands + outputs, pass 4)

Probe transcript: /home/kara/.hermes/stand-in/docs/lore/probe-pass4-20261124.out
(supplement: probe-pass4-denial.sh output appended in place, both probes rc=0).
sha256 of the stand-in .out at publish time: see commit message.
