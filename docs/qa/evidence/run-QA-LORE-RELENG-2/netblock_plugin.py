"""Offline-suite enforcement: audit-hook network kill switch (QA-LORE-RELENG-2).

Loaded with `-p netblock_plugin` (PYTHONPATH pointing at this directory). Any
attempt to resolve a name or open/connect an INET socket raises
`OfflineSuiteViolation`, so a green suite under this plugin is proof the test
run has no external network dependency.

AF_UNIX sockets and loopback-free local IPC are allowed (not network).
"""

import sys

BLOCKED_EVENTS = {
    "socket.getaddrinfo",
    "socket.gethostbyname",
    "socket.gethostbyaddr",
    "socket.connect",
    "http.client.connect",
    "urllib.Request",
}


class OfflineSuiteViolation(RuntimeError):
    """Raised when code under test reaches for the network."""


def _is_inet_address(address) -> bool:
    # socket.connect audit args = (socket, address); INET addresses are
    # (host, port) tuples, AF_UNIX addresses are str/bytes paths.
    return isinstance(address, tuple)


def _hook(event, args):
    if event not in BLOCKED_EVENTS:
        return
    if event == "socket.connect":
        address = args[1] if len(args) > 1 else None
        if not _is_inet_address(address):
            return
    raise OfflineSuiteViolation(f"offline-suite-violation: {event}({args[1:2]!r})")


mode = sys.argv  # keep linters quiet about unused import order

sys.addaudithook(_hook)
