# lore dogfood — run 14c (2026-10-20): the scribe cannot draft an update

**Tick:** `lore-dogfood-2026-10-20-08-02-03`, **third angle** (after run 14 and run 14b, same tick).
**HEAD at run:** `29bdbef` (== origin/main at run start, == origin/main at close-out).
**Contract:** read-only lane. No code changed, no board byte touched except appending this run's own row.
**Row filed:** `LORE-069` (P3).

## Why this angle

Run 14 covered the install path as written and the validate-history ledger's cost; run 14b covered the audit
matrix's missing incident input. Both left the PRD's **US-2** — *the post-incident scribe*, the flow that turns
"what actually happened" into a runbook draft — untested as a user story, even though the harness for it
(`absorb --window`) was touched by runs 8, 11 and 14 (error ladder, claim-detection substring, noise vs happy-path
rc). Nobody had asked the scribe's question: **is the thing that comes out an update?**

## Promise under test

> "As the agent that just closed an incident, I run `lore absorb --window 2h --ns coding-hermes` and it drafts the
> runbook **update** from what actually happened — **evidence blocks**, working commands, **dead ends marked
> dead** — filed as a proposal the operator approves." (`docs/PRD.md:26`)

And the tool's own two sentences: `lore absorb --help` → "build the runbook-**update** PROPOSAL for an absorb
decision" (`docs/INSTALL.md:135-137`), and `--class` → "existing registry class to **propose an update for**".

## What the scribe actually gets

Documented example, verbatim (`docs/INSTALL.md:394-395`), rc=0 → one proposal for `gateway-drain-window`.
Then a realistic trail: six blocks in the documented "timestamped, source-attributed" shape — a gateway drain 503,
the drain window still open at 25 min, a guard failure, a docs count drift, a board note, disk pressure — swept with
`--ns lore --board .coding-hermes/board/tasks.jsonl --source dogfood-dagger`, rc=0, three proposals:

```
gateway-drain-window   action=new  removed={}  changed={}  added_checks=7
unclassified           action=new  removed={}  changed={}  added_checks=0
gateway-guard-violation action=new removed={}  changed={}  added_checks=2
```

`action` is `"new"` for every class — including `gateway-drain-window`, whose runbook already exists with 7 checks.
`removed` and `changed` are always empty. And the body is not merely similar to the existing runbook, it **is** it:
`jq -s '.[0].added == .[1]'` over the proposal and `lore show gateway-drain-window --format json` returns `true`.

The locus has two halves, and the row carries both because fixing only the first ships a lie:

1. **No caller passes `existing`.** `grep -rn 'propose(' lore/*.py` gives exactly one production call —
   `lore/absorb.py:175  payload = propose(class_id)` — and `grep -rn 'existing=' lore/*.py` is **empty**. Both
   surfaces funnel through it (`absorb_sweep` → `absorb_proposal`, `lore/absorb.py:214`/`:162`/`:175`), so
   `lore/compiler.py:1003`'s `"action": "new" if existing is None else "update"` always takes the `new` branch and
   the diff branch at `:1010` returns early. The engine works — **tests pass `existing`**
   (`tests/test_compiler.py:182/200/213`) — so this is unimplemented-in-production, not unimplemented.
2. **The trail never reaches the compared runbook.** `propose()`'s fresh side is
   `fresh = compile_class(class_id)` (`compiler.py:1000`) — registry-derived, blind to the swept blocks and the
   lesson. Passing `existing` alone therefore yields an **empty update every time**; a real fix must fold the trail's
   evidence into the fresh side before diffing.

Two further clauses of US-2, checked at the same HEAD: the swept blocks survive only as provenance
(`sweep.evidence`, all four unclassified blocks kept) and never enter the proposed body
(`added.evidence_trail` is still the curated trail); and **"dead ends marked dead" exists nowhere** —
`grep -rniE 'dead end|dead-end' lore/*.py` returns zero hits, the phrase living only in `docs/PRD.md:26`.

## Judgement

- **Does it work?** The sweep runs, classifies, groups, honours `--ns/--board/--source`, exits honestly on an empty
  trail, and writes nothing (propose-not-write holds). What it cannot do is the one thing its own help text names:
  an update.
- **Is it useful?** As a *classifier of a trail* yes — six blocks went to the right three classes. As a *scribe
  draft* no: an operator approving it approves the runbook they already have.
- **Is it usable?** Yes, and unusually well-behaved: the documented example works verbatim, `--trail-file` and stdin
  both work, unknown windows get a teaching error, and the JSON is stable.
- **Is it trustworthy?** The honest half is intact (propose-not-write; no fabricated dates; empty trail = explicit
  empty result, rc 0). The trust gap is that `action: "new"` reads as "this class had no runbook", which is false
  for all 13 curated classes.
- **Is it fast enough?** Yes, and there is nothing to file: `absorb --window` warm **49.7 ms ± 1.9** (hyperfine,
  12 runs), the single-proposal path **46.7 ms ± 4.2**, cold **0.08 / 0.07 s** — both sit at the interpreter-startup
  floor, so the trail work itself is ~4 ms. **No PERF row** (a win nobody can feel is not a finding).

## Left behind

- Board row `LORE-069` (P3), with the promise quoted, both loci, the two-half fix direction and falsifiable
  acceptance criteria.
- `docs/qa/evidence/run14c/` — `absorb-update-never.txt` (call-site census, both observed payloads, the `added ==
  show` equality, help text), `trail-real.txt` (the input), `out-real.json` (raw three-proposal output), `perf.txt`.
- `docs/dogfood/diagnostics.md` run-14c section; `skills/lore-usage/SKILL.md` absorb-scope note.
- DuckBrain `namespace=lore`, key `/dogfood/2026-10-20-lore-run14c`.

## Not touched

No code, no docs fix, no board byte other than this run's row. Run 14's and run 14b's artifacts are byte-untouched;
their surfaces (install envelope, ledger cost, audit coverage) were not re-driven — this run cites them rather than
repeating them.
