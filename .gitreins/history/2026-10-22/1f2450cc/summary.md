# Verdict: LORE-069

**Task:** Wire existing runbook into absorb_proposal so absorb emits UPDATE action
**Evaluated:** 2026-10-22T14:38:09.513639
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ ACCEPTANCE: for a curated class with an existing runbook and a trail that adds evidence, run the absorb sweep in its documented window mode (option named in usage: lore absorb [-h] [--class CLASS_ID] [--lesson LESSON] [--window WINDOW]
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
                        'source' key)): expect action printed as update with a NON-EMPTY changed or added key naming the trail-derived content; a no-change trail expect an explicitly empty update (never new); `grep -rn 'existing='` lore expect at least 1 production hit; tests pin both cases at the absorb_proposal seam.: All sub-requirements verified with live output. (a) `uv run python -m lore absorb --help` prints the usage block byte-identical to the criterion (parser at lore/__main__.py:915-974). (b) Sweep on curated class gateway-drain-window with a 2-block trail: `uv run python -m lore absorb --window 2h --trail-file /tmp/trail.txt` -> exit 0, printed "class_id": "gateway-drain-window", "action": "update", "added": {"evidence_trail": [{"kind":"logsey-export","detail":"kind=incident detail='gateway drain 503 during rollout, retried and recovered'"}, ...]} — non-empty added key naming trail-derived content. (c) No-change trail: absorb_proposal('gateway-drain-window','plain prose, no timestamp') -> {"action":"update","added":{},"removed":{},"changed":{},"blocks":[]}; `printf 'nothing here' | lore absorb --window 45m` -> "no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)" exit 0; propose() with existing=None still yields action "new" (default path unchanged, lore/compiler.py:1011). (d) `grep -rn 'existing=' lore` -> 1 production hit: lore/absorb.py:315 `payload = propose(class_id, existing=existing, fresh=fresh)`. (e) Tests pin both cases at the absorb_proposal seam: tests/test_absorb.py:360 test_absorb_proposal_update_on_lesson_with_timestamped_evidence_lines (asserts action=="update", non-empty added.evidence_trail, removed=={}) and tests/test_absorb.py:390 test_absorb_proposal_no_change_trail_is_explicit_empty_update (asserts action=="update", added/removed/changed=={}), plus :405 prose variant. (f) Fresh test runs: `uv run pytest tests/test_absorb.py -q --tb=short` -> exit_code 0, "38 passed in 0.06s"; full config test_command `uv run pytest -x --tb=short -q` -> exit_code 0, "557 passed in 3.13s".
absorb_proposal now diffs the folded trail against the existing compiled runbook, emitting action=update with a non-empty added.evidence_trail for evidence-adding trails and an explicitly empty update for no-change trails, with both cases pinned by passing tests and a production `existing=` hit at lore/absorb.py:315.

## Summary

Judge Result: LORE-069

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ ACCEPTANCE: for a curated class with an existing runbook and a trail that adds evidence, run the absorb sweep in its documented window mode (option named in usage: lore absorb [-h] [--class CLASS_ID] [--lesson LESSON] [--window WINDOW]
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
                        'source' key)): expect action printed as update with a NON-EMPTY changed or added key naming the trail-derived content; a no-change trail expect an explicitly empty update (never new); `grep -rn 'existing='` lore expect at least 1 production hit; tests pin both cases at the absorb_proposal seam.: All sub-requirements verified with live output. (a) `uv run python -m lore absorb --help` prints the usage block byte-identical to the criterion (parser at lore/__main__.py:915-974). (b) Sweep on curated class gateway-drain-window with a 2-block trail: `uv run python -m lore absorb --window 2h --trail-file /tmp/trail.txt` -> exit 0, printed "class_id": "gateway-drain-window", "action": "update", "added": {"evidence_trail": [{"kind":"logsey-export","detail":"kind=incident detail='gateway drain 503 during rollout, retried and recovered'"}, ...]} — non-empty added key naming trail-derived content. (c) No-change trail: absorb_proposal('gateway-drain-window','plain prose, no timestamp') -> {"action":"update","added":{},"removed":{},"changed":{},"blocks":[]}; `printf 'nothing here' | lore absorb --window 45m` -> "no classifiable evidence blocks in the trail (no blocks found — nothing proposed, nothing written)" exit 0; propose() with existing=None still yields action "new" (default path unchanged, lore/compiler.py:1011). (d) `grep -rn 'existing=' lore` -> 1 production hit: lore/absorb.py:315 `payload = propose(class_id, existing=existing, fresh=fresh)`. (e) Tests pin both cases at the absorb_proposal seam: tests/test_absorb.py:360 test_absorb_proposal_update_on_lesson_with_timestamped_evidence_lines (asserts action=="update", non-empty added.evidence_trail, removed=={}) and tests/test_absorb.py:390 test_absorb_proposal_no_change_trail_is_explicit_empty_update (asserts action=="update", added/removed/changed=={}), plus :405 prose variant. (f) Fresh test runs: `uv run pytest tests/test_absorb.py -q --tb=short` -> exit_code 0, "38 passed in 0.06s"; full config test_command `uv run pytest -x --tb=short -q` -> exit_code 0, "557 passed in 3.13s".
absorb_proposal now diffs the folded trail against the existing compiled runbook, emitting action=update with a non-empty added.evidence_trail for evidence-adding trails and an explicitly empty update for no-change trails, with both cases pinned by passing tests and a production `existing=` hit at lore/absorb.py:315.

Overall: PASS ✓
