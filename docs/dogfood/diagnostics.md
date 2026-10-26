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

## Run 4 — the 3 a.m. drill, the library consumer, and all three install paths (2026-10-01, HEAD f60974c)

**Angle.** Runs 1–3 fed lore tidy symptom phrases. Run 4 pasted raw log
tails the way incidents actually arrive, drove the library from an external
consumer for the first time, and repeated the fresh-machine leg across ALL
THREE documented install paths (uv sync / pip fallback / uv tool install).

**What the drill taught.**

1. **Signature-bearing tails classify near-instantly and honestly.** Drain
   503 tail: 0.90 with signature + 5 keywords in 65 ms. Cooldown tail: 0.90.
   The evidence echo and the honesty labels held under ugly multi-line
   input — `--explain`, `consult --failure` (full 7-check runbook appended),
   and the `absorb --window` sweep (6-line logsey-contract trail → 3
   per-class proposals + 1 honest `unclassified`, `--source` threaded) all
   behaved as documented.

2. **The registry's vocabulary blind spot is now the recall bottleneck
   (LORE-041, LORE-043).** Git's canonical collision error ("Your local
   changes … would be overwritten by checkout / Aborting") shares ZERO
   vocabulary with `shared-checkout-collision` — and the near-miss echo
   ranks `secret-env-clobber` FIRST on the word "overwritten", pointing the
   responder at the wrong family. The same gap reaches the integration
   surface: a title carrying 3/8 collision keywords misses
   (`KEYWORD_THRESHOLD=0.6`, `lore/classifier.py:27`) and fail-open exit 0
   turns that into silence for the tick-start flow. The lesson matches
   LORE-016/023 but is sharper: this is not a *stranger paraphrase*, it is
   the CANONICAL error text of the fleet's most recurring incident class.

3. **Library consumer friction is small and known-shaped.** The one trap:
   `Classification` has no `near_misses` attribute — near-misses are a
   separate `near_misses(text)` call (`lore/classifier.py:248`). A first
   consumer guesses wrong exactly where the CLI looks richest (AttributeError).
   Same naming-split family as LORE-021 (`raw_score` vs `score=`); recorded
   as cross-evidence there. Everything else imported and ran as documented:
   `classify`, `classify_all`, `near_misses`, `compile_class` — 3 tails
   triaged, runbooks compiled, in 6 ms total.

4. **The flagship runbook carries the doctrine.** `lore show
   gateway-drain-window`: 7 ordered checks with healthy-vs-incident output,
   decisions, and DATED incident evidence (SIGKILL/214 in-flight 2026-08-14;
   queue_depth=14 loss 2026-09-05; 25–30 min drain window 2026-09-16). The
   recovery ladder IS the fleet's real doctrine (batch, pause-first,
   announce, never SIGKILL). The only blemish is the LORE-024 placeholder
   class — and run 4 adds: `consult --failure` prints that placeholder to
   the operator as the literal command to run.

5. **All three install paths pass fresh — the gap is one prerequisite
   sentence (LORE-044).** Fresh Debian 12 (Python 3.13.5, no uv, no unzip):
   anonymous clone 4 s (LORE-018's public flip proven end-to-end), uv
   bootstrap from the GitHub release tarball 4 s (the uv docs' curl-piped-
   to-shell installer is unusable on gated surfaces), `uv sync --extra dev`
   5 s, pip fallback 15 s, `uv tool install` 2 s; 353 tests in 2 s; headline
   matches correct on the bare box; unknown class exits 2 with the known
   list. What the docs never say: how to GET uv, and that bare Debian lacks
   `unzip` (needed by `uv self update`).

**Multi-tenant-box lesson (environment, not lore).** The bunker host's /tmp
is shared across agent users: a sibling agent owned `/tmp/pip.log`, so my
first pip-fallback attempt died on `Permission denied` AND my `tail` read
the sibling's log (a PEP 668 message from someone else's run). Every scratch
file on a multi-tenant box belongs in `$HOME`. Separately, kara-level ssh to
all bunker boxes currently rejects `id_ed25519_bunker` (key regenerated
2026-09-30 22:29, new pubkey never installed host-side); the agent leg is
unaffected (per-spawn keys) but the root-rescue path is dead until the key
is re-installed.

**Right way recap for run 4 (for the next agent).** Paste tails, not
paraphrases; read `--explain` bottom-up knowing the ranking is raw keyword
fraction, not relevance; wire integrations to `--failure`/raw text, not
titles; and when a fresh-box check fails on a multi-tenant host, check file
OWNERSHIP in /tmp before debugging the project.

## Run 5 — fix verification at HEAD + the operator surface (2026-10-01, HEAD 4265973)

Run 5 is the same-day repeat. Per the repeat-run doctrine it first audited run
4's claims (integration doc committed at 3eb36c7; LORE-041/044 closed by the
foreman in c16116f) and then verified the fixes as a USER: git's canonical
collision text now hits shared-checkout-collision at 0.90 with a clean
near-miss list, and INSTALL.md's new "Installing uv" section was followed
verbatim on a truly fresh bunker box (bunker-las-01 agent 23ada9bf; designated
bunker-las-03 rejected the agent key — its skip row is on the board). Anonymous
clone, uv bootstrap + `uv sync --extra dev` in 11 s, 364 tests + ruff green on
the fresh box.

The new surface was the operator side: run `lore validate --execute`, then ask
what survived. Answer: nothing — consult/compile still say "never validated" a
minute after a fully green lint on the same box (LORE-045). The lint result is
stdout-only; the RUNBOOK-STORE two-homes design already names this disease for
runbooks generally, and lore's own validation output is its first victim.
Also filed: the confident-match output prints the unclassified 0.00 line under
a 0.90 hit (LORE-046) — two answers on one screen.

