"""lore.compiler — runbook compiler per failure class.

PROPOSE-NOT-WRITE (hard design law, PRD risk section):

    The compiler NEVER writes a runbook into a published location. Its output
    is always an in-memory object or a structured diff/proposal — an operator
    publishes, never the compiler. This module therefore exposes NO
    ``publish`` / ``write_runbook`` / ``save`` entry point, performs no
    filesystem writes, and this rule is enforced by a test
    (``tests/test_compiler.py::test_no_publish_entrypoint``).

Signature rule: the runbook's ``signature`` is the class's FIRST curated
signature pattern (``signature_patterns[0]``). The full ordered pattern list
stays in ``lore.classes`` — the runbook carries the strongest/most readable
identifying pattern and points provenance at the registry for the rest.

Evidence / honesty rules (README "Design laws this repo inherits"):

- A runbook compiled WITHOUT explicit validated evidence carries
  ``last_validated=None`` (never a fabricated date) and ``status="proposal"``.
- Absent sections render as ``no data`` (see ``lore.runbook.Runbook.to_markdown``),
  never as zero or an empty success.
- ``unclassified`` compiles too, but honestly: it is a catch-all with NO
  recovery ladder derivable from history — its runbook says so instead of
  inventing one.
- Each per-class check set is seeded from the fleet's REAL incident history
  (PRD §"The problem, measured" cases 1-3 and the cited gap/board/commit
  trails). Where a fleet-real command exists it is used verbatim-shaped; where
  this repo has no sourced command the check says so instead of fabricating.
"""

from __future__ import annotations

from lore.classes import UNCLASSIFIED_ID, FailureClass, get_registry
from lore.runbook import (
    STATUS_PROPOSAL,
    STATUS_VALIDATED,
    Check,
    Runbook,
)

__all__ = [
    "NO_VALID_EVIDENCE",
    "UNCLASSIFIED_NO_LADDER",
    "Check",
    "Runbook",
    "compile_all",
    "compile_class",
    "propose",
    "render_proposal_diff",
]

# Honest-absence sentinel used in commands/expected fields the fleet trail
# does NOT actually source: rendered as "no data", never a fabricated command.
NO_VALID_EVIDENCE = "no data"

# The honest statement unclassified carries instead of an invented ladder.
UNCLASSIFIED_NO_LADDER = (
    "no recovery ladder exists for the catch-all class: it is not a specific "
    "failure, so no history-derived ladder can be honestly stated. Absorb the "
    "symptom into a curated class (or propose a new one with operator approval) "
    "and use that class's runbook."
)

# ---------------------------------------------------------------- checks
# Per-class ordered diagnostic checks, seeded from the fleet's REAL incident
# trail. Every command is read-only/verify/dry-run/SELECT-only unless marked
# MUTATING with the guardrail that gates it. Expected outputs describe the
# fleet's observed healthy vs incident shapes.
#
# Evidence kinds: "board" (row/task id), "gap" (named gap id), "commit",
# "incident" (post-mortem reference), "memory" (curated note reference).

