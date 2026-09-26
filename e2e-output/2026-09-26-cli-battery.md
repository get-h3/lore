# lore CLI E2E battery — 2026-09-26 (E2E-001)

Verification artifact, not a feature change. Every cell below ran the CLI as a
fresh subprocess via `uv run lore …` from this worktree
(`/home/kara/worktrees/lore-E2E-001`, branch `wt/E2E-001`). No `--execute`,
no external writes, no board edits. The class registry is in-memory
(`lore/classes.py` SEED_CLASSES, 14 classes) and every mutating-looking
command (`compile`, `validate`, `absorb`, `gate`) is propose-not-write by
design — stdout only.

## Method notes

- Exit codes were captured with `echo "EXIT=$?"` (no pipes) or
  `echo "EXIT=${PIPESTATUS[0]}"` (piped stdout), never the pipe's own status.
- Discovery: an early absorb cell run as `uv run lore absorb … | head` printed
  a full JSON proposal yet reported `EXIT=1`. Re-run with stdout redirected to
  a file it exits `0`. Cause: `head` closes the pipe, the writer dies on
  SIGPIPE. Recorded here because a battery that trusts piped exit codes would
  have filed a false defect. All large-output cells below use file
  redirection; the piped variant is noted as a harness artifact, not a lore
  bug.
- Registry is closed: unknown ids are rejected everywhere with exit 2 and a
  "Known: …" list (verified on `compile`, `validate`, `show`).

## Battery results

Legend: PASS = observed behavior matches documented CLI contract;
UNTESTABLE = not exercised, with reason.

### `lore match`

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 1 | `uv run lore match "gateway 503s during restart drain window"` | 0 | `gateway-drain-window  confidence=0.47  evidence: keyword:503; keyword:drain; keyword:gateway; keyword:restart; keyword:drain window` + `unclassified  confidence=0.00` | PASS |
| 2 | `uv run lore match "gateway 503s during restart drain window" --explain` | 0 | same two rows plus `near-misses:\n  guard-degradation  score=0.17  (1/6 keywords: gate)` — near-miss is evidence-only, never a label | PASS |
| 3 | `uv run lore match "gratuitous unicorns parade"` (negative/unknown) | 0 | `unclassified  confidence=0.00  evidence: none` — fail-open classification, never a wrong label | PASS |

### `lore consult`

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 4 | `uv run lore consult "gateway 503s during restart drain window" --json` | 0 | JSON: `matched: true`, one `runbook_refs` entry (`gateway-drain-window`, status `proposal`, `check_count: 7`) | PASS |
| 5 | `uv run lore consult "gratuitous unicorns parade" --json` (negative) | 0 | JSON: `matched: false`, empty refs — documented fail-open (no match = exit 0) | PASS |
| 6 | `uv run lore consult "gratuitous unicorns parade"` (negative, plain) | 0 | `no matching runbook` | PASS |
| 7 | `uv run lore consult --failure "guard pass from worktree but main-tree fail at same commit — not gate-equivalent" --json` | 0 | LORE-009 guard-failure mode: `matched: true`, class `guard-degradation`, `suggestions[]` carrying the runbook's 2 ordered checks | PASS |
| 8 | `uv run lore consult --failure "ruff: 1 file would be reformatted, secret scan FAIL" --json` (negative) | 0 | `matched: false`, no suggestions — fail-open holds in failure mode too | PASS |

### `lore compile`

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 9 | `uv run lore compile --class gateway-drain-window --format md` | 0 | markdown runbook: status proposal, last validated "no data (never validated)", signature `drain\s+503`, checks in order (stdout only) | PASS |
| 10 | `uv run lore compile` (all classes) | 0 | JSON array starting with `gateway-drain-window`; every entry carries `checks[].read_only: true` | PASS |
| 11 | `uv run lore compile --class bogus-class` (negative) | 2 | `error: unknown class_id 'bogus-class'; registry is closed. Known: …` (14 ids listed) | PASS |

### `lore validate` (plan-only by contract)

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 12 | `uv run lore validate --class gateway-drain-window` | 0 | JSON with `"mode": "plan"` and note `plan only — no command was executed; pass --execute to run the gate-approved read-only commands`; `would_run` lists the 7 gate-approved commands verbatim | PASS |
| 13 | `uv run lore validate --class gateway-degradation-window` (negative) | 2 | same closed-registry error shape as compile | PASS |
| 14 | `uv run lore validate --class gateway-drain-window --execute` | — | UNTESTABLE: `--execute` actually runs the gate-approved commands; the task forbids `--execute` and any execution side effects, so the opt-in execution path was intentionally not exercised. Plan mode (cell 12) is the task-mandated safe surface and is PASS. | UNTESTABLE |

