"""LORE-046: suppress the unclassified fallback row on confident match output.

Real-use dogfood hit: ``python -m lore match "drain 503"`` printed a second
``unclassified  confidence=0.00  evidence: none`` line under every confident
match — output read like two answers, and a scripting consumer splitting on
lines saw two class rows. Display-level fix in
:func:`lore.__main__._cmd_match` (classifier.py is NOT touched:
``classify_all`` keeps its always-carry-the-fallback contract, pinned by
``tests/test_lore016_qa_audit.py``).

- No ``--explain``: the fallback row is suppressed from the printed
  candidates when a curated class matched; a TRUE miss (the fallback is the
  only candidate) still prints ``unclassified confidence=0.00 evidence:
  none`` — absence stays a first-class answer.
- ``--explain``: the raw candidate list prints untouched, unclassified row
  included (evidence transparency).
- The ``no candidates`` empty-list branch and exit codes are unchanged:
  0 on a match or a true-miss-with-fallback, 1 on an empty list.
"""

from __future__ import annotations

import pytest

from lore.__main__ import main

GATEWAY_TEXT = "drain 503s while requests drain during restart"
NO_MATCH_TEXT = "xyzzy nothing here"
CONFIDENT_LINE = (
    "gateway-drain-window\tconfidence=0.90\t"
    "evidence: signature:drain 503; keyword:503; keyword:drain; keyword:restart"
)
UNCLASSIFIED_LINE = "unclassified\tconfidence=0.00\tevidence: none"


def _run(argv, capsys):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ------------------------------------------------- confident match: one row
def test_confident_match_prints_exactly_one_class_line(capsys):
    code, out, _err = _run(["match", GATEWAY_TEXT], capsys)
    assert code == 0
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines == [CONFIDENT_LINE]


def test_confident_match_has_no_unclassified_line(capsys):
    code, out, _err = _run(["match", GATEWAY_TEXT], capsys)
    assert code == 0
    assert UNCLASSIFIED_LINE not in out
    assert "unclassified" not in out


def test_confident_match_output_is_script_parseable_single_row(capsys):
    # A consumer splitting on lines must see exactly one class row.
    code, out, _err = _run(["match", GATEWAY_TEXT], capsys)
    assert code == 0
    class_id, confidence_field, _evidence = out.strip().split("\t")
    assert class_id == "gateway-drain-window"
    assert confidence_field == "confidence=0.90"


def test_other_confident_match_also_suppresses_fallback(capsys):
    # Second dogfood symptom: "secret .env clobber" — same single-row shape.
    code, out, _err = _run(["match", "secret .env clobber"], capsys)
    assert code == 0
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("secret-env-clobber\t")
    assert "unclassified" not in out


# ------------------------------------------------------- true miss: honest
def test_true_miss_still_prints_unclassified_line_exit0(capsys):
    code, out, _err = _run(["match", NO_MATCH_TEXT], capsys)
    assert code == 0
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines == [UNCLASSIFIED_LINE]
    assert out.startswith(UNCLASSIFIED_LINE)


def test_true_miss_is_the_only_candidate_per_classifier_contract(capsys):
    # The display fix only suppresses the row when a CURATED class matched.
    # Pin the underlying classifier contract this relies on: a miss yields
    # exactly one candidate and it is the fallback.
    from lore.classifier import classify_all

    cands = classify_all(NO_MATCH_TEXT)
    assert len(cands) == 1
    assert cands[0].class_id == "unclassified"
    assert cands[0].confidence == 0.0


# ------------------------------------------------------- --explain: raw list
def test_explain_on_confident_match_keeps_unclassified_row(capsys):
    code, out, _err = _run(["match", GATEWAY_TEXT, "--explain"], capsys)
    assert code == 0
    assert CONFIDENT_LINE in out
    assert UNCLASSIFIED_LINE in out


def test_explain_on_miss_also_keeps_unclassified_and_near_misses(capsys):
    code, out, _err = _run(["match", "--explain", NO_MATCH_TEXT], capsys)
    assert code == 0
    assert UNCLASSIFIED_LINE in out
    assert "near-misses" in out


# ------------------------------------------------ empty-list branch, exits 1
def test_no_candidates_branch_unchanged_exit1(capsys, monkeypatch):
    monkeypatch.setattr("lore.__main__.classify_all", lambda _text: [])
    code, out, _err = _run(["match", NO_MATCH_TEXT], capsys)
    assert code == 1
    assert "no candidates" in out


def test_no_candidates_explain_branch_also_exit1(capsys, monkeypatch):
    monkeypatch.setattr("lore.__main__.classify_all", lambda _text: [])
    code, out, _err = _run(["match", NO_MATCH_TEXT, "--explain"], capsys)
    assert code == 1
    assert "no candidates" in out


# ------------------------------------------- argparse error path unchanged
def test_match_missing_text_is_argparse_exit2():
    with pytest.raises(SystemExit) as exc:
        main(["match"])
    assert exc.value.code == 2