_CHECKS: dict[str, list[Check]] = {
    "gateway-drain-window": [
        Check(
            order=1,
            command="logsey query --pattern 'drain 503' --since 30m",
            expected_healthy="no rows",
            expected_incident="503s on in-flight requests while the gateway restarts/reloads",
            decision="confirm the class signature before touching anything",
            read_only=True,
            evidence=[
                {"kind": "incident", "detail": "PRD §The problem, measured case 1"}
            ],
        ),
        Check(
            order=2,
            command="grep -c 'drain 503' <gateway-log-path>",
            expected_healthy="0",
            expected_incident="non-zero and rising over the drain window (up to ~30 min)",
            decision="distinguish a drain window (bounded, expected) from a wedged gateway",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "four gateway-restart incidents pre-doctrine",
                },
                {"kind": "memory", "detail": "curated note: drain 503s kill ticks"},
            ],
        ),
        Check(
            order=3,
            command="curl -s -o /dev/null -w '%{http_code}' <gateway-health-url>",
            expected_healthy="200",
            expected_incident="503 during drain; 200 again once in-flight requests finish",
            decision="pause-first decision: hold config rollout until health returns 200",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "gateway restart doctrine: pause-first under load",
                }
            ],
        ),
        Check(
            order=4,
            command="grep -c 'enabled.*false' <scheduler-fleet-config>",
            expected_healthy="the projects about to be affected are already disabled (writes paused)",
            expected_incident="0 — writes were NOT paused before the restart (config-driven writes 503 during restart)",
            decision=(
                "pause writes FIRST: flip scheduler enabled=false / pause lanes before "
                "touching the gateway; enqueue-not-drop keeps queued work alive"
            ),
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "2026-08-27T09:45Z post-mortem: config writes during a gateway restart 503'd; work that was enqueued instead of dropped survived the restart",
                }
            ],
        ),
        Check(
            order=5,
            command="curl -s <gateway-metrics-url> | grep -c 'in_flight'",
            expected_healthy="in-flight counter present and steady",
            expected_incident="in-flight counter draining slowly (up to ~30 min) — a restart issued now 503s the remainder",
            decision=(
                "gate the restart on the in-flight counter reaching 0: announce the drain "
                "window, never hard-kill (SIGKILL) with requests still in flight"
            ),
            read_only=True,
            evidence=[
                {
                    "kind": "logsey-export",
                    "detail": "2026-08-14T02:07:41Z hermes-gateway: SIGKILL received during load; 214 in-flight requests terminated with 503",
                },
                {
                    "kind": "incident",
                    "detail": "2026-09-16T19:05Z post-mortem: across incidents 3-4 the drain window was observed at 25-30 min; dependents were not warned in advance during incidents 1-3",
                },
            ],
        ),
        Check(
            order=6,
            command="wc -l <gateway-queue-path>",
            expected_healthy="queue empty or at its steady-state depth",
            expected_incident="queue_depth > 0 with unflushed rows — restarting now loses the queued state",
            decision="never restart with queued unflushed state: check queue depth FIRST and drain or flush before the restart",
            read_only=True,
            evidence=[
                {
                    "kind": "logsey-export",
                    "detail": "2026-09-05T14:02:55Z hermes-gateway: restart executed with queue_depth=14 unflushed rows; queued state lost on restart",
                }
            ],
        ),
        Check(
            order=7,
            command="logsey query --pattern 'SIGKILL|503' --since 60m",
            expected_healthy="no SIGKILL lines; 503 count at baseline (0/hour)",
            expected_incident="SIGKILL during load, or 503 count above the pre/post-restart baseline",
            decision=(
                "verify with read-only probes only: keep before/after error-rate deltas as "
                "evidence; reload gracefully (never SIGKILL) and re-check /health"
            ),
            read_only=True,
            evidence=[
                {
                    "kind": "logsey-export",
                    "detail": "2026-09-16T18:35:02Z hermes-gateway: fourth gateway-restart incident: 96 503s inside the incident window; baseline outside the window measured 0 per hour",
                },
                {
                    "kind": "incident",
                    "detail": "2026-09-12T22:00Z post-mortem: the graceful reload produced no hard-kill lines in the gateway log; the 503 spikes traced to hard kills in incidents 1-3",
                },
            ],
        ),
    ],
    "shared-checkout-collision": [
        Check(
            order=1,
            command="git status --short",
            expected_healthy="only your own intended edits (or nothing)",
            expected_incident="staged files you did not stage (a sibling swept them), or staged set ≠ your edit",
            decision="re-verify the staged set before any commit; recover via path-limited reset --soft if swept",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "sibling worker git add -A swept in-flight files",
                },
                {
                    "kind": "gap",
                    "detail": "introspection-tests-and-sibling-sweeps: cannot lock ref 'HEAD' tell",
                },
            ],
        ),
        Check(
            order=2,
            command="ls .git/index.lock 2>/dev/null; ps aux | grep -c '[g]it '",
            expected_healthy="no index.lock; no other git process on this checkout",
            expected_incident="index.lock present or a sibling git process alive on the same checkout",
            decision="if a sibling is live: do NOT rm the lock; coordinate instead",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "index.lock fights between concurrent workers",
                }
            ],
        ),
        Check(
            order=3,
            command="git worktree list",
            expected_healthy="expected worktrees only, each with its own branch",
            expected_incident="a just-dispatched worker's worktree is gone (reaped) or doubled up",
            decision="if a fresh zero-commit worktree vanished: reap ran mid-wave — re-dispatch, never blame the worker",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "worktree.sh reap --all deleted a fresh zero-commit worktree (crier t363)",
                }
            ],
        ),
    ],
    "secret-env-clobber": [
        Check(
            order=1,
            command="docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | head -20",
            expected_healthy="live secret-bearing values present",
            expected_incident="example/placeholder values (key 401s downstream)",
            decision="confirm the clobber before any rewrite",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "PRD §The problem, measured case 3: recovery required reading Docker env by hand",
                }
            ],
        ),
        Check(
            order=2,
            command="diff <(grep -o '^[A-Z_]*' .env | sort) <(grep -o '^[A-Z_]*' .env.example | sort)",
            expected_healthy="key SETS differ: example is a subset/superset only in shape, values never compared",
            expected_incident="example twin overwrote live keys (same key names, placeholder values)",
            decision="decide which generations to restore; diff four secret generations by hand if lineage unclear",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": ".env/.env.example twin-clobber broke central logins until repaired by hand",
                }
            ],
        ),
    ],
    "disk-pressure-corruption": [
        Check(
            order=1,
            command="df -h <affected-volume>",
            expected_healthy="use% well under capacity",
            expected_incident="100%/near-full volume (ENOSPC context)",
            decision="confirm pressure as the corruption cause before repairing data",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "ENOSPC sqlite header wipe + truncated JSONL events",
                }
            ],
        ),
        Check(
            order=2,
            command="sqlite3 <db> 'PRAGMA quick_check;'",
            expected_healthy="ok",
            expected_incident="corruption errors naming page/header damage",
            decision="choose repair path: page-level recovery vs restore from backup snapshot",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "sqlite header-wipe corruption on fleet storage",
                }
            ],
        ),
        Check(
            order=3,
            command='tail -c 200 <truncated.jsonl> | python3 -c "import sys,json; [json.loads(l) for l in sys.stdin if l.strip()]"',
            expected_healthy="every line parses",
            expected_incident="JSONDecodeError on the torn final line",
            decision="torn-tail vs mid-file corruption: torn tail = truncate last line + re-sync writer",
            read_only=True,
            evidence=[
                {"kind": "incident", "detail": "truncated JSONL reads failing DuckDB"}
            ],
        ),
    ],
    "cooldown-pin-drift": [
        Check(
            order=1,
            command="jq -r 'select(.id==\"<project-row>\") | .status' <board>/tasks.jsonl | tail -1",
            expected_healthy="status agrees with fleet.toml for the same project",
            expected_incident="DB says paused/one value; fleet.toml says another (dual-store divergence)",
            decision="identify which store is authoritative for this pin before ANY change",
            read_only=True,
            evidence=[
                {
                    "kind": "gap",
                    "detail": "SCHED-GAP-025 → SCHED-GAP-121: same drift bit twice",
                },
                {
                    "kind": "incident",
                    "detail": "PUT casing pitfall: snake_case is canonical, PascalCase 200-noops",
                },
            ],
        ),
        Check(
            order=2,
            command="grep -A2 '\\[\\[projects\\]\\]' fleet.toml | grep -E 'name|enabled' ",
            expected_healthy="pin matches the DB side for the same project name",
            expected_incident="fleet.toml pin disagrees with the DB row",
            decision="pick the store with the fresher validated write; fix the OTHER store only",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "dual-store pins diverge silently between deploys",
                }
            ],
        ),
        Check(
            order=3,
            command="<scheduler-cli> set-cooldown <project> --verify",
            expected_healthy="--verify reports the change WITHOUT applying it (tripwire output)",
            expected_incident="--verify output disagrees with what a real apply would do, or the flag is gone",
            decision="dry-run tripwire before any real apply; if --verify is missing, the CLI changed — stop",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "the --verify tripwire was learned across two cooldown incidents",
                }
            ],
        ),
    ],
    "key-rotation-expiry": [
        Check(
            order=1,
            command="curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer <key>' <provider-url>/models",
            expected_healthy="200",
            expected_incident="401 across lanes while the key looks configured",
            decision="confirm expiry vs misconfiguration before re-issuing",
            read_only=True,
            evidence=[
                {"kind": "incident", "detail": "cross-lane 401 storms after rotation"}
            ],
        ),
        Check(
            order=2,
            command="grep -c '<key-name>' <service-config-path>",
            expected_healthy="key name present exactly where expected",
            expected_incident="key name absent, or present in a config file the service does not read",
            decision="distinguish 'key expired' from 'key never reached the consuming service'",
            read_only=True,
            evidence=[
                {"kind": "incident", "detail": "expired keys that looked configured"}
            ],
        ),
    ],
    "guard-degradation": [
        Check(
            order=1,
            command="git -C <main-tree> rev-parse HEAD && git -C <worktree> rev-parse HEAD",
            expected_healthy="same commit in both contexts",
            expected_incident="guard passed at a different commit than the gate runs at",
            decision="before trusting any guard result, pin WHICH commit it ran at",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "guard passed in worktree, main-tree gate failed at the same commit",
                }
            ],
        ),
        Check(
            order=2,
            command="git -C <main-tree> worktree add <control-wt> <same-commit>  # run the failing check there, then remove",
            expected_healthy="control worktree reproduces the PASS → context was the variable",
            expected_incident="control worktree FAILS → the failure is real and commit-owned, not context-owned",
            decision="prove gate-equivalence with a control worktree in the main tree before re-dispatching",
            read_only=False,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "control-worktree proof separated context failure from commit failure",
                }
            ],
        ),
    ],
    "spawn-hot-loop": [
        Check(
            order=1,
            command="ls -la <worker-log> && stat -c %s <worker-log>",
            expected_healthy="log growing after a spawn",
            expected_incident="-Q log stuck at 0 bytes across respawns",
            decision="empty log + rising CPU = the spawn itself is wedged; do NOT re-dispatch the same way",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "worker spin: -Q log at 0 bytes, rising CPU, no repo writes",
                }
            ],
        ),
        Check(
            order=2,
            command="ps -o pid,etime,pcpu,cmd -p <worker-pid>",
            expected_healthy="worker alive with plausible CPU",
            expected_incident="CPU climbing with zero output (spin) or process zombie",
            decision="kill by pid; land any in-tree work directly before any re-dispatch",
            read_only=True,
            evidence=[
                {
                    "kind": "gap",
                    "detail": "spawn-deaths: judge liveness via state.db messages, never the -Q log",
                }
            ],
        ),
        Check(
            order=3,
            command="grep -c 'spawn' <scheduler-log> --since-marker",
            expected_healthy="spawn count matches intended dispatches",
            expected_incident="spawn count far above intended dispatches (hot loop)",
            decision="find the loop trigger (bad exit code swallowed, deadline misread) before the next spawn",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "scheduler respawning the same tick repeatedly",
                }
            ],
        ),
    ],
    "ingest-backfill-gap": [
        Check(
            order=1,
            command="wc -l <destination.jsonl> && tail -1 <destination.jsonl>",
            expected_healthy="row count plausible for the window; last row timestamp is recent",
            expected_incident="last row timestamp STOPS inside the suspected window (hole starts there)",
            decision="measure the DESTINATION, never the pipeline's success status",
            read_only=True,
            evidence=[
                {
                    "kind": "gap",
                    "detail": "CHATGAP-001: cron status lied; destination coverage is the truth",
                }
            ],
        ),
        Check(
            order=2,
            command="grep -c '<window-start-ts>' <destination.jsonl>",
            expected_healthy="> 0 (rows exist at the window start)",
            expected_incident="0 rows in the named window",
            decision="name the window exactly before any backfill attempt",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "08-29/30 chat-archive hole, unrecoverable, annotated as a named gap",
                }
            ],
        ),
    ],
    "gateway-guard-violation": [
        Check(
            order=1,
            command="grep -n 'gateway\\|guard\\|denied' <guard-log-tail> | tail -20",
            expected_healthy="guard verdict lines name the failing lane and reason",
            expected_incident="a DENIED/banned verdict for a specific command text",
            decision="capture the exact command text that tripped the guard — it is the fix target",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "2026-09-24 dogfood: banned command tripped the gateway guard",
                }
            ],
        ),
        Check(
            order=2,
            command="grep -c 'DENIED\\|banned' <guard-log-tail>",
            expected_healthy="0 (no guard blocks in the window)",
            expected_incident="the same block repeats across ticks",
            decision="a repeated block is a reshaping bug, not a transient — attribute before retrying",
            read_only=True,
            evidence=[
                {
                    "kind": "gap",
                    "detail": "repeated guard failures mean the command shape, not the guard, is broken",
                }
            ],
        ),
    ],
    "docs-count-drift": [
        Check(
            order=1,
            command=(
                "python3 -c \"import sys, pytest; pytest.main(['--collect-only', "
                "'-q', '-p', 'no:cacheprovider'])\" | tail -1"
            ),
            expected_healthy="collected count equals the canonical count file",
            expected_incident="collected count differs from the doc-claimed count",
            decision="recount from source (the collector), never from the docs",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "LORE-029 count-sync guard: live collection is the truth",
                }
            ],
        ),
        Check(
            order=2,
            command="grep -rnE '[0-9]{2,4} (passed|tests)' README.md docs/ skills/",
            expected_healthy="every count literal equals the canonical count",
            expected_incident="a living doc cites a count that no longer matches",
            decision="list every stale literal before editing — drift is rarely in one file",
            read_only=True,
            evidence=[
                {
                    "kind": "incident",
                    "detail": "LORE-019: README test-count literal went stale after a wave",
                }
            ],
        ),
    ],
    UNCLASSIFIED_ID: [],
}
_RECOVERY_LADDERS: dict[str, list[str]] = {
    "gateway-drain-window": [
        "Stop config changes: batch them instead of trickling under load.",
        "Pause-first under load: hold the rollout until in-flight requests finish.",
        "Announce the expected drain window (up to ~30 min) to dependents before restarting.",
        "Watch drain-503 volume fall to zero, then confirm health endpoint 200 before resuming.",
    ],
    "shared-checkout-collision": [
        "Re-verify the staged set with a path-limited diff before committing anything.",
        "If a sibling swept your files: git reset --soft, re-stage ONLY your paths, commit path-limited.",
        "If index.lock is held by a LIVE sibling: coordinate; never rm the lock blindly.",
        "Land your work, then let the end-of-tick reap run — never mid-wave.",
    ],
    "secret-env-clobber": [
        "Read the live container env by hand (docker inspect) to establish what the service ACTUALLY sees.",
        "Diff the secret generations to find which value set is the live one.",
        "Repair the container env from the verified live generation, one key at a time.",
        "Re-verify the downstream auth path returns 200 before declaring recovery.",
    ],
    "disk-pressure-corruption": [
        "Free or expand the pressured volume FIRST — repair on a still-full volume re-corrupts.",
        "Snapshot the damaged DB before any repair attempt (never repair the only copy).",
        "Repair or restore; for torn JSONL, truncate the torn tail and re-sync the writer.",
        "Re-run the integrity probe (PRAGMA quick_check / re-parse) before resuming writers.",
    ],
    "cooldown-pin-drift": [
        "Determine the authoritative store for this pin (validated write recency), never assume.",
        "Fix ONLY the non-authoritative store.",
        "Dry-run the change with --verify and compare tripwire output to intent.",
        "Read the state back from BOTH stores to confirm convergence before resuming the project.",
    ],
    "key-rotation-expiry": [
        "Confirm which lanes 401 and whether the key is expired, revoked, or mis-wired.",
        "Re-issue/rotate the key at the provider.",
        "Propagate to EVERY consuming config (missing one lane re-creates the storm).",
        "Probe each lane with a real authenticated request, not a config read.",
    ],
    "guard-degradation": [
        "Pin the exact commit the guard ran at (rev-parse in BOTH contexts).",
        "Reproduce the failure in a control worktree at the SAME commit in the main tree.",
        "If the control fails: the failure is real — carry the staged patch to the main tree, re-proof, gate, commit there.",
        "If the control passes: the context was the variable — fix the context, not the commit.",
    ],
    "spawn-hot-loop": [
        "Stop the loop: kill the spinning worker by pid.",
        "Read state.db messages.tool_calls to judge what the session actually did (the -Q log is not liveness).",
        "Salvage any in-tree work and commit it before any re-dispatch.",
        "Re-dispatch with the spawn mechanics fixed (e.g. pty/background form), never the identical way.",
    ],
    "ingest-backfill-gap": [
        "Measure destination coverage over the exact window; treat pipeline success status as hearsay.",
        "Name the gap precisely (start/end timestamps) and annotate it where responders will look.",
        "Attempt backfill only from a source proven to still hold the window.",
        "If unrecoverable, record the gap as permanent and named — never silently zero it.",
    ],
    "gateway-guard-violation": [
        "Stop: read the guard's own verdict — which command text was denied and by which rule.",
        "Re-shape the command: split it into smaller steps, or use an allowed verb/tool for the same job.",
        "Sandbox or route it: run the risky part where it is permitted (a scope that allows it, an approved wrapper).",
        "Re-run the re-shaped form; a second denial of the ORIGINAL text means the shape never changed.",
    ],
    "docs-count-drift": [
        "Recount from source (pytest --collect-only, wc -l, the producer) — never from the docs.",
        "Sync every stale count literal in living docs in the SAME commit as the change.",
        "Let the count-sync guard sweep living docs; fix everything it names, not just the one you noticed.",
        "Prefer DERIVED counts in docs/tests over hardcoded literals (LORE-017 precedent).",
    ],
    UNCLASSIFIED_ID: [],
}

