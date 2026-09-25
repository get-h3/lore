# Dogfood integration report — lore, 2026-09-25

Tick: lore-dogfood-2026-09-25-07-43-16 · HEAD at run: `93baad0` · verdict: **SHIPPABLE** (this surface)

Second dogfood pass. The 2026-09-24 run covered the responder entry surface
(`match`/`compile`/`validate`), install, and perf (match ≈94 ms). This run took
the angle that did not exist yet: **the post-incident scribe + auditor
workflow** shipped since (`show`, `audit`, `absorb`, `gate`, `consult`, and the
LORE-016 `--explain` fix), plus a fresh-machine re-verification of both
documented install paths.

## Promise under test

> "QA/dogfood findings close through the SAME absorb-gate as incidents, with
> provenance (`--source`); an operator can sweep a prior evidence trail into
> per-class absorb proposals; the auditor sees coverage + honest freshness for
> every registry class; a guard failure can be consulted for its runbook."

All of it held, with two exceptions filed as board rows (LORE-018, LORE-020).

## What was exercised, live (this box, HEAD 93baad0)

- `lore consult --failure "<guard output mentioning drain 503>"` → printed
  `gateway-drain-window ... checks=7` with all 7 ordered checks. Garbage
  failure text → `no matching runbook`, exit 0 (fail-open holds).
- `lore match --explain "two foremen committed to the same worktree checkout"`
  (the exact LORE-016 gap example) → `unclassified` + near-misses:
  `shared-checkout-collision score=0.33 (2/6 keywords: worktree, checkout)`,
  `guard-degradation score=0.17`. The fix works; the CLI output is
  byte-identical without the flag.
- Scribe closeout of THIS run, as the README's LORE-009 contract prescribes:
  `absorb --class shared-checkout-collision --lesson ... --source
  dogfood-dagger` → proposal payload carrying `"source": "dogfood-dagger"`;
  `gate --decision absorb ...` → `GATE: ALLOW (absorb ->
  shared-checkout-collision) source: dogfood-dagger`; invented class →
  `GATE: DENY (1 errors)`, exit 1; `--decision no-new-lesson --reason ...` →
  ALLOW. Registry stayed closed end to end.
- `absorb --window 2h` sweep over a 5-line evidence trail (4 classifiable + 1
  noise) → 4 per-class proposals (drain-window, spawn-hot-loop,
  shared-checkout-collision, disk-pressure-corruption) + an `unclassified`
  proposal for the noise, each carrying window/ns provenance and its blocks.
  Two contract details a user hits first (filed): the trail must be a
  logsey-export payload (header + fenced block + bare-ISO timestamped lines —
  bracketed `[date]` prefixes parse as NOTHING with no hint why), and the CLI
  accepts `--source` on the window path but the sweep payload drops it
  (single-class absorb keeps it).
- `show gateway-drain-window --evidence` → full runbook with per-check
  evidence lines, `Status: proposal`, `Last validated: no data`.
  `show does-not-exist` → exit 2 with the full known-class list in the error.
- `audit` (table + json) → 10-class matrix; cross-checked: consult's "checks=7"
  matches audit's check_count 7 for drain-window; the "1 with zero real
  commands" summary line points at `unclassified` as intended.
- Library consumer (external script at /tmp/dogfood-consumer/consumer.py,
  public API only): `classify`, `classify_all`, `near_misses`,
  `consult_failure` → `ConsultFailureResult`, `compile_all()` → 10 runbooks
  all `status == "proposal"`. Two field-name frictions filed (LORE-021):
  `NearMiss.raw_score` vs the CLI's printed `score=`, and
  `Classification.evidence` being dicts, not objects.

## Fresh-machine install (ephemeral bunker, las-bunker-03, agent destroyed after)

- Agent e905ba6c (bare Debian, Python 3.13.5, no uv preinstalled): public
  `git clone https://github.com/get-h3/lore` FAILED — the repo is PRIVATE and
  anonymous HTTPS gets a 404 (verified from the control host too: `curl` →
  404, `gh repo view` → `isPrivate:true`). Tree staged via `git archive` of
  HEAD with existing access (visibility untouched — hard rule held).
- Pip-only path (the INSTALL.md fallback): `python3 -m venv .venv &&
  .venv/bin/pip install -e '.[dev]'` → **12 s**, then `match`, `pytest`
  (230 passed in 0.50 s), `ruff` all green on the fresh box.
- Recommended uv path (uv bootstrapped from the astral-sh release tarball —
  the one step INSTALL.md does not document): `uv sync --extra dev` → **4 s**,
  230 passed in 0.31 s, ruff clean.
- Fresh-box feature battery: consult (7-check runbook), match --explain
  (identical near-miss output), audit summary, gate ack (ALLOW), absorb
  --window (correct classification) — all worked on the bare box.
- bunker-qa.sh full battery (separate agent d421a20b, destroyed): **17 cells,
  zero FAIL** — toolchain-bootstrap OK ×7, fresh-install OK
  (lore-0.1.0 + ruff), ci-pass OK (native suite), upgrade OK (v0.1.0 → HEAD —
  the cell QA-LORE-1 asked for now exists and passes), chaos-resource PASS
  (3 GiB cap), chaos-errorpath OK, chaos-disconnect INFO, honest N/A ×4
  (no compose/UI/db in repo).

## Performance (Step 2b)

hyperfine, warm, 20 runs each: `match --explain` 60.5 ± 2.5 ms, `audit`
61.0 ± 2.5 ms, `absorb --window 2h` (5-block trail) 62.3 ± 3.1 ms — all
interpreter-startup bound, all comfortably fast. Nothing a user would feel →
no PERF row filed (a win nobody can feel is not a finding). Cold-vs-warm is
meaningless here: the cold number is pip/uv install time, measured above
(12 s / 4 s).

## Friction count

9 touches, 3 of them fileable (LORE-018 private-repo clone, LORE-020 trail
format + source-drop, LORE-021 library field names) plus doc staleness
(LORE-019: README "148 tests" ×2, stale usage skill). Everything else
worked as documented on first use.
