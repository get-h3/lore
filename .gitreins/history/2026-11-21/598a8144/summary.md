# Verdict: SUP-DEPS-LORE-20261121

**Task:** Scheduled lock-versus-PyPI drift sweep (report-only)
**Evaluated:** 2026-11-21T04:00:30.270646
**Result:** ✓ PASS

## Criteria

- ✓ **scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.**
  - Live run: `bash scripts/dep-drift.sh` queried PyPI and printed 'certifi 2026.10.23 -> 2026.11.20', 'platformdirs 4.14.7 -> 4.14.8', '2 of 34 locked packages behind PyPI latest', exit=0; uv.lock sha256 9b99cbec281d... identical before and after (report-only confirmed; script only reads the lock via tomllib, scripts/dep-drift.sh:36-39). Timer armed: `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 lore-dep-drift.timer -> lore-dep-drift.service'; is-enabled=enabled, is-active=active; unit files at deploy/systemd/lore-dep-drift.timer (OnCalendar=Mon *-*-* 07:45:00, Persistent=true) and .service (ExecStart=.../scripts/dep-drift.sh). Docs: README.md:439-447 and docs/INSTALL.md:454-463 describe the report-only arrangement and arming steps; deploy/systemd/README.md covers install. Gates: `uv run pytest -x --tb=short -q` -> '572 passed in 8.16s' (exit 0); tier1 lint and secrets guards passed (exit_code 0, gitleaks+builtin clean).
- ✓ **The drift-specific regression test (scripts/dep_drift_test.py, outside the default tests/ collection) actually passes, proving read-only behaviour and failure reporting**
  - `uv run pytest -q scripts/dep_drift_test.py` -> '1 passed in 0.78s' (exit 0). The test spins a fake PyPI server, asserts the lock bytes are unchanged after a run, that behind packages are reported ('1 of 3 locked packages behind PyPI latest'), non-registry sources noted, and failed lookups flagged 'Incomplete report'. deploy/systemd/README.md:15 documents that it sits outside the default tests/ collection and how to run it.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.: Live run: `bash scripts/dep-drift.sh` queried PyPI and printed 'certifi 2026.10.23 -> 2026.11.20', 'platformdirs 4.14.7 -> 4.14.8', '2 of 34 locked packages behind PyPI latest', exit=0; uv.lock sha256 9b99cbec281d... identical before and after (report-only confirmed; script only reads the lock via tomllib, scripts/dep-drift.sh:36-39). Timer armed: `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 lore-dep-drift.timer -> lore-dep-drift.service'; is-enabled=enabled, is-active=active; unit files at deploy/systemd/lore-dep-drift.timer (OnCalendar=Mon *-*-* 07:45:00, Persistent=true) and .service (ExecStart=.../scripts/dep-drift.sh). Docs: README.md:439-447 and docs/INSTALL.md:454-463 describe the report-only arrangement and arming steps; deploy/systemd/README.md covers install. Gates: `uv run pytest -x --tb=short -q` -> '572 passed in 8.16s' (exit 0); tier1 lint and secrets guards passed (exit_code 0, gitleaks+builtin clean).
  ✓ The drift-specific regression test (scripts/dep_drift_test.py, outside the default tests/ collection) actually passes, proving read-only behaviour and failure reporting: `uv run pytest -q scripts/dep_drift_test.py` -> '1 passed in 0.78s' (exit 0). The test spins a fake PyPI server, asserts the lock bytes are unchanged after a run, that behind packages are reported ('1 of 3 locked packages behind PyPI latest'), non-registry sources noted, and failed lookups flagged 'Incomplete report'. deploy/systemd/README.md:15 documents that it sits outside the default tests/ collection and how to run it.
dep-drift.sh verified live against PyPI with uv.lock checksum unchanged, lore-dep-drift.timer enabled+active and listed for Mon 07:45, README/INSTALL/deploy docs in place, and all gates green (572 passed plus the out-of-tree drift regression test passing).

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.: Live run: `bash scripts/dep-drift.sh` queried PyPI and printed 'certifi 2026.10.23 -> 2026.11.20', 'platformdirs 4.14.7 -> 4.14.8', '2 of 34 locked packages behind PyPI latest', exit=0; uv.lock sha256 9b99cbec281d... identical before and after (report-only confirmed; script only reads the lock via tomllib, scripts/dep-drift.sh:36-39). Timer armed: `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 lore-dep-drift.timer -> lore-dep-drift.service'; is-enabled=enabled, is-active=active; unit files at deploy/systemd/lore-dep-drift.timer (OnCalendar=Mon *-*-* 07:45:00, Persistent=true) and .service (ExecStart=.../scripts/dep-drift.sh). Docs: README.md:439-447 and docs/INSTALL.md:454-463 describe the report-only arrangement and arming steps; deploy/systemd/README.md covers install. Gates: `uv run pytest -x --tb=short -q` -> '572 passed in 8.16s' (exit 0); tier1 lint and secrets guards passed (exit_code 0, gitleaks+builtin clean).
  ✓ The drift-specific regression test (scripts/dep_drift_test.py, outside the default tests/ collection) actually passes, proving read-only behaviour and failure reporting: `uv run pytest -q scripts/dep_drift_test.py` -> '1 passed in 0.78s' (exit 0). The test spins a fake PyPI server, asserts the lock bytes are unchanged after a run, that behind packages are reported ('1 of 3 locked packages behind PyPI latest'), non-registry sources noted, and failed lookups flagged 'Incomplete report'. deploy/systemd/README.md:15 documents that it sits outside the default tests/ collection and how to run it.
dep-drift.sh verified live against PyPI with uv.lock checksum unchanged, lore-dep-drift.timer enabled+active and listed for Mon 07:45, README/INSTALL/deploy docs in place, and all gates green (572 passed plus the out-of-tree drift regression test passing).

Overall: PASS ✓
