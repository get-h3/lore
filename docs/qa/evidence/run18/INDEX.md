# Run 18 evidence — lore-dogfood-2026-11-23-14-15-27 (HEAD 23f800b)

Provenance: controller-side binding. `head.txt` records `git rev-parse HEAD`
(23f800b0a47d48b19aed099e5168a8fd0d07be1e) and the working-tree dirty count at
launch time (1 line = the pre-existing untracked `.coding-hermes/evidence/`
harness residue, row LORE-HYGIENE-20261122 — no tracked file dirty).

| file | what it is |
|---|---|
| quickstart.txt | documented match ×2 + first (buggy) consult probe; match outputs byte-exact vs README |
| consult1.out | corrected positional-title consult: runbook + 7 checks + local lint history ts |
| gate-default.out/.err | first gate run, default textfile dir: ALLOW rc 0, source line, empty stderr |
| h3-lore-prom-after.txt | /var/lib/node_exporter/textfile/h3_lore.prom after ALLOW+DENY arms: runs_total 7, last_success 0 |
| gate-deny.out/.err | DENY arm: registry-closed message, rc 1 |
| trigger.out/.err | FIRST trigger consumer attempt: arm-A 117 blocks→4 proposals, arm-B 0 replays, arm-C AttributeError `.parse()` (the LORE-20261013 evidence) |
| trigger-rerun.out/.err | the E402-fixed consumer re-run: arm-A 0 blocks because the first run's cursor already consumed the suffix (restart semantics, expected), arm-B 0, arm-C AttributeError reproduced — the committed `trigger_consumer.py` is the lint-fixed revision of the one that first ran (import moved above the fold; behavior identical; disclosure per salvage discipline) |
| trigger_consumer.py / trigger_consumer2.py | the staged consumer scripts (rev 1 hit the docs gap; rev 2 uses the real `.read()` and prints proposal shapes) |
| depdrift.out/.err | manual dep-drift.sh run: 4 of 34 behind, get-h3-lore 0.3.0 stamp, 1.45 s wall |
| hf-match.json | hyperfine n=20 ×2 arms: documented uv path 102.3±12.3 ms, raw venv 98.6±14.0 ms (loadavg 16.4/16 cores) |
| hf-gate.json | hyperfine n=15 gate+export 54.7±5.6 ms; counter ended exactly 17 (2 warmup + 15) — no lost increments |
| cold.txt | 3 one-shot cold match runs: 0.05/0.07/0.06 s, rc 0 ×3 |
| bunker-evidence.jsonl | fresh-box battery ledger, 24 rows: fresh-install/lint/tests/upgrade/ci-pass OK, chaos-resource PASS, chaos-corruption/errorpath OK, disconnect INFO, docker-deploy/chaos-shutdown SKIPPED (live-host safety gate), compose/ui N/A. Agent 955837c0 @ bunker-mvp, launched + collected, DESTROYED (list re-check: 0 hits) |

Not committed: the controller-side qa-evidence dir
(`~/.hermes/qa/evidence/lore-run18-20261123T144500/`) and the harness residue
`.coding-hermes/evidence/qa-20261123T144739Z/` (tracked by LORE-HYGIENE-20261122).

## Timer-miss evidence (LORE-20261012), quoted from the live host

- `ls -l ~/.local/share/lore/` → `dep-drift.log` mtime **2026-11-20 22:52**,
  `weekly-validate.log` mtime **2026-11-16 07:30** (neither touched today).
- `systemctl --user show lore-dep-drift.timer` → `LastTriggerUSec=Mon
  2026-11-23 07:56:59 -05`, `Result=success`; both timers
  enabled/active-waiting, next trigger 2026-11-30.
- `journalctl --user -u lore-dep-drift.service` and `-u lore-validate.service`
  → `-- No entries --` (zero entries, any date).
- Corroborating host context, same window: `earlyoom` at 07:47:08 —
  `low memory! ... mem avail: 829 of 52941 MiB (1.57%), swap free: 3 of 32767
  MiB (0.01%)`, SIGKILLs to uid-1000 processes (`(hermes)`, `bunker`,
  `(gitlab-runner)`); `systemd-journald: Forwarding to syslog missed 226
  messages` at 08:04:18; user-manager restarts at 08:22:33 (pid 1772310) /
  08:22:40 (pid 1774786) stopping+starting both lore timers.
