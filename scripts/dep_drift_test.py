import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dep-drift.sh"


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

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            versions = {"/older/json": "1.10", "/same/json": "2.0rc1"}
            if self.path not in versions:
                self.send_error(503)
                return
            body = json.dumps({"info": {"version": versions[self.path]}}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ | {
            "LORE_DEP_DRIFT_LOCK": str(lock),
            "LORE_DEP_DRIFT_PYPI": f"http://127.0.0.1:{server.server_port}",
        }
        result = subprocess.run(
            [str(SCRIPT)], env=env, text=True, capture_output=True, check=False
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