**Right way recap for run 5:** verify closed rows at HEAD, not via the suite;
the same-day bunker exemption needs an UNCHANGED repo — HEAD moved 3 commits
past run 4's leg, so the fresh box ran again; when the designated host
refuses the key, probe siblings and substitute rather than skip.

## Run 6 — 2026-10-04 (gate/closure loop + run 4/5 fix verification)

Ran the closure surface as the primary workflow for the first time: gate
(ALLOW/DENY probes incl. --record opt-in persistence), absorb (class
proposal + --window trail sweep, both the parse and explicit-empty paths),
consult (failure mode + tick-start + fail-open), then fix-verified LORE-045
(validate --execute → consult now carries the local-history lint timestamp
with an honesty label while show/audit keep last_validated=no-data for
operator attestation) and LORE-046 (unclassified noise line gone on
confident matches) at HEAD main d034465. PyPI get-h3-lore still 404 —
QA-LORE-4's closure remains process-state, and the gate ALLOW verdict with
--ref QA-LORE-4 --source dogfood-run6 in the integration report is the
closure artifact the foreman can act on. Warm match 40–50 ms; no PERF row.

## Run 7 — 2026-10-13 (closure→audit-record round trip + lint persistence on fresh machines, HEAD fdfcea5)

Angle untouched by runs 1-6: the full closure→persist→re-read loop as primary
surface, plus LORE-045's validate-history persistence re-proven on machines that
had never run lore (fresh consumer clone; fresh bunker-mvp box via agent lore-df7).

How the pieces actually fit (the mental model a new agent needs):

1. **The loop is consult → match → show/compile → validate (plan→execute) →
   gate --record → absorb proposals.** Everything is stdout-only except two
   writes, both local and both the point of the loop: `.lore/validate-history.jsonl`
   (appended per CWD by `validate --execute`) and the gate's `--record PATH`
   audit row (ALLOW only; a DENY appends nothing). "Propose-not-write" holds
   everywhere else — the registry is never mutated by any verb.
2. **The two persistence files answer different questions.** validate-history
   answers "did the commands still run on THIS box" (consult surfaces it with
   the 'local history, not operator attestation' label); gate --record answers
   "who approved closing this finding and when" (auditable JSONL). Neither
   touches the registry; neither fabricates a date.
3. **Errors hit, and their meaning:**
   - `$?` after `… | head` reads head's status, not lore's — pipe reads grade
     the wrong element; check exit codes directly (`lore compile --class x;
     echo $?` → 2 for the closed registry, correctly non-zero).
   - `uv run pytest` after a bare `uv sync` fails with lore's own guard message
     pointing at `uv sync --extra dev` — good UX, not a defect.
   - bunker timing stamps written as `~/t0` read back as `$HOME/t0` mismatch —
     scratch-leg hygiene, not a lore defect; the leg timings survive via per-leg
     probes.
4. **Fresh-box install contract re-proven end-to-end**: clone → uv tarball
   installer → `uv sync --extra dev` → 415 tests + ruff clean → first match
   0.14 s. The las bunker family (03/02/04/01) was offline; bunker-mvp
   answered with bunkerd active — host substitution per the ephemeral-leg rule,
   agent destroyed + residue census unchanged.
5. **Findings**: LORE-049 (guard-failure vocabulary falls between
   guard-degradation/secret-env-clobber/gateway-guard-violation — the fleet's own
   most common guard text consults to no runbook), LORE-050 (placeholder checks
   have no operator fill-in guidance; the lint history's drifted_orders=[] can
   mean "all template-skipped" — env-absent label doesn't say how few checks ran),
   LORE-051 (audit's aggregate status hides that `unclassified` is a bucket, not
   a class; 14 vs 13+1 for scripted counters).

## Run 8 (2026-10-13) — the machine contract

Run 8 asked the question a script asks: do the `--format json` surfaces agree
with each other, and do exit codes mean what a pipeline consumer assumes?

**What the contract family is.** lore exposes the same runbook data through
three JSON producers — `audit` (all classes, counts + freshness), `show <c>`
(one class, full runbook), `compile --class <c>` (same, as a list-wrapped
proposal). They are generated from the same compiled structures, and the run
proved it: stripping provenance/evidence_trail and canonicalizing, `show`
equals `compile[0]` byte-for-byte, and `audit`'s per-class check/command
counts agree with both.

**How the equality was nearly faked.** The first parity probe compared
drain-window's `show` against secret-env-clobber's `compile` (wrong class —
the tester grabbed the wrong fixture file). The diff was huge and real
looking; the "defect" was tester error. Lesson: a parity probe must pin BOTH
sides to the same fixture before believing a diff.

**The exit ladder is honest where probed.** Unknown class → 2 everywhere
(compile, gate absorb); gate ack → 0; consult unmatched → 0 with 'no matching
runbook' (fail-open by design); DENY → 1 with every violation listed. All
statuses were read with a direct `$?` after the command, never through a
pipe (PIPESTATUS trap).

**Where the contract frays: two edges, two rows.**
- `validate --execute` shells out via /bin/sh and treats exit 1 from a
  missing file the same as lint drift: 5/13 curated classes flip 'stale' on
  the project's own working box. The schema already has an `env_absent`
  outcome — it was [] in every class. LORE-052.
- `absorb --window`'s fail-closed error (rc=2) is identical for unrelated
  noise and for a real export missing its fence, and neither variant states
  the accepted shape (fenced block + bare-ISO lines — documented only in
  skills/lore-usage). LORE-053.

**Why run 8 exists.** Runs 1-7 proved humans can use lore; run 8 proved
machines can. The remaining friction is not correctness — it is that two
error paths teach the internal state of the tool instead of the contract.

## Run 9 (2026-10-17) — the fresh-machine delta: where the four fixes meet a box that isn't the dev box

**What changed under it.** Runs 1-8 rode the control checkout. Run 9's premise was the
opposite: HEAD had moved 69 files since run 8, including four user-visible fixes and one
compiler optimization — the interesting question was what those surfaces do on a box
that didn't build them. The leg used the fleet QA battery (fresh-install wheel, act CI,
upgrade, chaos cells) on bunker-mvp, then a hand-driven smoke of exactly the four fix
verbs on the SAME fresh agent, and a `bench.py` A/B across a worktree split at the
PERF-1 boundary.

