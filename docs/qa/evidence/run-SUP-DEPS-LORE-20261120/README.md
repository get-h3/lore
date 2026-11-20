# SUP-DEPS-LORE-20261120 — 9-package dependency drift refresh evidence

Tick: lore-foreman-2026-11-20-08-33-11 (foreman-direct; single-file lock chore per map routing
"Dependencies", same path as the 2026-11-18 predecessor row).

## Change

Nine package-scoped refreshes, exactly the row's measured intake list
(`uv lock --upgrade-package <pkg>` per package):

| Package | Before | After |
|---|---|---|
| cachecontrol | 0.14.4 | 0.15.0 |
| certifi | 2026.10.19 | 2026.10.23 |
| filelock | 4.2.4 | 4.2.12 |
| markdown-it-py | 4.2.0 | 4.3.0 |
| msgpack | 1.2.3 | 1.2.4 |
| pip | 26.2.1 | 26.3 |
| py-serializable | 2.1.0 | 2.2.0 |
| pytest | 9.1.1 | 9.2.0 |
| ruff | 0.17.1 | 0.17.6 |

Each call printed its own `Updated <pkg> vX -> vY` line; every after-version equals the
PyPI latest the row measured at 2026-11-20T07:05Z. platformdirs 4.14.7, iniconfig 2.3.1 and
tomli 2.5.0 were already current and untouched by the package-scoped selectors.

## Gate results (2026-11-20, uv 0.11.17)

| Gate | Result |
|---|---|
| `uv run pytest -q` | 572 passed in 6.48s, exit 0 (= recorded canonical baseline) |
| `uv run ruff check .` | All checks passed!, exit 0 |
| `uv run ruff format --check .` | 320 files already formatted, exit 0 |
| `bash scripts/check-test-count.sh` | PASS: canonical=572 matches live=572; class-count=13; no stale count literals |
| `grep -A1 '^name = "pytest"' uv.lock` | version = "9.2.0" (row requires >= 9.2.0) |
| `grep -A1 '^name = "ruff"' uv.lock` | version = "0.17.6" (row requires >= 0.17.6) |

### Venv sync disclosure (added at closeout)

The table above ran while `.venv` still held the pre-refresh pins: the first `uv run pytest -q`
did not upgrade the dev extra (dev tools live in `[project.optional-dependencies] dev`, and the
default sync set leaves installed extras untouched), so 572-passed there was under pytest 9.1.1 /
ruff 0.17.1 against the new lock. After `uv sync --extra dev` (venv now pytest 9.2.0,
ruff 0.17.6), the full battery was re-run under the refreshed pins — the authoritative result:

| Gate | Post-sync result |
|---|---|
| `uv run --no-sync pytest -q` | 572 passed in 6.95s, exit 0 under pytest 9.2.0 |
| `uv run --no-sync ruff check .` | All checks passed!, exit 0 under ruff 0.17.6 |
| `uv run --no-sync ruff format --check .` | 322 files already formatted, exit 0 |
| `bash scripts/check-test-count.sh` | PASS: canonical=572 matches live=572; class-count=13 |

Both runs agree (572, all green); the tier1 guard's own test stage (7.41s, 572 passed) also ran
pre-sync under pytest 9.1.1 — same count, disclosed here so the environment ordering is
reconstructable.

The lock-only diff adds no tests; live=canonical=572 pre and post (pytest 9.1.1 → 9.2.0 did
not change collection).

## Churn

`git diff --stat` at gate time: uv.lock only (126 insertions, 126 deletions), plus this
evidence file and the board close record — no unrelated churn.

## Held pins

None — all nine packages upgraded to latest; no deliberate hold-backs.

ch:trace row=SUP-DEPS-LORE-20261120 spec=none doc=docs/qa/evidence/run-SUP-DEPS-LORE-20261120/README.md witness=live:uv-lock-resolve-9-pkg
