"""REVIEW-LORE-001: durable gate approval records (opt-in `--record PATH`).

The gate stays propose-not-write by DEFAULT: without --record it creates no
file anywhere. With --record it APPENDS one JSONL audit record per invocation,
and only for an ALLOWED verdict — a denied gate writes nothing even when
--record is given.
"""

import json

from lore import __version__
from lore.__main__ import main
from lore.absorb import AbsorbDecision, gate_close, verdict_record


def _allow_args(lesson: str = "drain before restart") -> list[str]:
    """A decision the gate allows (gateway-drain-window is in the registry)."""
    return [
        "gate",
        "--decision",
        "absorb",
        "--class",
        "gateway-drain-window",
        "--lesson",
        lesson,
        "--ref",
        "REVIEW-LORE-001",
        "--source",
        "qa-dagger",
    ]


def test_record_appends_one_jsonl_record_per_invocation(tmp_path):
    rec = tmp_path / "g.jsonl"
    assert main(_allow_args() + ["--record", str(rec)]) == 0
    assert main(_allow_args("second lesson") + ["--record", str(rec)]) == 0
    lines = rec.read_text().splitlines()
    assert len(lines) == 2  # APPEND: two invocations, two records
    recs = [json.loads(line) for line in lines]
    assert recs[0]["class_id"] == "gateway-drain-window"
    assert recs[0]["decision"] == "absorb"
    assert recs[0]["lesson"] == "drain before restart"
    assert recs[0]["ack_ref"] == "REVIEW-LORE-001"
    assert recs[0]["source"] == "qa-dagger"
    assert recs[0]["allowed"] is True
    assert recs[0]["errors"] == []
    assert recs[0]["tool_version"] == __version__
    # grep-stable shape: same schema, same key order, every line
    assert list(recs[0].keys()) == list(recs[1].keys())
    assert set(recs[0]) == {
        "decided_at",
        "decision",
        "class_id",
        "lesson",
        "reason",
        "ack_ref",
        "source",
        "allowed",
        "errors",
        "tool_version",
    }


def test_record_honors_decided_at_and_does_not_invent_it(tmp_path):
    rec = tmp_path / "g.jsonl"
    rc = main(
        _allow_args()
        + ["--decided-at", "2026-09-29T12:00:00+00:00", "--record", str(rec)]
    )
    assert rc == 0
    (only,) = [json.loads(line) for line in rec.read_text().splitlines()]
    assert only["decided_at"] == "2026-09-29T12:00:00+00:00"


def test_record_stamps_current_utc_when_decided_at_omitted(tmp_path):
    rec = tmp_path / "g.jsonl"
    assert main(_allow_args() + ["--record", str(rec)]) == 0
    (only,) = [json.loads(line) for line in rec.read_text().splitlines()]
    assert only["decided_at"].endswith("Z")  # ISO-8601 UTC, never empty


def test_without_record_no_file_created_anywhere(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())
    assert main(_allow_args()) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_deny_exits_1_and_never_writes_even_with_record(tmp_path):
    rec = tmp_path / "g.jsonl"
    rc = main(
        [
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "",  # empty reason -> DENY
            "--record",
            str(rec),
        ]
    )
    assert rc == 1
    assert not rec.exists()  # the deny rule: a denied gate must not write


def test_deny_without_record_still_exits_1_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())
    assert main(["gate", "--decision", "no-new-lesson", "--reason", ""]) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_no_new_lesson_allow_is_recorded_too(tmp_path):
    rec = tmp_path / "g.jsonl"
    rc = main(
        [
            "gate",
            "--decision",
            "no-new-lesson",
            "--reason",
            "covered by v0.1 docs",
            "--ref",
            "QA-LORE-2",
            "--record",
            str(rec),
        ]
    )
    assert rc == 0
    (only,) = [json.loads(line) for line in rec.read_text().splitlines()]
    assert only["decision"] == "no-new-lesson"
    assert only["class_id"] is None
    assert only["reason"] == "covered by v0.1 docs"
    assert only["allowed"] is True


def test_verdict_record_pure_data_helper():
    """The helper itself writes nothing and honors an explicit decided_at."""
    d = AbsorbDecision(
        decision="absorb",
        class_id="gateway-drain-window",
        lesson="drain first",
    )
    v = gate_close(d)
    rec = verdict_record(v, decided_at="2026-09-29T00:00:00Z")
    assert rec["decided_at"] == "2026-09-29T00:00:00Z"
    assert rec["tool_version"] == __version__
