# lore — dogfood run 15b (2026-10-23): the scribe surface after LORE-069, and an independent read of the audit after LORE-067

**Verdict: SHIPPABLE on the scribe surface, with one exit-code defect (LORE-20261011 P3).**
**On the audit/coverage surface this session corroborates the tick's first delivery (LORE-067-R2 /
LORE-067-R3 / DOC-8) rather than filing its own duplicate rows.**

This is the SECOND delivery of tick `lore-dogfood-2026-10-23-12-08-40`. A sibling session landed
the tick's main run-15 close-out (commit `f4e0599`, log entry `2026-10-23 (run 15)`,
`docs/qa/evidence/run15/`) at 07:24:15 local while this session was mid-legs. Read that record
first; this document only adds what the sibling did not drive, and states the split plainly.

## Promise under test (this angle)

> A post-incident scribe can turn "how we fixed it" into a runbook **update** proposal, and a
> runbook auditor can read `lore audit` to learn which failure classes the fleet actually saw —
> the two halves of PRD US-2 (scribe) and US-3 (coverage).

Runs 14/14b/14c/14d drove both *before* the wiring landed (LORE-067 and LORE-069 were filed as
gaps). This run drives them **at the HEAD where the fixes shipped**.

## Environment

| item | value |
|---|---|
| code under test | clean `git clone` of `/home/kara/get-h3/lore` at `da91c1e`, then re-checked at `f4e0599` |
| install | `uv sync --extra dev` in the scratch clone → 2.2 s warm cache, 34 packages, `.venv/bin/lore` 8 subcommands live |
| scratch | `/tmp/lore-df23/{src,empty,fleet,scale10}` — nothing under test was modified |
| install leg | `bunker-qa.sh launch` on `bunker-mvp`, agent `96a5db78`, TTL 4 h (see §Install leg) |
| evidence | `docs/qa/evidence/run15b/` (12 files, captured by a re-runnable script) |

## What held up (measured, not asserted)

### LORE-069 — absorb now emits real UPDATE proposals

The documented window mode, on the real six-block trail a prior run left behind
(`docs/qa/evidence/run14c/trail-real.txt`):

```
lore absorb --window 2h --trail-file docs/qa/evidence/run14c/trail-real.txt --source dogfood-run15b
→ gateway-drain-window      action=update added=1 changed=0 removed=0
→ unclassified              action=update added=1 changed=0 removed=0
→ gateway-guard-violation   action=update added=1 changed=0 removed=0
```

Three classes, three proposals, `action=update` with a non-empty `added` each — exactly LORE-069's
acceptance criterion. The blocked classes were classified honestly (unclassified reported, not
dropped), and nothing was written.

The usage skill's claim that a **log-shaped** `--lesson` folds into a block also holds:

```
lore absorb --class gateway-drain-window --lesson "2026-10-23T08:00:00Z source=gateway level=error gateway drain 503 while restart: 96 503s in window"
→ {"action":"update","added":1,"blocks":1,"outcomes":["observed"]}
```

and a PROSE lesson produces an explicitly empty update (`added={}`, `blocks=[]`) with the lesson
still carried in the payload's `lesson` field. That is the honest behaviour the skill now
documents; no correction needed.

### PERF-2 — the single-pass ledger fix is live and still linear at 1.6× the corpus

Run 14 measured `lore audit` at 144 ms with a 3,161-row ledger and profiled 14 full re-reads of
it. At HEAD, over the ledger as it has GROWN (5,127 rows / 1.4 MB):

```
strace -f -e trace=openat … lore audit --format json  →  opens(validate-history.jsonl) = 1
hyperfine -w 3 -r 12                                   →  67.6 ms ± 7.4   (5,127 rows)
hyperfine -w 2 -r 6  (10× ledger, 51,270 rows)         → 154.7 ms ± 4.8
hyperfine -w 2 -r 6  (no ledger)                       →  54.7 ms ± 4.6
```

One open at 10× too. Marginal cost ≈ 1.9 µs/row, i.e. **linear**; the corpus is now 1.6× larger
than when the defect was filed and the command is 2.1× faster than the 144 ms pre-fix number.
Nothing a user would wait on → **no PERF row**. (Method note: warm timings only; the box was
loaded, so absolute numbers move ±10% between runs — the open-count is the load-independent
discriminator and it is the finding.)

### Audit surface — independent corroboration, not new rows

This session reproduced the sibling's findings from its own clean clone before reading its
commit:

- from an **empty dir** `lore audit` prints `compiled=False` for all **14** classes, while
  `lore show secret-env-clobber` on the same binary prints `# Runbook: Secret / .env clobber` with
  2 checks (rc=0) — `runbook_compiled` and `incident_seen` are the same boolean on every row;
- a fleet-shaped scratch board carrying `{"class_id": "disk-full-on-host"}` (a class with an
  incident and **no** runbook) yields **zero** mentions of that id in any format;
- neither the table nor `--format md` renders any incident column, and `coverage_note` is
  `""` on all rows as soon as one class is seen; the 90-day window and the resolved source path
  appear in no output.

Recorded as corroboration events **383** (LORE-067-R2) and **384** (LORE-067-R3) rather than as
sibling rows. Two of this session's own draft rows on that surface were dropped before commit —
one defect, one row.

## The finding: `absorb` accepts an unknown class with a green exit code

```
match  --class nope → rc=2
show   nope         → rc=2
compile --class nope → rc=2
absorb --class nope --lesson x → rc=0      ← prints {"error": "unknown class 'nope'"}
```

Every sibling verb treats an unknown class as a hard error (exit 2). `absorb` prints the error
object and exits **0**, so a script (`set -e`, CI step, foreman loop) reads a typo'd class as
success. The usage skill says "class must exist" — the prose is right, the exit code is not.
Filed as **LORE-20261011 (P3)**.

## Install leg (fresh machine)

`bunker-qa.sh launch /home/kara/get-h3/lore` → agent `96a5db78` on `bunker-mvp`, TTL 4 h,
QA-HEAD `f4e0599` (the sibling's close-out commit — the clone was clean at launch, so the tested
sha is recorded, not a dirty tree). Cells are collected with `bunker-qa.sh collect`; the cell
verdicts and the agent teardown are recorded in the run log entry, never inferred from the launch
banner. The sibling's own fresh-clone leg is at `docs/qa/evidence/run15/fresh-box-leg.txt`.

## What a maintainer should fix first (1 hour of their time)

1. **LORE-067-R2** (already filed by the tick's first delivery): stop reporting incident presence
   through a field named `runbook_compiled`. One column rename plus a real incident column, and
   the audit stops contradicting `lore show`.
2. **LORE-20261011** (this session): give `absorb` the same unknown-class exit code as its
   siblings. Three lines.
3. **LORE-067-R3**: a class with incidents and no runbook is the *product's* headline question —
   it should be a row, not silence.
