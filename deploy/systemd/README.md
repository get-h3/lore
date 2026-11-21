# Dependency drift user timer

These are host-specific examples. After the script has landed in the main checkout,
copy both unit files to `~/.config/systemd/user/`, adjusting their absolute paths
for the box, and create `~/.local/share/lore/` for the log. The main checkout
needs its existing `.venv` with `packaging` installed. Then run
`systemctl --user daemon-reload` and
`systemctl --user enable --now lore-dep-drift.timer`.

The timer reports behind-PyPI pins; it never updates the lock or environment.
Lookup failures are reported as incomplete. `scripts/audit-deps.sh` separately
scans for known vulnerabilities. The 07:45 start is staggered 15 minutes after
validation; it does not guarantee that a long validation run has finished.

Run the drift-specific regression with `uv run pytest -q scripts/dep_drift_test.py`;
it is outside the default `tests/` collection.
