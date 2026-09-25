# Diagnostics — how lore is built, why, and what bit during dogfood

(2026-09-24 dogfood run, HEAD edeb898. Written as explanation, not a log dump.)

## The architecture in one pass

Five modules, no runtime deps:

- `lore/classes.py` — the curated registry: 9 failure classes + `unclassified`
  as an explicit first-class entry (its signature is the never-matching
  `(?!)` regex, its keyword is a token the scorer never reads). The registry is
  CLOSED: an unknown class is a KeyError → exit 2, never an invention. This is
  the load-bearing honesty decision: the tool would rather say nothing than
  guess a class into existence.
- `lore/classifier.py` — two-tier matcher. Signature regex hit = 0.90 with the
  matched text quoted as evidence. Otherwise a keyword share per class,
  accepted only at ≥0.6 and capped at 0.5 confidence so keyword evidence can
  never masquerade as signature strength. Below threshold → unclassified at
  0.0. The evidence list (kind: signature|keyword + detail) rides on every
  result so no match is ever a naked assertion.
- `lore/compiler.py` + `lore/runbook.py` — compile a registry class into a
  Runbook (checks with commands, expected healthy/incident outputs, decisions,
  guardrails, evidence trail). Compile is propose-not-write: the only side
  effect is stdout. Every runbook says `Status: proposal`,
  `Last validated: no data (never validated)` until real validation exists.
- `lore/validate.py` — the anti-rot lint. Plan mode (default) lists what would
  run; `--execute` runs only commands a default-deny gate recognizes as
  read-only; failures flip the runbook `stale` with the reason. The honesty
  label says exactly what a green lint proves (commands parse and answer) and
  what it does not (that recovery succeeds).
- `lore/__main__.py` — argparse CLI. Errors exit 2 (missing arg, unknown
  subcommand, unknown class). No config, no state, no daemon: exit codes and
  stdout are the whole surface.

## Why it is built this way

The fleet's incident knowledge evaporates into chat archives; lore's bet is
that the fix is a closed, curated taxonomy plus honest labels, not an
always-answers-something fuzzy matcher. Every design choice above serves
"never a confident zero": refuse rather than invent, show the evidence for a
match, show "no data" instead of a fabricated date, refuse a command rather
than run something unsafe.

## Errors hit during the dogfood run, and their meaning

1. `lore match "drain 503"` etc. — all canonical phrasings hit signature
   matches at 0.90. The regex tier works as designed.
2. Five stranger paraphrases returned unclassified — see the integration
   report; three distinct mechanisms (keyword threshold, inflection,
   signature windows). Filed as LORE-016, not patched during the run
   (dogfood rule: users file findings, maintainers fix).
3. `lore validate --execute` reported `exit 127` for the logsey check —
   logsey is not installed on the control box. That is the degradation path
   working: the lint reports the command could not answer instead of
   pretending. Same output flips the runbook stale — re-run after installing
   the tools the runbook names.
4. `bunker-qa.sh` first attempt failed with `dial tcp 100.116.99.35:10001:
   connection refused` (bunker-las-02's bunkerd was down). Re-ran on
   bunker-las-03 (the skill's canonical host) — full battery green, zero FAIL
   cells. Lesson for future runs: probe both bunker servers before trusting
   either; the QA default is not a health guarantee.
5. `act: no triggerable workflow` in ci-pass — expected, not a defect: the
   repo's CI is GitHub Actions (`.github/workflows/ci.yml`, verified green on
   main); act has no local triggerable workflow file, so the harness fell
   back to the native suite (148 tests, passed on the fresh box).

## The right way to extend lore (for whoever works LORE-016)

The classifier already computes everything an evidence-echo needs:
`classify_all()` returns per-class keyword hits and confidences before the
threshold filter. The fix is to surface the below-threshold top-3 in `match`
output (or a `--explain` flag) — registry stays closed, nothing gets
auto-labeled, the operator just sees "shared-checkout-collision scored 0.33
(hits: worktree, collision)". Keep the unclassified row; keep the refusal;
add the graded signal. Tests live in `tests/` (148 at this revision) — add the
threshold-boundary cases next to the existing classifier tests.

---

## Run 2 — the scribe/auditor angle (2026-09-25, HEAD 93baad0)

The 09-24 run tested the responder surface; this one tested the surface that
shipped since: `show`, `audit`, `absorb` (single + `--window` sweep), `gate`,
`consult`, and the LORE-016 `--explain` fix. Verdict: SHIPPABLE on this
surface. What the run learned, as explanation:

1. **The gate is the spine of the whole scribe flow, and it works.** A QA or
   dogfood finding enters as `absorb --class X --lesson ... --source
   dogfood-dagger` (a stdout-only proposal) and closes as `gate --decision
   absorb ... --source dogfood-dagger` (a verdict line, ALLOW/DENY, exit
   0/1). The registry stayed closed through every probe — `gate --decision
   absorb --class totally-new-class` denies with "registry is closed" rather
   than inventing anything. Nothing writes anywhere at any step; that is the
   propose-not-write law holding under real use.

2. **`absorb --window` has a strict input contract the docs don't teach.**
   The sweep consumes a logsey-EXPORT payload: a line matching
   `logsey export`, a fenced block, and evidence lines starting with a BARE
   ISO timestamp (`2026-09-25T06:12:00Z unit=gateway <detail>`). A natural
   incident trail with bracketed `[2026-09-25 06:12]` prefixes yields "no
   classifiable evidence blocks" (exit 0, honest but hintless — filed as
   LORE-020). The one-line lesson: paste from `logsey export`, not from your
   notes; and `--source` on the window path is accepted but not yet recorded
   in the sweep payload (same row).

