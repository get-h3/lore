# ADDENDUM — lore-docs audit, delivery 2 of tick lore-ops-2026-11-24-21-03-06

Base artifact: `docs/qa/evidence/run-DOC-audit-20261124-2103/README.md`
(frozen at delivery 1, sha256 `f7d2040f66bd3b40efb8de6c9d1823da94a1f98f22095270454beb1a79ad50e6`).
This is a separately named addendum per the freeze rule: the base transcript is not edited, and any
probe run after its digest was computed lands here, never inside it.

## 1. Re-fire context

- Delivery 1 (same tick) filed DOC-13, DOC-5-R2-R2 and DOC-14 and pushed commit `dee6434`
  (2026-11-24T21:29:59Z) but was cut off before it could report or write its memory record.
- This delivery is the honest re-fire increment: premise re-verification of the filed rows at the
  published tip, plus the standing per-sweep censuses delivery 1's transcript never ran.
  No re-push of delivery-1 rows, no fresh ids for delivery-1 findings.

## 2. Probe root

- Worktree `/home/kara/get-h3/lore-wt-docsaudit-20261124` at `dee6434ec98c8b9ddce9f0be7b299c1782c2973e`
  (= origin/main at probe time), `git status --porcelain` empty.
- Audited surfaces byte-identical `0b0fd37..dee6434`: the diff touches only `.coding-hermes/board/*`
  and `docs/qa/evidence/*` (delivery 1's own filing).

## 3. Premise re-verification (raw outputs, run 2026-11-24 ~21:32-21:33 UTC)

### DOC-13 (README + lore/evidence.py say logsey `export` unimplemented)

```
$ grep -n -F 'for as long as' README.md        # corrected AC-1 token (see section 4)
404:  (`degrade_to_command_output`) for as long as logsey's `export` subcommand is
$ sed -n '400,406p' README.md                  # premise lines live
- Evidence blocks (`lore/evidence.py`): the curated evidence-kind vocabulary,
  the logsey-export contract parser, and the honest degradation path
  (`degrade_to_command_output`) for as long as logsey's `export` subcommand is
  unimplemented. Attaching evidence never sets `last_validated`.
$ grep -c 'not yet implemented' lore/evidence.py
1
$ grep -n -A2 'LOGSEY_EXPORT_CONTRACT_STATUS = (' lore/evidence.py
58:LOGSEY_EXPORT_CONTRACT_STATUS = (
59-    "unfrozen — logsey export subcommand not yet implemented "
60-    "(internal/cli/cli.go planned list)"
```

Sibling-binary re-runs (T3):

```
$ logsey --help | grep -n export
13:  export         emit a timestamped evidence block for post-mortems
$ logsey --version
logsey version 0.2.1
$ logsey export --window 3m --format md   (rc=0, head)
warning: index is stale (corpus changed since build; indexed rows=9832460)
hint: run 'logsey index rebuild' to restore indexed-query speed (~100x on this corpus)
## logsey evidence block

- captured: 2026-11-24T21:33:26Z
- corpus: /home/kara/.local/share/logsey/corpus.jsonl
```

Premise: LIVE (docs still claim unimplemented; producer ships and runs).

### DOC-5-R2-R2 (INSTALL.md pasted `--help` gate line stale)

```
$ sed -n '130,136p' docs/INSTALL.md
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
$ python3 -m lore --help   (at tip dee6434, rc=0, gate entry:)
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exports
                        node_exporter metrics; exit 0 = allowed, 1 = denied or
                        export failed
```

Premise: LIVE (paste still missing the metrics clause and the exit-1 qualifier).

### DOC-14 (README:463 `in v0.1` qualifier at the 0.3.0 stamp)

```
$ sed -n '461,465p' README.md
  matrix: per registry class, runbook-compiled, check count, real-command count
  (vs the honest `no data` sentinel), and freshness. Freshness is honest:
  `last_validated` is never auto-populated in v0.1 — no code path writes it
  (a lint run is not operator attestation; operator attestation is planned,
  not implemented) — so every runbook says `no data` until a human attests.
$ grep -n '^version' pyproject.toml
7:version = "0.3.0"
$ sed -n '18,22p' lore/compiler.py
- A runbook compiled WITHOUT explicit validated evidence carries
  ``last_validated=None`` (never a fabricated date) and ``status="proposal"``.
$ python3 -m lore compile --class gateway-drain-window --format md   (rc=0, head 6)
# Runbook: Gateway drain window (`gateway-drain-window`)
- **Status:** proposal
- **Last validated:** no data (never validated)
```

Premise: LIVE (sentence still present; stamp still 0.3.0; behavioral half still true —
the live compile output still says `no data (never validated)`).

### Prior deliveries' pending rows (premises)

- DOC-10-R2: `grep -c '0\.3\.0' README.md` -> 0; same for docs/RELEASE.md -> 0;
  README.md:381 still reads `Development version stamp **0.2.0**, released **2026-11-16**`.
  Premise LIVE.
- LORE-20261013: `grep -n -F '.read()' docs/ABSORB-TRIGGER.md` -> NO HIT. Premise LIVE.
- README-12 (readme lane's row): NOT re-measured this delivery — the probe covered the
  match-sample block (README.md:42-44, fenced), not the compile-sample block the row names.

## 4. Defect found in delivery 1's own row (corrected this delivery)

DOC-13's acceptance criterion 1 was `grep -c 'subcommand is unimplemented' README.md -> 0`.
That token is line-wrapped (README.md:404 ends `subcommand is`, line 405 starts
`unimplemented.`), so the grep already returned 0 before any fix — a vacuous assertion a worker
could satisfy without editing README. Corrected in place to `grep -c 'for as long as' README.md -> 0`
(exactly 1 occurrence today, README.md:404). Same finding, arithmetic correction of this lane's own
row filed minutes earlier — not a new finding and not a recurrence.

## 5. Standing censuses delivery 1 never ran

### 5.1 Close-out residue sweep (reader-facing corpus, evidence trees excluded)

```
STATUS: PASS -> 0   TIER: T -> 0   RESIDUAL: -> 0   filed_rows: -> 0   boardctl -> 0
verdict.json -> 1 (docs/traceability-doctrine.md:60 — the doctrine's own field-table example;
non-defect)
```

Clean. No foreman footer leaked into reader-facing prose.

### 5.2 Marker census

Tracked-file total: 1046 token occurrences across 140 files — dominated by `.gitreins/history/*`
patches and the board itself (tasks.jsonl 59, events.jsonl 18, snap 25). In reader-facing prose the
token appears only as doctrine references, not markers: README.md:503 and CHANGELOG.md:55 name the
marker grammar in prose; docs/traceability-doctrine.md carries the contract itself.

### 5.3 The repo's own checker (out-of-band arbitration)

```
$ python3 /home/kara/.hermes/scripts/trace_marker_check.py <worktree>
TRACE-MARKER VIOLATIONS in <worktree> (20):
  - R2 evidence path does not resolve | LORE-046:62 | ci-run-5557044-success
  - R2 evidence path does not resolve | LORE-047:69 | gate
  - R2 evidence path does not resolve | SUP-DEPS-LORE-20261006:71 | gitreins-verdict-43a694d5
  - R2 evidence path does not resolve | SUP-DEPS-20261013-LORE:74 | gitreins-verdict-128e762e
  - R2 evidence path does not resolve | LORE-20261008:79 | gitreins-verdict-PASS
  - R2 evidence path does not resolve | LORE-055:84 | gitreins-verdict-0fe290e2
  - R2 evidence path does not resolve | LORE-056:85 | live-verification
  - R2 evidence path does not resolve | LORE-062:92 | live-validate-json+pytest-510
  - R2 evidence path does not resolve | LORE-063:93 | pytest-collect-510+count-guard-PASS
  - R2 evidence path does not resolve | README-3:96 | gitreins-verdict-0fb127cb
  - R2 evidence path does not resolve | README-5:98 | show
  - R2 evidence path does not resolve | LORE-060-R2:99 | /tmp/lore060r2-fresh-validate.json
  - R2 evidence path does not resolve | README-9:103 | grep-match-class-line-367
  - R2 evidence path does not resolve | DOC-7:106 | grep-acceptance-0-future-planned-lore-show-absorb
  - R2 evidence path does not resolve | LORE-070:113 | live-cli-match-gateway-drain-503-confidence-0.90
  - R2 evidence path does not resolve | DOC-8:116 | audit-help-greps-events-jsonl-90-day
  - R2 evidence path does not resolve | PERF-3:120 | hyperfine-A-B-faster-than-plus-passive-419.9ms-vs-1993ms-baseline
  - R2 evidence path does not resolve | README-11-R2:123 | grep-uv-tool-upgrade-line-157
  - R2 evidence path does not resolve | DOC-5-R2:128 | fence-diff-empty-vs-live-help
  - R2 evidence path does not resolve | DOC-9:129 | grep-re-validation-planned-0
rc=1
```

All 20 are complete rows. The values are bare witness-form slugs (or pruned /tmp paths) sitting in
the evidence= field; the repo's own doctrine (## Fields) defines evidence= as "artifacts a reader
can open and re-walk", naming `.gitreins/history/<date>/<id>/verdict.json` as the resolvable form.

### 5.4 Checker-invisible dedicated-field markers

Two rows carry their marker in a dedicated JSON field whose VALUE starts at `row=`, so the
checker's token-adjacency regex cannot see them:

- `QA-LORE-4-SUP-1` (board line 65, complete): marker value carries
  `evidence=/tmp/<path redacted>` — a pruned scratch path.
- `LORE-064` (board line 94, complete): also checker-flagged (live-validate-json+pytest-510),
  listed here only to account for the dedicated-field shape.

### 5.5 Events citing pruned scratch paths

Three `qa_recurrence` events (ids 170, 171, 174) carry `evidence=/tmp/<paths redacted>` inside
their detail payloads.

### 5.6 Scratch-path attribution across all tracked files

28 `evidence=/tmp/`-form occurrences total: the 2 board rows + 3 events above are the finding
(board-surface claims a reader cannot re-walk). The remaining 23 sit in `.gitreins/history/*`
patches (historical record of past commit bytes) and `docs/dogfood/*` evidence trees +
`.coding-hermes/dogfood-log.md` (dated evidence corpus, not reader-facing docs) — recorded, not
filed.

## 6. Re-triage census (P1-P3 doc rows created before 2026-09-30)

Board decode (163 distinct ids, last append wins): **0** open P1-P3 rows created before
2026-09-30, of any flavor. Nothing to re-triage this tick.

## 7. Filing actions this delivery

1. DOC-13 acceptance-criteria correction (section 4) + disclosure note.
2. DOC-15 filed: board-surface unresolvable evidence pointers (20 checker rows + the
   dedicated-field row the checker cannot see, + 3 events; one mechanism).
3. One audit event indexing this delivery appended to events.jsonl.

Addendum frozen before filing; sha256 recorded in the audit event detail of this delivery.
