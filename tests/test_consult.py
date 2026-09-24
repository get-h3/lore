"""Tests for lore.consult — tick-start consult (LORE-007)."""

from __future__ import annotations

import json

import pytest

from lore.consult import MAX_MATCHED_CLASSES, consult, consult_task

# Canonical gateway-drain-window symptom text (matches the class signature).
GATEWAY_TEXT = "gateway drain window: scheduler restarting, 503s killing ticks"

# Text that should NOT match any curated class.
COFFEE_TEXT = "coffee machine broken"


def test_consult_matches_gateway_drain_and_ref_has_checks() -> None:
    result = consult(GATEWAY_TEXT)
    assert result.matched is True
    assert result.matched_classes[0] == "gateway-drain-window"
    assert len(result.runbook_refs) >= 1
    top_ref = result.runbook_refs[0]
    assert top_ref["class_id"] == "gateway-drain-window"
    assert top_ref["name"] == "Gateway drain window"
    assert top_ref["check_count"] > 0
    assert top_ref["status"] in ("proposal", "validated", "stale")
    # Refs, not payloads: no checks/ladder inside the ref dict.
    assert set(top_ref) == {
        "class_id",
        "name",
        "status",
        "last_validated",
        "check_count",
    }


def test_consult_no_match_is_empty_and_false() -> None:
    result = consult(COFFEE_TEXT)
    assert result.matched is False
    assert result.matched_classes == []
    assert result.runbook_refs == []
    assert isinstance(result.elapsed_ms, float)
    assert result.elapsed_ms >= 0.0


def test_consult_fail_open_on_compile_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(class_id: str) -> None:
        raise RuntimeError(f"compile exploded for {class_id}")

    monkeypatch.setattr("lore.compiler.compile_class", boom)
    result = consult(GATEWAY_TEXT)  # must NOT raise
    assert result.matched is True
    assert result.matched_classes[0] == "gateway-drain-window"
    # The broken compile omitted its ref but the match survived.
    assert all(r["class_id"] != "gateway-drain-window" for r in result.runbook_refs)


def test_consult_fail_open_on_missing_class(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(class_id: str) -> None:
        raise KeyError(f"unknown class_id {class_id!r}")

    monkeypatch.setattr("lore.compiler.compile_class", missing)
    result = consult(GATEWAY_TEXT)
    assert result.matched is True
    assert result.runbook_refs == []


def test_consult_elapsed_ms_is_float() -> None:
    result = consult(GATEWAY_TEXT)
    assert isinstance(result.elapsed_ms, float)
    assert result.elapsed_ms > 0.0


def test_consult_json_round_trip() -> None:
    result = consult(GATEWAY_TEXT)
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["matched"] is True
    assert payload["matched_classes"] == ["gateway-drain-window"]
    assert payload["runbook_refs"][0]["check_count"] > 0


def test_consult_cap_at_three() -> None:
    assert MAX_MATCHED_CLASSES == 3
    # Any text can never yield more than 3 matched classes.
    result = consult("503 drain gateway restart reload index.lock worktree reap ENOSPC")
    assert len(result.matched_classes) <= MAX_MATCHED_CLASSES


def test_consult_task_detail_alone_reaches_match() -> None:
    result = consult_task("tick title", "in-flight requests 503 while gateway restarts")
    assert result.matched is True
    assert "gateway-drain-window" in result.matched_classes


def test_consult_task_detail_optional() -> None:
    no_detail = consult_task(GATEWAY_TEXT)
    with_detail = consult_task(GATEWAY_TEXT, "")
    assert no_detail.matched is True
    assert no_detail.matched_classes == with_detail.matched_classes


def test_consult_task_no_match_false() -> None:
    result = consult_task("coffee machine broken")
    assert result.matched is False


def test_consult_perf_under_100ms_on_large_text() -> None:
    # ~2KB text, loose CI-safe bound.
    text = "gateway drain window: scheduler restarting, 503s killing ticks " * 32
    assert len(text) > 1500
    result = consult(text)
    assert result.matched is True
    assert result.elapsed_ms < 100.0


def test_cli_consult_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from lore.__main__ import main

    rc = main(["consult", GATEWAY_TEXT, "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["matched"] is True
    assert payload["matched_classes"][0] == "gateway-drain-window"


def test_cli_consult_no_match_exit_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from lore.__main__ import main

    rc = main(["consult", COFFEE_TEXT])
    out = capsys.readouterr().out
    assert rc == 0  # fail-open contract: no-match exits 0
    assert "no matching runbook" in out
