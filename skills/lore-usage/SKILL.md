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

The repo is PUBLIC (flipped 2026-09-25 per LORE-018's decision; anonymous
clone works). **A `uv tool install` tracks the HEAD you installed, not the
repo** — a pre-LORE-007 install exposes only 3 of 8 subcommands and errors
with "invalid choice" on the rest. If a documented subcommand "doesn't
exist", run `uv tool upgrade lore` before filing a bug.

## The eight subcommands (all implemented, verified 2026-09-25)

- `match "<symptom|log lines>" [--explain]` — classify. `--explain` adds a
  `near-misses:` section: top-3 below-threshold classes with raw keyword
  scores (nothing auto-labeled; registry stays closed).
- `consult --failure "<guard/failure output>"` — guard-failure suggestion:
  prints matching runbook id + ordered checks; fail-open (`no matching
  runbook`, exit 0) so pipelines can append unconditionally.
- `compile [--class X] [--format json|md]` — runbook proposal(s) to stdout.
  Unknown class → exit 2 (closed registry).
- `validate [--class X] [--execute]` — read-only command lint. DEFAULT IS
  PLAN-ONLY: lists what WOULD run, executes nothing. `--execute` runs only
  gate-approved read-only commands; a missing tool reports `error (exit 127)`
  and flips the runbook `stale` — the anti-rot signal working, not a crash.
  Two live-run truths (2026-09-25, LORE-022/024): `--execute` NEVER sets
  `last_validated` (operator attestation only, propose-not-write) — the
  `stale` flag, not the freshness field, is today's freshness signal; and a
  check carrying a `<placeholder>` path shell-errors as input redirection,
  staling its class — `--class shared-checkout-collision` is the one class
  that lints green as authored. Run it where the fleet actually runs: on a
  bare box everything stales (exit 128 "not a git repository" is the
  machine, not the runbook).
- `gate --decision absorb|no-new-lesson ...` — closure absorb-gate machine
  check. `absorb` needs `--class` + `--lesson` (class must exist); ack needs
  `--reason`. ALLOW → exit 0, DENY → exit 1 with all violations listed.
  `--source qa-dagger|dogfood-dagger` records provenance on the verdict line.
- `absorb --class X --lesson "..." [--source ...]` — the runbook-update
  PROPOSAL payload (stdout only, propose-not-write).
- `absorb --window 2h [--trail-file P|--ns N|--source ...]` — sweep a PRIOR
  evidence trail into per-class absorb proposals (stdout only). The trail
  must be a logsey-export payload: a line matching `logsey export`, a fenced
  block, then one evidence line per row starting with a BARE ISO timestamp
  (`2026-09-25T06:12:00Z unit=gateway <detail>` — bracketed `[date]` prefixes
  do NOT parse). Unparseable-but-claimed exports raise; non-claimed input is
  an explicit empty result (exit 0).
- `show <class> [--evidence] [--format json|md]` — one compiled runbook,
  human-markdown default, with per-check evidence when asked.
- `audit [--format table|json|md]` — coverage + freshness matrix over all
  registry classes; honest `no data` freshness (never fabricated — but note
  it does not reflect lint runs either: `last_validated` is never stamped in
  v0.1.x, see LORE-022; read the `stale` status column as the live signal).

## The right-way patterns

- `lore match` prints an `unclassified confidence=0.00` row ALWAYS last —
  that is by design (absence is a first-class answer), not an error. When you
  get it, rerun with `--explain` and rephrase the symptom with the near-miss
  class's own vocabulary (LORE-016 fix, verified live).
- Multi-line pastes are fine; leading-dash symptoms (`-Q log stuck`) work —
  argparse does not eat them.
- Close a QA/dogfood run through the same gate as an incident: `lore absorb
  --class <id> --lesson "<text>" --source dogfood-dagger` for the proposal,
  then `lore gate --decision absorb ... --source dogfood-dagger` (or
  `--decision no-new-lesson --reason "..."`) for the verdict line.
- Library use (all verified from an external script):
  `from lore.classifier import classify, classify_all, near_misses`;
  `from lore.consult import consult_failure`;
  `from lore.compiler import compile_class, compile_all`.
  Pitfalls: `NearMiss` exposes `raw_score` (the CLI prints it as `score=`),
  plus `n_hits/n_keywords/hit_keywords`; `Classification.evidence` is a list
  of DICTS (`e["kind"]`, `e["detail"]`), not objects; and `Classification`
  has NO `near_misses` attribute — near-misses are a SEPARATE call,
  `near_misses(text)` (a first-time consumer that guesses `c.near_misses`
  gets an AttributeError; run-4 verified).
