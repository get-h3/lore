# Dogfood integration report — 2026-10-29

Tick: `lore-dogfood-2026-10-29-13-47-29`
Product HEAD: `a92b577af80326cd54a978fdfd2a34e7dd8e538e` (equal to `origin/main`)

## Verdict

PROMISING-BUT-ROUGH. The documented CLI workflow works on the current checkout and on a fresh bunker agent, with fast user-visible timings. The audit surface reports real incident coverage and novel uncovered classes. The remaining rough edge is the existing PRD responder example: `lore consult --failure` succeeds for the full failure text, while the documented `lore match "spawn 503"` form remains an unclassified near miss (existing LORE-070; no new row). The install leg is gradeable and passed its relevant cells; N/A cells are correctly inapplicable to this CLI-only project.

## Promise and real-use evidence

A fleet operator can install `lore`, paste a symptom, retrieve the matching runbook and ordered checks, audit incident coverage, and generate a proposal-only absorb update without writing doctrine.

Local workflow at the exact HEAD:

- `uv run lore match "drain 503"`: rc 0; `gateway-drain-window`, confidence 0.90, signature and keyword evidence.
- `uv run lore match "gateway drain 503" --explain`: rc 0; normal match plus `near-misses:` and `guard-degradation score=0.17`.
- `uv run lore consult --failure "spawn 503 while restarting"`: rc 0; gateway-drain-window proposal, seven ordered checks.
- `uv run lore show gateway-drain-window --format json`: rc 0; class id, proposal status, seven checks.
- `uv run lore compile --class gateway-drain-window --format json`: rc 0; JSON list with one item, seven checks, proposal status. The first probe's parser expected an object; that was invalid probe input and was corrected from the observed output shape.
- `uv run lore validate --class shared-checkout-collision`: rc 0; plan-only output lists three read-only commands and executes none.
- `uv run lore validate --class shared-checkout-collision --execute --format json`: rc 0; all three checks returned `ok`, with honesty label that this proves commands parse and answer, not recovery.
- `uv run lore audit --format json`: rc 0; 14 classes, 254 incident records, zero uncovered classes in the repository's current board state.
- A scratch audit with one known class and one novel `postgres-deadlock-storm` event returned `incident_count=2`, `uncovered_classes=[postgres-deadlock-storm]`, and `incident_seen=[gateway-drain-window]`; an empty-directory control returned 14 registry rows and no uncovered classes.
- A valid two-block `absorb --window 2h --trail-file ... --ns coding-hermes --source dogfood-dagger` returned two proposal objects: one classified gateway-drain-window and one explicit unclassified; rc 0 and no writes.
- Unknown-class `absorb --class nope --lesson x` returned the documented JSON error and rc 2. A valid single-class absorb returned an update proposal with `added/removed/changed` empty and rc 0.
- `lore gate --decision absorb --class gateway-drain-window` denied with rc 1 and `absorb requires a lesson`; `--decision no-new-lesson --reason ...` allowed with rc 0.

Independent gates: `uv run pytest -q` -> 566 passed in 5.38s; `uv run ruff check .` -> All checks passed.

## Performance

Measured the real CLI from the local `.venv`, same commands and input scale, release-equivalent installed package:

- Warm `hyperfine --warmup 3 --runs 12 --export-json ... -- '.venv/bin/lore match "drain 503"'`: mean 52.5 ms ± 5.6 ms, range 44.5–63.2 ms, rc 0.
- Warm `hyperfine --warmup 3 --runs 12 --export-json ... -- '.venv/bin/lore audit --format json'`: mean 74.7 ms ± 9.6 ms, range 64.9–102.1 ms, rc 0.
- Cold fresh-process match via `/usr/bin/time -p`: 0.04s, 0.04s, 0.05s real across three runs.

These timings are below a wait a user would notice for this CLI workload, so no PERF row or profile was justified. Raw timing files are in `/tmp/lore-dogfood-20261029-134729/`; the report records the exact measured command and scale.

## Fresh-machine install leg

`bunker-qa.sh launch /home/kara/get-h3/lore` and `collect --evidence /tmp/bunker-qa-evidence-20261029T135159Z-2571581.jsonl` ran on `bunker-mvp`, testing the exact HEAD. The agent was `400bc545`; collect pulled 21 evidence rows and destroyed it. Read-back after collect: `bunker info 400bc545` returned `not_found`; the server census had no `400bc545` and three unrelated agents remained.

Gradeable cells from the agent-owned evidence: repo-head OK; fresh-install OK (`get-h3-lore-0.2.0` installed, build-only install with no standalone artifact expected); ci-pass OK (one triggerable workflow green); upgrade OK (v0.1.0 tree to HEAD reinstall); chaos-disconnect OK with a network cut and a `DISCONNECT_SUITE_SUMMARY`; chaos-resource PASS under a 3G cap; chaos-errorpath OK with rc 2 for missing config. Docker deploy, shutdown, corruption, and UI probe were N/A because lore has no compose/state/UI surface. This is not a silent install pass: the battery had 21 agent rows, each was read, and the inapplicable cells are explicitly classified.

## Existing finding and scope

LORE-070 remains the owner of the PRD `match "spawn 503"` example mismatch; this tick re-proved it through both `match --explain` and `consult --failure` and filed no duplicate. The board is read-only to this lane; no IDs were minted and no board rows/events were changed. `boardctl validate` before the run was RESULT OK with 117 legacy warnings and zero errors.

## Artifacts

This report, the diagnostics addendum, the usage-skill addendum, and the canonical dogfood log are the permitted dogfood artifacts. No product source, board state, scheduler state, visibility, permission, or credential changed. Raw evidence: `/tmp/lore-dogfood-20261029-134729/`, bunker evidence `/tmp/bunker-qa-evidence-20261029T135159Z-2571581.jsonl`.

ch:trace row=LORE-070:reproof spec=docs/PRD.md#US-1 test=566-passed+ruff-clean doc=docs/dogfood/2026-10-29-integration.md evidence=/tmp/lore-dogfood-20261029-134729+/tmp/bunker-qa-evidence-20261029T135159Z-2571581.jsonl witness=live:CLI+fresh-bunker verdict=PROMISING-BUT-ROUGH:LORE-070-reproof commit=pending memory=not-written
