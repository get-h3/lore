"""LORE-064: audit wiring — history-driven stale status in audit output.

PRD SC-3's audit freshness signal was wired into _audit_rows(): after
building each baseline row from the static registry, the function reads
.the local validate-history.jsonl (last_local_validation) and, when the
record shows drifted_orders, flips the row to status=stale with
stale_reason. This test suite proves that seam works correctly.
"""

import json
from pathlib import Path


def _make_history(path: Path, records: list[dict]) -> None:
    """Write JSONL history records to path (one per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def _read_rows(history_file: Path) -> list[dict]:
    """Call _audit_rows with the history seam."""
    import lore.__main__ as main

    return main._audit_rows(history_path=history_file)


class TestAuditHistoryDrift:
    """History with drifted_orders -> audit row shows stale + stale_reason."""

    def test_drifted_orders_flip_status(self, tmp_path: Path) -> None:
        """History with drifted_orders=[N] -> status=stale, stale_reason present."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "fast-forward-push-reject",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint-verified: commands parse and answer: [error]",
                    "outcomes": ["ok", "error"],
                    "drifted_orders": [2],
                    "executed_count": 2,
                    "total_checks": 2,
                },
            ],
        )
        rows = _read_rows(hf)
        ff = next(
            (r for r in rows if r["class_id"] == "fast-forward-push-reject"), None
        )
        assert ff is not None, "fast-forward-push-reject must be in audit"
        assert ff["status"] == "stale", f"Expected status=stale, got {ff['status']}"
        assert "stale_reason" in ff, "stale_reason must be present when drift detected"
        assert "lint" in ff["stale_reason"].lower(), (
            f"stale_reason should mention lint, got: {ff['stale_reason']}"
        )

    def test_clean_history_no_status_flip(self, tmp_path: Path) -> None:
        """History with drifted_orders=[] -> row keeps original status, no stale_reason."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "shared-checkout-collision",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint-verified: commands parse and answer: [ok, ok, ok]",
                    "outcomes": ["ok", "ok", "ok"],
                    "drifted_orders": [],
                    "executed_count": 3,
                    "total_checks": 3,
                },
            ],
        )
        rows = _read_rows(hf)
        scc = next(
            (r for r in rows if r["class_id"] == "shared-checkout-collision"), None
        )
        assert scc is not None
        assert scc.get("stale_reason") is None, (
            "Clean history should not add stale_reason"
        )

    def test_no_history_file_unchanged(self, tmp_path: Path) -> None:
        """Missing history file -> audit rows unchanged (no crash, no stale_reason)."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        # Do NOT create the file
        assert not hf.exists()
        rows = _read_rows(hf)
        assert len(rows) > 0, "Should still return registry rows"
        for row in rows:
            assert "stale_reason" not in row, (
                f"stale_reason must not appear without history: {row}"
            )

    def test_partial_drift_multiple_classes(self, tmp_path: Path) -> None:
        """Two classes in history: one drifted, one clean -> only drifted flips."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "fast-forward-push-reject",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint-verified: commands parse and answer: [error]",
                    "outcomes": ["error"],
                    "drifted_orders": [1],
                    "executed_count": 1,
                    "total_checks": 1,
                },
                {
                    "class_id": "shared-checkout-collision",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint-verified: commands parse and answer: [ok, ok, ok]",
                    "outcomes": ["ok", "ok", "ok"],
                    "drifted_orders": [],
                    "executed_count": 3,
                    "total_checks": 3,
                },
            ],
        )
        rows = _read_rows(hf)
        ff = next(
            (r for r in rows if r["class_id"] == "fast-forward-push-reject"), None
        )
        scc = next(
            (r for r in rows if r["class_id"] == "shared-checkout-collision"), None
        )
        assert ff is not None and scc is not None
        assert ff["status"] == "stale"
        assert "stale_reason" in ff
        assert scc.get("stale_reason") is None

    def test_env_absent_not_drift(self, tmp_path: Path) -> None:
        """outcomes=[env-absent, env-absent, env-absent], drifted_orders=[] -> no stale."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "shared-checkout-collision",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint-verified: commands parse and answer: [env-absent, env-absent, env-absent]",
                    "outcomes": ["env-absent", "env-absent", "env-absent"],
                    "drifted_orders": [],
                    "executed_count": 0,
                    "total_checks": 3,
                },
            ],
        )
        rows = _read_rows(hf)
        scc = next(
            (r for r in rows if r["class_id"] == "shared-checkout-collision"), None
        )
        assert scc is not None
        assert scc.get("stale_reason") is None, (
            "env-absent only must not produce stale_reason"
        )

    def test_class_not_in_history_unchanged(self, tmp_path: Path) -> None:
        """History exists but doesn't mention a class -> that class's row unchanged."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "shared-checkout-collision",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint: [ok, ok, ok]",
                    "outcomes": ["ok", "ok", "ok"],
                    "drifted_orders": [],
                    "executed_count": 3,
                    "total_checks": 3,
                },
            ],
        )
        rows = _read_rows(hf)
        # fast-forward-push-reject has no history record
        ff = next(
            (r for r in rows if r["class_id"] == "fast-forward-push-reject"), None
        )
        assert ff is not None
        assert "stale_reason" not in ff, (
            "Class absent from history should not get stale_reason"
        )


class TestAuditJsonFormat:
    """audit --format json includes stale_reason when drift is detected."""

    def test_json_row_has_stale_reason_key(self, tmp_path: Path) -> None:
        """Drifted class row in JSON output contains stale_reason field."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "fast-forward-push-reject",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint: [error]",
                    "outcomes": ["error"],
                    "drifted_orders": [1],
                    "executed_count": 1,
                    "total_checks": 1,
                },
            ],
        )
        rows = _read_rows(hf)
        ff = next(
            (r for r in rows if r["class_id"] == "fast-forward-push-reject"), None
        )
        assert ff is not None
        expected_keys = {
            "class_id",
            "name",
            "runbook_compiled",
            "check_count",
            "command_count",
            "last_validated",
            "status",
            "stale_reason",
        }
        assert expected_keys.issubset(set(ff.keys())), (
            f"JSON row missing keys: {expected_keys - set(ff.keys())}"
        )
        assert ff["status"] == "stale"
        assert ff["stale_reason"] is not None


class TestAuditTableOutput:
    """audit --format table includes stale_reason when drift is detected."""

    def test_table_row_has_stale_reason(self, tmp_path: Path) -> None:
        """Drifted class row includes stale_reason for table rendering."""
        hf = tmp_path / "lore" / "validate-history.jsonl"
        _make_history(
            hf,
            [
                {
                    "class_id": "shared-checkout-collision",
                    "timestamp": "2026-10-17T00:00:00+00:00",
                    "honesty_label": "lint: [error, error, error]",
                    "outcomes": ["error", "error", "error"],
                    "drifted_orders": [1, 2, 3],
                    "executed_count": 3,
                    "total_checks": 3,
                },
            ],
        )
        rows = _read_rows(hf)
        scc = next(
            (r for r in rows if r["class_id"] == "shared-checkout-collision"), None
        )
        assert scc is not None
        assert scc["status"] == "stale"
        assert scc["stale_reason"] is not None
        assert "drift" in scc["stale_reason"].lower()
