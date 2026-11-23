# Dependency drift user timer

These are host-specific examples. After the script has landed in the main checkout,
copy all unit files (`lore-dep-drift.service`, `lore-dep-drift.timer`,
`lore-dep-drift-failure.service`) and `dep-drift-failure-notice.sh` into
`~/.config/systemd/user/`, adjusting their absolute paths for the box, and create
`~/.local/share/lore/` for the logs. The main checkout needs its existing
`.venv` with `packaging` installed. Then run `systemctl --user daemon-reload`
and `systemctl --user enable --now lore-dep-drift.timer`.

The timer reports behind-PyPI pins; it never updates the lock or environment.
Lookup failures are reported as incomplete. `scripts/audit-deps.sh` separately
scans for known vulnerabilities. The 07:45 start is staggered 15 minutes after
validation; it does not guarantee that a long validation run has finished.

## Heartbeat and failure notice

Every real run of `scripts/dep-drift.sh` — successful, no-op (nothing behind
PyPI), or degraded (venv/lock/PyPI problems) — ends with a dated
`heartbeat: <ISO-8601 timestamp> dep-drift.sh ran (rc=<n>)` line on stdout,
which the unit's `StandardOutput=append:...` appends to
`~/.local/share/lore/dep-drift.log`. A no-op run therefore still refreshes the
log's mtime. Start-level service failures (missing exec, user-manager trouble)
also append a dated `failure-notice:` line to
`~/.local/share/lore/dep-drift-failures.log` via
`OnFailure=lore-dep-drift-failure.service`; the unit shape does not forbid
OnFailure, but note the report script exits 0 even when degraded, so the
heartbeat in the report log — not OnFailure — is the primary liveness signal.
Usage-only invocations (`--help`, unknown argument) emit no heartbeat.

## Run-18 caveat: timer state can say triggered while the service never ran

On Monday 2026-11-23 `systemctl --user show lore-dep-drift.timer` reported
`LastTriggerUSec=Mon 2026-11-23 07:56:59 -05` with `Result=success`, while
`journalctl --user -u lore-dep-drift.service` had zero entries for any date and
neither report log had been touched that day. Corroborating host context: an
earlyoom SIGKILL storm at 07:47:08, journald missing 226 messages, and two user
manager restarts ~08:22 stopping+starting both lore timers. Full evidence:
`docs/qa/evidence/run18/INDEX.md` ("Timer-miss evidence (LORE-20261012)"
section). Do not treat `LastTriggerUSec`/`Result` as proof the report ran —
verify the artifacts below after every scheduled run.

## Post-scheduled-run verification (each Monday after ~08:00, or after any timer/user-manager restart)

For each armed lore timer, check the report log's mtime and the dated lines:

```
stat -c '%y %n' ~/.local/share/lore/dep-drift.log ~/.local/share/lore/weekly-validate.log
tail -n 2 ~/.local/share/lore/dep-drift.log
grep -c "heartbeat: $(date +%Y-%m-%d)" ~/.local/share/lore/dep-drift.log
cat ~/.local/share/lore/dep-drift-failures.log
```

Expected post-Monday values:

- `dep-drift.log`: mtime ~ Monday 07:45 with a `heartbeat:` line dated today
  (the `grep -c` above must be at least 1), followed by the behind-count.
- `weekly-validate.log`: mtime ~ Monday 07:30. The weekly-validate unit
  (`~/.config/systemd/user/lore-validate.service`) is host-local and NOT part
  of this repo — do not modify its unit; the mtime check is its verification:
  after the Monday window the mtime above must be no older than the last
  schedule day, and `lore validate` output should be appended as the log's
  final content.
- `dep-drift-failures.log`: absent or unchanged (a new line means a start-level
  failure; check `journalctl --user -u lore-dep-drift.service`).

If `stat` shows the log is older than the last schedule day — or the timer
reports `LastTriggerUSec` on schedule day with no heartbeat line and an empty
journal — the run was silently missed despite timer state. Re-run
`scripts/dep-drift.sh` manually (rc 0) and investigate the window (the
2026-11-23 class: OOM storm + user-manager restarts).

Run the drift-specific regression with `uv run pytest -q scripts/dep_drift_test.py`;
it is outside the default `tests/` collection.
