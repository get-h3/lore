# QA-LORE-FOREMAN-1 — battery-r2: real bunker-mvp battery run (worker R2, attempt 2)

Row: `QA-LORE-FOREMAN-1` (P1, source `qa-dagger`). Wave:
`.coding-hermes/waves/lore-foreman-2026-11-03-20-34-57.json` (serial worker,
base `3f4be19a164177bc80a2f6e7488af646420826bb`).

This artifact SUPERSEDES the staged partial record `battery-r2-summary.md` /
`battery-r2.jsonl` in this directory, which documents attempt 1 only.

## Binding

- Tested HEAD: `3f4be19a164177bc80a2f6e7488af646420826bb` — the HEAD of
  `/home/kara/get-h3/lore` at run time and the worktree base (identical).
- Runner: `/home/kara/.hermes/scripts/bunker-qa.sh`, synchronous `run` mode.
- Resolve probe: `bunker-qa.sh resolve /home/kara/get-h3/lore` →
  `/home/kara/get-h3/lore` (exact product root, rc=0).
- Server: `bunker-mvp` (Hetzner CI/QA host 78.46.173.180). Temp agent
  `b0b931fb` (created 21:06:45 UTC, TTL 4h). Teardown `TEARDOWN-GONE`; no
  `--keep`.

## Launch gate — live host state

- `ssh bunker-mvp 'df -P /'` at worker start (20:47 UTC): `/dev/sda1
  157166028 116453044 34263492 78% /` — below the 94% launch threshold.
  The owner-side reclaim continued during this worker's session (78% → 67% →
  60% → 57% observed 20:52–21:05 UTC; `/home/bunker-*` homes 28 → 12). Every
  host mutation in that window belongs to the operator/daemon destroy queue;
  this worker ran only the battery and destroyed nothing.
- Attempt 1 (20:52 UTC) FAILED at spawn, no product cells, no agent spawned:
  `bunker: spawn agent: unavailable: dial tcp 100.115.67.116:19090: connect:
  connection refused` (2 attempts, `RUNNER_EXIT=1`). Cause: `bunkerd.service`
  was restarting during the operator's destroy/reconcile queue (systemd stop
  20:53:33, SIGKILL mid-archive 20:55:04, restart 20:55:04). The staged
  `battery-r2.jsonl` lifecycle row records this attempt.
- Attempt 2 gated on the daemon listener (ss check every 60s, bounded 45
  checks): `PORT_19090_UP after check 13 (2026-11-03T21:06:25Z)`; `bunker
  list` then served the real registry. Battery launched immediately.

## Battery (attempt 2)

- 21:06:45 → 21:09:08 UTC, `CELLS-DONE`, teardown `TEARDOWN-GONE`.
- Raw evidence: `bunker-qa-lore-r2.jsonl` (22 rows, byte-complete copy of the
  runner's evidence file).
- Per-row parse/classification: `bunker-qa-lore-r2-cells.json` (22/22 rows
  parsed, 0 errors; 14 product cells, 8 harness rows, 0 wrapper rows).
- Runner session log: `bunker-qa-lore-r2-runner-log.txt`.

## Cell results — 14 product cells

| cell | runner status | grade | note |
|---|---|---|---|
| fresh-install | OK | PASS | pip install -e .[dev] on a clean machine (get-h3-lore 0.2.0 + deps) |
| lint | OK | PASS | ruff check . (rc=0) |
| tests | OK | PASS | test suite rc=0 on the clean machine |
| ci-pass | OK | PASS | act: 1 jobs green, act_result=pass rc=0 (1 triggerable workflow) |
| upgrade | FAIL | FAIL | see below — genuine finding, kept FAIL |
| docker_build | N/A | N/A | no Dockerfile trigger |
| compose_config | N/A | N/A | no compose file trigger |
| docker-deploy | N/A | N/A | no compose file |
| ui-probe | N/A | N/A | no web UI detected |
| chaos-disconnect | INFO | INFO | "passes with network cut (no network dep)" — recorded INFO, not upgraded |
| chaos-shutdown | N/A | N/A | no compose file |
| chaos-corruption | N/A | N/A | no db/state files in repo |
| chaos-resource | PASS | PASS | suite survives 3G memory cap (cap enforced, child verified) |
| chaos-errorpath | OK | PASS | clean error on missing config (rc=2) |

Product totals: 6 PASS, 1 FAIL, 1 INFO, 6 N/A, 0 UNVERIFIED. Harness rows:
8 × `toolchain-bootstrap` OK (venv+pytest, gcc/g++ wrappers, make, compose
plugin, buildx, node+npm v22.15.0) — environment provisioning, not product
assertions.

## The one FAIL: upgrade

`previous release get-h3-lore==0.1.0 would not install (tag v0.1.0): rc=1
cmd=[pip install get-h3-lore==0.1.0] — ERROR: Could not find a version that
satisfies the requirement get-h3-lore==0.1.0 (from versions: none)`.
lore has never published to PyPI, so pip cannot resolve the previous release
from anywhere. The recorded FAIL is preserved as FAIL (not downgraded to N/A):
either lore should publish releases (making the upgrade cell meaningful) or the
runner's upgrade cell should consume the shipped previous-tag tree for
unpublished projects. Open finding for the foreman/owner; evidence only — not
fixed in this row.

## Runner summary-layer discrepancy (harness defect, not a product result)

`qa_run_summary` printed `Passed: 0 | Audited: 0 — NOTHING AUDITED` and `run`
exited rc=3 despite 14 verdict-bearing product rows. Cause:
`bunker-qa.sh` parses rows with a sed pattern requiring compact JSON
(`"cell":"name"`, no space after the colon) while the agent-side cell writer
emits `python3 json.dumps` rows with spaced separators (`"cell": "name"`), so
the summary regex matches zero rows. The 22 rows in the raw JSONL are the
audit signal; the rc=3 verdict is a false negative at the summary layer.
Flagged here for the bunker lane; no runner code was modified in this task.

## Provenance notes

- Shared scratch dir `/home/kara/.hermes/cache/scratch/lore-foreman-2026-11-03-20-34-57`
  also holds: the agent spawn bundle for b0b931fb (contains a live API key —
  deliberately NOT committed), a prepared partial closeout message
  (`qa-r2-commit.txt`) staged by the foreman-side monitor at 21:09–21:10 UTC
  while attempt 2 was already finished (its view lagged ~17 min), and unrelated
  files from other lanes. None of these are referenced by this artifact beyond
  this note.
- Attempt-1's evidence file was truncated and rewritten by attempt 2 in the
  same path (`bunker-qa-lore-r2.jsonl`); the lifecycle FAIL row for attempt 1
  survives only in the staged `battery-r2.jsonl`.

ch:trace row=QA-LORE-FOREMAN-1 spec=docs/qa/evidence/run-QA-LORE-FOREMAN-1/README.md#4 wave=.coding-hermes/waves/lore-foreman-2026-11-03-20-34-57.json#QA-LORE-FOREMAN-1 test=none:detached-bunker-battery doc=docs/qa/evidence/run-QA-LORE-FOREMAN-1 evidence=docs/qa/evidence/run-QA-LORE-FOREMAN-1/bunker-qa-lore-r2.jsonl witness=live:bunker-mvp:df verdict=none:pending-foreman-judge commit=none:worker-commit memory=none:foreman-closeout

STATUS: complete
TIER: T3
EVIDENCE: docs/qa/evidence/run-QA-LORE-FOREMAN-1/bunker-qa-lore-r2.jsonl
