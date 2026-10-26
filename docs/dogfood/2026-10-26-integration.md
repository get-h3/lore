# Dogfood integration report — 2026-10-26

Tick: `lore-dogfood-2026-10-26-12-43-59`
Product HEAD: `d015baaef21d04c46f4dbca0598b965c26e6b8f2`

## Promise

A fleet operator can install `lore`, paste a failure symptom, retrieve the matching runbook and its ordered checks, and audit recent incident coverage honestly. A post-incident scribe can produce a proposal-only absorb update. The documented fresh-machine path is `git clone`, install `uv`, `uv sync --extra dev`, then run the CLI.

## Evidence boundary

The canonical checkout was `/home/kara/get-h3/lore`, branch `main`, HEAD `d015baaef21d04c46f4dbca0598b965c26e6b8f2`, equal to `origin/main` at the start of the run. The checkout had only pre-existing untracked `.gitreins/history/` runtime artifacts; no product source or board state was changed. Local CLI probes used the existing `.venv` and scratch directories. The bunker battery recorded the same QA HEAD.

## Real-use results

The README's working examples continued to work. `lore match "drain 503"` returned `gateway-drain-window` with confidence 0.90. `lore match "spawn 503"`, the exact PRD US-1 example, returned `unclassified confidence=0.00`; the same failure text through `lore consult --failure "spawn 503 while restarting"` returned the gateway-drain-window runbook and seven checks. This is a fresh re-proof of the existing LORE-070 documentation finding, not a new classifier row.

The absorb exit contract is now honest at this HEAD: `absorb --class nope-class --lesson x` returned the JSON error and rc=2; a valid `absorb --class gateway-drain-window --lesson x` returned rc=0 with an explicit proposal-only empty update. No write occurred.

The audit JSON surface returned an object with `classes` and `summary`. From the repository root it reported `incident_count=218`, `uncovered_classes=[]`, and no `incident_seen` classes in the current event window. Scratch controls behaved distinctly: a current structured event for `postgres-deadlock-storm` produced `incident_count=1` and `uncovered_classes=[postgres-deadlock-storm]`; a current known-class event produced `incident_seen=[gateway-drain-window]`; an old prose-only task mentioning a class produced no incident class. The incident data path and window behavior held on the tested controls. Consumers must read `.classes` and `.summary`, not assume a top-level array.

Time-to-first-success was under one second on the warm local checkout: the first working match completed in approximately 62 ms in the captured run.

## Performance measurement

The measured headline operations were CLI invocations from the checkout, with the same `.venv`, command, and input scale:

- Warm `hyperfine --warmup 3 --runs 12 '.venv/bin/lore match "drain 503"'`: mean 101.2 ms ± 24.5 ms, range 83.2–173.3 ms.
- Warm `hyperfine --warmup 3 --runs 12 '.venv/bin/lore audit --format json'`: mean 119.8 ms ± 35.6 ms, range 90.3–213.5 ms.
- Cold-process `/usr/bin/time -p .venv/bin/lore match 'drain 503'`: 0.05–0.07 s real across three fresh processes.

These are below a user-noticeable wait for this CLI workload. No new PERF row was filed. The existing PERF-3 task remains pending and was not re-filed or re-measured with a new candidate. Captured local outputs are in `/tmp/lore-dogfood-20261026-local/`; no flamegraph was justified by these numbers.

## Fresh-machine install leg

The required `bunker-qa.sh` leg ran on reachable `bunker-mvp`, agent `de18c55d`, against the recorded QA HEAD, and the agent was destroyed. The post-collect inventory showed the agent absent. `bunker2` was also reachable with active `bunkerd`; `bunker3` and `bunker4` were unreachable, but no fallback was needed.

The collected cells were not a clean install PASS. `fresh-install` was FAIL because the harness reported `install rc=0 but no artifact found (toolsd not in PATH, PREFIX/bin/toolsd missing, or zero-size)` even though its detail also records `get-h3-lore-0.1.2` and dependencies installed. This is detector/harness evidence, not a proven lore install failure. The same battery recorded `upgrade` OK, `ci-pass` OK with one green job, 562 tests surviving the network-cut cell, resource-cap PASS, and clean missing-config rc=2. Because the intended fresh-install artifact/smoke proof was not gradeable, installability at this HEAD remains UNPROVEN; it is not reported as a silent pass. No board row was written from the harness-shaped failure because the target board is read-only for this lane and the evidence does not prove a product defect.

## Value judgment

Verdict: PROMISING-BUT-ROUGH. The core CLI is useful and fast enough, the structured audit controls are now materially more trustworthy, and the unknown-class exit-code fix works. Usability remains rough because the PRD's own responder example still returns an unclassified result, and the fresh-machine battery's artifact detector cannot grade the installed lore artifact. The existing LORE-070 row owns the responder-example defect; the install evidence is ready for the owning QA/harness lane to classify and file if it is not already covered.

## Artifacts and limitations

This report and the canonical dogfood log entry are the write-back artifacts from this read-only dogfood lane. The diagnostics trail already contains the tick addendum and was not rewritten. No code, board row, board event, scheduler state, visibility, permission, or credential was modified. The usage skill already contains the current audit and responder guidance, so it was not duplicated.

ch:trace row=none:read-only-dogfood spec=docs/PRD.md#US-1+US-3 test=/tmp/lore-dogfood-20261026-probe.py doc=docs/dogfood/2026-10-26-integration.md evidence=/tmp/lore-dogfood-20261026-local+/tmp/lore-dogfood-20261026-1243-evidence.jsonl witness=lore-dogfood-2026-10-26-12-43-59 verdict=PROMISING-BUT-ROUGH:LORE-070-reproof+fresh-install-unproven commit=a35ebe2 memory=none:not-written