_GUARDRAILS: dict[str, list[str]] = {
    "gateway-drain-window": [
        "Never restart the gateway with in-flight requests still draining from the previous restart.",
        "Never treat drain 503s as a gateway fault — during a drain window they are EXPECTED; distinguish bounded drain from wedged before acting.",
        "Never trickle config changes under load — batch them and pause-first.",
    ],
    "shared-checkout-collision": [
        "Never put two workers in one shared checkout.",
        "Never run worktree.sh reap --all except at end-of-tick post-merge — it deletes fresh zero-commit worktrees.",
        "Never git add -A / git add . in a shared tree — stage your own paths explicitly.",
        "Never rm a live sibling's index.lock — coordinate instead.",
    ],
    "secret-env-clobber": [
        "Never copy .env.example over .env (or deploy an example twin over live secrets).",
        "Never rewrite container env from the config FILE alone — verify what the container actually sees first.",
        "Never compare secret VALUES in a diff that could land in logs — compare key NAMES, repair values out-of-band.",
    ],
    "disk-pressure-corruption": [
        "Never repair a database while its volume is still pressured — free space first.",
        "Never repair the only copy — snapshot before touching.",
        "Never resume writers before the integrity probe passes.",
    ],
    "cooldown-pin-drift": [
        "Never run --apply on a cooldown policy while a drain is in progress.",
        "Never --apply without a --verify dry-run first (the tripwire exists because of SCHED-GAP-025/121).",
        "Never fix both stores in one shot — identify the authoritative store, fix the other, then converge.",
        "Never trust a 200 from a pin write — PUT casing noops return 200; read the state back.",
    ],
    "key-rotation-expiry": [
        "Never revoke a key before its replacement is live in every consuming config.",
        "Never declare rotation done from a config write alone — probe one real authenticated request per lane.",
    ],
    "guard-degradation": [
        "Never trust a worktree guard result as gate-equivalent — prove with a control worktree in the main tree.",
        "Never re-dispatch on a worktree failure — prove context-vs-commit first (pristine control worktree at the same commit).",
        "Never bypass a guard before attributing the failure to the baseline (run the guard's own lint on the base blob).",
    ],
    "spawn-hot-loop": [
        "Never re-dispatch an identical spawn while a worker is spinning — kill by pid first.",
        "Never judge worker liveness by the -Q log alone — read state.db messages.",
        "Never re-dispatch before committing any in-tree work the dead worker left behind.",
    ],
    "ingest-backfill-gap": [
        "Never leave a capture gap unannotated — name the window exactly.",
        "Never trust a pipeline's own success status as evidence of capture — verify DESTINATION coverage.",
        "Never claim backfilled data that the destination cannot show; an unrecoverable gap stays named.",
    ],
    "gateway-guard-violation": [
        "Never retry a banned command verbatim — a hardline block is deterministic, retrying proves nothing.",
        "Never weaken or bypass the guard to let one command through — re-shape the command instead.",
        "Never treat a guard block as a transient — the same denial repeating across ticks is a reshaping bug.",
    ],
    "docs-count-drift": [
        "Never hardcode a test/class count in a test — derive it from the source of truth.",
        "Never ship a count-changing wave without syncing the doc literals in the same commit.",
        "Never 'fix' the doc by rounding to a vague phrase — the guard needs exact numbers.",
    ],
    UNCLASSIFIED_ID: [],
}

