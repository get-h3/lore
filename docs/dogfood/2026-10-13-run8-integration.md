# lore dogfood run 8 — machine-contract surface (2026-10-13, HEAD 25ddbb6)

## Promise tested

A script can consume lore: the `--format json` family (audit / show / compile)
agrees with itself, exit codes match the documented ladder, the gate DENY
matrix is closed, and `absorb --window` turns a real evidence trail into
per-class proposals. Runs 1-7 covered the human surfaces; run 8 is the
machine contract.

## What was driven, results

- `audit --format json` rc=0: 14 entries (13 curated + unclassified bucket),
  summary honesty note intact; gateway-drain-window 7 checks / 7 commands,
  consistent with `show`/`compile`.
- Parity probe: `show <c> --format json` vs `compile --class <c> --format
  json` — `jq -S 'del(.provenance,.evidence_trail)'` diff is byte-clean for
  the same class. First probe accidentally compared drain-window against
  secret-env-clobber (tester error, not a product defect) — recomputed and
  confirmed PARITY=ok.
- Exit ladder (all with direct `$?`, no pipes):
  unknown class compile → 2; gate absorb unknown class → DENY + exit 1 with
  the closed-registry explanation; gate no-new-lesson → ALLOW exit 0 with
  source provenance; consult unmatched failure → honest fail-open exit 0.
- `absorb --window` three shapes: fenced bare-ISO trail → per-class proposal
  JSON rc=0 (2 blocks classified); bracketed-prefix trail → honest
  "no blocks found" rc=0; unparseable/claimed → rc=2 with an error that
  names internal tooling state instead of the accepted shape (LORE-053).
- `validate --execute` full sweep: 14 classes, 35 real command results,
  8 outcome=error across 5 classes; 5/13 curated classes flip 'stale' on the
  project's own working box (/bin/sh process-substitution, missing fleet.toml
  and ~/.hermes paths). env_absent_orders stayed [] everywhere (LORE-052).
- Fresh-leg citation: sibling run 7 (commit 25ddbb6, same day) proved
  415 tests + ruff clean on a fresh bunker-mvp agent incl. lint-persistence
  across surfaces. No install leg re-run: SKIPPED-install-bunker with
  citation (las-03/02/04/01 offline; run-7 leg is same-day evidence).
- Perf: match 81.0ms ± 12.9 warm, audit 78.5ms ± 4.9 (uv-run overhead
  included). Nothing a user would notice; no PERF row.

## Verdict

SHIPPABLE on the machine-contract surface. The JSON family agrees with
itself, the exit ladder is honest everywhere it was probed, and the one
rough edge (absorb error text) is usability, not correctness.

## Sibling-run note

Run 7 (another lane, commit 25ddbb6) landed mid-tick with LORE-049/050/051.
Run 8 restored the board from HEAD before appending and filed its distinct
findings under LORE-052/053; our duplicate of run-7's LORE-051 premise was
dropped, not filed.
