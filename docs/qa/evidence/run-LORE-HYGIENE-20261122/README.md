# run-LORE-HYGIENE-20261122 — QA battery evidence no longer dirties the repo

Row: LORE-HYGIENE-20261122 (P3). The bunker-qa.sh collector persisted each
battery's evidence ledger + per-cell logs INSIDE the repo-under-test at
`.coding-hermes/evidence/<tick>/` — 100-500K of untracked residue per run that
tripled over three batteries and refused every `scripts/release.sh --dry-run`
clean-tree precheck.

## Two-layer fix

1. HARNESS (deployed `~/.hermes/scripts/bunker-qa.sh`, NOT in this repo):
   `persist_evidence()` now writes to the durable OUT-OF-TREE root
   `~/.hermes/qa/evidence/<project>/<tick>/` via the new self-contained helper
   `qa_evidence_persist_root()` (`BUNKER_QA_EVIDENCE_PERSIST_ROOT` overrides the
   root; `BUNKER_QA_TICK` unchanged; no-repo SKIP contract unchanged). The run's
   closeout citation surfaces (header usage text, tick-id comment, collect-OK
   detail line, persist comment) were updated to the new path.
   - deployed sha256: 035b26fe3259003d067cf27b8310c54875d44fac93e203d947690b428f0f7115
   - pre-edit backup: `bunker-qa.sh.bak-LORE-HYGIENE-20261122-20261125T123045Z`
     sha256 d3a4432d80eac82e1e8a99bf6a64f2b1b8b3301f1f17189143444ab56cc94589
   - full diff: harness-diff.txt (54 lines, 6 hunks; the only remaining
     `.coding-hermes/evidence` string in the script is the comment that names
     the old path as history)
2. BELT-AND-BRACES (this repo): `.gitignore` gains `.coding-hermes/evidence/`
   with a comment naming the row, plus tests/test_lore_hygiene_evidence_residue.py
   pinning that a probe file under the legacy path is check-ignore-admitted AND
   invisible to `git status --porcelain`. Even a pre-fix harness generation
   can never read as dirty residue again. Canonical test count synced
   586 -> 588 (scripts/test-count.txt) and the six living-doc literals updated
   (guard-demanded; one of them sits inside a pasted INSTALL.md pytest block).

## Evidence map

- BEFORE-red-control.txt — pre-fix state at HEAD 2d28070: porcelain showed
  `?? .coding-hermes/evidence/`; release.sh REFUSED at the clean-tree precheck.
- harness-edit-gates.txt — the mandatory gates: bash -n, the new deployed-copy
  versioned suite (test_bunker_qa_evidence_persist.sh: 13/13 PASS vs fixed,
  RED vs backup reproducing the defect arm-by-arm: EVIDENCE-DIR inside the
  repo, dirty porcelain, legacy path created), existing-suite parity
  (identical counts backup-vs-fixed for the four suites whose generation has
  drifted independently of this edit; act_grade 21/0 + classifier 80/0 green
  against the edited harness), shellcheck rule-histogram parity, sha256s.
- harness-diff.txt — the exact harness change.
- AFTER-proof.txt — post-fix surface proof (porcelain clean, release
  clean-tree precheck "ok" at the committed tips).

The three accumulated residue dirs (qa-20261122T202851Z, qa-20261123T144739Z,
qa-20261124T210609Z; 464K) were MOVED to the durable root
`~/.hermes/qa/evidence/lore/` (same tick sub-names, contents untouched) so the
evidence any earlier closeout cited stays on reusable disk, and the legacy
directory was removed from the checkout.
