# QA-LORE-RELENG-2 — network independency, proven instead of noted

Row: `QA-LORE-RELENG-2` (P3, filed by `lore-qa` 2026-11-04 from the
`chaos-disconnect` cell: "passes with network cut (no network dep)").

The QA lane could only REPORT the observation. This artifact converts it into a
reproducible, enforced proof at an exact commit.

- Commit under test: `07ef9c9a6c613b9cb7009d383c4d265b453f04cf` (`origin/main`)
- Run timestamp (UTC): 2026-11-16T20:45:30Z
- Environment: repo-local `.venv`, Python 3.14.5, pytest 9.1.1
- Raw logs live next to this file (stored as `.txt` — the repo gitignores `*.log`,
  which would have silently kept them out of the commit); `run-meta.txt` carries the
  exit codes and the commit under test.

## Method — audit-hook kill switch, not a namespace

`unshare -rn` is unavailable on this host (`write failed /proc/self/uid_map:
Operation not permitted`), so isolation is enforced inside the interpreter
instead. `netblock_plugin.py` installs a `sys.addaudithook` hook that raises
`OfflineSuiteViolation` on:

`socket.getaddrinfo`, `socket.gethostbyname`, `socket.gethostbyaddr`,
`socket.connect` (INET addresses only — AF_UNIX paths are local IPC, not
network), `http.client.connect`, `urllib.Request`.

An audit hook cannot be bypassed by `from socket import socket` import style,
which is why it is stronger than monkeypatching module attributes.

## Kill switch is RED-proven first

If the plugin silently failed to load, a green suite would prove nothing. So the
switch is falsified deliberately before it is trusted:

```
PYTHONPATH=<evidence-dir> \
  python -m pytest <evidence-dir>/redproof_test_netblock.py -p netblock_plugin -q
```

`redproof_test_netblock.py` is tracked, carries no `test_` prefix, and is
therefore invisible to a normal `pytest tests/` run (`572 tests collected`
unchanged) while still collectable when passed explicitly by path.

Result (`redproof-dns-blocked.txt`, exit 1):

```
E  netblock_plugin.OfflineSuiteViolation: offline-suite-violation: socket.getaddrinfo((443,))
1 failed in 0.36s
```

A plain `socket.getaddrinfo("example.com", 443)` therefore CANNOT succeed in the
offline run.

## Full suite under the kill switch

```
PYTHONPATH=<evidence-dir> python -m pytest tests/ -p netblock_plugin -q
```

| Run | Command | Result | Exit |
|---|---|---|---|
| Offline-enforced | `pytest tests/ -p netblock_plugin -q` | **572 passed**, 0 failed, 0 skipped | 0 |
| Baseline (no hook) | `pytest tests/ -q` | 572 passed | 0 |
| Red-proof (DNS attempt) | `pytest <redproof> -p netblock_plugin -q` | 1 failed (blocked) | 1 |
| Lint | `ruff check .` | All checks passed | 0 |
| Format | `ruff format --check .` | 627 files already formatted | 0 |
| Count guard | `bash scripts/check-test-count.sh` | PASS canonical=572 live=572, class-count=13 | 0 |

The two suite runs collect the SAME 572 tests and both pass, so nothing was
deselected or skipped to make the offline run green. Zero `OfflineSuiteViolation`
was raised, i.e. no test, fixture, or import path reached for DNS, an HTTP client,
or an INET socket.

## Known limits of this proof (stated, not glossed)

The audit hook governs the CPython process the tests run in: `socket`,
`http.client`, `urllib`, and anything built on them (requests/httpx both land on
`socket.getaddrinfo`). It does NOT see a client spawned as a SUBPROCESS
(`git push`, `curl`, `pip`), nor a resolver inside a C extension that bypasses
`socket` — those would need kernel-level isolation instead, and `unshare -rn` is
refused on this host. So the honest claim is: nothing in-process in the suite
touches the network; a future subprocess-spawned network call is outside this
gate's coverage.

## Result

Resolved as informational-but-enforced: the repo's suite has no external network
dependency, and this is now falsifiable — if a future change starts calling out,
the offline run fails loudly with the offending audit event. Reproduce with the
two commands above; nothing else is required.
