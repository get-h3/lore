"""Reproducible red-proof for the QA-LORE-RELENG-2 offline kill switch.

Collected ONLY when passed explicitly by path (no `test_` prefix, so a normal
`pytest tests/` run never sees it). It MUST FAIL under `-p netblock_plugin`:

    PYTHONPATH=docs/qa/evidence/run-QA-LORE-RELENG-2 \
      .venv/bin/python -m pytest \
      docs/qa/evidence/run-QA-LORE-RELENG-2/redproof_test_netblock.py \
      -p netblock_plugin -q
"""

import socket


def test_dns_lookup_must_be_blocked_by_the_plugin():
    socket.getaddrinfo("example.com", 443)
