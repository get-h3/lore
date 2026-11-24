
===== HEADER =====
tick: lore-ops-2026-11-24-21-03-06 (lore-docs audit lane)
probe root: /home/kara/get-h3/lore-wt-docsaudit-20261124
HEAD at freeze: 0b0fd37ee5953dd9027cc7ba3c3db1cabaa8e1be
worktree dirty state at freeze: ?? docs/qa/evidence/run-DOC-audit-20261124-2103/;
corpus: README.md CONTRIBUTING.md SECURITY.md CHANGELOG.md docs/INSTALL.md docs/ABSORB-TRIGGER.md docs/PRD.md docs/RELEASE.md docs/RUNBOOK-STORE.md docs/traceability-doctrine.md (evidence trees docs/qa, docs/dogfood, docs/acceptance, docs/release-evidence excluded)

===== VERIFICATION GATE (repo's own) =====
..........                                                               [100%]
586 passed in 7.32s
All checks passed!

===== CLI HELP SURFACE (captured 2026-11-24 at 7945410 from /home/kara/get-h3/lore; lore/ and docs/ unchanged 7945410..cited tip — diff was board+gitreins evidence only) =====
===== parent help =====
usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        only)
    validate            read-only command lint (LORE-006). DEFAULT = plan/dry-
                        run: lists what WOULD run, executes NOTHING; pass
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exports
                        node_exporter metrics; exit 0 = allowed, 1 = denied or
                        export failed
    absorb              build the runbook-update PROPOSAL for an absorb
                        decision (stdout only — propose-not-write, nothing is
                        written)
    show                print the compiled runbook for ONE class (LORE-010);
                        human-markdown default, --format json optional
    audit               coverage + freshness matrix over every registry class
                        (LORE-010, PRD US-3); honest 'no data' freshness —
                        never fabricated dates

options:
  -h, --help            show this help message and exit
rc_parent=0
===== per-verb help =====

##### verb match #####
usage: lore match [-h] [--explain] [--class CLASS_ID] text

positional arguments:
  text              symptoms or log line(s)

options:
  -h, --help        show this help message and exit
  --explain         echo near-misses: classes that almost matched (raw keyword
                    fraction below threshold) — evidence only, never a label
  --class CLASS_ID  filter results to only the named class (must be a valid
                    registry class)
rc_match=0

##### verb compile #####
usage: lore compile [-h] [--class CLASS_ID] [--format {json,md}]

options:
  -h, --help          show this help message and exit
  --class CLASS_ID    compile one class; omit to compile every registry class
  --format {json,md}  output format (default: json)
rc_compile=0

##### verb show #####
usage: lore show [-h] [--evidence] [--format {json,md}] class_id

positional arguments:
  class_id            existing registry class to show

options:
  -h, --help          show this help message and exit
  --evidence          add the class's evidence/provenance detail (registry
                      provenance + evidence blocks)
  --format {json,md}  output format (default: md)
rc_show=0

##### verb audit #####
usage: lore audit [-h] [--format {table,json,md}]

options:
  -h, --help            show this help message and exit
  --format {table,json,md}
                        output format (default: table)

Incident evidence source (DOC-8):
  Incident records are read from .coding-hermes/board/events.jsonl
  (plus tasks.jsonl), resolved against the CURRENT WORKING
  DIRECTORY (one parent-directory fallback), over a
  90-day window. A missing board degrades to empty incident facts
  with exit 0 and the coverage_note says the source was
  unavailable. Novel classes land in summary.uncovered_classes.
rc_audit=0

##### verb absorb #####
usage: lore absorb [-h] [--class CLASS_ID] [--lesson LESSON] [--window WINDOW]
                   [--trail-file TRAIL_FILE] [--ns NS] [--board BOARD]
                   [--source SOURCE]