**The mechanism that bit (LORE-057) is one line of Python, and it teaches a general
lesson about "green on my box".** `scripts/check-test-count.sh:33` collects the live
test count via `python3 -m pytest --collect-only`. The test that wraps the guard
(`tests/test_count_guard.py::test_shell_guard_flags_and_clears_stale_class_count`)
spawns the guard and asserts rc=1 on stale class-count prose. On the dev box,
`python3` on PATH *is* the project venv (uv front-loads it), so the child collect
succeeds and the assertion about drift is reached. On the bunker agent, the QA battery
calls pytest by its absolute venv path and never touches PATH — so the guard's child
`python3` is the system interpreter with no pytest, the count line comes back empty,
and the guard exits 2 with the most honest message in the repo: "could not determine
live test count (... guard misconfigured, not drift)". The test then fails on
`2 == 1`. The A/B (evidence run9/diag4.log) proves the guard is right and the test's
environ is under-specified: same scratch copy, `PATH` sans venv → rc=2; `PATH` with
venv → rc=0, "PASS: canonical=473 matches live=473". Fix direction: NOT more venv
assumptions in the docs — make the test inject the interpreter it's already running
under (sys.executable via env PATH prepend) so the box that proves the drill doesn't
need the dev box's lucky PATH.

**The fresh box also taught what "install" means now.** The fresh-install cell
installs the WHEEL (`get-h3-lore-0.1.2`), which carries no test suite — and the
battery's chaos-disconnect cell therefore had nothing to cut: disc.log empty,
cell graded UNVERIFIED with an explicit vacuity marker (LORE-058). On 10-04 the same
cell graded INFO "passes with network cut (no network dep)" because the install then
still put pytest in reach. Nothing failed; the *coverage* silently moved. The row
packages both fix directions: grade the shape N/A honestly, or make fresh-install
keep the dev extra so the disconnect cell cuts a real suite again.

**What real use re-proved without new rows.** Every fix contract held on BOTH boxes
(--class tri-state; consult exit-2 missing-input with fail-open intact; round-2
finding-list signatures incl. bare 'secrets detected in diff' and git-canonical
collision phrases; gate --record parent creation with DENY arms writing nothing).
PERF-1's dataclasses.replace clone held under equal-load A/B: compile_all_registry
158.63 → 81.94 µs/op (1.94×, bench.py --number 200 --repeats 3, pre-worktree
0bf0220 vs HEAD 9b97fa2). LORE-051's audit-bucket premise re-confirmed at the byte
level (unclassified still appears as a 14th class row; `total_classes: 14`). The
exit ladder re-swept honest on the two verbs the delta touched (match --class,
consult early-guard).

**Operator errors worth their ink (each one a real-user shape):**
- `show --class X` exits 2: show's class is POSITIONAL while match/consult take
  FLAGS. A user fluent in one verb's form gets the other wrong; --help answers it
  in one read.
- `consult --failure` takes the failure TEXT, not a path. The battle rhythm is
  "point at the log"; the contract is "inline text". For a one-class CLI that
  fail-opens rather than crashes, a PATH in --failure = silent no-match where a
  fresh user expects their file to be read. Worth a UX row some day, not a defect.
- `gate absorb` needs no --reason — class+lesson is the veto pair; no-new-lesson is
  the ack pair. Enforced in lore/absorb.py, not in --help prose.

**Why the verdict is SHIPPABLE anyway.** Three of the run's four defects found were
one-P3 flat (count-guard PATH, chaos-disconnect vacuity, P4 ruff-pin note) and the
fourth was a confirm (LORE-051 still open, standing). The product's core promise —
paste a symptom line, get an honest class, compile the runbook, gate the lesson,
show the work — held at every surface, on both machines, with every number quoted.
# Run 10 (2026-10-17) — the runbook text meets a sibling tool's real flag contract, on a box that didn't build any of it

**What changed under it.** Runs 1-9 covered lore's own verbs and the QA harness. Run 10's
angle was the thin one the battery can't see: lore's runbook EXPRESSIONS are shell
strings aimed at OTHER tools (logsey, git, curl, grep) — and a runbook is only as valid
as the real tool's contract on the day it runs. That premise held until the
gateway-drain-window class was driven on the live CLI.

**The mechanism that bit (LORE-060) is a drift between two siblings in the same fleet.**
The runbook says `logsey query --pattern 'drain 503' --since 30m` (twice: orders 1 and
7). The real logsey binary (on the same box, same PATH) says `logsey query "<sql>"` —
one positional SQL string, no `--pattern`, no `--since`. The result is that lore's
validate --execute grades the acceptance class `gateway-drain-window` "stale" because
THE RUNBOOK is wrong about its own fleet's tooling, not because the tool is missing.
The gate-colored check still runs — it just exits 2 and the freshness story reads
"stale check ↑ self-invalidated" where the underlying story is "runbook drafted from
an older/experimental logsey contract".

