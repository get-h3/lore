"""LORE-010 tests: the CLI surface (show/audit) + the absorb --window sweep.

Covers: show hit/unknown-class/--evidence/--format json paths, audit in all
three formats (honest 'no data' freshness, no fabricated dates, zero-real-
command summary), the absorb --window sweep over piped trails (hit, empty,
unparseable, bad duration, provenance recording), and the propose-not-write
guard over the whole sweep path.
"""

from __future__ import annotations

import json

import pytest

from lore.__main__ import main
from lore.absorb import parse_duration
from lore.classes import UNCLASSIFIED_ID, get_registry

NO_DATA = "no data"


def _run(argv):
    return main(argv)


# ------------------------------------------------------------------ lore show
def test_cli_show_known_class_md(capsys):
    code = _run(["show", "gateway-drain-window"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.startswith("# Runbook: Gateway drain window (`gateway-drain-window`)")
    assert "## Checks (in order)" in out
    assert f"Last validated:** {NO_DATA}" in out  # honest freshness


def test_cli_show_json_matches_compile_shape(capsys):
    code = _run(["show", "gateway-drain-window", "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["class_id"] == "gateway-drain-window"
    assert set(data) >= {"name", "signature", "checks", "status", "last_validated"}


def test_cli_show_unknown_class_exit2(capsys):
    code = _run(["show", "does-not-exist"])
    assert code == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "does-not-exist" in err


def test_cli_show_evidence_adds_provenance_and_trail(capsys):
    code = _run(["show", "gateway-drain-window", "--evidence"])
    assert code == 0
    out = capsys.readouterr().out
    assert "## Evidence / provenance detail" in out
    assert "- Provenance: Compiled by lore.compiler" in out
    # the class's seeded trail kinds show up as evidence lines
    assert "- incident:" in out or "- memory:" in out


def test_cli_show_evidence_json(capsys):
    code = _run(["show", "gateway-drain-window", "--evidence", "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    # attach_evidence doubled the seed trail (seed + attached blocks)
    assert len(data["evidence_trail"]) >= 2


# ----------------------------------------------------------------- lore audit
def _audit_json():
    _run(["audit", "--format", "json"])


def test_cli_audit_json_all_classes_honest_freshness(capsys):
    code = _run(["audit", "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    rows = data["classes"]
    assert [r["class_id"] for r in rows] == [c.id for c in get_registry().all_classes()]
    for r in rows:
        assert r["runbook_compiled"] is True
        assert isinstance(r["check_count"], int)
        assert r["command_count"] <= r["check_count"]
        # HONESTY: no fabricated dates — every class reports 'no data' today.
        assert r["last_validated"] == NO_DATA
    assert data["summary"]["total_classes"] == len(rows)
    # The note states the truth: nothing auto-populates the field in v0.1.
    assert "never auto-populated" in data["summary"]["note"]
    assert "operator attestation" in data["summary"]["note"]
    assert "populated only by" not in data["summary"]["note"]


def test_cli_audit_table_rendered_aligned(capsys):
    code = _run(["audit", "--format", "table"])
    assert code == 0
    out = capsys.readouterr().out
    assert "class_id" in out
    assert "last_validated" in out
    assert f"{NO_DATA}" in out
    assert out.strip().splitlines()[-1].startswith("summary:")


def test_cli_audit_md_table(capsys):
    code = _run(["audit", "--format", "md"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.startswith("| class_id |")
    assert "|---" in out
    assert "| gateway-drain-window |" in out
    assert "**Summary:**" in out


# ------------------------------------------------- absorb --window sweep unit
def test_parse_duration_forms():
    assert parse_duration("2h") == 7200
    assert parse_duration("45m") == 2700
    assert parse_duration("90s") == 90
    assert parse_duration("2") == 7200  # bare = hours
    with pytest.raises(ValueError):
        parse_duration("abc")
    with pytest.raises(ValueError):
        parse_duration("0h")
    with pytest.raises(ValueError):
        parse_duration("-3h")


_TRALE_HEADER = "logsey export --window 2h"
_FENCED_TRAIL = f"""{_TRALE_HEADER}
```
2026-09-24T10:00:00 unit=loreforge gateway drain 503 while restart
2026-09-24T10:05:00 unit=loreforge index.lock fight on the shared checkout
```
"""


def test_absorb_sweep_groups_by_class():
    from lore.evidence import parse_logsey_export

    blocks = parse_logsey_export(_FENCED_TRAIL)
    assert len(blocks) == 2
    from lore.absorb import absorb_sweep

    proposals = absorb_sweep(blocks, window="2h", ns="X", board="/tmp/board")
    by_id = {p["class_id"]: p for p in proposals}
    assert "gateway-drain-window" in by_id
    assert "shared-checkout-collision" in by_id
    gw = by_id["gateway-drain-window"]
    assert gw["sweep"]["ns"] == "X"
    assert gw["sweep"]["window"] == "2h"
    assert gw["provenance"]["kind"] == "absorb-sweep"
    assert gw["provenance"]["board"] == "/tmp/board"


def test_absorb_sweep_unclassified_kept_honest():
    from lore.evidence import parse_logsey_export

    trail = f"""{_TRALE_HEADER}
```
2026-09-24T10:00:00 unit=loreforge the coffee machine is making a weird noise
```
"""
    blocks = parse_logsey_export(trail)
    from lore.absorb import absorb_sweep

    proposals = absorb_sweep(blocks)
    assert [p["class_id"] for p in proposals] == [UNCLASSIFIED_ID]
    assert proposals[0]["sweep"]["blocks_class"] == 1


def test_absorb_sweep_empty_blocks_yields_empty_list():
    from lore.absorb import absorb_sweep

    assert absorb_sweep([]) == []


# ----------------------------------------------------- CLI absorb --window
def test_cli_absorb_window_hit_from_stdin(capsys, monkeypatch):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(_FENCED_TRAIL))
    code = _run(["absorb", "--window", "2h", "--ns", "X"])
    assert code == 0
    out = capsys.readouterr().out
    proposals = json.loads(out)
    assert isinstance(proposals, list)
    ids = {p["class_id"] for p in proposals}
    assert "gateway-drain-window" in ids
    assert "shared-checkout-collision" in ids
    for p in proposals:
        assert p["provenance"]["ns"] == "X"
        assert p["provenance"]["window"] == "2h"


def test_cli_absorb_window_empty_trail_exit0(capsys, monkeypatch):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("just some prose, no blocks at all\n"))
    code = _run(["absorb", "--window", "2h"])
    assert code == 0
    out = capsys.readouterr().out
    assert "no classifiable evidence blocks" in out
    assert "nothing written" in out


def test_cli_absorb_window_trail_file(capsys, tmp_path):
    trail = tmp_path / "trail.txt"
    trail.write_text(_FENCED_TRAIL, encoding="utf-8")
    code = _run(["absorb", "--window", "2h", "--trail-file", str(trail)])
    assert code == 0
    proposals = json.loads(capsys.readouterr().out)
    assert proposals  # parsed from the file


def test_cli_absorb_window_unparseable_export_exit2(capsys):
    code = _run(["absorb", "--window", "2h", "--trail-file", "/dev/null-nonexistent"])
    assert code == 2


def test_cli_absorb_window_header_without_block_exit2(capsys, monkeypatch):
    import io

    # Claims an export (header) but no fenced block: LogseyExportParseError.
    monkeypatch.setattr("sys.stdin", io.StringIO(_TRALE_HEADER + "\n"))
    code = _run(["absorb", "--window", "2h"])
    assert code == 2
    assert "does not parse" in capsys.readouterr().err


def test_cli_absorb_window_bad_duration_exit2(capsys, monkeypatch):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(_FENCED_TRAIL))
    code = _run(["absorb", "--window", "banana"])
    assert code == 2
    assert "--window" in capsys.readouterr().err


def test_cli_absorb_without_window_still_single_proposal(capsys):
    code = _run(
        [
            "absorb",
            "--class",
            "gateway-drain-window",
            "--lesson",
            "drain before restart",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["class_id"] == "gateway-drain-window"
    assert payload["lesson"] == "drain before restart"


def test_cli_absorb_neither_window_nor_class_exit2(capsys):
    code = _run(["absorb"])
    assert code == 2
    assert "--window" in capsys.readouterr().err


# ------------------------------------------------- propose-not-write (sweep)
def test_cli_absorb_window_performs_no_filesystem_writes(tmp_path, monkeypatch):
    """Hard law: the sweep is stdout-only. Snapshot the cwd tree, run the
    sweep over a piped trail, prove nothing appeared/changed anywhere."""
    import hashlib
    import io
    import os

    def _tree_digest(root):
        entries = []
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                p = os.path.join(dirpath, fn)
                st = os.stat(p)
                with open(p, "rb") as fh:
                    digest = hashlib.sha256(fh.read()).hexdigest()
                entries.append((p, st.st_size, digest))
        return sorted(entries)

    before = _tree_digest(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(_FENCED_TRAIL))
    code = _run(
        ["absorb", "--window", "2h", "--ns", "X", "--board", str(tmp_path / "b.jsonl")]
    )
    assert code == 0
    assert _tree_digest(tmp_path) == before


# ------------------------------------------------------------------- version
def test_version_single_source_of_truth():
    """LORE-041: the declared package version must agree everywhere it lives.

    pyproject.toml is the single source of truth; lore.__version__ and the
    uv.lock entry must match it. This pins the drift class where the module
    constant lagged the pyproject version (0.1.0 vs 0.1.1 at bump time).
    """
    import importlib.metadata
    import pathlib
    import tomllib

    pyproject = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"][
        "version"
    ]

    # module constant matches pyproject
    import lore

    assert lore.__version__ == declared, (
        f"lore.__version__ ({lore.__version__}) != pyproject version ({declared})"
    )

    # installed distribution metadata matches (the editable install is
    # refreshed by `uv sync`; the lock carries the same version)
    assert importlib.metadata.version("lore") == declared

    # uv.lock carries the same version (no lock drift after a bump)
    lock = (pathlib.Path(__file__).resolve().parent.parent / "uv.lock").read_text(
        encoding="utf-8"
    )
    import re

    lock_version = re.search(r'name = "lore"\nversion = "([^"]+)"', lock)
    assert lock_version is not None, "uv.lock has no lore package entry"
    assert lock_version.group(1) == declared, (
        f"uv.lock lore version ({lock_version.group(1)}) != pyproject ({declared})"
    )

    # sanity: not a placeholder and still in the 0.1.x line this repo ships
    assert declared.startswith("0.1.")
