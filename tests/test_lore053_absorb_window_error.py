"""LORE-053 — absorb --window error messages TEACH the accepted trail shape.

Two contracts pinned at the real process boundary (subprocess against
``python -m lore``), matching the exact CLI shapes from the task row:

1. Input with NO export marker at all is empty/unclaimed input: exit 0 with
   the existing "no classifiable evidence blocks" message — NOT an error.
2. Input that HAS an export marker but no (valid) fenced block exits 2 with
   a TEACHING error: names the accepted shape ("fenced code block", bare
   ISO-8601 timestamp), shows one example line, and quotes NO internal
   tooling state (no "unfrozen", no LOGSEY_EXPORT_CONTRACT_STATUS text).
   The two failure modes are distinguishable: "no fenced block" vs "no
   parseable evidence lines".
"""

from __future__ import annotations

import subprocess
import sys

_ACCEPTED = "accepted shape: a fenced code block (``` or ```jsonl)"
_EXAMPLE = "2026-10-18T14:30:00Z"
# Internal tooling state that must NEVER reach the user-facing error.
_UNFROZEN = "unfrozen — logsey export subcommand not yet implemented"


def _run_absorb(stdin_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "lore", "absorb", "--window", "2h"],
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False,
    )


def test_no_export_marker_is_unclaimed_input_exit0_not_error():
    """``random noise`` (no marker, no fence): exit 0, empty-trail message."""
    r = _run_absorb("random noise\n")
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert "no classifiable evidence blocks" in r.stdout
    assert "nothing written" in r.stdout
    assert r.stderr.strip() == ""


def _assert_teaching_error(msg: str, what_went_wrong: str) -> None:
    # What went wrong (the two failure modes are distinguishable).
    assert what_went_wrong in msg
    # The accepted shape, stated clearly.
    assert _ACCEPTED in msg
    assert "ISO-8601 timestamp" in msg
    # One example line.
    assert _EXAMPLE in msg
    # No internal tooling state leaks to the user.
    assert _UNFROZEN not in msg
    assert "LOGSEY_EXPORT_CONTRACT_STATUS" not in msg


def test_marker_without_fence_exit2_teaching_error():
    """Marker present, fence missing: exit 2 + teaching error."""
    r = _run_absorb("logsey export --window 1h\n")
    assert r.returncode == 2
    _assert_teaching_error(r.stderr, "no fenced block")


def test_marker_with_fence_but_no_valid_lines_exit2_teaching_error():
    """Marker + fence, fence body has no timestamped lines: exit 2 + teaching."""
    trail = "logsey export --window 1h\n```\nnot a timestamp\n```\n"
    r = _run_absorb(trail)
    assert r.returncode == 2
    _assert_teaching_error(r.stderr, "no parseable evidence lines")


def test_both_teaching_errors_are_distinguishable():
    """The two failure modes produce DIFFERENT what-went-wrong clauses."""
    r_no_fence = _run_absorb("logsey export --window 1h\n")
    r_bad_lines = _run_absorb("logsey export --window 1h\n```\nnot a timestamp\n```\n")
    assert r_no_fence.returncode == r_bad_lines.returncode == 2
    assert "no fenced block" in r_no_fence.stderr
    assert "no parseable evidence lines" in r_bad_lines.stderr
    assert r_no_fence.stderr != r_bad_lines.stderr