**Why the OTHER classes pass: the aggregate-mechanism question.** The bisect for
"the logsey runbook class failed" had to answer: is this a lore-side classifier bug, a
lore-side staleness mislabel, or a genuine drift in one runbook's text? A clean
committed clone gives you a CWD-keyed, fresh, no-.lore environment. From that shape:

- `shared-checkout-collision` → stale:no, env_absent empty. (No mobile runbook, no
  external tool in its orders.)
- `fast-forward-push-reject` / `docs-count-drift` / `worktree-reap-data-loss` →
  all stale:no, env_absent empty. (Also git/grep/curl-wc-shaped.)

None of these grue anything; lore's classification engine is fine. Only the
logsey-angled runbook text is stale. The "stalebynvironment vs stale-bydrift" framing
(LORE-061) came from the same bisect on the OTHER side — a bare bunker box, where every
tool is legitimately absent, produces the SAME "stale" name on the same class for a
legitimately DIFFERENT reason, and nothing in the plain-text runbook or the table says so
(the data layer names `env-absent` correctly; the render layer doesn't).

**The other mechanism run 10 added to this file is more boring and more permanent: a
documented install path, measured as a system.** The battery's fresh-install cell proves
the WHEEL is installable. It doesn't prove a user following docs/INSTALL.md gets a
working tool in a bounded time. Run 10's hand leg (clone from GitHub with anonymous
https, bootstrap uv from the astral-sh release tarball, `uv venv` + `uv pip install`,
first match) completed in box-seconds — the uv tarball download (~2m) dominates a
first-touch run; after that the whole path is seconds. Everything graded green, which
means the documented path is honestly documented as of HEAD 9b97fa2, on this date, on a
3.12.3/uv-0.36.0/Debian box.

**Preceding runs' lessons that run 10 hit again.** Run 9's skill updates (argument-form
map, fresh-box truth) were load-bearing mid-run: `--class` vs positional class, `--help`
before scripting a battery, the PATH assumption for pytest. Run 10 also hit, and tested
live, LORE-052's shape (5/13 classes still stale-by-environment) on the fresh box: 14/14
classes emitted honesty_label `lint-verified... does NOT prove recovery succeeds` on the
first .lore history created there.

**What should outlive this run in how future dogfooding of lore works:** a runbook-compilation
tool's acceptance criteria must drive the runbook's OWN quoted invocations against the real
siblings, not just parse them. The `validate --execute` signal is honest — it correctly says
"the runbook is stale" — but "stale" is a TOOL-side verdict that needs a reason rendered
(LORE-061), and the fleet's runbooks embed contracts that drift with sibling tools
(LORE-060). Neither is a fixture problem. Both are the product's real subject matter:
a runbook that doesn't run is worse than no runbook, and lore now proves it twice.

---

## Run 14 (2026-10-20, HEAD `a6984b4`) — the ledger stops being free, and what a "fresh box" actually proves

Run 14 is the first perf-shaped dogfood pass since PERF-1, and it found the
product's first *scaling* cost. Two mechanics are worth keeping.

### The cost is a loop shape, not a slow function

Everything lore ships reads the same local file: `.lore/validate-history.jsonl`,
one JSONL record per class per `validate --execute` run (written by
`persist_validate_history`, `lore/validate.py:1147`; read by
`last_local_validation`, `lore/validate.py:1194`). The reader is written the
honest, simple way — open the file, `readlines()`, `json.loads` every non-blank
line, keep the last record for the requested `class_id`. On its own that is
fine: `consult` and `compile` call it **once**.

`lore audit` calls it **once per registry class** (`lore/__main__.py:604`,
inside the `_audit_rows` loop at `__main__.py:560`). So audit's cost is
`classes x ledger_rows`, and the ledger grows by 14 rows per lint run — the
fleet's own battery writes ~176 rows/day on this box. The profile is
unambiguous: 14 `readlines()` calls and 44,254 `json.loads` for a 3,161-row
ledger; 442,540 for 31,610 rows, with `last_local_validation` at 1.974 s
cumulative of a 1.998 s audit. Measured wall time tracks the row count almost
exactly: 144 ms → 1.056 s → 9.564 s at 3,161 → 31,610 → 316,100 rows.

The lesson for a future fixer, and the reason the row carries acceptance
criteria: **the read path's semantics are "newest record wins by FILE ORDER"**,
not `max(timestamp)` — the scan keeps the last matching line. The 4-arm probe
(`docs/qa/evidence/run14/freshness-arms.txt`) pins it: clean-then-drifted ⇒
stale, drifted-then-clean ⇒ proposal. An obvious "optimization" to a
timestamp comparison (or to `dict`-insertion with `max()`) would silently
change which record decides freshness.

### A "fresh agent" is fresh in exactly one dimension

The install leg drove the documented quickstart on a deleted-on-teardown
bunker agent, with three findings about reading such a box honestly:

- **Preserved mtimes are not provenance.** `~/.local/bin/uv` on the agent
  carried mtime `01:01` while the agent itself was born at `08:07` — the
  release archive's own timestamp, preserved through extraction. Reading the
  file mtime alone suggests "uv was pre-installed hours ago"; reading the
  *directory* mtime (`08:09:39`, my installer run) plus the leg's own census
  (`command -v uv` ⇒ ABSENT before it) settles it correctly: uv arrived during
  this leg, from the documented installer.
