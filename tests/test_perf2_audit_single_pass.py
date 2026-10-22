"""PERF-2: ``lore audit`` reads the validate-history ledger in ONE pass.

The disease (board row PERF-2, measured at HEAD a6984b4): ``_audit_rows()``
called ``last_local_validation(class_id, path=...)`` inside the one-row-per-
class loop, so a 14-class audit re-read and re-parsed the ENTIRE
``.lore/validate-history.jsonl`` 14 times — 44,254 ``json.loads`` at the
live 3,161-row ledger (144 ms mean, 1.06 s at 10x growth). The parse work
was the cost.

The fix: ``lore.validate.last_local_validation_batch(path)`` scans the file
ONCE and returns ``{class_id: newest record}``; ``_audit_rows()`` does dict
lookups in the loop. Semantics are unchanged and pinned here:

- newest record per class wins by FILE ORDER (the scan keeps the last
  matching line), never max(timestamp) — pinned with an arm where the
  newest-by-position record carries an OLDER timestamp;
- torn/blank/non-dict lines are skipped, never fatal (same read contract
  as ``last_local_validation``);
- a missing/unreadable ledger yields ``{}`` → the audit rows are exactly
  the registry baseline (no stale flips, no invented data);
- the audit result matches the multi-pass baseline: for every registry
  class the batch map equals what ``last_local_validation`` reports.

SAFETY: no real subprocess anywhere. The synthetic ledger is written by
hand in the exact record shape ``persist_validate_history`` writes (plus
one LORE-061-style ``env_absent_orders`` field, which the reader must
pass through unmodified). CLI runs go through ``main()`` with
``monkeypatch.chdir`` so the CWD-relative ``HISTORY_FILE`` resolves into
the tmp dir (same pattern as the LORE-045/LORE-064 tests). Class ids are
derived from ``SEED_CLASSES`` + the unclassified bucket — never hardcoded.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lore.__main__ import _audit_rows, main
from lore.classes import SEED_CLASSES, UNCLASSIFIED_ID, get_registry
from lore.validate import (
    HONESTY_LABEL,
    last_local_validation,
    last_local_validation_batch,
)

HISTORY_REL = ".lore/validate-history.jsonl"

#: 14 registry classes (13 curated + the unclassified bucket), derived —
#: never a hardcoded literal list.
ALL_CLASS_IDS = [cls.id for cls in SEED_CLASSES] + [UNCLASSIFIED_ID]

#: Batch count for the synthetic ledger (~the live 3,161-row size:
#: 14 classes x 226 batches + one file-order arm record).
BATCHES = 226

#: PERF-2 acceptance: warm in-process audit budget for the ~3.2k-row
#: ledger (generous margin over the measured single-pass ~40 ms; the old
#: 14-pass code spent ~144 ms on the same input).
AUDIT_BUDGET_S = 0.100


# ----------------------------------------------------------------- helpers
def _record(class_id: str, *, minute: int, drifted: list[int]) -> dict:
    """A history record shaped exactly like persist_validate_history writes."""
    ts = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)
    return {
        "class_id": class_id,
        "timestamp": ts.isoformat(),
        "honesty_label": HONESTY_LABEL,
        "outcomes": ["ok"] * 3,
        "drifted_orders": list(drifted),
        "executed_count": 3,
        "total_checks": 3,
    }


def _write_ledger(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )


def _synthetic_ledger(path: Path) -> list[dict]:
    """3161-row-class ledger: ALL_CLASS_IDS x BATCHES batches + 1 arm.

    Batch order is the file order, so the LAST batch per class is its
    newest record. Exactly one class's newest record is drifted (the rest
    are green), and one trailing record re-writes a green result with an
    OLDER timestamp — newest-by-FILE-ORDER must win, not max(timestamp).
    """
    drifted_id = ALL_CLASS_IDS[0]
    file_order_id = ALL_CLASS_IDS[1]
    records: list[dict] = []
    for batch in range(BATCHES):
        for cid in ALL_CLASS_IDS:
            drifted = [2] if (cid == drifted_id and batch == BATCHES - 1) else []
            records.append(_record(cid, minute=batch, drifted=drifted))
    # File-order arm: older timestamp, written LAST → must win.
    records.append(_record(file_order_id, minute=0, drifted=[]))
    _write_ledger(path, records)
    return records


def _row_for(rows: list[dict], class_id: str) -> dict:
    hit = next((r for r in rows if r["class_id"] == class_id), None)
    assert hit is not None, f"class {class_id} missing from audit rows"
    return hit


# ------------------------------------------------------------- batch reader
class TestLastLocalValidationBatch:
    def test_batch_matches_multi_pass_baseline(self, tmp_path: Path) -> None:
        """PERF-2 acceptance: the batch map equals the per-class scans.

        For EVERY registry class, ``last_local_validation_batch`` must
        report the same newest record as the multi-pass
        ``last_local_validation`` baseline — the refactor may change HOW
        MANY times the file is read, never WHAT it reports.
        """
        ledger = tmp_path / HISTORY_REL
        _synthetic_ledger(ledger)
        batch = last_local_validation_batch(path=ledger)
        assert sorted(batch) == sorted(ALL_CLASS_IDS)
        for cid in ALL_CLASS_IDS:
            assert batch[cid] == last_local_validation(cid, path=ledger), cid

    def test_batch_skips_torn_blank_and_non_dict_lines(self, tmp_path: Path) -> None:
        """Same read contract as last_local_validation: never fatal."""
        ledger = tmp_path / HISTORY_REL
        good = _record(ALL_CLASS_IDS[0], minute=1, drifted=[])
        lines = [
            "",
            "{not json",
            json.dumps(good),
            json.dumps(["a", "list"]),  # valid JSON, not a dict
        ]
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        batch = last_local_validation_batch(path=ledger)
        assert batch == {ALL_CLASS_IDS[0]: good}

    def test_missing_ledger_yields_empty_map(self, tmp_path: Path) -> None:
        assert last_local_validation_batch(path=tmp_path / "nope.jsonl") == {}

    def test_batch_passes_records_through_unmodified(self, tmp_path: Path) -> None:
        """Fields this module never writes (env_absent_orders) survive."""
        ledger = tmp_path / HISTORY_REL
        rec = _record(ALL_CLASS_IDS[2], minute=0, drifted=[])
        rec["env_absent_orders"] = [1, 3]
        _write_ledger(ledger, [rec])
        batch = last_local_validation_batch(path=ledger)
        assert batch[ALL_CLASS_IDS[2]]["env_absent_orders"] == [1, 3]


# ------------------------------------------------------------- audit wiring
class TestAuditSinglePass:
    def test_audit_matches_multipass_rows(self, tmp_path: Path, monkeypatch) -> None:
        """Audit rows off the single-pass read equal a per-class baseline.

        The drifted-newest class flips stale with a drift reason; the
        class whose newest record is green-by-FILE-ORDER (older timestamp
        written last) stays proposal — file order wins, not timestamp.
        """
        ledger = tmp_path / HISTORY_REL
        _synthetic_ledger(ledger)
        monkeypatch.chdir(tmp_path)
        rows = _audit_rows()
        assert len(rows) == len(ALL_CLASS_IDS)
        # Newest record is drifted → stale, same reason wording as before.
        stale = _row_for(rows, ALL_CLASS_IDS[0])
        assert stale["status"] == "stale"
        assert stale["stale_reason"].startswith("lint drift: check 2")
        # Newest-BY-FILE-ORDER record is green → proposal (not stale),
        # even though its newest-by-TIMESTAMP record was drifted.
        by_order = _row_for(rows, ALL_CLASS_IDS[1])
        assert by_order["status"] == "proposal"
        assert "stale_reason" not in by_order

    def test_audit_cli_under_budget(self, tmp_path: Path, monkeypatch, capsys) -> None:
        """PERF-2 acceptance: a warm ``lore audit`` completes < 100 ms.

        One warmup call pays any lazy init (mirrors hyperfine --warmup),
        then the measured run must parse the ~3.2k-row ledger once and
        render the full matrix inside the budget.
        """
        ledger = tmp_path / HISTORY_REL
        _synthetic_ledger(ledger)
        monkeypatch.chdir(tmp_path)
        main(["audit", "--format", "json"])  # warmup
        capsys.readouterr()
        start = time.perf_counter()
        code = main(["audit", "--format", "json"])
        elapsed = time.perf_counter() - start
        out = capsys.readouterr().out
        assert code == 0
        payload = json.loads(out)
        assert payload["summary"]["total_classes"] == len(ALL_CLASS_IDS)
        assert elapsed < AUDIT_BUDGET_S, (
            f"lore audit took {elapsed * 1000:.1f} ms (budget "
            f"{AUDIT_BUDGET_S * 1000:.0f} ms) on a "
            f"{len(ALL_CLASS_IDS) * BATCHES + 1}-row ledger — single-pass "
            "read regressed?"
        )

    def test_audit_cli_json_unchanged_vs_baseline(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """The 14-row JSON matrix is byte-stable against a hand baseline.

        For every class the CLI row's freshness fields must match what the
        multi-pass reader says about that class's newest record — the
        output contract (LORE-064) is untouched by the read-path change.
        """
        ledger = tmp_path / HISTORY_REL
        _synthetic_ledger(ledger)
        monkeypatch.chdir(tmp_path)
        code = main(["audit", "--format", "json"])
        out = capsys.readouterr().out
        assert code == 0
        payload = json.loads(out)
        batch = last_local_validation_batch(path=ledger)
        for row in payload["classes"]:
            rec = batch[row["class_id"]]
            if rec.get("drifted_orders"):
                assert row["status"] == "stale"
                assert row["stale_reason"].startswith("lint drift:")
            else:
                assert row["status"] == "proposal"
                assert "stale_reason" not in row


# ----------------------------------------------------------- registry pin
def test_class_ids_derived_from_seed_registry() -> None:
    """The ledger builder's class set IS the registry (13 + bucket).

    Guards the derivation itself: if SEED_CLASSES grows, the synthetic
    ledger grows with it instead of silently benchmarking a stale class
    list (PERF-2: never hardcode class counts).
    """
    registry_ids = [cls.id for cls in get_registry().all_classes()]
    assert sorted(registry_ids) == sorted(ALL_CLASS_IDS)
    assert len(ALL_CLASS_IDS) == len(SEED_CLASSES) + 1  # + the bucket
