# LORE-067-R3 — incident coverage path, live acceptance evidence

HEAD at run: `9d6bb0d` + this task's diff (branch `wt/LORE-067-R3`).
Method: two throwaway scratch directories, each with its own
`.coding-hermes/board/`, driven by the REAL CLI subprocess:

```sh
cd /tmp/lore067-accept-a && <repo>/.venv/bin/python -m lore audit --format json
cd /tmp/lore067-accept-b && <repo>/.venv/bin/python -m lore audit --format json
```

Raw JSON is stored beside this note as `accept-1-novel-class.json` and
`accept-2-old-prose.json`.

## Acceptance 1 — in-window event names a class with no runbook

Board: `.coding-hermes/board/events.jsonl` holds exactly one event,

```json
{"timestamp":"2026-10-24T05:37:00+00:00","detail":{"class_id":"postgres-deadlock-storm","action":"new"}}
```

Result (from `accept-1-novel-class.json`):

```json
{
  "incident_count": 1,
  "incident_seen_rows": [],
  "uncovered_classes": ["postgres-deadlock-storm"]
}
```

`summary.uncovered_classes` carries the class, and `summary.incident_count`
carries the event count. (No registry row is emitted for a class the registry
does not know — the report is the summary entry, per the row's acceptance
"either/or".)

## Acceptance 2 — generic in-window event + 2024 prose-only tasks

Board: one generic in-window event plus `tasks.jsonl` holding a 2024-dated
task whose `title` is `mention gateway-drain-window in passing` and whose
`detail` is `documentation prose only`.

Result (from `accept-2-old-prose.json`):

```json
{
  "incident_count": 1,
  "incident_seen_rows": [],
  "uncovered_classes": []
}
```

No row reports `incident_seen`, and the uncovered list stays empty: the old
task is both outside the 90-day window and prose-only, so it manufactures no
incident.

## Red proof

With `lore/incidents.py` and `lore/__main__.py` reverted to `HEAD` (fix
removed), `tests/test_lore067_incident_audit.py` fails both cases with
`KeyError: 'incident_count'`; restored, both pass.