- **A hard-coded third-party version in a leg script is a leg artifact, not a
  product finding.** The first leg failed at `curl` with a 404 because the
  script pinned a uv release tag that does not exist; every later stage
  cascaded to rc=127 (`uv: command not found`). The correct framing — kept in
  the run's evidence rather than buried — is that the *product's* documented
  path (installer, then `uv sync --extra dev`) was then driven as written and
  passed, in ~4 s of box time.
- **A documented installer can be complete and still surprise a
  non-interactive shell.** `curl -LsSf https://astral.sh/uv/install.sh | sh`
  exits 0 and appends a PATH line to `~/.bashrc`/`~/.profile`; a login shell
  finds `uv`, a bare `ssh host 'cmd'` shell does not. Not a lore defect (and
  INSTALL.md points at the installer, whose own output names the PATH step) —
  but it is why a leg script must run its own census rather than assume the
  documented command's preconditions.

### What changed in the delta since run 13 — and what that says about the board

Three of the four commits landed since run 13 (`c1ac048` bucket marker,
`c63b82d`+`c9a0eb4` freshness wiring, `f50478b`/`deb398a` absorb error text)
are visible to a user in this run's transcript, and the fourth (`cfc8f9c`, dep
bump) is visible in the fresh box's `uv sync` output (ruff 0.17.1). The fixes
that runs 1-13 filed are being worked and are holding their contracts. The
board's own `boardctl validate` is red (3 errors, 42 warnings) from *older*
rows — two carry the out-of-vocabulary status `closed`, one events id descends
— which no lane has owned yet; run 14 left that alone and added nothing to the
count.

## Run 14b (2026-10-20, HEAD `6de0660`) — the coverage matrix has no incident input

Second angle of the same tick as run 14 (which covered the install path and the ledger's cost). This one drove the
PRD's User Stories as stories — `US-1`/`US-2`/`US-3`, which no earlier run had done (run 13 exercised `SC-1..SC-4`
and `US-4`). It found the product's headline mechanism missing rather than broken.

### The shape of the defect: a promised measurement with no data path

`lore audit` is documented as the *coverage* matrix (PRD `US-3`, `docs/PRD.md:28`): "every failure class seen in the
last 90 days … the classes with incidents but no runbook — coverage as a number, not a feeling", restated as SC-2
(`docs/PRD.md:63`) "runs on the fleet's last 90 days of incidents". What ships is an inventory of the shipped
registry, and the difference is visible in two lines of code:

```
lore/__main__.py:583   for rb in compile_all():        # the rows come from the compiled registry, nothing else
lore/__main__.py:592   "runbook_compiled": True,       # a CONSTANT — the "no runbook" gap can never print False
```

and the registry itself is a literal (`lore/classes.py:38` `SEED_CLASSES`, `lore/compiler.py:76` `_CHECKS`), so
`summary.total_classes == 14` is a tuple length, not a measurement over incidents. The discriminating probe is the
one worth remembering for the next audit-shaped target: **run the tool from an empty directory.** Same binary, no
repository, no `.lore` ledger, no incident data:

```
$ cd /tmp/<empty> && <venv>/python -m lore audit --format json    # rc=0, 14 rows
$ cd <repo>       && <venv>/python -m lore audit --format json    # identical 14 rows and identical summary
```

If a "coverage" report reads the same with and without every local data source, the report is about the code, not
about the system. The only history-driven field on the whole row is `status`/`stale_reason` (the `LORE-064`
wiring) — which is exactly why that wiring *looked* like the matrix was live.

### The ingestion exists, but only on the write path

`grep -rniE 'incident|duckbrain|logsey' lore/*.py` returns only literal evidence `detail` strings inside `_CHECKS`,
help text, and `parse_logsey_export` at `lore/__main__.py:461` — used by `absorb` on a **caller-supplied** trail.
So the trail parser is real; it feeds proposals (`US-2`), never coverage (`US-3`). A class the fleet actually hits
that is not in `SEED_CLASSES` folds into `unclassified` and cannot move any number. This is the trap the honesty
work around `last_validated` does not cover: the tool is scrupulous about the field it cannot fill, and silent
about the count it fills from a constant.

Related-but-distinct, and worth keeping apart when triaging: `LORE-064` (P1, fixed by `c63b82d`) was a signal that
*existed* and was left unwired — a reconnection. This one is `LORE-067`: a capability that does not exist — a
build. `LORE-065` (US-4 sync, P3) is the closest precedent for the grading.

### The board under the tool is red, and that baseline was unrecorded

A dogfood lane reads the board before it reads the product, and this one could not get a green:

```
RESULT: FAIL (3 error(s), 42 warning(s))
  LORE-050 / LORE-054: status "closed" — outside the vocabulary, and not even a read alias
  events.jsonl line 177: id 176 after id 177 — same tick, same ts => intra-tick append order, not a bad id
```

Both pre-date the tick; neither is run 14's or run 14b's. The durable lesson is the **baseline discipline**: on a
board that is already red, "validate passes" is unavailable as evidence, so the run records the pre-append counts
(3/42), attributes only a positive delta to its own write (here: `+0` errors, `+0` warnings), and files the
pre-existing repair as its own row (`LORE-068`) instead of leaving the next lane to mis-attribute it.

### What this run measured, and what it deliberately did not

- Warm `lore audit --format json`: **0.11 s ×3** (`/usr/bin/time -p`). Run 14's hyperfine on the same command:
  144.2 ms ± 15.7 ms with the repo's 3,161-row ledger, 48.3 ± 2.5 ms with none. The 0.11 vs 0.144 s spread is
  method and load, not a regression — the same code, unchanged across `a6984b4..6de0660` (docs/board only).
