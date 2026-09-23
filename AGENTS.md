# AGENTS.md — lore

Runbook compiler — compiles the fleet's incident history into living, re-validated
runbooks per failure class. *"How did we fix this last time — and does it still work?"*

## Build / Test / Run

```sh
uv sync --extra dev        # provision .venv + pytest/ruff (uv; bare pytest exits 127 pre-venv)
uv run pytest -q           # tests
uv run ruff check .        # lint
uv run lore match "<symptoms>"   # or: python -m lore match "<symptoms>"
```

## Board

`.coding-hermes/board/tasks.jsonl` — JSONL-canonical, last row per id wins.
`LORE-*` task ids. Satellite lanes (lore-qa/-pm/-dogfood/-releng/-sync) read this
board via a symlinked dir.

## Git conventions

- Small, path-limited commits. Subject format: `type: description. Addresses <task-id>.`
- Worktree-mode workers: commit on `wt/<taskid>`, never push or merge (the foreman merges).
- GitReins Tier-1 guard runs pre-commit (secrets/lint/tests, see `.gitreins/config.yaml`);
  board-only commits rely on `allow_skips: true` so empty lanes skip instead of
  false-DEGRADED-blocking.
- Never commit `.gitreins/` runtime artifacts (tasks.yaml, logs/, usage.jsonl) — ignored.