# lore dogfood — run 14b (2026-10-20): the audit matrix has no incident input

**Tick:** `lore-dogfood-2026-10-20-08-02-03`, **second angle** (same tick as run 14).
**HEAD at run:** `6de0660` (run 14 landed `d754a1c`, `ade12c5`, `6de0660` on top of `a6984b4` — docs/board only,
`lore/*.py` byte-unchanged across that range, so every run-14 code conclusion holds here).
**Lane contract:** read-only. No code changed, no board byte touched except appending this run's own two rows.
**Rows filed:** `LORE-067` (P3), `LORE-068` (P2).

## Why this angle

Run 14 same-tick covered the install path as written on a fresh box, the validate-history ledger's **cost**
(`PERF-2`), two doc/guard defects (`LORE-066`, `LORE-063-R2`), and delta fix-verification. The rerun chain is
9 fix-verbs → 10 install-envelope → 11 absorb-ladder → 12 skill-ingest → 13 PRD-SC/US → 14 ledger-cost.

What no run had driven is the **PRD's User Stories as stories** — run 13 exercised SC-1..SC-4 and US-4 only.
US-1/US-2/US-3 are the three sentences the product exists for. US-3 is the sharpest of them, because it promises a
*measurement*: "every failure class **seen in the last 90 days** … the classes with incidents but no runbook —
coverage as a number, not a feeling" (`docs/PRD.md:28`), reinforced by SC-2 (`docs/PRD.md:63`) "runs on the fleet's
last 90 days of incidents".

## The promise vs. what the tool does

```
$ .venv/bin/python -m lore audit --format json
{"classes":[{"class_id":"gateway-drain-window","runbook_compiled":true,"check_count":7,...}, x14],
 "summary":{"total_classes":14,"classes_with_zero_real_commands":1,"stale_classes":0,...}}
```

Four columns: `runbook_compiled`, `check_count`, `command_count`, `last_validated`/`status`. There is no
`incidents_seen`, no `last_seen`, no window, and no field that could ever say "this class has incidents and no
runbook". The data path, read end to end:

| locus | what it proves |
|---|---|
| `lore/__main__.py:583` `for rb in compile_all():` | audit rows come from `compile_all()` and nothing else |
| `lore/__main__.py:592` `"runbook_compiled": True,` | **hard-coded literal** — never `False`, for any class, ever |
| `lore/compiler.py:985` `def compile_all(...)` | iterates the registry |
| `lore/compiler.py:954` `for c in _CHECKS.get(cls.id, [])` | runbook bodies are the literal table |
| `lore/compiler.py:76` `_CHECKS: dict[str, list[Check]] = {` | 13 hand-authored check sets |
| `lore/classes.py:38` `SEED_CLASSES: tuple[FailureClass, ...] = (` | 13 hand-authored classes |
| `lore/classes.py:543` `_REGISTRY = ClassRegistry(SEED_CLASSES + (UNCLASSIFIED_CLASS,))` | `total_classes == 14` is a tuple length |

**The discriminator that makes this a finding rather than an inference** — incident/ledger data changes nothing:

```
$ cd /tmp/<empty dir> && <venv>/python -m lore audit --format json   # no repo, no .lore ledger, no incident data
-> rc=0, total_classes=14, identical class list
$ cd <repo>          && <venv>/python -m lore audit --format json   # repo WITH its 3,161-row ledger
-> IDENTICAL summary and class list (only `status`/`stale_reason` is history-driven — the LORE-064 wiring)
$ grep -rniE 'incident|duckbrain|logsey' lore/*.py
-> only literal `detail` strings inside `_CHECKS`, `parse_logsey_export` (used by `absorb` on a CALLER-SUPPLIED
   trail, lore/__main__.py:461), and help text
```

So the ingestion machinery exists but is wired to the **write** path (absorb proposals) and never to the **read**
path (coverage). A class the fleet hits that is not in `SEED_CLASSES` lands in `unclassified` and cannot move any
number: `total_classes` is 14 at zero incidents and at ten thousand.

## What I judged, honestly

- **Does it work?** The command works and is fast and its *own* docstring is honest ("One row per registry class",
  `lore/__main__.py:616`); `README.md:390-403` also says "per registry class". The unmet half is the PRD's
  (US-3 / SC-2) and the README one-liner's "compiles the fleet's *actual* incident history" (`README.md:10`).
- **Is it useful?** As a registry/freshness report, yes — it is a real inventory with a never-fabricated
  `last_validated`. As a *coverage* report over incidents, no: it cannot name a gap, because the gap column is a
  constant and the class list is a Python tuple.
- **Is it usable?** Yes — one command, `--format json|md|table`, instant. Nothing to learn.
- **Is it trustworthy?** Yes about what it does *not* know (`last_validated: "no data"`, the honesty note in
  `summary`). The trust gap is one level up: SC-2's "≥8 failure classes" reads as a coverage achievement and is
  permanently satisfiable by editing a tuple.