### `lore gate` (machine-check of a closure decision; prints a verdict, writes nothing)

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 15 | `uv run lore gate --decision absorb --class gateway-drain-window --lesson "Verify drain window via logsey before restarting the gateway" --ref LORE-E2E-001 --decided-at 2026-09-26T10:00:00Z` | 0 | `GATE: ALLOW (absorb -> gateway-drain-window)` | PASS |
| 16 | `uv run lore gate --decision no-new-lesson --reason "symptom already covered by gateway-drain-window runbook" --ref LORE-E2E-001` | 0 | `GATE: ALLOW (no-new-lesson)` | PASS |
| 17 | `uv run lore gate --decision absorb` (negative: missing --class/--lesson) | 1 | `GATE: DENY (2 errors)` + `error: absorb requires a class_id` + `error: absorb requires a lesson` — denial is exit 1 per help contract ("exit 0 = allowed, 1 = denied") | PASS |
| 18 | `uv run lore gate --decision bogus-decision` (negative: argparse) | 2 | usage error `invalid choice: 'bogus-decision' (choose from 'absorb', 'no-new-lesson')` | PASS |

### `lore absorb` (proposal builder; stdout only — nothing is written)

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 19 | `uv run lore absorb --class gateway-drain-window --lesson "Pin drain-window checks before any gateway restart"` | 0 | proposal JSON: `action: new`, full `added` runbook, empty `removed`/`changed`, note `proposal only — an operator must approve before this lands anywhere` | PASS |
| 20 | `uv run lore absorb` (negative: missing required args) | 2 | `error: absorb requires --class and --lesson (or --window for the sweep)` | PASS |
| 21 | `uv run lore absorb --window 2h --trail-file /dev/null` (negative: empty trail) | 0 | `no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)` — honest fail-open | PASS |
| 22 | `uv run lore absorb --window 2h --trail-file /tmp/lore-e2e/trail.txt` (positive sweep) | 0 | trail file = `logsey export --window 2h` header + fenced block with 3 timestamped lines (2 gateway-drain, 1 noise); output is a proposal JSON array for `gateway-drain-window` built from the 2 classifiable blocks; noise block not attributed (no fabricated evidence) | PASS |

### `lore show`

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 23 | `uv run lore show gateway-drain-window` | 0 | human-markdown runbook (same compiled shape as compile --format md) | PASS |
| 24 | `uv run lore show gateway-drain-window --format json` | 0 | valid JSON (checked with `python3 -m json.tool`), 6213 bytes, `class_id: gateway-drain-window` | PASS |
| 25 | `uv run lore show no-such-class-xyz` (negative) | 2 | `error: unknown class_id 'no-such-class-xyz'; registry is closed. Known: …` (14 ids) | PASS |

### `lore audit`

| # | Command | Exit | Observation | Result |
|---|---------|------|-------------|--------|
| 26 | `uv run lore audit` | 0 | table: 14 classes, all `compiled=True`, honest `last_validated = no data` everywhere, summary line `14 classes; 1 with zero real commands` + freshness honesty note | PASS |
| 27 | `uv run lore audit --format json` | 0 | JSON `classes[]` with per-class `runbook_compiled`, `check_count`, `command_count`, `last_validated: "no data"`, `status: "proposal"` | PASS |

## Summary

- 27 cells: 26 PASS, 1 UNTESTABLE (`validate --execute`, excluded by task
  safety rules), 0 FAIL.
- All eight subcommands exercised through real subprocesses
  (`uv run lore …`), each with at least one positive and, where the CLI
  supports it, one negative/unknown case.
- Shared contract verified across three commands: unknown class id → exit 2
  with a closed-registry error listing known ids.
- Fail-open contract verified: `match`/`consult`/`absorb --window` return
  exit 0 on no-match/empty input and never fabricate a label, a date, or an
  evidence block.
- Propose-not-write verified: `compile`, `validate` (plan), `absorb`, and
  `gate` print proposals/verdicts to stdout only; no file under the repo or
  any external store was written by any battery cell.
- No production code was modified and no board files were touched; the
  observed contracts are already pinned by `tests/test_cli_surface.py` and
  siblings, so no additional test was added (per task, report alone is
  sufficient).