- **No PERF row.** The ledger cost is `PERF-2`'s (run 14, same tick); re-filing it would be a duplicate row. The
  row for the incident input carries an explicit warning that fixing it must not deepen that loop.
- Nothing was re-driven that run 14 drove; its staged probe scripts under `docs/qa/evidence/run14/` were left
  staged and uncommitted, and every commit here is path-limited.

## Run 14c (2026-10-20, HEAD `29bdbef`) — the scribe is wired to "new", never to "update"

Third angle of the same tick (run 14: ledger cost + install-as-written; run 14b: the audit matrix has no incident
input). This one drove **PRD US-2**, the post-incident scribe, as a user story — and found the same *shape* of
defect as `LORE-064`, on the other half of the product: a mechanism that exists, is tested, and is unreachable from
the surface the docs describe.

### The mechanism is real, the wiring is absent

`lore/compiler.py:993` implements a genuine runbook **diff** — `action: "new" if existing is None else "update"`,
plus `changed`/`removed` computed by comparing signature, checks-by-order, ladder, guardrails and evidence trail.
Its unit tests exercise the update branch (`tests/test_compiler.py:182/200/213` pass an `existing` runbook).

In production, nothing ever passes one. `grep -rn 'propose(' lore/*.py` returns a single call site —
`lore/absorb.py:175`, `payload = propose(class_id)` — and `grep -rn 'existing=' lore/*.py` returns nothing at all.
Both user surfaces go through that call: the `--window` sweep via `absorb_sweep` (`lore/absorb.py:214`) →
`absorb_proposal` (`:162`), and the single `--class/--lesson` path directly. So the answer to "can `lore absorb`
produce an update?" is no, and the answer is one argument long.

The observed consequences, which is how this was caught rather than inferred: every proposal from a real six-block
trail carries `action: "new"`, `removed: {}`, `changed: {}`, and an `added` body equal to
`lore show <class> --format json` (verified with `jq -s`, `true`) — for `gateway-drain-window`, a curated class with
seven checks. The CLI's own help calls the subcommand a "runbook-**update** PROPOSAL" and `--class` "existing
registry class to propose an update **for**"; both sentences describe a capability the call graph cannot reach.

### The second half is the trap for the fixer

`propose()` builds its fresh side with `fresh = compile_class(class_id)` (`lore/compiler.py:1000`) — from the curated
registry only. The swept trail is parsed, classified and preserved (as `sweep.evidence`, one entry per block), but it
never touches the runbook being compared. So an "obvious" fix — pass `existing=compile_class(class_id)` — would flip
the label to `update` and ship an **empty diff forever**, which is worse than today's honest `new` because it claims
an update that contains nothing. The row states both halves and requires the fixer to say which one they did; the
general lesson is the one worth keeping: *when a mechanism is unwired, check whether its INPUTS reach the comparison
before endorsing the reconnection.*

### What the run measured, and why it filed no PERF row

`absorb --window` warm 49.7 ms ± 1.9 (hyperfine, 12 runs), with the six-block trail; the single-proposal path
46.7 ms ± 4.2; cold 0.08 / 0.07 s. Both sit at the interpreter-startup floor (~45 ms), so the trail work is ~4 ms.
There is no number here a user could feel, and saying so is the correct result — the scaling defect in this product
is the *audit* path's (`PERF-2`), filed by run 14 in this same tick, and re-filing a perf row for a floor-bound
command would devalue it.

### Method note for the next scribe-shaped target

The whole finding came from driving the documented example verbatim and then asking one question of the payload: not
"did it run" (it did, rc=0, three well-classified proposals) but "**does this object contain what its own promise
says it contains**" — an update for a class that has a runbook, evidence from the window, dead ends marked. Reading
the payload against the promise is what surfaced a two-line call-graph gap that every green run had been hiding.

## Run 14d (2026-10-20, HEAD `b29cbf5`) — the documented responder example, and what "unclassified" costs at 3 a.m.

Fourth angle of the same tick (14: ledger cost + install; 14b: audit coverage; 14c: US-2 scribe). This one drove
**US-1**, the incident responder, with the story's own words — and found the defect in the *example*, not in the
engine.

### The mechanism is honest; the example is not

`lore match "spawn 503"` — the literal command in `docs/PRD.md:24` — returns `unclassified 0.00`. So does the story's
quoted symptom ("scheduler spawns 503-ing at spawn time"). The cause is the classifier's contract, not a bug:
`gateway-drain-window` is accepted on the signature `drain 503`, and the invented symptom shares exactly one token
with it while lending `spawn` to `spawn-hot-loop`, so the two classes tie at 0.17/0.17 — far below the 0.6 long-text
gate and the 0.3 short-text gate (`lore/classifier.py:34-59`). The interesting part for a future author of examples:
the tool's own `--explain` route names `gateway-drain-window` as the top near-miss, so the *engine* is pointing at
the right answer while the *documented invocation* prints only `unclassified`.

### Two lessons worth keeping

- **An honest negative is still the wrong answer when the docs chose the example.** The README teaches that
  `unclassified` means "the fleet has never seen this", and here that reading is false — the fleet has a 7-check
  runbook for the class the user is standing in. When the product's answer is deliberately absence-as-an-answer,
  the examples are part of the contract and deserve the same verification as the code path.