- Paste tails, not paraphrases. Signature-bearing input classifies instantly
  (0.90 in ~50-65 ms); phrasing the symptom in your own words risks the
  registry's vocabulary blind spots. Fixed in LORE-041: git's canonical
  collision error ("would be overwritten by checkout") now labels
  now labels `shared-checkout-collision` at 0.90; earlier it missed AND the near-miss
  echo ranked `secret-env-clobber` first on "overwritten". Fixed in
  LORE-043: the title-only consult path no longer goes silent on short
  titles — a text of ≤8 words (board-title 25th percentile; measured)
  accepts keyword evidence at a ≥0.3 gate instead of the long-text 0.6, so
  the 4-word title "worker worktree checkout collision" (3/8 keywords = 0.375) now labels
  `shared-checkout-collision` at keyword strength.
  Long-text behavior is unchanged: a 10-word paraphrase that scored 0.5
  still refuses and only echoes as a near-miss.
- Guard-failure consults: paste the guard's text verbatim — the DECISION
  vocabulary AND the finding list both classify now (LORE-049 + rework).
  "guard FAILED: secrets detected sk-… in diff; gitleaks gate rejected
  commit" consults to `gateway-guard-violation`; so do the bare finding
  tails ("secrets detected in diff: a sk-prefixed token leaked",
  "gitleaks gate rejected commit", "lint failed") and the run-4-era
  gate-equivalence phrasing ("guard … not gate-equivalent … main tree" →
  `guard-degradation`). Gate-equivalence and plain guard-tripping are
  different classes: same failure family, different recovery ladder.
- Fresh-box install (run 4, all three paths pass): anonymous clone works;
  `uv sync --extra dev` ≈9 s incl. a 4 s uv bootstrap from the astral-sh/uv
  GitHub release tarball; pip fallback (`venv` + `pip install -e ".[dev]"`)
  ≈15 s; `uv tool install` ≈2 s. INSTALL.md does not yet say how to GET uv
  (its docs' installer is a curl-piped-to-shell one-liner — the tarball
  route needs only curl+tar), and bare Debian lacks `unzip`, which
  `uv self update` wants (LORE-044).

## Dev loop

```sh
uv run pytest -q    # expect: 523 passed (count synced to scripts/test-count.txt, LORE-029)
uv run ruff check . # expect: All checks passed!
```

Board: `.coding-hermes/board/tasks.jsonl` (JSONL, last row per id wins,
`LORE-*` ids). Commits: `type: description. Addresses <task-id>.`; GitReins
Tier-1 guard runs pre-commit; never commit `.gitreins/` runtime artifacts.

## The closure loop (run 6, 2026-10-04 — the surface this skill under-documents)

- `gate` denials exit 1; ALLOWs exit 0 and write a JSONL row ONLY if
  `--record PATH` was passed (opt-in; DENY never writes even with `--record`).
- `absorb --window` needs a LOGSEY-EXPORT-shaped trail: a `logsey export`
  line, a fenced block, then per-row lines starting with a BARE ISO
  timestamp. A plain log is an explicit empty result (exit 0), not an error;
  an input that CLAIMS an export but does not parse exits 2.
- `validate --execute` never sets `last_validated` (operator attestation),
  but it appends `./.lore/validate-history.jsonl` **per CWD**, and `consult`
  reads that local history: after a green lint, consult shows
  "last lint-validated <ts> on this box (local history, not operator
  attestation); executed X/Y checks" while show/audit keep `no data`.
  The executed ratio (LORE-050) is the honesty scope of the drift verdict:
  `drifted_orders: []` over `executed 0/7` means the lint EXERCISED NOTHING,
  not that the runbook is healthy. Verify a "stale" claim by
  checking WHICH command you asked — the two honesty fields diverge by design.
- Fixture pitfall: validate's checks run in the CURRENT directory — run
  `--execute` from a real checkout or git-based checks exit 128 and the
  class records drifted_orders (in a non-repo CWD that is correct behavior,
  the anti-rot signal working).

## The machine contract (run 8, 2026-10-13)

- `show <c> --format json` == `compile --class <c> --format json` element 0
  (modulo provenance/evidence_trail provenance blocks) — verified byte-equal
  via `jq -S del(...)`. Scripts may use either.
- Exit ladder, verified with direct `$?`: unknown class → 2 (compile and
  gate absorb both); gate ack → 0; gate DENY → 1 (violations listed on
  stderr-style output); consult unmatched → 0 fail-open 'no matching
  runbook'. Script on the exit code, not the prose.
