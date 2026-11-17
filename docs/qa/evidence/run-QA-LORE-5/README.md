# QA-LORE-5 — `.qa/chaos-probes/corruption.sh` (torn-state probe)

Run: `lore-foreman-2026-11-17-05-00-08`. Merged at `70229d8` (worker commit `7702ce1`,
merge `c8588d7`). Tier-1 gitreins verdict `736e959b` (passed:true, commit `70229d8`).

## What shipped

`.qa/chaos-probes/corruption.sh` — 251 lines, mode `100755` in the merged tree
(`git ls-tree HEAD .qa/chaos-probes/corruption.sh` → `100755 blob 7eb30110…`).

Why a probe and not a test file: the clean-machine battery's generic chaos-corruption cell
builds its candidate set from `*.db` / `*.sqlite` / `*.sqlite3`, and lore's durable state is
`.lore/validate-history.jsonl` (per-cwd, git-ignored). The harness has an opt-in hook —
`bunker-qa.sh:3595` `[ -x .qa/chaos-probes/corruption.sh ]` — that REPLACES the generic cell
logic and self-grades on the probe's rc (0=OK, 1=FAIL, 2=INFO/environment gap, 124=hang).

## The two rungs

1. **Torn ledger.** A throwaway `mktemp -d` gets `.lore/validate-history.jsonl` built from the
   product's own classifier output: two well-formed records, a line truncated MID-RECORD (no
   trailing newline — what an interrupted append leaves), one non-JSON garbage line, and then a
   third well-formed record written AFTER the damage. Both public readers must scan past both
   malformed lines and report the post-damage record: `lore consult "<symptoms>"` must carry
   `last lint-validated 2026-11-16T12:00:00Z`, keep the `(local history, not operator
   attestation)` honesty label, and keep the `executed 6/7 checks` clause;
   `lore audit --format json` must still surface the post-damage drift (`"stale_classes": 1`).
2. **Unreadable ledger.** The history path is replaced by a directory (works as root, unlike
   `chmod 000`), and the CLI must degrade cleanly: no `Traceback (most recent call last)`, no
   hang, no crash.

Everything lives inside the temp dir; nothing in the repo tree is written.

## Live proof (merged tree, `main` at `70229d8`)

```
$ PATH=$PWD/.venv/bin:$PATH bash .qa/chaos-probes/corruption.sh; echo "rc=$?"
torn ledger: read past 2 malformed lines, newest record still reported by consult+audit; unreadable ledger: clean degrade, no traceback
rc=0
```

## Harness wiring proof

The hook condition is literal: `[ -x .qa/chaos-probes/corruption.sh ]` → **YES** on the merged
tree. Emulating `bunker-qa.sh:3596-3605` byte-for-byte (`pp_out=$(timeout 120 <probe> 2>&1)`,
`case rc`) yields:

```
cell chaos-corruption -> OK | rc=0 | detail: torn ledger: read past 2 malformed lines, newest
record still reported by consult+audit; unreadable ledger: clean degrade, no traceback
```

i.e. the cell can no longer answer `N/A "no db/state files in repo"` — it grades the probe.

## Gates (merged tree)

| Gate | Result |
|---|---|
| `python -m pytest -q` | `572 passed in 8.04s` |
| `bash scripts/check-test-count.sh` | PASS canonical=572 live=572; class-count=13; no stale count literals |
| `python -m ruff check .` | All checks passed |
| probe hand-run | rc=0 (above) |

## Disclosed limits

- **Red-proof not executed.** The intended negative control (patch a scratch copy of
  `lore/validate.py` so the reader `break`s at the first malformed line, then require the probe
  to return rc=1) was attempted and **blocked by the harness approval gate** (the scratch-tree
  `rm -rf` needed consent that an unattended tick cannot give; silence is not consent). It was
  not retried. What is established instead: the probe's assertions are non-vacuous by
  construction — rung 1 requires the POST-DAMAGE timestamp `2026-11-16T12:00:00Z`, which a
  reader that stopped at the torn line could not print (it would print the older record), and
  the class id is derived from `lore match` at run time rather than hardcoded (premise drift
  exits rc=2 instead of a false OK).
- **The full clean-machine battery was not re-run this tick**, so no bunker `cells.txt` line
  exists for chaos-corruption. What is proven here is the hook path the battery executes and
  the probe's verdict under it; the battery's own cell line lands on the next QA-lane run.
- No pytest test was added on purpose: the rung assertions live in the probe, and a collected
  test would force a canonical test-count bump into dated `docs/qa/evidence` and
  `docs/release-evidence` records that this row does not own.
