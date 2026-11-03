# QA-LORE-FOREMAN-1 battery attempt R2

The runner reached bunker-mvp but could not spawn an agent. The exact failure was:

`spawn failed on bunker-mvp: spawn attempt 2 failed: bunker: spawn agent: unavailable: dial tcp 100.115.67.116:19090: connect: connection refused`

No lore product cells executed; the result is UNVERIFIED, not a product failure. The runner wrote one lifecycle `run_battery` FAIL record to `battery-r2.jsonl`, bound to tested repository HEAD `3f4be19a164177bc80a2f6e7488af646420826bb`.

The preflight host disk reading was previously below the 94% threshold (`df -P /`: 87%), but the bunker control endpoint became unavailable before agent spawn. A later `bunker list --server bunker-mvp --status all` also returned connection refused. This artifact does not authorize host cleanup or claim battery coverage.

ch:trace row=QA-LORE-FOREMAN-1 spec=docs/qa/evidence/run-QA-LORE-FOREMAN-1/README.md#4 wave=.coding-hermes/waves/lore-foreman-2026-11-03-20-34-57.json#QA-LORE-FOREMAN-1 test=none:detached-bunker-battery doc=docs/qa/evidence/run-QA-LORE-FOREMAN-1/battery-r2-summary.md evidence=docs/qa/evidence/run-QA-LORE-FOREMAN-1/battery-r2.jsonl witness=none:bunker-mvp-control-endpoint-unreachable verdict=none:pending-foreman-judge commit=none:worker-commit memory=none:foreman-closeout
STATUS: partial
TIER: T3
EVIDENCE: docs/qa/evidence/run-QA-LORE-FOREMAN-1/battery-r2.jsonl
