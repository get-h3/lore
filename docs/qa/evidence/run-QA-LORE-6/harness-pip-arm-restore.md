# QA-LORE-6 — QA harness pip previous-tag tree arm restored (qa-up-prev-pip)

Tick: lore-foreman-2026-11-23-04-28-28 · Wave worker: glm-5.3-flash @ ollama-cloud (session local-e238e78d, workdir /home/kara/get-h3/lore)

## Defect (red-proof from the lore-qa ledger)

Fire lore-qa-2026-11-22-20-12-17, cell upgrade, FAIL:
`pip install get-h3-lore==0.2.0` → "No matching distribution found for get-h3-lore==0.2.0"
while the repo carries tag v0.2.0 and lore publishes nothing to PyPI. The registry
install is a harness premise failure graded as a product verdict — the harness's pip
tree-upgrade arm (qa-up-prev-pip) was lost. Recurring: v0.1.0 on 11-03, v0.2.0 on
11-22; same fleet defect as QA-TERMINAL-JAIL-19-R2.

Harness provenance: the arm is present (4 hits) in
`~/.hermes/scripts/bunker-qa.sh.bak-QA-BUNKER-REVIEW-3-20261102` and in every backup
through 2026-11-02; every backup from 2026-11-05 onward has 0 hits. Live file before
this fix: md5 f5c64b53b847d29d6ed661d2d2c733b5, 393960 bytes, grep -c qa-up-prev-pip = 0,
DETECT_UP_PREV_DIR only ever set to ~/qa-up-prev-npm.

## Fix (verbatim restore, insert-only)

Restored the three hunks byte-for-byte from .bak-QA-BUNKER-REVIEW-3-20261102:

1. detect_upgrade_inputs pip branch (live lines 1642-1654): PyPI probe
   (curl https://pypi.org/pypi/$PKG_NAME/json) → DETECT_UP_PREV_DIR="~/qa-up-prev-pip"
   when the package is absent from PyPI.
2. ship_prev_tag_tree pip elif (live lines 1719-1723): stale-tree cleanup
   (rm -rf ~/qa-up-prev-pip ~/qa-up-prev-pip.absent), stream previous tag tree,
   verify pyproject.toml.
3. Generated remote script UP_PREV resolution (live lines 3852-3856): pip elif
   consuming $HOME/qa-up-prev-pip/pyproject.toml into UP_PREV.

Pre-edit snapshot: ~/.hermes/scripts/bunker-qa.sh.bak-QA-LORE-6-20261123.
Post-restore md5 (as recorded after this fix, before the separate QA-LORE-8 edit):
07e4adfd9df4041965b153e9c7c81e34.

## Verification (foreman-run, all observed live)

- diff vs pre-edit snapshot: 24 inserted lines, 0 deleted lines, 0 modified lines.
- ALL-24-VERBATIM-FROM-BACKUP: every inserted line exists verbatim in
  .bak-QA-BUNKER-REVIEW-3-20261102.
- npm/rust/go arms untouched: qa-up-prev-npm and qa-up-prev/ counts identical
  before/after.
- bash -n on the live harness: exit 0.
- Functional probe of hunk 1 (detect_upgrade_inputs extracted from the live file and
  run against this repo): ECOSYSTEM=pip, PKG_NAME=get-h3-lore, PREV_TAG=v0.2.0,
  UP_PREV_DIR=~/qa-up-prev-pip.
- Ground truth: PyPI pypi.org/pypi/get-h3-lore/json → HTTP 404 (not published), so
  the PyPI-probe condition is the live path for lore.
- Functional probe of hunk 3 (the harness's own generator):
  `bunker-qa.sh __gen-remote /home/kara/get-h3/lore` → rc=0, generated script carries
  the pip arm at generated lines 1952-1956
  (`if [ -f "$HOME/qa-up-prev-pip/pyproject.toml" ]; then UP_PREV=...`).

## Honest limits

- Hunk 2 (ship_prev_tag_tree execution) streams over SSH at battery launch; it is
  restored verbatim from the backup that originally passed QA-TERMINAL-JAIL-19
  batteries but was NOT exercised live this tick. The next lore-qa clean-machine
  battery re-grades the upgrade cell end-to-end; until then this row's claim is
  generation-level (detect + generated script), not a live agent battery.
- "Fixed in harness" claims are only true for the md5 that was tested
  (fleet harness_notes convention). The QA-LORE-8 tick edits the same file
  immediately after; its own evidence records its own before/after md5s.

## Worker note

The worker's CLI client hit a gateway disconnect after the work was done ("turn
outcome is unknown"); the server-side session completed the remaining hunks. The
foreman verified every artifact above directly against the live file — no worker
self-report is relied on.
