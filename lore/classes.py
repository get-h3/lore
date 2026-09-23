"""Curated failure-class registry for the lore runbook compiler.

The registry is a CLOSED curated list, seeded from fleet incident history
(2026-09). Two hard rules from the PRD's risk section:

1. Absorbing a symptom into ``unclassified`` is always allowed.
2. The public API must NOT let callers invent new classes at runtime —
   :meth:`ClassRegistry.register` raises :class:`RuntimeError` unconditionally.
   New classes are added by editing this module's seed table, never at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

UNCLASSIFIED_ID = "unclassified"

SEED_PROVENANCE = (
    "Seeded from fleet incident history 2026-09 (gateway/scheduler/ops post-mortems)."
)


@dataclass(frozen=True)
class FailureClass:
    """One curated failure class."""

    id: str
    name: str
    description: str
    signature_patterns: tuple[str, ...]
    keywords: tuple[str, ...]
    provenance: str


# The seed table. ids must be unique; every entry needs signatures + keywords.
# These patterns/keywords describe the fleet's lived incidents; the classifier
# (lore.classifier) consumes them via compiled regexes.
SEED_CLASSES: tuple[FailureClass, ...] = (
    FailureClass(
        id="gateway-drain-window",
        name="Gateway drain window",
        description=(
            "In-flight requests 503 while a gateway/proxy restarts or reloads; "
            "batch config changes under load need pause-first and an expected "
            "drain window (up to ~30 min)."
        ),
        signature_patterns=(
            r"drain\s+503",
            r"gateway\s+(restart|reload|drain)",
            r"in[- ]flight\s+requests?\s+(finish|drain|503)",
        ),
        keywords=("503", "drain", "gateway", "restart", "reload", "drain window"),
        provenance=SEED_PROVENANCE
        + " Learned across four gateway-restart incidents before the doctrine was formalized.",
    ),
    FailureClass(
        id="shared-checkout-collision",
        name="Shared checkout collision",
        description=(
            "Two agents/workers operate the same checkout or worktree: git "
            "index.lock fights, a reap deletes a fresh zero-commit worktree, or "
            "staged files get swept by a sibling."
        ),
        signature_patterns=(
            r"index\.lock",
            r"worktree\s+(reap|deleted|collision)",
            r"(sibling|concurrent)\s+worker\s+.{0,40}(reset|stage|sweep|checkout)",
        ),
        keywords=("index.lock", "worktree", "reap", "sibling", "collision", "checkout"),
        provenance=SEED_PROVENANCE
        + " From shared-tree worker collisions and worktree reaper deletions.",
    ),
    FailureClass(
        id="secret-env-clobber",
        name="Secret / .env clobber",
        description=(
            "Live secret-bearing .env files overwritten by .env.example twins or "
            "sibling deploys; every downstream key 401s until the container env is "
            "repaired and secret generations diffed."
        ),
        signature_patterns=(
            r"\.env(\.example)?\s+(twins?|clobber|overwrite)",
            r"clobber(ed|ing)?\s+(by\s+)?(the\s+)?(example|\.env)",
            r"container[- ]env\s+repair",
        ),
        keywords=(
            ".env",
            ".env.example",
            "clobber",
            "overwritten",
            "secrets",
            "container env",
        ),
        provenance=SEED_PROVENANCE
        + " From the .env/.env.example twin-clobber that broke central logins until repaired by hand.",
    ),
    FailureClass(
        id="disk-pressure-corruption",
        name="Disk-pressure corruption",
        description=(
            "A full or pressured volume corrupts databases or state mid-write "
            "(sqlite header wipes, truncated JSONL, ENOSPC partial commits)."
        ),
        signature_patterns=(
            r"ENOSPC",
            r"disk\s+pressure.{0,60}corrupt",
            r"(sqlite|database)\s+header\s+(wip|corrupt|truncat)",
        ),
        keywords=(
            "ENOSPC",
            "disk pressure",
            "corrupt",
            "truncated",
            "header wiped",
            "volume",
        ),
        provenance=SEED_PROVENANCE
        + " From ENOSPC sqlite/JSONL corruption events on fleet storage.",
    ),
    FailureClass(
        id="cooldown-pin-drift",
        name="Cooldown / pin drift",
        description=(
            "Cooldown or enable/pin state diverges between its two stores "
            "(DB vs fleet.toml): one says paused, the other still enabled, and a "
            "project spawns (or stays paused) against doctrine."
        ),
        signature_patterns=(
            r"fleet\.toml\s+.{0,40}(but|while).{0,40}\bDB\b",
            r"\bDB\b.{0,40}(but|while).{0,40}fleet\.toml",
            r"cooldown\s+(authority|pin|state)\s+drift",
        ),
        keywords=("cooldown", "fleet.toml", "pin", "drift", "paused", "dual-store"),
        provenance=SEED_PROVENANCE
        + " From SCHED-GAP-025 → SCHED-GAP-121: the same drift bit twice a year-class apart.",
    ),
    FailureClass(
        id="key-rotation-expiry",
        name="Key rotation / expiry",
        description=(
            "Provider/API keys expired, revoked, or mis-rotated: auth 401s across "
            "lanes while the key looks configured."
        ),
        signature_patterns=(
            r"40[13]\s+Unauthorized.{0,60}rotat",
            r"rotat(ed|ion).{0,40}(expired|revoked|401)",
            r"expired\s+key.{0,60}(re-?issu|401|auth)",
        ),
        keywords=(
            "401",
            "expired",
            "rotation",
            "revoked",
            "unauthorized",
            "credentials",
        ),
        provenance=SEED_PROVENANCE
        + " From provider-key expiries that surfaced as cross-lane 401 storms.",
    ),
    FailureClass(
        id="guard-degradation",
        name="Guard / gate degradation",
        description=(
            "A verification guard passes in one context but is not gate-equivalent "
            "in the real one (worktree pass vs main-tree fail, stale config vs "
            "live service, harness-capped probes)."
        ),
        signature_patterns=(
            r"guard\s+(pass|result).{0,80}not\s+gate[- ]equivalent",
            r"(worktree|control).{0,60}(pass|fail).{0,40}main[- ]tree",
            r"gate\s+(fail|equivalence).{0,80}same\s+commit",
        ),
        keywords=(
            "guard",
            "gate",
            "worktree",
            "control",
            "not gate-equivalent",
            "degraded",
        ),
        provenance=SEED_PROVENANCE
        + " From worktree-guard vs main-tree gate divergence proven with control worktrees.",
    ),
    FailureClass(
        id="spawn-hot-loop",
        name="Spawn hot loop",
        description=(
            "A scheduler or supervisor respawns the same worker/tick in a tight "
            "loop: the -Q log stays empty, CPU rises, nothing lands — the spawn "
            "itself is wedged, not the work."
        ),
        signature_patterns=(
            r"spawn(ing|s)?\s+.{0,40}(over\s+and\s+over|loop|repeatedly|respawn)",
            r"worker\s+spin",
            r"[-−]Q\s+log\s+.{0,40}(0\s*bytes|empty|stuck)",
        ),
        keywords=("spawn", "hot loop", "worker spin", "respawn", "0 bytes", "stuck"),
        provenance=SEED_PROVENANCE
        + " From scheduler/worker respawn loops diagnosed by empty -Q logs and rising CPU.",
    ),
    FailureClass(
        id="ingest-backfill-gap",
        name="Ingest backfill gap",
        description=(
            "A capture/ingest pipeline reported success but the destination has a "
            "time-window hole: rows missing, chat-archive or telemetry gap "
            "unrecoverable without a named-gap annotation and backfill."
        ),
        signature_patterns=(
            r"(ingest|capture|archive|telemetry).{0,80}(gap|hole|missing)",
            r"time[- ]window\s+hole",
            r"missing\s+rows.{0,40}destination",
        ),
        keywords=(
            "backfill",
            "gap",
            "ingest",
            "archive hole",
            "missing rows",
            "unrecoverable",
        ),
        provenance=SEED_PROVENANCE
        + " From the 08-29/30 chat-archive hole that backups could not restore (CHATGAP-001).",
    ),
)

UNCLASSIFIED_CLASS = FailureClass(
    id=UNCLASSIFIED_ID,
    name="Unclassified",
    description=(
        "Explicit catch-all: the symptom did not match any curated class strongly "
        "enough to be labeled. Absorbing into unclassified is always allowed; "
        "inventing a new class is not (registry is closed, curated in source)."
    ),
    # The catch-all matches nothing by construction: the pattern is a no-op
    # (never matches) and its keyword is a name-token the classifier never
    # scores (unclassified is excluded from keyword scoring). Both fields are
    # present so registry integrity treats it like every other class.
    signature_patterns=(r"(?!)",),
    keywords=("unclassified",),
    provenance=SEED_PROVENANCE,
)


class ClassRegistry:
    """Read-only registry over the curated class list.

    The public surface is lookup-only. ``register`` exists solely to be
    refused: the registry is closed, and runtime class invention is refused
    with :class:`RuntimeError` (new classes are curated into the seed table
    with operator approval, per the PRD's classification-sprawl risk).
    """

    def __init__(self, classes: tuple[FailureClass, ...]):
        ids = [c.id for c in classes]
        if len(ids) != len(set(ids)):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            raise ValueError(f"duplicate class ids in registry: {dupes}")
        self._classes: dict[str, FailureClass] = {c.id: c for c in classes}

    def get(self, class_id: str) -> FailureClass | None:
        return self._classes.get(class_id)

    def all_classes(self) -> tuple[FailureClass, ...]:
        """Every class, curated classes first, unclassified last."""
        curated = [c for c in self._classes.values() if c.id != UNCLASSIFIED_ID]
        unclassified = self._classes.get(UNCLASSIFIED_ID)
        if unclassified is not None:
            curated.append(unclassified)
        return tuple(curated)

    def register(self, **kwargs: object) -> FailureClass:
        """Refused by design: the registry is a closed curated list."""
        raise RuntimeError(
            "the failure-class registry is closed and curated: new classes are "
            "added to lore/classes.py SEED_CLASSES with operator approval, "
            "never invented at runtime (absorbing into 'unclassified' is always allowed)"
        )

    def __len__(self) -> int:
        return len(self._classes)

    def __contains__(self, class_id: object) -> bool:
        return class_id in self._classes


_REGISTRY: ClassRegistry | None = None


def get_registry() -> ClassRegistry:
    """Process-wide registry singleton (seed classes + unclassified)."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ClassRegistry(SEED_CLASSES + (UNCLASSIFIED_CLASS,))
    return _REGISTRY
