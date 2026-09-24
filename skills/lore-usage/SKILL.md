# SKILL.md — lore usage (for agents landing in this repo)

## What lore is

Runbook compiler for a fleet of agents. You paste a symptom; it names the
failure class the fleet has seen before (with the evidence that identified it);
it compiles a runbook proposal per class (ordered read-only checks, expected
healthy-vs-incident outputs, recovery guardrails, evidence citations). It never
writes a published runbook: everything is a proposal until an operator
approves. Zero runtime dependencies, Python 3.11+.

## Install / run

```sh
uv tool install git+https://github.com/get-h3/lore   # standalone `lore` binary
# or, from a checkout:
uv sync --extra dev && uv run lore match "<symptoms>"
```

Subcommands that exist today: `match`, `compile`, `validate`. Help is honest —
`show`/`absorb`/`audit` are planned and NOT implemented; do not call them.

## The right-way patterns

- `lore match "<symptom or pasted log lines>"` — multi-line pastes are fine.
  Output: `class_id  confidence=X.XX  evidence: kind:detail; …` plus an
  `unclassified confidence=0.00` row that is ALWAYS printed last. That second
  row is by design (absence is a first-class answer), not an error.
- `lore compile --class <id> --format md|json` (default format is json).
  Unknown class id → exit 2, never an invented class (registry is closed).
- `lore validate [--class X] [--execute]` — DEFAULT IS PLAN-ONLY: it lists the
  commands it WOULD run and executes nothing. `--execute` runs only
  gate-approved read-only commands; a missing tool reports
  `error (exit 127)` and flips the runbook `stale` with a reason — that is the
  anti-rot signal working, do not treat it as a crash.
- Library use: `from lore.classifier import classify, classify_all`;
  `from lore.compiler import compile_class, compile_all`. `Classification`
  carries `class_id/confidence/matched_signature/matched_keywords/evidence`;
  `Runbook.to_dict()` is a stable 10-key shape. No other imports needed.

## The one pitfall that matters

The classifier matches on (1) signature regex → 0.90, else (2) ≥60% of a
class's keyword list → ≤0.5, else (3) unclassified. It recognizes the fleet's
canonical incident phrasings perfectly; a stranger's paraphrase of the same
incident often falls to unclassified ("two foremen committed to the same
worktree checkout" → unclassified). When you get `unclassified confidence=0.00`:

1. Re-check the curated class list (`uv run lore compile --format md | grep
   '^# Runbook:'`) and re-word the symptom using the runbook's own Signature
   line (e.g. say "drain 503", not "requests failing during restart").
2. Do NOT loosen code thresholds to force a match — file the phrasing gap on
   the board instead (see LORE-016, the evidence-echo proposal).

## Dev loop

```sh
uv run pytest -q    # expect: 148 passed in <1s
uv run ruff check . # expect: All checks passed!
```

Board: `.coding-hermes/board/tasks.jsonl` (JSONL, last row per id wins,
`LORE-*` ids). Commits: `type: description. Addresses <task-id>.`; GitReins
Tier-1 guard runs pre-commit; never commit `.gitreins/` runtime artifacts.
