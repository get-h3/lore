# QA-LORE-8 — failure-branch-only cell ci-act removed from owed-cell NOT-COLLECTED accounting

Tick: lore-foreman-2026-11-23-04-28-28 · Wave worker: glm-5.3-flash @ ollama-cloud (session local-0bc79ed8)

## Defect (red-proof)

The battery emits the ci-act cell ONLY from act-failure branches of the ci-pass cell
(green/skipped CI simulations never emit it), but derive_owed_cells derives the owed
roster from shell-command-position `cell <name>` calls, so ci-act was always owed.
Every green fire landed a spurious row. Ground truth, lore fire
lore-qa-2026-11-22-20-12-17: ledger cells carry
`"ci-pass": "OK(act 1 job green)"` AND `"ci-act": "NOT-COLLECTED(harness QA-LORE-8)"`.
Foreman replay of the roster derivation over the harvested battery script
(agent-qa-run.sh) listed ci-act among 16 owed cells while the fire's evidence carries
no ci-act row — reproduced mechanically before the fix.

## Fix

One inserted block inside derive_owed_cells
(~/.hermes/scripts/bunker-qa.sh, after the names awk assignment, live line 5538):

```
    # QA-LORE-8 (2026-11-23): failure-branch-only cells are never independently
    # owed. The battery emits ci-act only beside a FAILED ci-pass act leg, so a
    # green or skipped CI fire legitimately has no ci-act row; NOT-COLLECTED
    # accounting must not invent one. A genuinely dropped CI leg is still
    # covered by ci-pass itself (its absence still emits a NOT-COLLECTED row).
    names=$(printf '%s\n' "$names" | grep -vx 'ci-act' || true)
```

Pre-edit snapshot: ~/.hermes/scripts/bunker-qa.sh.bak-QA-LORE-8-20261123.
Post-fix md5: f398984ca5104f01520a9cea39a81c2e (recorded after the QA-LORE-6
restore; that fix's own md5 trail is in run-QA-LORE-6/).

## Verification (foreman-run, all observed live)

- diff vs pre-edit snapshot: exactly the 6-line inserted block; emit loop,
  present_cells, and every other byte unchanged (insert-only).
- The cell-call awk extractor itself is byte-identical before/after
  (md5 b88d4b1a289b92e1291c083b55342632 both) — detection logic untouched.
- Roster replay over the harvested lore-qa-2026-11-22 battery script:
  before = 16 owed cells including ci-act; after = 15; the ONLY removed line is
  ci-act (diff `6d5 < ci-act`); ci-pass and all other cells retained.
- Negative direction covered structurally: ci-pass remains owed (present in the
  after roster) and the emit loop is byte-identical, so a genuinely dropped CI leg
  still yields its NOT-COLLECTED row.
- bash -n on the live harness: exit 0.

## Honest limits

- The fix was proven by replaying the derivation over the real harvested battery
  script, not by firing a new battery; the next green lore-qa fire must show NO
  ci-act NOT-COLLECTED row in its ledger cells.
- "Fixed in harness" is only true for the md5 tested (f398984c...), per the fleet
  harness_notes convention.
