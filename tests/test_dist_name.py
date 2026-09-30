"""Distribution-naming contract (RELEASE-LORE-002 / QA-LORE-2).

Hermetic (no network): pins the naming decision that the bare `lore` name on
PyPI is occupied by an unrelated foreign package (instacart/lore), so this
project's DISTRIBUTION name is `get-h3-lore` while the import package and the
console script stay `lore`, and the project is source-install only (no PyPI
publish). Same text-assertion style as tests/test_readme_links.py.
"""

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FOREIGN_NAME = "lore"
DIST_NAME = "get-h3-lore"


def _pyproject() -> dict:
    return tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))


def test_distribution_name_is_not_the_squatted_bare_name() -> None:
    project = _pyproject()["project"]
    assert project["name"] == DIST_NAME
    assert project["name"] != FOREIGN_NAME, (
        "the bare distribution name 'lore' is occupied on PyPI by an unrelated "
        "package (instacart/lore) — it must never be this project's name"
    )


def test_console_script_still_named_lore() -> None:
    scripts = _pyproject()["project"].get("scripts", {})
    assert scripts.get("lore") == "lore.__main__:main"


def test_import_package_still_lore_with_version() -> None:
    import lore

    assert lore.__version__.startswith("0.1.")


def test_never_pip_install_lore_warning_in_docs() -> None:
    """The install posture (source-only, never the squatted name) must not rot."""
    for doc in ("README.md", "docs/INSTALL.md"):
        text = (REPO / doc).read_text(encoding="utf-8")
        assert DIST_NAME in text, f"{doc} never states the distribution name"
        assert "pip install lore" in text, (
            f"{doc} carries no 'never pip install lore' warning"
        )
