# Dogfood integration report — lore, 2026-09-25 (run 3)

Tick: lore-dogfood-2026-09-25-11:02 -05 · HEAD at run: `3ab56f5` · verdict: **PROMISING-BUT-ROUGH** (this surface)

Third dogfood pass. Run 1 (09-24) covered the responder entry surface
(`match`/`compile`/`validate` plan mode) and install; run 2 (09-25 morning)
covered the scribe/auditor surface (`show`/`audit`/`absorb`/`gate`/`consult`).
This run took the angle neither touched: **the re-validation/anti-rot loop
("does it still run?") exercised on LIVE fleet state, plus the README's USER
install path (`uv tool install`) on a fresh machine.**

## Promise under test

> "lore turns the six greps into one runbook lookup — and answers **does the
> fix still run?** via the read-only command lint; the README's user can
> `uv tool install git+https://github.com/get-h3/lore` and get the tool."

The lookup half held again. The freshness half did not — not because the lint
lies, but because the docs promise a stamp the implementation deliberately
never makes (LORE-022).

## What was exercised, live (control host, HEAD 3ab56f5)

- **Installed-tool reality check.** The box had `lore v0.1.0` installed via
  `uv tool install` — exactly the README's user. It exposed **3 of the 8
  documented subcommands** (`show`/`audit`/`gate`/`absorb`/`consult` →
  "invalid choice", exit 2) and `lore --version` is unsupported (argparse
  error). No doc mentions that a tool install goes stale with HEAD or that
  `uv tool upgrade lore` exists. The user-visible lesson is now in the usage
  skill; the silent staleness itself is environment, not a code defect.
- **Documented upgrade path works:** `uv tool upgrade lore` → 0.1.0 → 0.1.1,
  cloned the now-public repo anonymously, exit 0. All eight subcommands
  appear afterwards. (The 0.1.1 bump exists precisely so this upgrade is not
  a silent no-op — verified working from the tool side.)
- **Plan mode stays honest:** `lore validate` (default) lists all 29 checks
  across 11 classes with `mode: plan`, `would_run[]`, `would_refuse[]` —
  executes nothing.
- **`lore validate --execute` — the anti-rot loop, first live run:**
  full-sweep outcomes **5 ok / 23 error / 1 refused**; 9/10 real classes
  flipped `stale` with per-check reasons. The lint is genuinely useful:
  `shared-checkout-collision` validated 3/3 green (its checks are plain git
  commands); every class whose checks carry `<placeholder>` paths or need
  `logsey` honestly reported why it could not answer. The full pass costs
  0.15 s wall (≈29 subprocess spawns) — see Performance.
- **The freshness contradiction (LORE-022, P1).** README.md:281 and
  `lore audit`'s own summary line say `last_validated` "is populated only by
  `lore validate --execute` runs". Measured: a full execute sweep AND a
  fully-green single-class run (`validate --class shared-checkout-collision
  --execute` → 3/3 ok) both leave `lore show` at "Last validated: no data
  (never validated)" and `lore audit` at "no data". Source confirms intent,
  not a bug: `lore/validate.py` — "apply_lint never sets last_validated and
  never moves status to validated — only an operator attestation may do
  that". The implementation is the honesty law working; the PROMISE is wrong
  in two user-visible places, and the auditor persona (PRD US-3) can never
  see a validated runbook on v0.1.x.
- **Classifier probes with 8 real fleet incident lines (LORE-023, P2).**
  Hits at signature 0.90: worker spin → spawn-hot-loop; chat-archive gap →
  ingest-backfill-gap; gateway-restart 503s → gateway-drain-window. Misses:
  "empty commit landed with my message but zero files" → unclassified with
  **near-misses: none** — a textbook shared-checkout-collision symptom whose
  seeded keywords (`index.lock, worktree, reap, sibling, collision,
  checkout`) share no word with the phrasing; "core.bare got flipped...pushes
  fail" → same dead end; "env clobber" → near-miss secret-env-clobber at
  only 0.17 (the bigram misses the seeded `.env clobber` regex). The
  LORE-016 `--explain` mitigation cannot suggest a class that scores 0.
- **Validator vs compiler disagreement (LORE-026, P3).** Two of lore's own
  seeded checks are refused by the default-deny gate: `grep --since-marker`
  (flag not allow-listed) and `git worktree add` (write-shaped — correct
  refusal, but the runbook emits it unchecked). The two halves of lore do
  not agree with each other.
- **Placeholder checks can never lint green (LORE-024, P2).** Every check
  carrying `<gateway-log-path>`-style tokens dies with `/bin/sh: Syntax
  error: end of file unexpected` — `<...>` parses as input redirection. 7 of
  10 real classes flipped stale with ZERO passing checks; only
  shared-checkout-collision can ever go green as authored. The per-check
  outcomes exist; the class-level stale rule (any error → stale) lets one
  placeholder poison six good checks.

## Fresh-machine install (ephemeral bunker, las-bunker-03, agent destroyed after)

- Agent `811bc7cb` (bare Debian, no uv preinstalled). **The README USER path
  — `uv tool install git+https://github.com/get-h3/lore` — was tested for
  the first time and works**: exit 0 in **3 s** after a **6 s** uv bootstrap
  (astral.sh installer — the step INSTALL.md does not document; the README
  says only "uv is recommended"). Anonymous public clone confirmed working
  (LORE-018's fix holds from a cold box).
- Fresh-box feature battery: `--help` (8 subcommands), `match "drain 503"` →
  gateway-drain-window 0.90, `match "key rotation expired"` → 0.90, full
  `validate --execute` (honest errors: logsey 127, placeholder syntax
  errors, and a new variant — `git status` exit 128 "not a git repository"
  flipping shared-checkout-collision stale on the bare box), `audit` table.
- Repository visibility untouched (hard rule). Agent destroyed
  (`DESTROY_EXIT=0`), key removed. Install script + log lived only in the
  agent's HOME; no tokens involved.
- The fresh-box lint staling everything is filed as LORE-027: the report
  cannot distinguish "runbook rotted" from "wrong box" — a scope note in
  INSTALL.md is needed.

## Performance (Step 2b)

hyperfine, warm, 20 runs: `lore match "drain 503"` (tool install) **46.7 ±
2.6 ms**. One-shot timings: full `validate --execute` sweep (29 checks, ~29
subprocesses) **0.15 s**; plan-mode `validate` **0.04 s**; `audit --format
json` **0.05 s**. Everything is comfortably fast and user-imperceptible —
no PERF row filed (a win nobody can feel is not a finding).

## Friction count

7 fileable touches (LORE-022 P1; LORE-023, LORE-024 P2; LORE-025, LORE-026,
LORE-027 P3 — LORE-025's stale skill text patched in-run alongside its row)
plus 2 unfiled cosmetic nits (no `--version`; stale tool install fails with
bare argparse usage and no upgrade hint). Everything else behaved as
documented on first use.
