# Dogfood integration report — 2026-10-26

Tick: `lore-dogfood-2026-10-26-12-43-59`
Product HEAD: `d015baaef21d04c46f4dbca0598b965c26e6b8f2`

## Promise and real use

lore promises a runbook lookup from a symptom, ordered validation checks, proposal-only absorb output, and an audit matrix. A detached HEAD worktree ran the documented CLI surface with isolated HOME/state:

- `uv sync --extra dev`: rc 0.
- README match examples reproduced: `drain 503` -> `gateway-drain-window` at confidence 0.90; `secret .env clobber` -> `secret-env-clobber` at 0.90; the coffee-machine example -> explicit `unclassified` at 0.00; `gateway drain 503` -> `gateway-drain-window` at 0.90.
- `compile --class gateway-drain-window --format json`: rc 0, structured runbook proposal.
- `validate --class gateway-drain-window`: rc 0, plan-only output that names commands without executing them.
- `absorb --window 2h --trail-file <two-line trail> --source dogfood-dagger`: rc 0, one gateway proposal with two observed evidence blocks; proposal-only output.
- `audit --format json`: rc 0, 14 classes and `summary.incident_count=218`; the actual JSON shape is an object containing `classes` and `summary`.
- Unknown `absorb --class does-not-exist --lesson x`: rc 2 with `unknown class`, matching the current implementation.

The existing LORE-070 issue was re-proven as a current surface concern: `consult --failure "spawn 503 while restarting" --json` returned rc 0 but `class_id: null` and zero checks in this detached HEAD, while the committed usage skill and diagnostics claim that form returns `gateway-drain-window` with seven checks. No new board row was created because this is the same finding family; the foreman should compare the current behavior with LORE-070's committed evidence before deciding whether it is a regression or environment/data discrepancy.

## Performance

Command: `hyperfine --warmup 3 --runs 12 'env HOME=/tmp/lore-dogfood-20261026-124359/home2 .venv/bin/python -m lore match "drain 503"'`.

Warm: 61.6 ms ± 13.9 ms, range 51.0–101.2 ms. Cold isolated-HOME process: 0.04 s real, 0.04 s user, 0.00 s sys. `audit --format json` was 0.08 s one-shot on the current ledger. Nothing was slow enough to be user-noticeable; no PERF row or profile was warranted.

## Install leg

`bunker-qa.sh launch /home/kara/get-h3/lore` tested QA-HEAD `d015baa` on `bunker-mvp`, but spawn failed before a usable agent existed because the remote root and `/tmp` were 100% full: `mktemp: failed to create directory via template '/tmp/tmp.XXXXXXXXXX': No space left on device`. `bunkerd` was active. `bunker3` and `bunker4` were unreachable; `bunker2` had SSH/bunkerd but was not registered in the bunker CLI config. The failed launch's agent `9587d8b1` was destroyed and the follow-up list showed three remaining agents, not that id. Installability remains unproven and is recorded as explicit `SKIPPED-install-bunker` evidence in the run record; no visibility, permissions, credentials, or board state were changed.

## Verification

`uv run pytest -q`: 562 passed in 4.23 s.

The run record is parked in DuckBrain under namespace `lore`, key `/dogfood/2026-10-26-lore-dogfood-lane`, and was read back with the distinctive tick, verdict, and install-skip phrases. Scratch evidence was under `/tmp/lore-dogfood-20261026-124359/` and the detached worktree was removed.

ch:trace row=none:read-only-dogfood spec=docs/dogfood/2026-10-26-integration.md#promise test=562-passed-in-4.23s doc=skills/lore-usage/SKILL.md evidence=/tmp/lore-dogfood-20261026-124359 witness=lore-dogfood-2026-10-26-12-43-59 verdict=PROMISING-BUT-ROUGH:install-unproven-and-LORE-070-reproof commit=pending memory=/dogfood/2026-10-26-lore-dogfood-lane
