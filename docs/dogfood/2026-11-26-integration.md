# Lore dogfood: 2026-11-26

Tick: lore-dogfood-2026-11-26-14-57-21
Tested tree: fda946c302814b77c5c58d21fc79593ba06f767c

## Promise and verdict

A responder can match an incident symptom, obtain a proposal containing checks and recovery steps, and plan a safe validation. Local workflow works and the fresh-machine install cell passed. Verdict: PROMISING-BUT-ROUGH; fresh-machine end-to-end first use was not independently timed.

## Actual use and diagnostics

From the existing checkout, `uv run python -m lore match 'drain 503'` returned gateway-drain-window, confidence 0.90. `uv run python -m lore compile --class gateway-drain-window --format json` returned a JSON array containing one proposal with seven checks and four recovery steps. The markdown form produced a runbook. `uv run python -m lore validate --class gateway-drain-window --format json` returned plan mode, seven planned checks, zero refused, and explicitly stated nothing was executed. No recovery command was run. `uv run python -m lore audit --format json` reported 320 incidents and 14 registry classes; this pass did not independently validate the incident count or coverage completeness. An unknown class was refused with exit 2. An unrelated coffee-machine symptom was explicitly unclassified.

`match 'spawn 503'` remained unclassified, whereas `consult --failure 'spawn 503 while restarting'` returned the gateway runbook. PRD US-1 explicitly documents this distinction; the existing completed LORE-070 addressed its misleading example, so no recurrence is asserted. An attempted `consult --format json` was rejected: that flag is not offered by consult; this was an operator error, not a filed defect. Compile JSON is an array, not an object.

## Performance

Using `/usr/bin/time` on the documented `uv run` invocation: the first observed match took 0.32 s and the next 0.09 s. These are first-observed and warm process timings, not a controlled OS-cache cold benchmark. Compile took 0.08 s on each of two consecutive processes. Nothing measured was slow enough for a user to notice; no performance finding was filed.

## Installation and open follow-up

The fresh-machine leg ran via `bunker-qa.sh` on bunker-mvp agent b7ce8053. The collected fresh-install cell is OK: `pip install -e .[dev]` installed get-h3-lore 0.3.0 and the `lore` executable. Lint, tests, CI, upgrade and applicable chaos cells also passed; Docker lifecycle cells were safety-skipped. The agent log reported CELLS-DONE. Evidence: `/home/kara/.hermes/qa/evidence/lore/qa-20261126T151545Z` and `/home/kara/.hermes/cache/scratch/lore-dogfood-20261126-evidence.jsonl`. The destroy command timed out during archival, but a subsequent agent-specific info returned not_found and a fresh all-agent census omitted b7ce8053: removal was verified.

## Boundaries

No board task was filed, and no product code changed. DuckBrain recall failed because its MCP subprocess would not start, so prior memory and a durable ledger write could not be verified. No clean-install time-to-first-success is available; local operation used an existing environment. This was a bounded CLI workflow, not a complete usability or correctness audit.
