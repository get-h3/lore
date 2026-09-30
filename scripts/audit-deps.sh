#!/usr/bin/env bash
# Project-scoped dependency audit for lore.
#
# WARNING: bare `pip-audit` (no -r) audits the AMBIENT interpreter environment
# — every host site-package — and is INVALID here. Always audit via this
# script, which exports only the project's resolved dependencies (uv export
# from uv.lock, dev extras included) and audits exactly that list.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
uv sync --extra dev
uv export --format requirements-txt --no-hashes --no-emit-project --all-extras -o /tmp/lore-audit-reqs.txt
uv run pip-audit -r /tmp/lore-audit-reqs.txt --no-deps "$@"