# Per-class evidence trail: DuckBrain rows / board events / commits where the
# steps were learned. Honest scope: these reference the fleet trail the seed
# was compiled from (board row LORE-003 named the same incidents).
_EVIDENCE_TRAILS: dict[str, list[dict]] = {
    "gateway-drain-window": [
        {"kind": "board", "detail": "LORE-003 seed class 'gateway drain window'"},
        {
            "kind": "incident",
            "detail": "PRD §The problem, measured case 1 (four incidents + compaction-boundary loss)",
        },
        {"kind": "memory", "detail": "curated note 'drain 503s kill ticks'"},
    ],
    "shared-checkout-collision": [
        {"kind": "board", "detail": "LORE-003 seed class 'shared-checkout collision'"},
        {
            "kind": "incident",
            "detail": "worktree reap deletion of a fresh zero-commit worktree (crier t363)",
        },
        {
            "kind": "gap",
            "detail": "sibling-sweep recovery: git reset --soft + path-limited restage",
        },
    ],
    "secret-env-clobber": [
        {"kind": "board", "detail": "LORE-003 seed class 'secret/env clobber'"},
        {
            "kind": "incident",
            "detail": "PRD §The problem, measured case 3 (.env/.env.example twin clobber)",
        },
    ],
    "disk-pressure-corruption": [
        {"kind": "board", "detail": "LORE-003 seed class 'disk-pressure corruption'"},
        {
            "kind": "incident",
            "detail": "ENOSPC sqlite header wipe + JSONL truncation on fleet storage",
        },
    ],
    "cooldown-pin-drift": [
        {"kind": "board", "detail": "LORE-003 seed class 'cooldown pin drift'"},
        {
            "kind": "gap",
            "detail": "SCHED-GAP-025 → SCHED-GAP-121 (dual-store drift bit twice)",
        },
    ],
    "key-rotation-expiry": [
        {"kind": "board", "detail": "LORE-003 seed class 'key rotation/expiry'"},
        {
            "kind": "incident",
            "detail": "provider-key expiries surfacing as cross-lane 401 storms",
        },
    ],
    "guard-degradation": [
        {"kind": "board", "detail": "LORE-003 seed class 'guard degradation'"},
        {
            "kind": "incident",
            "detail": "worktree guard PASS vs main-tree gate FAIL at the same commit (control-worktree proof)",
        },
    ],
    "spawn-hot-loop": [
        {"kind": "board", "detail": "LORE-003 seed class 'spawn hot-loop'"},
        {
            "kind": "incident",
            "detail": "worker spin diagnosed via empty -Q log + rising CPU",
        },
    ],
    "ingest-backfill-gap": [
        {"kind": "board", "detail": "LORE-003 seed class 'ingest/backfill gap'"},
        {
            "kind": "gap",
            "detail": "CHATGAP-001: 08-29/30 chat-archive hole, unrecoverable, annotated",
        },
    ],
    "gateway-guard-violation": [
        {
            "kind": "incident",
            "detail": "2026-09-24 integration dogfood: 'banned command tripped the gateway guard' had no home in the registry",
        },
        {
            "kind": "board",
            "detail": "LORE-017 seed class 'gateway guard violation' (closed-registry seed edit)",
        },
    ],
    "docs-count-drift": [
        {
            "kind": "board",
            "detail": "LORE-032 seed class 'docs-count-drift' (closed-registry seed edit)",
        },
        {
            "kind": "incident",
            "detail": "LORE-019/LORE-025/LORE-028: stale doc counts after waves (README, usage skill, docs drift)",
        },
        {
            "kind": "gap",
            "detail": "LORE-029 count-sync guard: scripts/test-count.txt is the canonical count; sweep living docs for drift",
        },
        {
            "kind": "incident",
            "detail": "2026-09-26 discovery stress test: 'docs still cite the old test count' returned unclassified",
        },
    ],
    UNCLASSIFIED_ID: [
        {
            "kind": "board",
            "detail": "LORE-003 catch-all bucket (explicit, honesty-first)",
        },
    ],
}