- `audit --format json` lists 14 entries: 13 curated classes PLUS the
  `unclassified` bucket (see run-7 LORE-051 — no flag marks the bucket).
  Filter `.class_id != "unclassified"` before counting classes.
- `absorb --window` trail contract: a `logsey export` marker line, a FENCED
  ``` block, then one evidence line per row starting with a BARE ISO
  timestamp. Anything claiming to be an export without the fence → rc=2
  (error text does not state this contract — LORE-053). No marker at all →
  rc=0 empty result.
- `validate --execute` runs commands under bash (LORE-052 switched from
  /bin/sh): process substitution (`diff <(...)`) now works. Missing files
  (fleet.toml, ~/.hermes paths) exit 1 → class flips 'stale' via the
  env_absent outcome (not drifted). On a box without the fleet layout,
  expect 1 drifted class (gateway-drain-window, runbook text wrong per
  LORE-060) + 1 env-absent class (cooldown-pin-drift, missing fleet.toml)
  + 12 green classes; shared-checkout-collision is the reliably-green
  class (LORE-052).

## The argument-form map (run 9, 2026-10-17)

Three argument shapes live in the six verbs; every run-9 operator miss was a form
miss. Before scripting, check the shape per verb (or just `--help` that verb):

- `match "text" [--class <id>] [--explain]` — text POSITIONAL, --class FLAG.
- `consult <title>…` or `consult --failure "<text>"` — --failure takes the
  failure TEXT INLINE, not a file path (a path string classifies as its own
  text and fails open to a silent no-match, exit 0).
- `show <class_id> [options]` — class POSITIONAL (no --class flag; exits 2
  with a usage error otherwise). `compile [--class X]` takes the FLAG.
- `validate [--class X] [--execute]`, `gate --class <id>`,
  `absorb --class <id> --lesson "…"` — flag forms.

## Fresh-box truth (bunker battery, run 9)

- A hand pytest run on a fresh agent without the venv bin on PATH can surface
  ONE failure: tests/test_count_guard.py exits the CHILD guard with rc=2
  'could not determine live test count (... guard misconfigured, not drift)'
  because the guard's `python3 -m pytest` resolves to system python. The guard
  is honest; the test's env is under-specified — board row LORE-057. On such a
  box run: `export PATH=~/tools/venv/bin:$PATH` first (battery legs already
  have this; only hand-run pytest shells don't).
- `chaos-disconnect` in the fleet battery grades UNVERIFIED (vacuity) since
  fresh-install moved to the wheel: the wheel carries no test suite, so the
  disconnect cell has nothing to cut (LORE-058). It is NOT a lore defect.
- The audit table still lists `unclassified` as a regular class row
  (run-7 LORE-051, pending): filter `.class_id != "unclassified"` before
  counting classes.

## The runbook-text-vs-sibling-tool contract (run 10, 2026-10-17)

A lore runbook is shell strings aimed at OTHER tools; its validity drifts with the
sibling tool's real CLI, not with lore's own code. Two live truths at HEAD 9b97fa2:

- **gateway-drain-window's logsey checks (orders 1 and 7) do not run on the real logsey
  CLI** — `logsey query --pattern X --since <wd>` exits 2 ("unexpected second argument");
  logsey takes ONE quoted SQL string (`logsey query "<sql>"`). The class grades `stale`
  from its own runbook text (board row LORE-060), not because logsey is missing. Do not
  "fix" this by removing logsey from PATH in a test — the runbook TEXT is the defect.
- **`stale` conflates env-absent and drifted at the render layer** — the data layer
  separates them (`env_absent_orders` vs `drifted_orders`), but the plain-text runbook
  and the audit table print one word. On a box without logsey, gateway-drain-window
  reads "stale" for a healthy reason (board row LORE-061). Before treating a stale
  class as a regression, run `validate --execute` and read `env_absent_orders` vs
  `drifted_orders` in the JSON, not the table.

Fresh-machine install envelope (hand leg, bunker-mvp agent 26678b35, destroyed):
clone -> uv tarball bootstrap -> `uv venv`+`uv pip install -e ".[dev]"` -> first match:
all rc=0; in-box seconds after uv lands (uv tarball download ~2m dominates first touch).
Bare fresh box + first `validate --execute` creates `.lore/validate-history.jsonl`
14/14 rows honestly (env-absent on a tool-less box, honesty_label preserved) —
the per-CWD history is correct on a machine that never ran lore before (LORE-045 hold).

## The validate-history ledger is a COST, not just a cache (run 14, 2026-10-20, HEAD a6984b4)

`.lore/validate-history.jsonl` is written by every `validate --execute` (one
record per registry entry, 14 per run) and read by `consult`, `compile` and
`audit`. Three things to know before touching or trusting it:

- **`audit` reads it once PER CLASS.** `_audit_rows` (`lore/__main__.py:560`)
  loops the registry and calls `last_local_validation` (`lore/validate.py:1194`)
  per class; that function `readlines()`s the WHOLE file and `json.loads` every
  line. So audit's cost is `classes x rows`: measured on this repo's own ledger
  (3,161 rows / 878 KB / ~176 rows/day) audit is **144 ms**, **1.06 s** at
  31,610 rows and **9.56 s** at 316,100 — linear, unbounded, no rotation knob
  exists. `consult`/`compile` call it once and stay ~55 ms. Board row: PERF-2.
  - Before optimizing it: the semantics are **newest record wins by FILE
    ORDER** (last matching line), NOT `max(timestamp)`. Probing that is 4
    commands — clean-then-drifted ⇒ `stale`, drifted-then-clean ⇒ `proposal`.
- **A ledger record is not attestation.** It never sets `last_validated`
  (`show`/`audit` still print `no data`); only `consult` surfaces it, labelled
  "local history, not operator attestation". The ledger is per CWD, so a fresh
  clone starts empty and every class honestly reads `proposal`.
- **The `unclassified` bucket gets a record too.** It has zero checks
  (`audit` marks it `"bucket": true`), so its row is `total_checks: 0` /
  `outcomes: []` while the label still says "commands parse and answer on the
  live system" — 225 of this repo's 3,161 rows are that record. Board row:
  LORE-066.

## The count-sync guard has a self-reference blind spot (run 14)

`scripts/count_sweep.py:102-103` exempts an entire LINE from the test-count
family as soon as it contains `scripts/test-count.txt`. The dev-loop line above
both quotes that file AND asserts a number — so it is the one line the guard
cannot check, and it has now gone stale twice (463 → 510 → 523). Verify by
hand whenever you touch that line: `pytest -q` vs `cat scripts/test-count.txt`
vs the literal. Board row: LORE-063-R2 (recurrence of LORE-063).

## `lore audit` answers a REGISTRY question, not a coverage question (run 14b, 2026-10-20, HEAD `6de0660`)

Read this before you quote `lore audit` to anyone as "coverage".

`lore audit` prints **one row per compiled registry class** — that is exactly what its own docstring says
(`lore/__main__.py:616`) and what the README's Shipped bullet says ("per **registry class**"). The rows are built by
`compile_all()` (`lore/__main__.py:583`), the class list is the literal `SEED_CLASSES` tuple
(`lore/classes.py:38`) plus the `unclassified` bucket, and the runbook bodies are the literal `_CHECKS` table
(`lore/compiler.py:76`). Consequences worth knowing before you rely on it:

- `summary.total_classes` is the **size of that tuple (14)**, not a count of classes the fleet actually hit. It is
  14 whether this box has seen zero incidents or ten thousand.
- `runbook_compiled` is the literal `True` (`lore/__main__.py:592`) — it can never print `False`, so "a class with
  incidents but no runbook" is **unreachable in this output**. Do not present the column as a gap detector.
- There is **no incident input** at audit time. Proven by running it from an empty directory: identical 14 rows and
  identical summary with no repository, no `.lore` ledger and no incident data. The only history-driven field is
  `status`/`stale_reason` (the `LORE-064` wiring) — which is why the matrix can look live while the coverage half
  is a constant.
- The trail parser exists (`parse_logsey_export`, `lore/__main__.py:461`) but only `lore absorb --window` uses it,
  on a **caller-supplied** trail; it feeds proposals, never coverage.

The fields that ARE honest and must stay that way: `last_validated` reports `"no data"` until a human attests (no
code path writes it — a lint run is not attestation), and the `summary.note` says so. So use audit for what it
measures — which registry classes exist, how many checks each carries, and whether the local lint has flagged
drift — and do not use it as evidence of incident coverage. PRD `US-3` / `SC-2` promise the incident-coverage
reading; that gap is filed as **`LORE-067`**.

Cost: cheap. Warm `lore audit --format json` ≈ 0.11 s on the control box (and ≈ 48 ms with no
`.lore/validate-history.jsonl`); it grows with that ledger — see the ledger-cost section above and `PERF-2`.
