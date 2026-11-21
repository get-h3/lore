#!/usr/bin/env bash
# Report locked registry packages behind PyPI without modifying the environment.
if [ "${1:-}" = "--help" ]; then
    printf '%s\n' 'Usage: scripts/dep-drift.sh' 'Report locked packages behind PyPI; never update dependencies.'
    exit 0
fi
if [ "$#" -ne 0 ]; then
    printf '%s\n' 'Unknown argument; use --help.' >&2
    exit 0
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python="$root/.venv/bin/python"
if [ ! -x "$python" ]; then
    printf '%s\n' 'Dependency drift unavailable: project .venv/bin/python is missing.'
    exit 0
fi
"$python" - "$root" <<'PY'
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request

try:
    from packaging.version import InvalidVersion, Version
except ImportError:
    print('Dependency drift unavailable: packaging is not installed in the project venv.')
    sys.exit(0)

root = Path(sys.argv[1])
lock_path = Path(os.environ.get('LORE_DEP_DRIFT_LOCK', root / 'uv.lock'))
base = os.environ.get('LORE_DEP_DRIFT_PYPI', 'https://pypi.org/pypi').rstrip('/')
try:
    with lock_path.open('rb') as stream:
        packages = tomllib.load(stream)['package']
except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
    print(f'Dependency drift unavailable: cannot read lock file: {exc}')
    sys.exit(0)

registry = []
for package in packages:
    name, version = package['name'], package['version']
    if 'registry' not in package.get('source', {}):
        print(f'Not on PyPI (local or non-registry source): {name} {version}')
    else:
        registry.append((name, version))

def lookup(item):
    name, locked = item
    try:
        url = f'{base}/{urllib.parse.quote(name, safe="")}/json'
        with urllib.request.urlopen(url, timeout=10) as response:
            latest = json.load(response)['info']['version']
        return item, latest, Version(locked) < Version(latest), None
    except (OSError, ValueError, KeyError, TypeError, InvalidVersion) as exc:
        return item, None, False, str(exc)

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(lookup, registry))
print(f'{"Package":<30} {"Locked":<20} Latest')
behind = 0
failed = 0
for (name, locked), latest, is_behind, error in results:
    if error:
        failed += 1
        print(f'Unavailable: {name} {locked}: {error}')
    elif is_behind:
        behind += 1
        print(f'{name:<30} {locked:<20} {latest}')
print(f'{behind} of {len(registry)} locked packages behind PyPI latest')
if failed:
    print(f'Incomplete report: {failed} PyPI lookup(s) failed; the behind count is a lower bound.')
PY
status=$?
if [ "$status" -ne 0 ]; then
    printf 'Dependency drift unavailable: report process exited %s.\n' "$status" >&2
fi
exit 0
