# Runbook: Gateway drain window (`gateway-drain-window`)

- **Status:** proposal
- **Last validated:** no data (never validated)
- **Provenance:** Compiled by lore.compiler from the curated class registry (lore.classes) and the fleet's incident history. Operator approval required to publish (propose-not-write).
- **Signature:** `drain\s+503`

## Checks (in order)

### Check 1 (read-only)

```sh
logsey query --pattern 'drain 503' --since 30m
```
- Healthy: no rows
- Incident: 503s on in-flight requests while the gateway restarts/reloads
- Decision: confirm the class signature before touching anything
- Evidence: incident: PRD §The problem, measured case 1

### Check 2 (read-only)

```sh
grep -c 'drain 503' <gateway-log-path>
```
- Healthy: 0
- Incident: non-zero and rising over the drain window (up to ~30 min)
- Decision: distinguish a drain window (bounded, expected) from a wedged gateway
- Evidence: incident: four gateway-restart incidents pre-doctrine
- Evidence: memory: curated note: drain 503s kill ticks

### Check 3 (read-only)

```sh
curl -s -o /dev/null -w '%{http_code}' <gateway-health-url>
```
- Healthy: 200
- Incident: 503 during drain; 200 again once in-flight requests finish
- Decision: pause-first decision: hold config rollout until health returns 200
- Evidence: incident: gateway restart doctrine: pause-first under load

## Recovery ladder

1. Stop config changes: batch them instead of trickling under load.
2. Pause-first under load: hold the rollout until in-flight requests finish.
3. Announce the expected drain window (up to ~30 min) to dependents before restarting.
4. Watch drain-503 volume fall to zero, then confirm health endpoint 200 before resuming.

## Guardrails (never X)

- Never restart the gateway with in-flight requests still draining from the previous restart.
- Never treat drain 503s as a gateway fault — during a drain window they are EXPECTED; distinguish bounded drain from wedged before acting.
- Never trickle config changes under load — batch them and pause-first.

## Evidence trail

- memory: drain 503s kill ticks
- incident: 2026-08-14T02:15Z post-mortem note: hard kill under load left no drain window; all 214 in-flight requests 503'd
- incident: 2026-08-27T09:45Z post-mortem note: config writes during a gateway restart 503'd; work that was enqueued instead of dropped survived the restart
- incident: 2026-09-05T14:20Z post-mortem note: restart with queue_depth=14 unflushed lost the queued state; queue depth was checked only after the loss
- incident: 2026-09-12T22:00Z post-mortem note: the graceful reload produced no hard-kill lines in the gateway log; the 503 spikes traced to hard kills in incidents 1-3
- incident: 2026-09-16T19:05Z post-mortem note: across incidents 3-4 the drain window was observed at 25-30 min; dependents were not warned in advance during incidents 1-3
- board-event: 2026-09-16T18:40Z doctrine thread opened after the fourth gateway-restart incident
- board-event: 2026-09-16T18:55Z note: the draft doctrine summary from the third incident was lost at a session compaction boundary; only the memory line survived
- duckbrain-row: 2026-09-16 gateway/restart-policy: restarts under load 503 in-flight scheduler spawns
- duckbrain-row: 2026-09-16 gateway/drain-window: observed drain window 25-30 min across incidents 3-4
- board: LORE-003 seed class 'gateway drain window'
- logsey-export: SIGKILL received during load; 214 in-flight requests terminated with 503
- logsey-export: tick spawn failed: upstream returned 503 (gateway restarting)
- logsey-export: config rollout applied while gateway restarting; config-driven writes failed with 503
- logsey-export: new work kept being enqueued during the restart; queue drained after recovery, nothing dropped
- logsey-export: restart executed with queue_depth=14 unflushed rows; queued state lost on restart
- logsey-export: graceful reload started; in-flight counter 214 -> 0 over ~28 min; 503s bounded to the drain window
- logsey-export: post-reload health endpoint returned 200; 503 error rate back to pre-restart baseline
- logsey-export: fourth gateway-restart incident: 96 503s inside the incident window; baseline outside the window measured 0 per hour
