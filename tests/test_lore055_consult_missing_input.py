"""LORE-055 — consult with no title and no --failure must be a usage error.

Real-use hit: ``python -m lore consult`` (no arguments at all) slipped past
the classify step with ``title=None``, classified the empty input as a
no-match, and exited 0 with ``no matching runbook`` — silently reading (to a
scripting consumer) as "no runbook matched" when the real problem was a
missing/typo'd flag upstream. The help contract (LORE-007/009) requires a
title unless ``--failure <text>`` is supplied.

Contract pinned here (subprocess-level, per acceptance):

- ``consult`` with neither input → **exit 2**, concise ``error:`` message on
  stderr naming both required inputs (title / --failure).
- ``consult 'unrelated symptom'`` (a real, non-matching title) → exit 0 and
  ``no matching runbook`` — the intentional no-match is UNCHANGED fail-open.
- Same no-match shape holds for ``consult --failure`` (never an error once
  real input reaches the classifier; only the MISSING input is the error).
"""

# ch:trace row=LORE-055

from __future__ import annotations

import subprocess
import sys

# Text that classifies against no curated class (intentional no-match).
NO_MATCH_TEXT = "unrelated symptom"


def _run_consult(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "lore", "consult", *argv],
        capture_output=True,
        text=True,
        check=False,
    )


# --------------------------------------- missing input: usage error, exit 2
def test_consult_no_input_exit2():
    """`lore consult` with no title and no --failure exits 2."""
    result = _run_consult()
    assert result.returncode == 2


def test_consult_no_input_error_message_names_both_inputs():
    result = _run_consult()
    assert result.returncode == 2
    # Concise required-input error on stderr, not on stdout.
    stderr = result.stderr
    assert "error:" in stderr
    assert "--failure" in stderr
    assert "title" in stderr
    # No fail-open output on the error path.
    assert "no matching runbook" not in result.stdout


def test_consult_no_input_only_empty_stderr_is_capped():
    """--failure '' (empty string) is missing input too, matching the
    getattr(..., None) falsy check the handler uses."""
    result = _run_consult("--failure", "")
    assert result.returncode == 2
    assert "error:" in result.stderr


# ------------------------------- valid no-match: still fail-open, exit 0
def test_consult_unrelated_symptom_exit0_no_match():
    result = _run_consult(NO_MATCH_TEXT)
    assert result.returncode == 0
    assert "no matching runbook" in result.stdout
    assert "error:" not in result.stderr


def test_consult_failure_no_match_still_exit0():
    result = _run_consult("--failure", NO_MATCH_TEXT)
    assert result.returncode == 0
    assert "no matching runbook" in result.stdout


# ------------------------- real input still works unchanged (wiring intact)
def test_consult_with_title_and_match_unchanged():
    """A matching title keeps the pre-LORE-055 success path."""
    result = _run_consult("gateway drain window: 503s while restarts drain")
    assert result.returncode == 0
    assert "runbook: gateway-drain-window" in result.stdout
