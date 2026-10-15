"""Placeholder fill-in hints (LORE-050, GAP A).

Runbook checks carry ``<placeholder>`` template slots (e.g.
``grep -c 'drain 503' <gateway-log-path>``). Dogfood run 7 measured the
operator-facing surfaces rendering those slots with NO instruction about
what fills them — the operator knowledge existed only in the class's
provenance, never at the point of use. This module is the fix's data:

- :data:`PLACEHOLDER_HINTS` — per-slot-name hints describing WHERE the
  value comes from (the kind of artifact the operator needs: a log path,
  a health URL, an env/config key name, a board directory). They name
  SOURCES, never a specific host's paths, URLs, ids or secrets — the
  table is deployment-neutral by construction.
- :func:`placeholder_hints` — token+hint pairs for one command, in
  first-appearance order, deduped; unknown slot names get
  :data:`DEFAULT_HINT` (an honest generic, never an invented value).

Rendering rule: every surface that prints a check command (the compiled
runbook markdown, ``lore validate`` plan/execute output, ``lore consult
--failure`` check lists) prints one fill-in line per slot, next to the
command. JSON surfaces stay byte-identical (the existing to_dict pins
hold) — hints are an operator-facing rendering affordance.

Scope note (deliberate divergence from the lint's execution-side rule):
``lore.validate._unfilled_placeholder_token`` is quote-AWARE because it
decides whether a command is safe to EXECUTE — a quoted ``<...>`` there
is literal text, never a slot. Hint extraction scans the RAW command: in
the seeded runbooks a quoted slot (``grep '<key-name>'``,
``jq 'select(.id=="<project-row>")'``) IS a template slot the operator
must fill — the fix targets the runbook's readability, not execution.
"""

from __future__ import annotations

import re

__all__ = [
    "DEFAULT_HINT",
    "PLACEHOLDER_HINTS",
    "placeholder_hints",
    "placeholder_tokens",
]

_PLACEHOLDER_RE = re.compile(r"<[A-Za-z0-9_.\-]+>")

# Per-slot-name fill-in hints: WHERE the value comes from, described as
# the KIND of artifact (deployment-neutral — no host paths, no URLs, no
# ids, no secrets). Slots used by the curated seed checks are all named
# here; unknown names fall back to :data:`DEFAULT_HINT` (a pinned test
# asserts the seed table stays covered by the named entries).
DEFAULT_HINT = (
    "the deployment-specific value for this slot on the box the check runs "
    "on (a path, URL, name, or id); the class provenance and evidence "
    "trail show where the value was observed"
)

PLACEHOLDER_HINTS: dict[str, str] = {
    "gateway-log-path": (
        "the gateway/proxy log file path on the box running the gateway "
        "(where the drain-503 lines are written)"
    ),
    "gateway-health-url": (
        "the gateway's HTTP health endpoint URL (the one status checks poll)"
    ),
    "gateway-metrics-url": (
        "the gateway's metrics endpoint URL (the source of the in-flight counter)"
    ),
    "gateway-queue-path": (
        "the gateway's durable queue file path (the state a restart flushes)"
    ),
    "scheduler-fleet-config": (
        "the scheduler's fleet configuration file path (the one defining project pins)"
    ),
    "scheduler-cli": "the scheduler's CLI command on PATH on this box",
    "scheduler-log": "the scheduler's log file path",
    "scheduler-log-path": "the scheduler's log file path",
    "container": (
        "the affected container's name or ID (docker ps on the host running "
        "the service)"
    ),
    "affected-volume": (
        "the mount path of the pressured volume (the Filesystem column of df -h)"
    ),
    "db": "the path of the affected SQLite database file",
    "truncated.jsonl": "the path of the JSONL file with the torn final line",
    "destination.jsonl": (
        "the capture destination's JSONL file path (the sink the pipeline writes)"
    ),
    "project-row": (
        "the affected project/lane id (the same id the scheduler and board use)"
    ),
    "project": "the affected project/lane id",
    "board": "the affected project's board directory (its .coding-hermes path)",
    "provider-url": (
        "the API provider's base URL whose key is suspected (the provider's API host)"
    ),
    "key": (
        "the provider API key credential for THIS provider — taken from the "
        "operator's secret store / environment config on the box, never "
        "pasted into the runbook or its output"
    ),
    "key-name": (
        "the env/config key NAME suspected dead (grep the name; never print the value)"
    ),
    "service-config-path": (
        "the consuming service's config file path (the file the service actually reads)"
    ),
    "main-tree": "the main checkout's root path (the tree the gate runs in)",
    "worktree": "the agent worktree's root path (git worktree list)",
    "control-wt": "a fresh control worktree path created at the same commit",
    "same-commit": "the commit SHA pinned by the check above it (git rev-parse HEAD)",
    "worker-log": (
        "the spinning worker's output log path (where the -Q redirect writes)"
    ),
    "worker-pid": "the worker process's PID (ps/pgrep on this box)",
    "window-start-ts": (
        "the gap window's start timestamp (ISO-8601), from the named-gap annotation"
    ),
    "guard-log-tail": "the guard's log file path (the log the failures appear in)",
    "gateway-log-dir": "the directory the gateway writes its logs into",
}


def placeholder_tokens(command: str) -> list[str]:
    """Every ``<token>`` template slot in the command, raw scan.

    In first-appearance order, deduplicated. Raw (NOT quote-aware) on
    purpose: a quoted slot is still a slot the operator must fill — see
    the module docstring for the deliberate divergence from the
    execution-side rule.
    """
    tokens: list[str] = []
    for match in _PLACEHOLDER_RE.finditer(command or ""):
        token = match.group(0)
        if token not in tokens:
            tokens.append(token)
    return tokens


def placeholder_hints(command: str) -> list[tuple[str, str]]:
    """(token, hint) pairs for one command; unknown names get the default.

    The pairs arrive in first-appearance order (deduplicated), ready for
    each rendering surface to prefix and indent.
    """
    hints: list[tuple[str, str]] = []
    for token in placeholder_tokens(command):
        name = token[1:-1]  # strip the angle brackets for the table lookup
        hints.append((token, PLACEHOLDER_HINTS.get(name, DEFAULT_HINT)))
    return hints