def _class_or_fail(class_id: str) -> FailureClass:
    reg = get_registry()
    cls = reg.get(class_id)
    if cls is None:
        known = ", ".join(c.id for c in reg.all_classes())
        raise KeyError(
            f"unknown class_id {class_id!r}; registry is closed. Known: {known}"
        )
    return cls


def compile_class(
    class_id: str,
    *,
    evidence: list[dict] | None = None,
    last_validated: str | None = None,
) -> Runbook:
    """Compile the runbook for one curated failure class.

    ``evidence``: optional caller-supplied trail dicts ({"kind","detail"}).
    When None, the class's curated seed trail is used. Evidence supplied by
    the caller does NOT fabricate validation: ``last_validated`` stays None
    (status "proposal") unless explicitly passed by an operator attestation.
    """
    cls = _class_or_fail(class_id)

    signature = (
        cls.signature_patterns[0] if cls.signature_patterns else NO_VALID_EVIDENCE
    )

    is_unclassified = cls.id == UNCLASSIFIED_ID
    if is_unclassified:
        ladder: list[str] = [UNCLASSIFIED_NO_LADDER]
        guardrails = [
            "Never invent a class at runtime — the registry is closed; propose with operator approval instead."
        ]
        checks: list[Check] = []
    else:
        ladder = list(_RECOVERY_LADDERS.get(cls.id, []))
        guardrails = list(_GUARDRAILS.get(cls.id, []))
        checks = [Check.from_dict(c.to_dict()) for c in _CHECKS.get(cls.id, [])]

    trail = (
        list(evidence)
        if evidence is not None
        else list(_EVIDENCE_TRAILS.get(cls.id, []))
    )

    status = STATUS_PROPOSAL
    if last_validated is not None:
        status = STATUS_VALIDATED

    return Runbook(
        class_id=cls.id,
        name=cls.name,
        signature=signature,
        checks=checks,
        recovery_ladder=ladder,
        guardrails=guardrails,
        evidence_trail=trail,
        provenance=(
            "Compiled by lore.compiler from the curated class registry "
            "(lore.classes) and the fleet's incident history. Operator approval "
            "required to publish (propose-not-write)."
        ),
        last_validated=last_validated,
        status=status,
    )