- **Fast enough?** Yes. Warm `lore audit --format json` = **0.11 s ×3** (`/usr/bin/time -p`, this box); run 14
  measured the same command with hyperfine at **144.2 ms ± 15.7 ms** with the repo's ledger and **48.3 ± 2.5 ms**
  with no ledger, so the spread between my 0.11 s and run 14's 0.144 s is method/load, not a regression. The
  scaling defect (the ledger re-read once per class) is already owned by **`PERF-2`** from run 14 — this run files
  **no** PERF row and only warns the fixer not to make that loop worse.

**Verdict:** 🟡 **PROMISING-BUT-ROUGH** on the coverage surface (the promise is the product's headline; the
mechanism behind it does not exist) — everything else driven this run is SHIPPABLE. Run 13's SC-2 `PASS` is
re-graded here: it read the registry listing as the coverage matrix.

## Second finding: the repo's own board is red

`boardctl validate` cannot return `OK` on this checkout, independently of anything dogfood does:

```
RESULT: FAIL (3 error(s), 42 warning(s))
  tasks.jsonl line 76  (LORE-050): status "closed" not in vocabulary {...}
  tasks.jsonl line 83  (LORE-054): status "closed" not in vocabulary {...}
  events.jsonl line 177: event id 176 descends below earlier id 177 (ids must ascend; gaps tolerated)
```

Provenance from the bytes: `closed` is not even a *read alias* (unlike the `done` rows elsewhere on this board);
the events inversion is intra-tick append order from tick `lore-qa-2026-10-07-09-11-11` (ids 176/177 carry the
same tick and the same `ts`). Both pre-date this tick. Recorded as the **baseline** for this run's appends
(`LORE-067`/`LORE-068` added **0** new errors and **0** new warnings), and filed as `LORE-068` because a lane that
closes on `RESULT: OK` cannot distinguish its own damage from a pre-existing 3.

## Not touched (stated so the next run does not re-chase)

- No code, no docs fix, no board byte other than this run's two rows. The `closed` statuses and the events order
  are exactly as found.
- Run 14's surfaces (install leg, ledger cost, freshness arms) are **not** re-driven here; its evidence under
  `docs/qa/evidence/run14/` stands, and run 14's three staged probe scripts were left staged and uncommitted.

## Artifacts left behind

- Board rows: `LORE-067` (P3, coverage has no incident input), `LORE-068` (P2, board gate red).
- `docs/qa/evidence/run14b/audit-no-incident-input.txt` — the empty-dir vs repo discriminator, raw JSON both sides.
- `docs/qa/evidence/run14b/loci.txt` — the file:line table above plus the grep census.
- `docs/qa/evidence/run14b/timing.txt` — warm ×3 numbers and run 14's hyperfine basis.
- `docs/qa/evidence/run14b/board-validate.txt` — the pre-append validate baseline.
- `docs/dogfood/diagnostics.md` run-14b section; `skills/lore-usage/SKILL.md` audit-scope note.
- DuckBrain: `namespace=lore`, key `/dogfood/2026-10-20-lore-run14b`.

## Commit-time collision: the guard failed on a sibling's uncommitted files

Both commits were first attempted **with the guard** and both were refused:

```
Tier 1 Guards: FAIL  (test mode: full)
  ✓ secrets — clean
  ✗ lint — 3 files would be reformatted
  ✓ tests (full)
ruff format --check: 3 file(s) would be reformatted — run `ruff format
docs/qa/evidence/run14/mkhistory.py docs/qa/evidence/run14/passbench.py docs/qa/evidence/run14/probe-freshness.py`
```

Diagnosis, not assumption: those three paths are `A` (staged, uncommitted) in the shared index, are **not** in
`HEAD` (`git cat-file -e HEAD:<path>` fails for all three), and were written by the same-tick run-14 lane — its
probe scripts, left staged when its loop ended. My diff contains **zero** `.py` files
(`git diff --name-only HEAD -- <my paths> | grep -c '\.py$'` = 0): commit 1 is board + dogfood-log, commit 2 is
docs + skill + `.txt`/`.json` evidence. So the failing lint lane protects nothing in my change, and the guard's
own `tests (full)` cell had already passed.

Per `shared-checkout-commit-stewardship` ("a commit whose diff is BOARD/BOOKKEEPING-ONLY … bypass deliberately
with `git commit --no-verify` and verify the row content at HEAD afterward; never `--no-verify` a commit carrying
code changes"), both commits were re-run with `--no-verify` and then verified by content at `HEAD`.

**Not done, deliberately:** the three files were not reformatted, unstaged, or committed. They are another lane's
in-flight work; touching them would publish that lane's unverified edits under this run's message. The consequence
is worth flagging to the owning lane: **the shared checkout's guard-lint lane is currently red for every lane**, so
run 14's own commit would fail the same way until those three files are formatted or removed.

