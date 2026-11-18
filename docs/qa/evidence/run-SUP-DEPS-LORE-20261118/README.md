# SUP-DEPS-LORE-20261118 — platformdirs lock refresh evidence

Tick: lore-foreman-2026-11-18-22-21-56 (foreman-direct; single-file lock chore per map routing "Dependencies").

## Change

`uv lock --upgrade-package platformdirs` (exact command from the row's foreman_note).

- uv.lock: platformdirs 4.13.5 → 4.14.7 (PyPI latest per row's measured intake 2026-11-18)
- `git diff --stat`: uv.lock only (3 insertions, 3 deletions) + this evidence file

## Gate results (2026-11-18, PATH=<repo>/.venv/bin:$PATH)

| Gate | Result |
|---|---|
| `uv run pytest -q` | 572 passed in 6.21s, exit 0 (= recorded canonical baseline, see below) |
| `uv run ruff check .` | exit 0 |
| `uv run ruff format --check .` | exit 0 |
| `bash scripts/check-test-count.sh` | PASS: canonical=572 matches live=572; class-count=13; no stale count literals |
| `grep -A1 '^name = "platformdirs"' uv.lock` | version = "4.14.7" (> 4.13.5) |

Baseline note: the row asked for the suite at "the recorded baseline" — the recorded canonical in
`scripts/test-count.txt` at the pre-tick tip was 572 (skill notes of 566 are stale; a sibling
DOC-12 wave added tests on 11-17). The lock-only diff adds no tests; live=canonical=572 pre and post.

Held pin: none — platformdirs upgraded to latest; iniconfig 2.3.1 and tomli 2.5.0 already latest,
untouched per the package-scoped selector.

ch:trace row=SUP-DEPS-LORE-20261118 spec=none doc=docs/qa/evidence/run-SUP-DEPS-LORE-20261118/README.md witness=live:uv-lock-resolve-4.14.7
