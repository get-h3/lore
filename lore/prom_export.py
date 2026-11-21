"""Publish gate verdicts for the node_exporter textfile collector."""

from __future__ import annotations

import fcntl
import os
import re
import tempfile
from pathlib import Path

DEFAULT_TEXTFILE_DIR = "/var/lib/node_exporter/textfile"
_COUNTER = re.compile(r"^lore_gate_runs_total ([0-9]+)$", re.MULTILINE)


def export_gate_verdict(allowed: bool) -> None:
    """Atomically publish a serialized read/increment/write of the gate counter."""
    directory = Path(os.environ.get("H3_LORE_TEXTFILE_DIR", DEFAULT_TEXTFILE_DIR))
    target = directory / "h3_lore.prom"
    # A stable, separate lock serializes concurrent writers across replacements.
    with (directory / ".h3_lore.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            try:
                previous = target.read_text(encoding="utf-8")
            except (FileNotFoundError, UnicodeDecodeError):
                previous = ""
            matches = _COUNTER.findall(previous)
            count = int(matches[0]) + 1 if len(matches) == 1 else 1
            content = (
                "# HELP lore_gate_runs_total Total gate verdicts exported.\n"
                "# TYPE lore_gate_runs_total counter\n"
                f"lore_gate_runs_total {count}\n"
                "# HELP lore_gate_last_success Whether the last gate allowed closure.\n"
                "# TYPE lore_gate_last_success gauge\n"
                f"lore_gate_last_success {int(allowed)}\n"
            )
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=directory,
                    prefix=".h3_lore.",
                    suffix=".tmp",
                    delete=False,
                ) as temp:
                    temp_path = Path(temp.name)
                    os.fchmod(temp.fileno(), 0o644)
                    temp.write(content)
                os.replace(temp_path, target)
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