def compile_all(*, evidence: list[dict] | None = None) -> list[Runbook]:
    """One Runbook per registry class (curated first, unclassified last)."""
    return [
        compile_class(cls.id, evidence=evidence) for cls in get_registry().all_classes()
    ]


# ---------------------------------------------------------------- proposals
def propose(class_id: str, existing: Runbook | None = None) -> dict:
    """Structured diff between a freshly compiled runbook and an existing one.

    Returns a proposal dict — never writes anything. When ``existing`` is
    None the proposal is a full "new runbook" proposal. Sections compared:
    signature, checks (by order), recovery_ladder, guardrails, evidence_trail.
    """
    fresh = compile_class(class_id)
    proposal: dict = {
        "class_id": class_id,
        "action": "new" if existing is None else "update",
        "added": {},
        "removed": {},
        "changed": {},
        "note": "proposal only — an operator must approve before this lands anywhere",
    }

    if existing is None:
        proposal["added"] = fresh.to_dict()
        return proposal

    if fresh.signature != existing.signature:
        proposal["changed"]["signature"] = {
            "old": existing.signature,
            "new": fresh.signature,
        }

    old_checks = {c.order: c for c in existing.checks}
    new_checks = {c.order: c for c in fresh.checks}
    added_checks = [
        new_checks[o].to_dict() for o in sorted(set(new_checks) - set(old_checks))
    ]
    removed_checks = [
        old_checks[o].to_dict() for o in sorted(set(old_checks) - set(new_checks))
    ]
    changed_checks = []
    for o in sorted(set(new_checks) & set(old_checks)):
        if new_checks[o] != old_checks[o]:
            changed_checks.append(
                {
                    "order": o,
                    "old": old_checks[o].to_dict(),
                    "new": new_checks[o].to_dict(),
                }
            )
    if added_checks:
        proposal["added"]["checks"] = added_checks
    if removed_checks:
        proposal["removed"]["checks"] = removed_checks
    if changed_checks:
        proposal["changed"]["checks"] = changed_checks

    for section in ("recovery_ladder", "guardrails", "evidence_trail"):
        old_items = getattr(existing, section)
        new_items = getattr(fresh, section)
        added = [x for x in new_items if x not in old_items]
        removed = [x for x in old_items if x not in new_items]
        if added:
            proposal["added"][section] = added
        if removed:
            proposal["removed"][section] = removed

    return proposal


def render_proposal_diff(class_id: str, existing: Runbook | None = None) -> str:
    """Unified-diff text of the proposal (existing markdown vs fresh markdown).

    Pure text rendering — no filesystem write. When ``existing`` is None the
    diff is against an empty baseline (i.e. everything is added).
    """
    import difflib

    fresh = compile_class(class_id)
    old_md = existing.to_markdown() if existing is not None else ""
    new_md = fresh.to_markdown()
    old_lines = old_md.splitlines(keepends=True)
    new_lines = new_md.splitlines(keepends=True)
    if existing is None:
        old_lines = []
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"runbook/{class_id}/current",
        tofile=f"runbook/{class_id}/proposed",
    )
    return "".join(diff)