- **Check every ENTRY FORM for the same input.** The same symptom text that yields "no matching runbook" through
  `lore consult "spawn 503"` resolves the class through `lore consult --failure "spawn 503 while restarting"`. A
  responder's 3 a.m. experience therefore depends on which verb form they happened to type, and nothing in the
  example, the README bullet or the help text says which one to use mid-fire. When a surface has several entry
  points for one question, drive the input through ALL of them — the divergence is the finding even when one path
  is perfect.

### What was verified and left alone

The README's five documented example strings all reproduce byte-exactly (including the deliberate
`unclassified`), and US-1's other clause — "checks in order" — holds for all 14 registry rows (contiguous from 1,
ascending, and identical between `compile` and `show`). Classifier recall on paraphrases is a CLOSED family
(LORE-016 / LORE-023 / REVIEW-LORE-002 / LORE-043), so `LORE-070` is scoped to the documentation with the family
explicitly named as out of scope — filed as a doc row at P4 under Bane's doc-severity ruling.

### Measured, and deliberately not filed as perf

`match` 56.2 ms ± 4.1 warm (12 runs), `match --explain` 49.9 ms ± 3.5, cold 0.09/0.10 s — the interpreter floor, with
classification under a millisecond. There is nothing here to optimize and no user wait to report.

## Run 15 (2026-10-23, HEAD `da91c1e`) — the incident path LORE-067 wired, driven as a user

### What the fix actually is

`LORE-067` (closed by `96c7cc2` + `8f217c9`) added `lore/incidents.py` and one call in `_audit_rows`. The shape:

- `_find_events_path()` / `_find_board_path()` (`lore/incidents.py:47-74`) resolve
  `.coding-hermes/board/{events,tasks}.jsonl` against **`Path.cwd()` and `cwd.parent`** — no flag, no env var, no
  config. Missing file = `None` = "no incidents", still `rc=0`.
- `incident_classes()` (`:174`) windows the events file at `:203` (default 90 days), extracts `class_id` from event
  `detail` (JSON or embedded text, `:99-138`), and unions that with a board-task prose scan (`:141-171`) that has **no
  window at all**.
- Both signals can only produce ids the registry already knows: the regex is `_build_class_pattern(SEED_CLASSES ids)`
  (`:88-96`, `:240-246`).
- `_audit_rows` then does `is_seen = rb.class_id in seen_classes` and writes that value to **both** `runbook_compiled`
  and `incident_seen` (`lore/__main__.py:610-634`); `incident_count()` is called at `:611` and its result dropped.

So the fix wired the *presence* of a signal into a column that documented *runbook existence*, instead of adding a
column beside it. Before the fix the column was a constant `True` (run 14b's finding); after it, the column is a
different fact that happens to be false for most rows, in most directories, for the classes that are most obviously
covered.

### The probes that separate mechanism from defect

1. **CWD is the source.** Same HEAD, four directories: repo root (10/14 seen), fresh clone in a bunker box (same),
   empty dir (0/14), foreign fleet repo `get-h3/shim` (0/14 — 430 events, different vocabulary). A coverage number
   that changes with where you `cd` is not a coverage number.
2. **Control vs treatment on the class universe.** Fixture boards with one in-window event:
   `{"class_id":"gateway-drain-window"}` → `incident_seen=['gateway-drain-window']` (mechanism works);
   `{"class_id":"postgres-deadlock-storm"}` → `rows=14`, `incident_seen=[]`, novel id absent from the entire output.
   The discriminator is what makes this a defect in the *story* rather than a bug in the parser: the parser is fine,
   the universe is closed.
3. **Window law on the secondary signal.** One generic event + two tasks dated 2024 whose titles merely name class
   ids → two "incidents". Remove the tasks → none. Prose is a signal; the window is not applied to it.
4. **The tests that should have caught it.** `tests/test_cli_surface.py:85-88` asserts
   `isinstance(r["runbook_compiled"], bool)` — any bool passes — and `:95` accepts `"coverage_note" in r or
   r["runbook_compiled"] is True`. `tests/test_lore051_audit_bucket.py:130` records the change as a comment. 560
   green tests, zero assertions on the documented meaning of the column. When a fix rewrites a contract, the test
   that used to pin the contract is where the regression becomes visible — here it was relaxed instead.

### Errors hit on the way (mine, not the product's)

- `bunker exec <agent> --script <file>` mangled the script: the upload wrapper wrote
  `~/.bunker/exec-script.sh` and the shell reported `unexpected EOF while looking for matching '\''` (line 38 on the
  first attempt, line 28 on the second — different scripts, same symptom). The staged file was byte-complete
  (`wc -c` = 2376, `sed -n '24,30p'` correct), so the corruption is in the wrapper's own quoting, not the transfer.
  **Right way:** `bunker cp --server <s> <local> <agent>:<name>` then
  `bunker exec --server <s> <agent> -- bash -lc 'bash $HOME/<name>'`. Both of the failed attempts were dropped from
  the evidence; the leg that produced `fresh-box-leg.txt` is the staged-file run.
- One probe script's inline `python3 -c` summary had a list-comprehension bug (`string indices must be integers`) in
  the treatment arm; the arm was re-run with the file-based `jq` reduction before anything was recorded. The failed
  attempt is not cited as product behaviour.

### Right way to read audit today

Use `check_count` for "does a runbook exist", `status`/`stale_reason` for freshness, and treat `compiled` /
`incident_seen` as a **cwd-scoped, registry-closed incident hint** until `LORE-067-R2` / `-R3` land. Do not quote
`summary.total_classes` as fleet coverage — it is the size of a literal tuple.

Row ids for the fixes: `LORE-067-R2` (column semantics + tests), `LORE-067-R3` (novel classes invisible, prose
counted as incidents, incident count discarded), `DOC-8` (undocumented source path + the stale skill claim corrected
here), `LORE-068-R2` (board validator FAIL from a duplicate `foreman_note` key on `DOC-6`).
## Run 15b (2026-10-23): the scribe surface at the HEAD where LORE-069 shipped, and a fresh-machine battery

**Why this section exists.** Run 15 (same tick, first delivery, commit `f4e0599`) drove the audit
coverage surface end to end and left a full record above. This section is the tick's SECOND
delivery: it drives the surface run 15 did not — `lore absorb` after LORE-069's fix — and it adds
the one thing a coverage audit cannot self-certify, a full fresh-machine battery on a disposable
bunker agent.

**How the two records relate.** No finding here duplicates run 15's. This session independently
reproduced run 15's audit findings from its own clean clone (empty dir → 14/14 `compiled=False`
while `show` prints the runbook; a novel `class_id` yields no row; `coverage_note` invisible in
table/md) and recorded them as corroboration events **383** / **384** on `LORE-067-R2` /
`LORE-067-R3` instead of minting sibling rows. Two draft rows of its own on that surface were
deleted before commit, on the rule that one defect gets one row.

