"""Minimal lore CLI.

Full CLI surface (show/absorb/audit/validate) is a later board task; this
module implements ``match`` and the LORE-004 ``compile`` subcommand:

    python -m lore match "<symptoms>"
    python -m lore compile [--class <class_id>] [--format json|md]

``compile`` prints compiled runbook PROPOSALS to stdout. It never writes a
runbook to disk anywhere (propose-not-write): the only side effect is stdout.
Unknown --class exits non-zero via the registry (closed, curated).
"""

from __future__ import annotations

import argparse
import json
import sys

from lore.classifier import classify_all
from lore.compiler import compile_all, compile_class
from lore.runbook import Runbook


def _cmd_match(args: argparse.Namespace) -> int:
    candidates = classify_all(args.text)
    if not candidates:
        print("no candidates")
        return 1
    for c in candidates:
        evidence = "; ".join(f"{e['kind']}:{e['detail']}" for e in c.evidence) or "none"
        print(f"{c.class_id}\tconfidence={c.confidence:.2f}\tevidence: {evidence}")
    return 0


def _cmd_compile(args: argparse.Namespace) -> int:
    runbooks: list[Runbook]
    if args.class_id:
        try:
            runbooks = [compile_class(args.class_id)]
        except KeyError as exc:
            print(f"error: {exc.args[0]}", file=sys.stderr)
            return 2
    else:
        runbooks = compile_all()

    if args.format == "json":
        print(json.dumps([rb.to_dict() for rb in runbooks], indent=2))
    else:
        out = [rb.to_markdown() for rb in runbooks]
        print("\n".join(out))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lore",
        description="Match symptoms and compile runbooks from fleet incident history.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    match_p = sub.add_parser("match", help="classify a symptom text")
    match_p.add_argument("text", help="symptoms or log line(s)")
    match_p.set_defaults(func=_cmd_match)

    compile_p = sub.add_parser(
        "compile", help="compile runbook proposal(s) per failure class (stdout only)"
    )
    compile_p.add_argument(
        "--class",
        dest="class_id",
        default=None,
        help="compile one class; omit to compile every registry class",
    )
    compile_p.add_argument(
        "--format",
        choices=("json", "md"),
        default="json",
        help="output format (default: json)",
    )
    compile_p.set_defaults(func=_cmd_compile)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
