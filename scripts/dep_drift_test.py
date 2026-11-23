import json
import os
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dep-drift.sh"

HEARTBEAT_RE = re.compile(
    r"^heartbeat: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4} "
    r"dep-drift\.sh ran \(rc=0\)$"
)


def run_drift(env_overrides):
    env = os.environ | env_overrides
    return subprocess.run(
        [str(SCRIPT)], env=env, text=True, capture_output=True, check=False
    )


def start_pypi(versions_by_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in versions_by_path:
                self.send_error(503)
                return
            body = json.dumps(
                {"info": {"version": versions_by_path[self.path]}}
            ).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_drift_report_is_read_only_and_reports_failures(tmp_path):
    lock = tmp_path / "uv.lock"
    lock.write_text(
        '[[package]]\nname="older"\nversion="1.9"\n'
        'source={registry="https://pypi.org/simple"}\n'
        '[[package]]\nname="same"\nversion="2.0rc1"\n'
        'source={registry="https://pypi.org/simple"}\n'
        '[[package]]\nname="offline"\nversion="1"\n'
        'source={registry="https://pypi.org/simple"}\n'
        '[[package]]\nname="local"\nversion="1"\nsource={editable="."}\n'
    )
    original = lock.read_bytes()

    server, thread = start_pypi({"/older/json": "1.10", "/same/json": "2.0rc1"})
    try:
        result = run_drift(
            {
                "LORE_DEP_DRIFT_LOCK": str(lock),
                "LORE_DEP_DRIFT_PYPI": f"http://127.0.0.1:{server.server_port}",
            }
        )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    assert result.returncode == 0
    assert "older" in result.stdout and "1.10" in result.stdout
    assert "Not on PyPI (local or non-registry source): local 1" in result.stdout
    assert "Unavailable: offline" in result.stdout
    assert "1 of 3 locked packages behind PyPI latest" in result.stdout
    assert "Incomplete report" in result.stdout
    assert lock.read_bytes() == original
    # LORE-20261012: every successful run leaves a fresh dated heartbeat line,
    # and it is the final line so the report table above stays parseable.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines and HEARTBEAT_RE.match(lines[-1])


def test_noop_run_appends_dated_heartbeat_and_stays_read_only(tmp_path):
    lock = tmp_path / "uv.lock"
    lock.write_text(
        '[[package]]\nname="current"\nversion="2.0"\n'
        'source={registry="https://pypi.org/simple"}\n'
    )
    original = lock.read_bytes()

    server, thread = start_pypi({"/current/json": "2.0"})
    try:
        result = run_drift(
            {
                "LORE_DEP_DRIFT_LOCK": str(lock),
                "LORE_DEP_DRIFT_PYPI": f"http://127.0.0.1:{server.server_port}",
            }
        )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    assert result.returncode == 0
    assert "0 of 1 locked packages behind PyPI latest" in result.stdout
    assert lock.read_bytes() == original
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines and HEARTBEAT_RE.match(lines[-1])
