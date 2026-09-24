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