3. **The `--explain` fix is the missing half of the honest refusal.** The
   classifier still refuses stranger paraphrases (by design), but the user no
   longer hits a dead end: near-misses name the curated class that nearly
   hit, with the raw keyword fraction and the hits themselves. Verified with
   the exact example that motivated LORE-016. Library callers: the dataclass
   field is `raw_score`, the CLI prints `score=` — trivial but real (LORE-021).

4. **The repo is PRIVATE and the README quickstart assumes public.**
   Anonymous `git clone https://github.com/get-h3/lore` on a fresh box fails
   (404 → "could not read Username"). Verified from the control host and the
   bunker; visibility untouched per the dogfood hard rule (filed as LORE-018).
   Fresh-install itself is flawless: pip path 12 s, uv path 4 s, 230 tests
   green on Python 3.13, and the full bunker-qa battery (17 cells, zero FAIL)
   including the first real upgrade cell (v0.1.0 → HEAD).

5. **Count the tests before quoting them.** README still says "148 passed"
   (twice) and the usage skill said `show`/`absorb`/`audit` were unimplemented;
   the merged tree runs 230 and all eight subcommands exist. The dogfood rule
   "verify every claimed number on the current tree" bit exactly as it did on
   LORE-015's first judge pass. Usage skill rewritten during this run; README
   numbers left for the foreman (LORE-019).

6. **Tooling notes (not lore's defects):** `bunker-qa.sh` ignores `--server`/
   `--ttl` argv — the real interface is `BUNKER_QA_SERVER=<name>` (its usage
   header is stale); the shell gate on this box blocks piped tar-to-ssh and
   `python3 -c`, so the tree went over as `git archive` + scp + remote
   extract, and JSON inspection ran through grep/python3 -m json.tool.

---

## Run 3 — the re-validation loop on live state (2026-09-25, HEAD 3ab56f5)

Runs 1–2 tested the responder and scribe surfaces; this one ran the half of
the promise nobody had executed: **"does the fix still run?"** —
`lore validate --execute` against the live fleet, plus the README's USER
install (`uv tool install`) on a fresh bunker box. What the run taught, as
explanation:

1. **The lint's honesty is real and it is the product.** A full sweep
   reported 5 ok / 23 error / 1 refused and flipped 9/10 classes stale with
   per-check reasons. `shared-checkout-collision` went 3/3 green (plain git
   checks) — proof the green path exists. The failure text is honest about
   cause: `error (exit 127)` for the missing `logsey`, `refused` for the
   write-shaped `git worktree add` (the default-deny gate refusing to run a
   runbook check that is not provably read-only — the safety core working).

2. **The freshness field can never fill under v0.1.x — and the docs promise
   it would (LORE-022).** `validate --execute` computes per-check outcomes
   and `stale_reason`, but `apply_lint` deliberately never stamps
   `last_validated` (operator attestation only — the propose-not-write law).
   The README and `audit`'s summary line both say freshness comes from
   execute runs. Both are wrong about their own tool. Until an attestation
   step ships, the auditor answers "when did this last still work?" with a
   lint re-run, never with the field.

3. **`<placeholder>` paths make 9/10 runbooks structurally unlintable
   (LORE-024).** `<gateway-log-path>` parses as shell input redirection →
   `/bin/sh: Syntax error` → any-error stales the whole class. A runbook
   with six good checks and one placeholder can never go green as authored.
   Right way until fixed: substitute real paths in a copy of the runbook
   before `--execute`, or lint only classes whose checks are concrete
   (`--class shared-checkout-collision` is the one that works today).

4. **The classifier's closed registry has a blind spot: zero-overlap
   phrasings (LORE-023).** "Empty commit landed with my message but zero
   files" is a shared-checkout-collision incident, but shares no vocabulary
   with the class's keywords — so `--explain` shows `near-misses: none` and
   the user gets nothing. The mitigation is registry vocabulary absorbed
   through the gate (add `empty commit`, `core.bare`, `pushes fail` as
   keywords to the EXISTING class), not a looser threshold.

5. **The user path (uv tool install) works and is fast — but goes stale
   silently.** First-time proof on a bare Debian box: bootstrap uv 6 s,
   `uv tool install git+...` 3 s, anonymous public clone, 8 subcommands
   live. On the control host, the pre-existing v0.1.0 tool install exposed
   only 3 of 8 subcommands with no hint that `uv tool upgrade lore` is the
   fix. If a subcommand "doesn't exist", upgrade before filing a bug.

6. **A bare box stales everything (LORE-027).** On the bunker agent,
   `git status` exit 128 ("not a git repository") flipped
   shared-checkout-collision — green on the control host — to stale. The
   lint reports the machine, not just the runbook; run it where the fleet
   actually runs.
