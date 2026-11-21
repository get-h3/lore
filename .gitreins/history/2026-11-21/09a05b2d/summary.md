# Verdict: SUP-DEPS-LORE-20261121

**Task:** Scheduled lock-versus-PyPI drift sweep (report-only)
**Evaluated:** 2026-11-21T03:58:38.877659
**Result:** ✓ PASS

## Criteria

- ✓ **scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.**
  - (a) Live run: sha256sum uv.lock before and after `scripts/dep-drift.sh` both 9b99cbec281d5a47cc327fa7421be1a1465c2b6f87a287799a36f0ee0b6fafe5, script_exit=0, live output 'certifi 2026.10.23 -> 2026.11.20; platformdirs 4.14.7 -> 4.14.8; 2 of 34 locked packages behind PyPI latest'; script is read-only (scripts/dep-drift.sh:1-82, tomllib read + PyPI GET, no writes). (b) `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 -05 lore-dep-drift.timer lore-dep-drift.service'; is-enabled=enabled, is-active=active. (c) README.md:439-447 and docs/INSTALL.md:454-463 document the script, its report-only nature, the unit install paths, and `systemctl --user enable --now lore-dep-drift.timer`. (d) Gates: `uv run pytest -x --tb=short` exit 0, '572 passed in 7.40s'; tier1 lint and secrets lanes passed (exit_code 0).
- ✓ **Seam: the armed ~/.config/systemd/user units match the repo's deploy/systemd/ examples the docs point at, and the service has actually executed (log sink exists).**
  - diff deploy/systemd/lore-dep-drift.timer ~/.config/systemd/user/lore-dep-drift.timer -> identical; diff of the .service -> identical; ~/.local/share/lore/dep-drift.log exists (286 bytes, Nov 20 22:52) confirming a real run through the armed unit; `systemctl --user cat lore-dep-drift.service` resolves to the installed unit.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.: (a) Live run: sha256sum uv.lock before and after `scripts/dep-drift.sh` both 9b99cbec281d5a47cc327fa7421be1a1465c2b6f87a287799a36f0ee0b6fafe5, script_exit=0, live output 'certifi 2026.10.23 -> 2026.11.20; platformdirs 4.14.7 -> 4.14.8; 2 of 34 locked packages behind PyPI latest'; script is read-only (scripts/dep-drift.sh:1-82, tomllib read + PyPI GET, no writes). (b) `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 -05 lore-dep-drift.timer lore-dep-drift.service'; is-enabled=enabled, is-active=active. (c) README.md:439-447 and docs/INSTALL.md:454-463 document the script, its report-only nature, the unit install paths, and `systemctl --user enable --now lore-dep-drift.timer`. (d) Gates: `uv run pytest -x --tb=short` exit 0, '572 passed in 7.40s'; tier1 lint and secrets lanes passed (exit_code 0).
  ✓ Seam: the armed ~/.config/systemd/user units match the repo's deploy/systemd/ examples the docs point at, and the service has actually executed (log sink exists).: diff deploy/systemd/lore-dep-drift.timer ~/.config/systemd/user/lore-dep-drift.timer -> identical; diff of the .service -> identical; ~/.local/share/lore/dep-drift.log exists (286 bytes, Nov 20 22:52) confirming a real run through the armed unit; `systemctl --user cat lore-dep-drift.service` resolves to the installed unit.
The drift sweep is real and verified end-to-end: scripts/dep-drift.sh ran live against PyPI leaving uv.lock byte-identical, the user timer is enabled/active and visible in list-timers with a next elapse of Mon 07:45, README and INSTALL both document the arrangement, and the full gate battery (572 tests, lint, secrets) is green.

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ scripts/dep-drift.sh reports uv.lock-vs-PyPI drift live and report-only (uv.lock checksum unchanged by a run); lore-dep-drift.timer+service armed and visible in systemctl --user list-timers; README+INSTALL document the arrangement; gates green.: (a) Live run: sha256sum uv.lock before and after `scripts/dep-drift.sh` both 9b99cbec281d5a47cc327fa7421be1a1465c2b6f87a287799a36f0ee0b6fafe5, script_exit=0, live output 'certifi 2026.10.23 -> 2026.11.20; platformdirs 4.14.7 -> 4.14.8; 2 of 34 locked packages behind PyPI latest'; script is read-only (scripts/dep-drift.sh:1-82, tomllib read + PyPI GET, no writes). (b) `systemctl --user list-timers --all` shows 'Mon 2026-11-23 07:45:00 -05 lore-dep-drift.timer lore-dep-drift.service'; is-enabled=enabled, is-active=active. (c) README.md:439-447 and docs/INSTALL.md:454-463 document the script, its report-only nature, the unit install paths, and `systemctl --user enable --now lore-dep-drift.timer`. (d) Gates: `uv run pytest -x --tb=short` exit 0, '572 passed in 7.40s'; tier1 lint and secrets lanes passed (exit_code 0).
  ✓ Seam: the armed ~/.config/systemd/user units match the repo's deploy/systemd/ examples the docs point at, and the service has actually executed (log sink exists).: diff deploy/systemd/lore-dep-drift.timer ~/.config/systemd/user/lore-dep-drift.timer -> identical; diff of the .service -> identical; ~/.local/share/lore/dep-drift.log exists (286 bytes, Nov 20 22:52) confirming a real run through the armed unit; `systemctl --user cat lore-dep-drift.service` resolves to the installed unit.
The drift sweep is real and verified end-to-end: scripts/dep-drift.sh ran live against PyPI leaving uv.lock byte-identical, the user timer is enabled/active and visible in list-timers with a next elapse of Mon 07:45, README and INSTALL both document the arrangement, and the full gate battery (572 tests, lint, secrets) is green.

Overall: PASS ✓