**The one new finding.** `absorb` is the only verb that answers an unknown class with a green
exit code:

| verb | input | rc |
|---|---|---|
| `lore match --class nope` | unknown class | 2 |
| `lore show nope` | unknown class | 2 |
| `lore compile --class nope` | unknown class | 2 |
| `lore absorb --class nope --lesson x` | unknown class | **0** |

`absorb` prints `{"error": "unknown class 'nope'"}` and exits 0, so a `set -e` consumer, a CI
step or a foreman loop treats a typo'd class as success. The usage skill's prose ("class must
exist", `skills/lore-usage/SKILL.md`) was already right — the exit code was not — and the caveat
is now written next to that command. Filed as `LORE-20261011` (P3).

**What held up, measured.** LORE-069's acceptance criterion is met in the documented window mode:
the real six-block trail at `docs/qa/evidence/run14c/trail-real.txt` yields three proposals, all
`action=update` with `added=1` (`gateway-drain-window`, `unclassified`, `gateway-guard-violation`).
A log-shaped `--lesson` folds into one block with `outcome="observed"`; a prose `--lesson` yields
an explicitly empty update with the text still carried in `lesson` — both honest, both as the
skill now documents.

**PERF-2 re-proof against the grown ledger.** The defect was filed at 3,161 rows / 144 ms. The
ledger is now 5,127 rows / 1.4 MB: `strace -f -e trace=openat` counts **one** open of
`validate-history.jsonl` per audit (14 before the fix) and also one at a synthetic 10× ledger
(51,270 rows); hyperfine gives 67.6 ± 7.4 ms (5,127) / 154.7 ± 4.8 ms (51,270) / 54.7 ± 4.6 ms
(no ledger) ⇒ ~1.9 µs marginal per row, linear, and 2.1× faster than the pre-fix number at a
larger corpus. No PERF row: 155 ms at 10× the real corpus is not something a user waits on. The
open-count is the load-independent discriminator; the wall numbers move ±10% on a loaded box.

**Fresh-machine battery (install leg), agent `96a5db78` on `bunker-mvp`, TTL 4 h, QA-HEAD
`f4e0599`, 20 evidence rows.** `fresh-install` OK (`get-h3-lore-0.1.2` wheel + deps),
`toolchain-bootstrap` OK (go 1.27.3, python venv, gcc/g++, node 22.15.0, compose+buildx),
`ci-pass` OK (`act`: 1 job green), `upgrade` OK (v0.1.0 tree → HEAD reinstall clean),
`chaos-resource` PASS (3 GiB cap), `chaos-errorpath` OK (rc=2 on a missing config);
`docker-deploy` / `chaos-shutdown` / `chaos-corruption` / `ui-probe` N/A by construction (no
compose file, no db/state files, no web UI). **One cell is UNVERIFIED and is reported as such:**
`chaos-disconnect` — `disc.log` was empty, so the network cut was never exercised; rc=0 there is
not a pass. That is the same vacuity `LORE-058` recorded, and the stale-fix question belongs to
the QA harness (`bunker-qa.sh`), not to lore; it is not filed as a lore recurrence because the
cited fix is in the harness's deploy path, which this run did not exercise. Agent teardown: destroy
reported failure, then the agent was GONE from the server list — teardown recovered, no residue
(confirmed by a follow-up `bunker list`).

**Rules this run re-confirms for the next reader.**
- A `--lesson`-shaped probe is not a trail probe: the single path can only fold a LOG-SHAPED line
  into a block. Grading "absorb ignores my lesson" from a prose lesson is a false red.
- `bunker-qa.sh collect` prints `rc=0` inside a pipeline even when destroy fails; the cell rows,
  not the exit code, are the verdict.
- The board validator's FAIL in this repo is pre-existing and row-tracked (`LORE-068-R2`): the
  baseline at HEAD is 1 error / 94 warnings, and this run's appends added 0 / 0.

## 2026-10-26 run addendum

ch:trace row=none:read-only-dogfood spec=docs/dogfood/2026-10-26-integration.md#promise test=562-passed-in-4.23s doc=skills/lore-usage/SKILL.md evidence=/tmp/lore-dogfood-20261026-124359 witness=lore-dogfood-2026-10-26-12-43-59 verdict=PROMISING-BUT-ROUGH:install-unproven-and-LORE-070-reproof commit=pending memory=/dogfood/2026-10-26-lore-dogfood-lane
