# lore dogfood — run 14d (2026-10-20): the responder's own example finds nothing

**Tick:** `lore-dogfood-2026-10-20-08-02-03`, **fourth angle** (after runs 14, 14b, 14c, same tick).
**HEAD at run:** `b29cbf5` (== origin/main at run start and at close-out).
**Contract:** read-only lane. No code changed, no board byte touched except this run's own row.
**Row filed:** `LORE-070` (P4).

## Why this angle

Run 14 took the install path and the ledger's cost; run 14b took the audit matrix; run 14c took PRD **US-2** (the
scribe). The product's headline story — **US-1, the 3 a.m. incident responder** — had never been driven as a story,
only as a classifier unit (runs 1, 4) and as contract parity (run 8). So this run asked US-1's own question with
US-1's own words.

## Promise under test

> "As an agent at 3 a.m. facing **"scheduler spawns 503-ing at spawn time,"** I ask `lore match "spawn 503"` and get
> the drain-window runbook — **checks in order**, the exact logsey query, the known-good command sequence."
> (`docs/PRD.md:24`)

## What happens

```
$ python -m lore match "spawn 503"
unclassified    confidence=0.00    evidence: none            rc=0
$ python -m lore match "scheduler spawns 503-ing at spawn time"
unclassified    confidence=0.00    evidence: none            rc=0
$ python -m lore match "spawn 503" --explain
unclassified    confidence=0.00
near-misses:
  gateway-drain-window  score=0.17  (1/6 keywords: 503)
  spawn-hot-loop        score=0.17  (1/6 keywords: spawn)
```

The drain-window class *is* the top near-miss, but at 0.17 it is far below both gates (`KEYWORD_THRESHOLD = 0.6`
for long text, `SHORT_KEYWORD_THRESHOLD = 0.3` for short — `lore/classifier.py:34-59`), and the example's own verb
form (`match`, no `--explain`) shows the user only `unclassified` — which the README teaches them to read as "the
fleet has never seen this". The mechanism is structural: the class is accepted on the signature `drain 503`, and
`spawn 503` shares one token with it while lending the other token to a *different* class, so the two tie.

**The useful half** — the same symptom text resolves through a different form:

```
$ python -m lore consult "spawn 503"                       -> no matching runbook          rc=0
$ python -m lore consult --failure "spawn 503 while restarting"
   -> this class has a runbook: gateway-drain-window ... checks=7     (7 checks, fill-in hints) rc=0
```

So the 3 a.m. reader following US-1 verbatim is told "nothing" twice, while the runbook was one flag away, and
nothing in the PRD, the README's responder bullet, or the consult help text points at that form mid-fire.

## What held up (checked, not assumed)

- **The README's documented examples all reproduce exactly**: `drain 503` → `gateway-drain-window` 0.90;
  `secret .env clobber` → `secret-env-clobber` 0.90; `the coffee machine is making a weird noise` → `unclassified`
  0.00 *as documented*; `gateway drain 503` → 0.90; `key rotation expired` → `key-rotation-expiry` 0.90. The defect
  is specific to the PRD's example, not to the docs as a whole.
- **"Checks in order" holds for all 14 registry rows** — `order` contiguous from 1, ascending in list position, and
  identical between `compile --format json` and `show --format json` (`docs/qa/evidence/run14d/checks-in-order.txt`).
- The unclassified answer itself is honest and rc=0 — absence really is a first-class answer here; the problem is
  that the docs chose an example where that honest answer is the wrong one.

## Why this is a doc row and not a recall re-file

Classifier recall on paraphrases is a filed-and-**closed** family: LORE-016 (stranger phrasings), LORE-023 (real
incident vocabulary), REVIEW-LORE-002 (natural incident phrasings), LORE-043 (consult title-mode 0.375 < 0.6) are
all `complete`. The row says so explicitly and asks for the **documentation** fix — change the example, or add the
one-clause pointer to `consult --failure` (the honest teaching moment for a 3 a.m. reader, and no code change). If
the fleet's real phrasing deserves to be accepted as a drain-window signal, the row names that as option (c) and
requires it to be filed separately against that family, not bundled in.

## Cost (Step 2b)

`lore match` warm **56.2 ms ± 4.1** (hyperfine, 12 runs); the same command with `--explain` **49.9 ms ± 3.5**; cold
**0.09 / 0.10 s** (`drop_caches`). Both sit at the interpreter-startup floor, so classification itself is under a
millisecond. **No PERF row** — nothing here a user could feel.

## Verdict

🟡 **PROMISING-BUT-ROUGH** on the documented responder entry point (the story's own example is a dead end until
one flag is taught); the mechanism, the ordering contract, and the honesty of `unclassified` are all sound.

## Left behind

- Board row `LORE-070` (P4), with the promise quoted, both arms, the near-miss scores, the closed-family
  cross-reference, and three explicit fix options with acceptance criteria.
- `docs/qa/evidence/run14d/` — `us1-example-fails.txt` (all arms verbatim), `match-battery.txt` (every documented
  example string and the PRD narrative strings, class per line), `checks-in-order.txt` (the passing invariant),
  `perf.txt`.
- `docs/dogfood/diagnostics.md` run-14d section; `skills/lore-usage/SKILL.md` responder-entry note.
- DuckBrain `namespace=lore`, key `/dogfood/2026-10-20-lore-run14d`.

## Not touched

No code, no docs fix, no board byte other than this run's row. Runs 14/14b/14c artifacts are byte-untouched and
none of their surfaces were re-driven.
