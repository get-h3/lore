# Auger spec export — namespace golden-ns

Read-only deterministic rendering of every declared table.
Scope: whole namespace (no rows are written).

## Decisions (2 rows)
### D-001
- id: D-001
- project_id: P-000001
- chosen: pause before gateway restart
- why_not: restart immediately breaks in-flight requests
- confidence: 0.8
- status: answered

## Assumptions (1 rows)
### A-001
- id: A-001
- project_id: P-000001
- text: the drain window remains bounded
- falsifier: 503s continue after 30 minutes

## Unknowns (1 rows)
### U-001
- id: U-001
- project_id: P-000001
- text: whether queued state survives restart
- owner: gateway-team
- trigger: next restart drill
- containment: pause rollout

## Break records (1 rows)
### BR-000001
- id: BR-000001
- project_id: P-000001
- decision_id: D-001
- breaks_what: immediate restart
- consequence: in-flight requests return 503