options:
  -h, --help            show this help message and exit
  --class CLASS_ID      existing registry class to propose an update for
                        (required without --window)
  --lesson LESSON       the lesson text (required without --window)
  --window WINDOW       LORE-010 sweep: sweep a PRIOR EVIDENCE TRAIL (stdin,
                        or --trail-file) instead of taking --class/--lesson;
                        parse a duration like 2h/45m/90 and group classifiable
                        blocks into per-class absorb PROPOSALS (stdout only —
                        nothing is written)
  --trail-file TRAIL_FILE
                        read the evidence trail from PATH instead of stdin
                        (with --window)
  --ns NS               optional namespace label recorded in the proposal
                        provenance (no live lookups in this PR)
  --board BOARD         optional board path label recorded in the proposal
                        provenance (no live lookups in this PR)
  --source SOURCE       LORE-009: provenance marker recorded into the proposal
                        payload (e.g. 'qa-dagger' or 'dogfood-dagger').
                        Omitted = the payload keeps its original shape (no
                        'source' key)
rc_absorb=0

##### verb consult #####
usage: lore consult [-h] [--failure FAILURE] [--detail DETAIL] [--json]
                    [title]

positional arguments:
  title              task title (symptom text); required unless --failure is
                     given

options:
  -h, --help         show this help message and exit
  --failure FAILURE  LORE-009: guard-failure mode — treat the value as guard-
                     failure OUTPUT text (e.g. a gitreins guard log tail)
                     instead of a task title; on a class match prints the
                     matching runbook's ordered checks ('this class has a
                     runbook'). Fail-open: no match = exit 0
  --detail DETAIL    optional task detail; classified together with the title
  --json             print the ConsultResult as JSON
rc_consult=0

##### verb validate #####
usage: lore validate [-h] [--class CLASS_ID] [--format {json,md}] [--execute]

options:
  -h, --help          show this help message and exit
  --class CLASS_ID    lint one class; omit to lint every registry class
  --format {json,md}  output format (default: json)
  --execute           OPT-IN: actually run the gate-approved read-only
                      commands (default is plan-only, nothing is executed)
rc_validate=0

##### verb gate #####
usage: lore gate [-h] --decision {absorb,no-new-lesson} [--class CLASS_ID]
                 [--lesson LESSON] [--reason REASON] [--ref REF]
                 [--record PATH] [--decided-at DECIDED_AT] [--source SOURCE]

Export each gate verdict to h3_lore.prom in H3_LORE_TEXTFILE_DIR (default:
/var/lib/node_exporter/textfile). Export errors fail the command.

options:
  -h, --help            show this help message and exit
  --decision {absorb,no-new-lesson}
                        'absorb' (a runbook lesson) or 'no-new-lesson'
                        (explicit ack)
  --class CLASS_ID      existing registry class for an 'absorb' decision
  --lesson LESSON       proposed lesson text (absorb)
  --reason REASON       why no new lesson (no-new-lesson)
  --ref REF             board row / incident id
  --record PATH         REVIEW-LORE-001 OPT-IN: append one durable JSONL audit
                        record to PATH for an ALLOWED verdict (decided_at,
                        decision, class_id, lesson, reason, ack_ref, source,
                        allowed, errors, tool_version). Denials do not write
                        audit records; metrics are exported for both verdicts.
  --decided-at DECIDED_AT
                        optional ISO-8601 timestamp (never invented when
                        omitted)
  --source SOURCE       LORE-009: provenance marker for this closure — e.g.
                        'qa-dagger' or 'dogfood-dagger' (QA/dogfood findings
                        close through the same absorb-gate as incidents).
                        Omitted = default incident-closure behavior (no source
                        printed)
rc_gate=0
===== unknown-verb probe =====
usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...
lore: error: argument command: invalid choice: 'nosuchverb' (choose from 'match', 'consult', 'compile', 'validate', 'gate', 'absorb', 'show', 'audit')
rc_unknown=2
===== module inventory =====
lore/__init__.py
lore/__main__.py
lore/absorb.py
lore/classes.py
lore/classifier.py
lore/compiler.py
lore/consult.py
lore/evidence.py
lore/incidents.py
lore/placeholders.py
lore/prom_export.py
lore/runbook.py
lore/trigger.py
lore/validate.py
===== env reads in source =====
lore/placeholders.py:99:        "operator's secret store / environment config on the box, never "
lore/prom_export.py:17:    directory = Path(os.environ.get("H3_LORE_TEXTFILE_DIR", DEFAULT_TEXTFILE_DIR))
lore/validate.py:74:             the environment lacks the tool; NOT drift by itself
lore/validate.py:767:    Exit 127 is the shell's ``command not found`` — the environment lacks
lore/validate.py:775:        return "command not found on this box (exit 127) — environment absent"
lore/validate.py:939:        expectation still holds — the environment lacks the tool.
lore/validate.py:1087:    the environment lacks the command, not runbook rot) are not drift.
===== entry points =====
1087:def main(argv: list[str] | None = None) -> int:

===== CORPUS CENSUS (captured 2026-11-24 at 7945410 from /home/kara/get-h3/lore, same unchanged surfaces as above) =====
===== flags (candidate: expected hits; control in CAPS) =====
--explain      5
--class        16
--format       22
--evidence     4
--window       9
--trail-file   2
--ns           5
--board        4
--source       8
--failure      7
--detail       3
--json         3
--execute      19
--decision     3
--lesson       2
--reason       2
--ref          2
--record       4
--decided-at   1
CONTROL-lesson 2
===== verbs =====
match     42
compile   26
show      15
audit     31
absorb    32
consult   23
validate  47
gate      45
===== env var =====
README.md:285:`H3_LORE_TEXTFILE_DIR` to an existing writable directory to override it.
docs/INSTALL.md:424:`H3_LORE_TEXTFILE_DIR`. `lore_gate_runs_total` counts exported runs and
env_hits_rc=0
===== -m lore entry forms =====
README.md:43:uv run python -m lore match "drain 503"
README.md:55:uv run python -m lore match "secret .env clobber"
README.md:65:uv run python -m lore match "the coffee machine is making a weird noise"
README.md:83:uv run python -m lore match "gateway drain 503" --explain
README.md:100:uv run python -m lore compile --class gateway-drain-window --format md
README.md:133:uv run python -m lore compile --class does-not-exist ; echo "exit=$?"
README.md:301:uv run python -m lore consult "gateway drain 503" --json
docs/INSTALL.md:114:uv run python -m lore --help
docs/INSTALL.md:188:uv run python -m lore match "drain 503"
docs/INSTALL.md:198:uv run python -m lore match "secret .env clobber"
docs/INSTALL.md:206:uv run python -m lore match "key rotation expired"
docs/INSTALL.md:216:uv run python -m lore match "coffee machine"
===== lore gate flag specifics =====
README.md:262:   `lore gate --decision absorb --class <id> --lesson "<text>" --source dogfood-dagger`
README.md:267:   Example: `lore gate --decision no-new-lesson --reason "covered by v0.1 docs"
README.md:520:`lore compile`, `lore validate`, `lore gate`, `lore absorb`, `lore show` and
CHANGELOG.md:14:- **LORE-EXPORT-1** — `lore gate` exports its runs as a Prometheus textfile
CHANGELOG.md:213:- `lore consult` (LORE-007), `lore gate` (LORE-008), the `lore absorb
docs/INSTALL.md:417:   effect. Separately, `lore gate --record PATH` (opt-in) appends a JSONL

===== TIP ADVANCE RECORD (probes 7945410 -> cited tip) =====
git log --oneline 7945410..origin/main:
0b0fd37 evidence: bind gitreins run 8afd3ba1 (QA-LORE-6) — tier2 PASS verdict.json on tip f1ff0728
6b8b656 board: close QA-LORE-6 — tree-upgrade arm proven live (battery re-run upgrade OK, no false product FAIL)
f1ff072 evidence: QA-LORE-6 battery re-run proof — upgrade cell grades OK via tree arm (tick lore-foreman-2026-11-24-20-42-52)

git diff --stat 7945410..origin/main (tail):
 .coding-hermes/board/events.jsonl                  |   1 +
 .coding-hermes/board/tasks.jsonl                   |   2 +-
 .gitreins/history/2026-11-24/8afd3ba1/commit.patch | 151 ++++++
 .gitreins/history/2026-11-24/8afd3ba1/summary.md   |  48 ++
 .gitreins/history/2026-11-24/8afd3ba1/verdict.json | 557 +++++++++++++++++++++
 .../history/2026-11-24/8afd3ba1/worktree.patch     |  22 +
 .../lore-foreman-2026-11-24-20-42-52.txt           | 129 +++++
 7 files changed, 909 insertions(+), 1 deletion(-)
