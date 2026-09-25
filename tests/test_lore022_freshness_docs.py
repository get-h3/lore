"""LORE-022: pin the corrected freshness promise — v0.1 never auto-populates
``last_validated``.

The old wording ("last_validated is populated only by ``lore validate
--execute`` runs") was FALSE: no v0.1 code path writes that field — a lint
run is not operator attestation (``apply_lint`` deliberately never stamps
it). These tests pin the corrected, truthful wording in every user-visible
surface (README, the ``lore audit`` summary note, the audit docstrings) and
pin that the ``validate --execute`` help makes no population claim.
"""

import inspect
from pathlib import Path

import lore.__main__ as main_mod

_REPO_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------- lore audit CLI
def test_audit_summary_note_makes_no_population_claim(capsys):
    # The `lore audit --format json` machine-checkable note must state the
    # truth: nothing auto-populates last_validated in v0.1; the lint itself
    # (stale flag / drift reason) is today's freshness signal.
    code = main_mod.main(["audit", "--format", "json"])
    out = capsys.readouterr().out
    assert code == 0
    assert "populated only by" not in out
    assert "never auto-populated" in out
    assert "operator attestation" in out


def test_validate_help_makes_no_population_claim(capsys):
    # `lore validate --help` must describe --execute (runs gate-approved
    # read-only commands) WITHOUT claiming it populates last_validated.
    try:
        main_mod.main(["validate", "--help"])
    except SystemExit:
        pass  # argparse exits 0 after printing help
    out = capsys.readouterr().out
    assert "populat" not in out, "validate help must make no population claim"


# ----------------------------------------------------------------- docstrings
def test_audit_docstrings_state_the_truth():
    doc = inspect.getdoc(main_mod._audit_rows)
    assert doc is not None
    assert "never auto-populated" in doc
    assert "operator attestation" in doc
    assert "populated only by" not in doc


# ----------------------------------------------------------- source doc pins
def test_readme_freshness_promise_is_truthful():
    readme = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "populated only by" not in readme
    assert "never auto-populated" in readme
    assert "operator attestation" in readme


def test_main_source_summary_note_is_truthful():
    src = (_REPO_ROOT / "lore" / "__main__.py").read_text(encoding="utf-8")
    assert "populated only by" not in src
    assert "never auto-populated" in src
    assert "operator attestation" in src
