# 2026-09-16 drain-window trail — LORE-011 acceptance input

Scope: ONLY observations that existed on/before 2026-09-16. This is the raw
trail the doctrine was later derived from: four gateway-restart incidents,
the one surviving curated memory line, board events, and DuckBrain rows.
Every line is an OBSERVATION as it was recorded at the time — no doctrine
statements, no derived rules. The doctrine itself is the scoring baseline,
not trail input.

Line kinds use the lore.evidence KINDS closed vocabulary. Raw gateway /
journald lines are inside the logsey export fence (they parse as
kind=logsey-export blocks via parse_logsey_export); every other line is
explicitly kind-labeled `- [kind] detail`.

## logsey export — raw lines around each incident

logsey export --window 2026-08-14T02:00Z..2026-09-16T19:10Z
```jsonl
{"ts":"2026-08-14T02:07:41Z","unit":"hermes-gateway","severity":"error","message":"SIGKILL received during load; 214 in-flight requests terminated with 503"}
{"ts":"2026-08-14T02:08:03Z","unit":"coding-hermes-scheduler","severity":"error","message":"tick spawn failed: upstream returned 503 (gateway restarting)"}
{"ts":"2026-08-27T09:31:12Z","unit":"hermes-gateway","severity":"error","message":"config rollout applied while gateway restarting; config-driven writes failed with 503"}
{"ts":"2026-08-27T09:31:40Z","unit":"coding-hermes-scheduler","severity":"info","message":"new work kept being enqueued during the restart; queue drained after recovery, nothing dropped"}
{"ts":"2026-09-05T14:02:55Z","unit":"hermes-gateway","severity":"error","message":"restart executed with queue_depth=14 unflushed rows; queued state lost on restart"}
{"ts":"2026-09-12T21:18:30Z","unit":"hermes-gateway","severity":"info","message":"graceful reload started; in-flight counter 214 -> 0 over ~28 min; 503s bounded to the drain window"}
{"ts":"2026-09-12T21:47:10Z","unit":"hermes-gateway","severity":"info","message":"post-reload health endpoint returned 200; 503 error rate back to pre-restart baseline"}
{"ts":"2026-09-16T18:35:02Z","unit":"hermes-gateway","severity":"error","message":"fourth gateway-restart incident: 96 503s inside the incident window; baseline outside the window measured 0 per hour"}
```

## Kind-labeled evidence blocks (non-log sources)

- [memory] drain 503s kill ticks
- [incident] 2026-08-14T02:15Z post-mortem note: hard kill under load left no drain window; all 214 in-flight requests 503'd
- [incident] 2026-08-27T09:45Z post-mortem note: config writes during a gateway restart 503'd; work that was enqueued instead of dropped survived the restart
- [incident] 2026-09-05T14:20Z post-mortem note: restart with queue_depth=14 unflushed lost the queued state; queue depth was checked only after the loss
- [incident] 2026-09-12T22:00Z post-mortem note: the graceful reload produced no hard-kill lines in the gateway log; the 503 spikes traced to hard kills in incidents 1-3
- [incident] 2026-09-16T19:05Z post-mortem note: across incidents 3-4 the drain window was observed at 25-30 min; dependents were not warned in advance during incidents 1-3
- [board] LORE-003 seed class 'gateway drain window'
- [board-event] 2026-09-16T18:40Z doctrine thread opened after the fourth gateway-restart incident
- [board-event] 2026-09-16T18:55Z note: the draft doctrine summary from the third incident was lost at a session compaction boundary; only the memory line survived
- [duckbrain-row] 2026-09-16 gateway/restart-policy: restarts under load 503 in-flight scheduler spawns
- [duckbrain-row] 2026-09-16 gateway/drain-window: observed drain window 25-30 min across incidents 3-4