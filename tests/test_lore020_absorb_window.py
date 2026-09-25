"""LORE-020 tests: absorb --window must plumb --source into sweep proposals.

Two defects under test:
1. The --window sweep path dropped --source (the single-proposal path kept
   it), so sweep proposals lost their provenance marker.
2. Contract under test stays byte-compatible: omitting --source keeps the
   payload WITHOUT a 'source' key (same None-rule as absorb_proposal), and
   an empty trail with --source set is still an explicit empty result, exit 0
   (propose-not-write holds).
"""

from __future__ import annotations

import io
import json

from lore.__main__ import main

_TRAIL_HEADER = "logsey export --window 2h"
_FENCED_TRAIL = f"""{_TRAIL_HEADER}
```
2026-09-24T10:00:00 unit=loreforge gateway drain 503 while restart
2026-09-24T10:05:00 unit=loreforge index.lock fight on the shared checkout
```
"""


def test_cli_absorb_window_source_recorded_per_class(capsys, monkeypatch):
    """--window + --source qa-dagger: EVERY per-class proposal carries
    "source": "qa-dagger" (RED: the sweep path dropped args.source)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(_FENCED_TRAIL))
    code = main(["absorb", "--window", "2h", "--source", "qa-dagger"])
    assert code == 0
    proposals = json.loads(capsys.readouterr().out)
    assert isinstance(proposals, list) and proposals
    assert {p["class_id"] for p in proposals} >= {
        "gateway-drain-window",
        "shared-checkout-collision",
    }
    for p in proposals:
        assert p["source"] == "qa-dagger"


def test_cli_absorb_window_no_source_keeps_payload_shape(capsys, monkeypatch):
    """Omitting --source on the sweep path keeps the payload WITHOUT a
    'source' key — same None-rule as the single-proposal path."""
    monkeypatch.setattr("sys.stdin", io.StringIO(_FENCED_TRAIL))
    code = main(["absorb", "--window", "2h"])
    assert code == 0
    proposals = json.loads(capsys.readouterr().out)
    for p in proposals:
        assert "source" not in p


def test_cli_absorb_window_empty_trail_with_source_exit0(capsys, monkeypatch):
    """Empty trail + --source: explicit empty result, exit 0 (not an error,
    nothing written) — the empty-trail contract holds with provenance set."""
    monkeypatch.setattr("sys.stdin", io.StringIO("just some prose, no blocks at all\n"))
    code = main(["absorb", "--window", "2h", "--source", "dogfood-dagger"])
    assert code == 0
    out = capsys.readouterr().out
    assert "no classifiable evidence blocks" in out
    assert "nothing written" in out
