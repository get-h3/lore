# lore dogfood run 7 — 2026-10-13 (closure→audit-record surface + lint-persistence re-proof at HEAD)

**Verdict: SHIPPABLE** on the driven surface. 415 tests + ruff clean at HEAD `fdfcea5`,
verified twice (control checkout + fresh bunker-mvp box).

## Angle (not touched by runs 1-6)

Run 6 sub-probed `gate --record` (ALLOW persists, DENY doesn't). Run 7 made the
**full closure→persist→re-read round trip** the primary surface, drove the
`validate-history.jsonl` persistence on **fresh machines** (run 5 filed LORE-045
against the local checkout only), and re-proved run 4's LORE-043 title-gate fix on
its own example. Everything else (match/compile/show/audit/absorb) was re-proved
en route as the loop's dependencies.

## The driven loop, as a user

1. `match` — signature hits 0.90 (`gateway-drain-window`, `key-rotation-expiry`,
   `shared-checkout-collision`); novel text → `unclassified`, honest 0.00.
2. `consult` tick-start mode — the exact title from the LORE-043 fix
   (`worker worktree checkout collision`) → `shared-checkout-collision`,
   check_count 3. Run 4's fix holds at HEAD.
3. `show`/`compile` — runbook proposal, propose-not-write, honest `no data` freshness.
4. `validate` — default = plan mode, executes nothing, writes nothing (scratch dir
   verified: no `.lore/` before `--execute`, created after). `--execute` honest:
   `env-absent (exit 127)` for logsey, `template` for placeholder checks.
5. **Persistence re-proof**: after `--execute`, `consult` (text + json), `compile --format md`,
   and `show` all carry `last lint-validated <ts> on this box (local history, not operator
   attestation)`. Verified on the control checkout, the fresh consumer clone, AND the
   bunker-mvp fresh box. LORE-045's fix survives a cold machine.
6. `gate` — ALLOW with `--record` appends one JSONL audit row (`decision`, `allowed`,
   `ack_ref`, `source`, `tool_version 0.1.2`); DENY (unknown class) exits 1 and writes
   nothing — file stayed 1 line. Run 6's finding re-proven.
7. `absorb` — class proposal + `--window` sweep over a 5-line logsey-shaped trail →
   3 proposals (gateway-drain-window, shared-checkout-collision, unclassified);
   the unclassified proposal is a full catch-all runbook with an explicit "no ladder can
   be honestly stated" recovery line. Plain-log trails degrade to an explicit empty
   result (exit 0), as documented.
8. `audit` — 14 classes, every row honest `no data` freshness, zero real commands only
   in the catch-all.

## Fresh-machine legs

- Control clone `uv run` fresh venv: 415 passed, ruff clean (bare-`uv sync` pytest
  failure is caught by lore's own guard message pointing at `uv sync --extra dev` — good UX).
- **Bunker leg (host substitution: las-03/02/04/01 all offline; bunker-mvp answered,
  bunkerd active):** agent `lore-df7` (ttl 2h), fresh Debian, Python 3.12.3, no uv.
  Clone → uv tarball installer (documented path) → `uv sync --extra dev` → first
  `match` 0.14 s, 415 tests, ruff clean. Leg timings: clone ~2 s, uv install ~15 s,
  sync ~10 s. Destroyed + verified (residue census unchanged pre/post).
- PyPI name-squat warning in README re-confirmed live: `pypi.org/pypi/lore/json` is
  200 (a DIFFERENT project), `get-h3-lore` is 404. The README's warning is correct
  and a real fresh user hitting `pip install lore` needs it.

## Findings (filed as LORE-049..051 on the board)

- **LORE-049 (P2) — real guard-failure vocabulary falls in the classifier's seams.**
  The most common guard failure in this fleet's own ops ("guard FAILED: secrets
  detected sk-… in diff") consults to `no matching runbook`; only the
  run-4-era "guard … not gate-equivalent" phrasing hits `guard-degradation`.
  Root cause: guard-degradation's 3 signature patterns and 6 keywords all encode
  gate-EQUIVALENCE vocabulary, and no class owns plain "guard failed / secrets
  detected / lint failed" text. Fresh evidence beyond run 4 (which tested only
  collision titles): `match --explain` shows the same text split 0.17/0.17/0.12
  across three classes — no signal, all noise.
- **LORE-050 (P2) — operator-facing texts assume operator tooling: `<gateway-log-path>`
  has no instruction, and a green lint can grade a class "not drifted" that was never
  executable.** Two related gaps surfaced by `validate --execute` on a fresh box:
  (a) runbook checks carry placeholder args with no "what goes here" (operator
  knowledge documented nowhere); (b) the history record's drift verdict is computed
  over EXECUTED commands only — on gateway-drain-window that meant 1 executed
  (`env-absent`) + 6 template-skipped = `drifted_orders: []` (not drifted) with an
  `env-absent` honesty label that nowhere says 6/7 checks never ran. Lint-labeled,
  not attested, correct per the honesty laws — but the per-class nuance ("2/7 real")
  is invisible to consult/compile consumers.
- **LORE-051 (P3) — the aggregate `status` column in `lore audit` hides the catch-all.**
  `audit` prints `unclassified  compiled=True checks=0 real-cmds=0` with no status
  marker that it is not a real failure class; a scripted consumer counting classes
  gets 14, not 13 curated + 1 bucket. Summary line does say "1 with zero real
  commands" — good — but the row itself carries no flag.

## Performance

Headline `match` warm: 67.5 ms ± 3.3 (hyperfine 20 runs, control checkout);
67-70 ms in the second measurement set — consistent with run 6's 40-60 ms. Fresh-box
cold: 0.14 s. Nothing a user would notice; no PERF row filed.

## Artifacts

- docs/dogfood/2026-10-13-run7-integration.md (this file)
- docs/dogfood/diagnostics.md (run-7 section appended)
- skills/lore-usage/SKILL.md (guard-failure-vocabulary caveat + tile note appended)
- Board rows LORE-049/050/051; .coding-hermes/dogfood-log.md entry