verdict: advance touches only .coding-hermes/board/* and .gitreins/history/*; no README.md, docs/*, lore/*, tests/* or scripts/* paths in the diff — audited surfaces byte-identical across the advance.

===== CLASS REGISTRY FROM PRODUCER =====
rows=14 curated=13 bucket: unclassified

===== UNKNOWN-CLASS EXIT CODES (README.md:134 exit=2 claim) =====
compile --class does-not-exist rc=2
error: unknown class_id 'does-not-exist'; registry is closed. Known: gateway-drain-window, shared-checkout-collision, secret-env-clobber, disk-pressure-corruption, cooldown-pin-drift, key-rotation-expiry, guard-degradation, spawn-hot-loop, ingest-backfill-gap, gateway-guard-violation, docs-count-drift, worktree-reap-data-loss, fast-forward-push-reject, unclassified
show does-not-exist rc=2
error: unknown class_id 'does-not-exist'; registry is closed. Known: gateway-drain-window, shared-checkout-collision, secret-env-clobber, disk-pressure-corruption, cooldown-pin-drift, key-rotation-expiry, guard-degradation, spawn-hot-loop, ingest-backfill-gap, gateway-guard-violation, docs-count-drift, worktree-reap-data-loss, fast-forward-push-reject, unclassified

===== QUICKSTART SAMPLE BYTE-CHECKS (README.md:42-134) =====
$ lore match "drain 503"
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain
$ lore match "secret .env clobber"
secret-env-clobber	confidence=0.90	evidence: signature:.env clobber; keyword:.env; keyword:clobber
$ lore match "the coffee machine is making a weird noise"
unclassified	confidence=0.00	evidence: none
$ lore match "gateway drain 503" --explain
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain; keyword:gateway
unclassified	confidence=0.00	evidence: none
near-misses:
  guard-degradation  score=0.17  (1/6 keywords: gate)
-- README quoted lines 49/59/69/87-91 --
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain
secret-env-clobber	confidence=0.90	evidence: signature:.env clobber; keyword:.env; keyword:clobber
unclassified	confidence=0.00	evidence: none
gateway-drain-window	confidence=0.90	evidence: signature:drain 503; keyword:503; keyword:drain; keyword:gateway
unclassified	confidence=0.00	evidence: none
near-misses:
  guard-degradation  score=0.17  (1/6 keywords: gate)
```

===== FINDING F1 (logsey export contract status): README.md:402-405 =====
- Evidence blocks (`lore/evidence.py`): the curated evidence-kind vocabulary,
  the logsey-export contract parser, and the honest degradation path
  (`degrade_to_command_output`) for as long as logsey's `export` subcommand is
  unimplemented. Attaching evidence never sets `last_validated`.
-- lore/evidence.py:10-19 docstring --
Logsey export contract — HONESTY LABEL:

    LOGSEY_EXPORT_CONTRACT_STATUS (below) names the truth: logsey's ``export``
    subcommand is PLANNED AND NOT IMPLEMENTED (logsey internal/cli/cli.go
    ``planned`` slice; README: "not implemented"), so there is NO frozen
    on-disk format to parse against today. :func:`parse_logsey_export` accepts
    the documented PRD-level contract shapes, tolerantly, and labels itself
    unfrozen. When logsey's export lands and freezes a wire format, tighten
    the parser here — nothing else in the model has to move.

-- lore/evidence.py LOGSEY_EXPORT_CONTRACT_STATUS (grep -n + body) --
58:LOGSEY_EXPORT_CONTRACT_STATUS = (
LOGSEY_EXPORT_CONTRACT_STATUS = (
    "unfrozen — logsey export subcommand not yet implemented "
    "(internal/cli/cli.go planned list)"
-- sibling logsey binary + repo (T3 on the sibling surface) --
13:  export         emit a timestamped evidence block for post-mortems
logsey version 0.2.1
-- logsey export --window 3m --format md (first 6 lines, rc=0) --
## logsey evidence block

- captured: 2026-11-24T21:16:50Z
- corpus: /home/kara/.local/share/logsey/corpus.jsonl
- window: last 3m (rows before 2026-11-24T21:13:50Z or without a parsable ts are excluded)
- engine: JSONL corpus mini-engine (pre-DuckDB, LOGSEY-006)
-- logsey repo: export landing commits --
e8ad93d 2026-11-24 15:03:26 -0500 board(logsey): file README-069 — status table lists export/doctor twice each (readme tick 19-48-16)
eba2b58 2026-10-29 04:46:43 -0500 logsey: merge wt/LOGSEY-104 — default export serves the fresh index, uncapped (LOGSEY-104)
5575d40 2026-10-29 03:46:12 -0500 logsey: default export serves the fresh DuckDB index, uncapped (LOGSEY-104)
43e2e55 2026-10-22 09:54:03 -0500 logsey: fix export OOM — stream corpus with window filter (QA-LOGSEY-9)

===== FINDING F2 (INSTALL --help paste gate line): docs/INSTALL.md:131-134 =====
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exit 0 =
                        allowed, 1 = denied
-- binary parent help gate entry (actual) --
usage: lore [-h] {match,consult,compile,validate,gate,absorb,show,audit} ...

Match symptoms and compile runbooks from fleet incident history.

positional arguments:
  {match,consult,compile,validate,gate,absorb,show,audit}
    match               classify a symptom text
    consult             tick-start consult (LORE-007): attach matching runbook
                        refs to work context; fail-open (no match = exit 0)
    compile             compile runbook proposal(s) per failure class (stdout
                        --execute to run the gate-approved read-only commands
    gate                closure absorb-gate (LORE-008): machine-check a lesson
                        decision (absorb or no-new-lesson ack); exports
                        node_exporter metrics; exit 0 = allowed, 1 = denied or
                        export failed

===== FINDING F3 (README:463 in-v0.1 qualifier) =====
  matrix: per registry class, runbook-compiled, check count, real-command count
  (vs the honest `no data` sentinel), and freshness. Freshness is honest:
  `last_validated` is never auto-populated in v0.1 — no code path writes it
  (a lint run is not operator attestation; operator attestation is planned,
  not implemented) — so every runbook says `no data` until a human attests.

===== ANCHOR RENDER CHECKS (public GitHub render) =====
install.md http=200 slug=1
readme.md http=200 slug=1

===== LINK / PATH-REF / ANCHOR CENSUSES (run at 7945410; docs unchanged across the advance) =====
root: /home/kara/get-h3/lore
markdown files scanned: 39 (excluded: .coding-hermes, evidence, dogfood, docs/qa, docs/acceptance, docs/release-evidence, build, .venv, .gitreins)
dead relative links: 0
distinct dead targets: 0
  resolve by suffix swap [('.md', '.spec.md')]: 0   <- mechanical generator class
  resolve neither way: 0   <- pages never captured; needs a manifest, not a rewrite
corpus files scanned: 39 (excluded: .coding-hermes, .gitreins, .venv, build, docs/acceptance, docs/qa, docs/release-evidence, dogfood, evidence)
path tokens resolved: 199

DEAD repo-path references (2 distinct) — candidates, read each line before filing:
  lore/scripts/bench.py                          cited at docs/dogfood/2026-10-17-run9-integration.md:87
  tests/test_x.py                                cited at docs/traceability-doctrine.md:37
(anchor census at 7945410: 259 md scanned, 0 dead internal anchors; both cited path-ref candidates are non-defects: tests/test_x.py is the doctrine's illustrative syntax example (docs/traceability-doctrine.md:37), lore/scripts/bench.py lives in the dogfood evidence tree docs/dogfood/2026-10-17-run9-integration.md:87)

===== BOARD OWNER SEARCH (board at cited tip) =====
RELEASE-LORE-002	complete	P1	[P1] QA blocking: PyPI distribution name lore is occupied by unrelated instacart/lore; decide a distinct distr
LORE-045	complete	P2	[P2] validate --execute results evaporate: a successful live lint leaves no trace anywhere — consult and compi
LORE-20261008	complete	P2	absorb --window fail-closed error is user-hostile: unparseable trail's error text quotes internal tooling stat
LORE-053	complete	P2	absorb --window fail-closed error teaches nothing: identical text for unrelated noise and a real export missin
rows parsed: 160 (skipped non-object/unparseable lines: 0)
hits: 5

===== DIGEST =====
