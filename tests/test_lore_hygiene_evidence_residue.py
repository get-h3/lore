"""Regression test for LORE-HYGIENE-20261122: QA battery residue stays invisible.

The bunker-qa.sh collector used to persist each battery's evidence ledger and
per-cell logs INSIDE the repo under ``.coding-hermes/evidence/<tick>/``. Every
QA battery therefore left 100-500K of untracked residue in the checkout and
``scripts/release.sh``'s clean-tree precheck (``git status --porcelain``)
refused every release dry-run for a reason no reviewer could act on.

Two-layer fix, both proven here:

1. The harness now persists OUTSIDE the tree
   (``~/.hermes/qa/evidence/<project>/<tick>/``) — proven live by the harness's
   own versioned suite (test_bunker_qa_evidence_persist.sh, deployed copy), not
   by this file.
2. Belt-and-braces: .gitignore carries ``.coding-hermes/evidence/`` so even a
   pre-fix harness generation writing the legacy path can never read as dirty
   tree residue again — THIS file pins that rule.

A file that is gitignored is also invisible to ``git status --porcelain``, so
the release precheck can never trip on the legacy path again.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_RESIDUE_DIR = REPO_ROOT / ".coding-hermes" / "evidence"


def _git(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command at the repo root (subprocess style of test_count_guard)."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("git is genuinely unavailable on this box")


@pytest.fixture()
def legacy_residue_probe() -> Path:
    """Create a battery-shaped residue probe under the legacy path, clean after."""
    probe_dir = LEGACY_RESIDUE_DIR / "qa-ignore-probe-lore-hygiene"
    probe_dir.mkdir(parents=True, exist_ok=True)
    probe_file = probe_dir / "evidence.jsonl"
    probe_file.write_text('{"cell":"probe","status":"OK"}\n', encoding="utf-8")
    try:
        yield probe_file
    finally:
        # Remove the probe tree; drop the parent dirs we created if empty so the
        # checkout is left exactly as the harness (post-fix) leaves it: no
        # .coding-hermes/evidence directory at all.
        probe_file.unlink(missing_ok=True)
        probe_dir.rmdir()
        for parent in (LEGACY_RESIDUE_DIR, LEGACY_RESIDUE_DIR.parent):
            try:
                parent.rmdir()
            except OSError:
                break  # not empty (pre-existing content) — leave it alone


def test_legacy_evidence_path_is_gitignored(legacy_residue_probe: Path) -> None:
    """git check-ignore must admit a probe file under .coding-hermes/evidence/.

    The belt-and-braces rule pins the legacy battery residue path so a pre-fix
    harness generation (or any other writer) cannot dirty the release
    clean-tree precheck again. Exit code 0 = the path IS ignored.
    """
    proc = _git("check-ignore", "-v", str(legacy_residue_probe.relative_to(REPO_ROOT)))
    assert proc.returncode == 0, (
        f"legacy residue path is NOT ignored (rc={proc.returncode}): "
        f"{legacy_residue_probe.relative_to(REPO_ROOT)}"
    )
    assert ".coding-hermes/evidence/" in proc.stdout, (
        f"expected the .coding-hermes/evidence/ rule to fire, got: {proc.stdout}"
    )


def test_legacy_evidence_path_never_reads_as_dirty(
    legacy_residue_probe: Path,
) -> None:
    """git status --porcelain must stay clean with residue present.

    This is the exact surface scripts/release.sh's precheck reads. With the
    probe file on disk under the legacy path, porcelain must not list it —
    LORE-HYGIENE-20261122's demanded post-battery behaviour, belt layer.
    """
    assert legacy_residue_probe.exists(), "fixture probe missing"
    porcelain = _git("status", "--porcelain").stdout or ""
    residue_lines = [
        line for line in porcelain.splitlines() if ".coding-hermes/evidence" in line
    ]
    assert residue_lines == [], (
        f"legacy residue path reads as dirty tree: {residue_lines}"
    )
