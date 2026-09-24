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

### Check 4 (read-only)

```sh
grep -c 'enabled.*false' <scheduler-fleet-config>
```
- Healthy: the projects about to be affected are already disabled (writes paused)
- Incident: 0 — writes were NOT paused before the restart (config-driven writes 503 during restart)
- Decision: pause writes FIRST: flip scheduler enabled=false / pause lanes before touching the gateway; enqueue-not-drop keeps queued work alive
- Evidence: incident: 2026-08-27T09:45Z post-mortem: config writes during a gateway restart 503'd; work that was enqueued instead of dropped survived the restart

### Check 5 (read-only)

```sh
curl -s <gateway-metrics-url> | grep -c 'in_flight'
```
- Healthy: in-flight counter present and steady
- Incident: in-flight counter draining slowly (up to ~30 min) — a restart issued now 503s the remainder
- Decision: gate the restart on the in-flight counter reaching 0: announce the drain window, never hard-kill (SIGKILL) with requests still in flight
- Evidence: logsey-export: 2026-08-14T02:07:41Z hermes-gateway: SIGKILL received during load; 214 in-flight requests terminated with 503
- Evidence: incident: 2026-09-16T19:05Z post-mortem: across incidents 3-4 the drain window was observed at 25-30 min; dependents were not warned in advance during incidents 1-3

### Check 6 (read-only)

```sh
wc -l <gateway-queue-path>
```
- Healthy: queue empty or at its steady-state depth
- Incident: queue_depth > 0 with unflushed rows — restarting now loses the queued state
- Decision: never restart with queued unflushed state: check queue depth FIRST and drain or flush before the restart
- Evidence: logsey-export: 2026-09-05T14:02:55Z hermes-gateway: restart executed with queue_depth=14 unflushed rows; queued state lost on restart

### Check 7 (read-only)

```sh
logsey query --pattern 'SIGKILL|503' --since 60m
```
- Healthy: no SIGKILL lines; 503 count at baseline (0/hour)
- Incident: SIGKILL during load, or 503 count above the pre/post-restart baseline
- Decision: verify with read-only probes only: keep before/after error-rate deltas as evidence; reload gracefully (never SIGKILL) and re-check /health
- Evidence: logsey-export: 2026-09-16T18:35:02Z hermes-gateway: fourth gateway-restart incident: 96 503s inside the incident window; baseline outside the window measured 0 per hour
- Evidence: incident: 2026-09-12T22:00Z post-mortem: the graceful reload produced no hard-kill lines in the gateway log; the 503 spikes traced to hard kills in incidents 1-3

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

- board: LORE-003 seed class 'gateway drain window'
- incident: PRD §The problem, measured case 1 (four incidents + compaction-boundary loss)
- memory: curated note 'drain 503s kill ticks'
