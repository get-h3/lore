"""Minimal lore CLI.

Full CLI surface (show/absorb/audit/validate) is a later board task; this
module implements only ``match``:

    python -m lore match "<symptoms>"
"""

from __future__ import annotations

import argparse

from lore.classifier import classify_all


def _cmd_match(args: argparse.Namespace) -> int:
    candidates = classify_all(args.text)
    if not candidates:
        print("no candidates")
        return 1
    for c in candidates:
        evidence = "; ".join(f"{e['kind']}:{e['detail']}" for e in c.evidence) or "none"
        print(f"{c.class_id}\tconfidence={c.confidence:.2f}\tevidence: {evidence}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lore",
        description="Match symptoms to curated failure classes (full CLI later).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    match_p = sub.add_parser("match", help="classify a symptom text")
    match_p.add_argument("text", help="symptoms or log line(s)")
    match_p.set_defaults(func=_cmd_match)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
