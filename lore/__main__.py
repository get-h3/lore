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

from lore.absorb import (
    DECISION_ABSORB,
    DECISION_NO_NEW_LESSON,
    AbsorbDecision,
    absorb_proposal,
    gate_close,
)
from lore.classifier import classify_all, near_misses
from lore.compiler import compile_all, compile_class
from lore.consult import ConsultResult, consult
from lore.runbook import Runbook
from lore.validate import is_read_only_command, lint_runbook


def _cmd_match(args: argparse.Namespace) -> int:
    candidates = classify_all(args.text)
    if not candidates:
        print("no candidates")
        return 1
    for c in candidates:
        evidence = "; ".join(f"{e['kind']}:{e['detail']}" for e in c.evidence) or "none"
        print(f"{c.class_id}\tconfidence={c.confidence:.2f}\tevidence: {evidence}")
    if getattr(args, "explain", False):
        # Evidence echo for the honest refusal: classes that *almost* matched
        # (raw keyword fraction below threshold) — never labels, just signal.
        misses = near_misses(args.text)
        if misses:
            print("near-misses:")
            for nm in misses:
                kws = ", ".join(nm.hit_keywords)
                print(
                    f"  {nm.class_id}  score={nm.raw_score:.2f}  "
                    f"({nm.n_hits}/{nm.n_keywords} keywords: {kws})"
                )
        else:
            print("near-misses: none")
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


def _cmd_consult(args: argparse.Namespace) -> int:
    """LORE-007: tick-start consult. FAIL-OPEN is the contract — a no-match
    is not an error (exit 0, "no matching runbook"); a broken compile omits
    that ref instead of crashing the caller's tick."""
    result: ConsultResult = consult(
        f"{args.title}\n{args.detail}" if args.detail else args.title
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    if not result.matched:
        print("no matching runbook")
        return 0
    for ref in result.runbook_refs:
        lv = ref["last_validated"] if ref["last_validated"] else "never"
        print(
            f"runbook: {ref['class_id']} ({ref['name']}) "
            f"status={ref['status']} last_validated={lv} checks={ref['check_count']}"
        )
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """LORE-006: the read-only command lint.

    DEFAULT IS PLAN-ONLY (``--dry-run`` is the default, not the exception):
    it lists which commands WOULD run and executes NOTHING. Actual
    execution requires the explicit ``--execute`` opt-in, and even then the
    default-deny gate refuses every command it cannot positively recognize
    as read-only. Honesty: a green lint proves commands parse and answer,
    NOT that recovery succeeds.
    """
    runbooks: list[Runbook]
    if args.class_id:
        try:
            runbooks = [compile_class(args.class_id)]
        except KeyError as exc:
            print(f"error: {exc.args[0]}", file=sys.stderr)
            return 2
    else:
        runbooks = compile_all()

    if not args.execute:
        # Plan/dry-run: list what WOULD run; never execute anything.
        if args.format == "json":
            plan = [
                {
                    "class_id": rb.class_id,
                    "mode": "plan",
                    "note": (
                        "plan only — no command was executed; pass --execute "
                        "to run the gate-approved read-only commands"
                    ),
                    "would_run": [
                        {"order": c.order, "command": c.command}
                        for c in sorted(rb.checks, key=lambda x: x.order)
                        if c.command.strip() and c.command.strip() != "no data"
                    ],
                    "absent": [
                        c.order
                        for c in sorted(rb.checks, key=lambda x: x.order)
                        if c.command.strip() == "no data"
                    ],
                    "would_refuse": [
                        {"order": c.order, "command": c.command}
                        for c in sorted(rb.checks, key=lambda x: x.order)
                        if c.command.strip()
                        and c.command.strip() != "no data"
                        and not is_read_only_command(c.command)
                    ],
                }
                for rb in runbooks
            ]
            print(json.dumps(plan, indent=2))
        else:
            for rb in runbooks:
                print(f"# {rb.class_id} — plan (nothing executed)")
                if not rb.checks:
                    print("  no data (no checks)")
                for c in sorted(rb.checks, key=lambda x: x.order):
                    if c.command.strip() == "no data":
                        print(f"  check {c.order}: absent (no data — not a command)")
                    elif is_read_only_command(c.command):
                        print(f"  check {c.order}: would run: {c.command}")
                    else:
                        print(f"  check {c.order}: would REFUSE: {c.command}")
                print()
        return 0

    # Explicit --execute: run gate-approved read-only commands only.
    reports = [lint_runbook(rb) for rb in runbooks]
    if args.format == "json":
        print(json.dumps([r.to_dict() for r in reports], indent=2))
    else:
        for report in reports:
            print(f"# {report.class_id}")
            for r in report.results:
                suffix = f" (exit {r.exit_code})" if r.exit_code is not None else ""
                print(f"  check {r.order}: {r.outcome}{suffix}: {r.command}")
            reason = report.stale_reason
            print(f"  stale_reason: {reason if reason else 'none'}")
            print(f"  honesty: {report.honesty_label}")
            print()
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    """LORE-008: machine-checked closure gate. Prints the verdict + errors.

    Exit 0 when allowed, 1 when denied. The gate NEVER writes anything.
    """
    d = AbsorbDecision(
        decision=args.decision,
        class_id=args.class_id,
        lesson=args.lesson,
        reason=args.reason,
        ack_ref=args.ref,
        decided_at=args.decided_at,
    )
    verdict = gate_close(d)
    print(verdict.summary())
    for err in verdict.errors:
        print(f"error: {err}")
    return 0 if verdict.allowed else 1


def _cmd_absorb(args: argparse.Namespace) -> int:
    """LORE-008: absorb half of the gate — print the proposal payload JSON.

    Propose-not-write: stdout only; the registry is never mutated.
    """
    print(json.dumps(absorb_proposal(args.class_id, args.lesson), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lore",
        description="Match symptoms and compile runbooks from fleet incident history.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    match_p = sub.add_parser("match", help="classify a symptom text")
    match_p.add_argument("text", help="symptoms or log line(s)")
    match_p.add_argument(
        "--explain",
        action="store_true",
        default=False,
        help=(
            "echo near-misses: classes that almost matched (raw keyword "
            "fraction below threshold) — evidence only, never a label"
        ),
    )
    match_p.set_defaults(func=_cmd_match)

    consult_p = sub.add_parser(
        "consult",
        help=(
            "tick-start consult (LORE-007): attach matching runbook refs to "
            "work context; fail-open (no match = exit 0)"
        ),
    )
    consult_p.add_argument("title", help="task title (symptom text)")
    consult_p.add_argument(
        "--detail",
        default="",
        help="optional task detail; classified together with the title",
    )
    consult_p.add_argument(
        "--json", action="store_true", help="print the ConsultResult as JSON"
    )
    consult_p.set_defaults(func=_cmd_consult)

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

    validate_p = sub.add_parser(
        "validate",
        help=(
            "read-only command lint (LORE-006). DEFAULT = plan/dry-run: "
            "lists what WOULD run, executes NOTHING; pass --execute to run "
            "the gate-approved read-only commands"
        ),
    )
    validate_p.add_argument(
        "--class",
        dest="class_id",
        default=None,
        help="lint one class; omit to lint every registry class",
    )
    validate_p.add_argument(
        "--format",
        choices=("json", "md"),
        default="json",
        help="output format (default: json)",
    )
    validate_p.add_argument(
        "--execute",
        action="store_true",
        help=(
            "OPT-IN: actually run the gate-approved read-only commands "
            "(default is plan-only, nothing is executed)"
        ),
    )
    validate_p.set_defaults(func=_cmd_validate)

    # ---- LORE-008: absorb-gate on close. Anchored at the END of build_parser
    # (after validate's set_defaults, before `return parser`) so sibling
    # subcommand edits merge trivially.
    gate_p = sub.add_parser(
        "gate",
        help=(
            "closure absorb-gate (LORE-008): machine-check a lesson decision "
            "(absorb or no-new-lesson ack); exit 0 = allowed, 1 = denied"
        ),
    )
    gate_p.add_argument(
        "--decision",
        required=True,
        choices=(DECISION_ABSORB, DECISION_NO_NEW_LESSON),
        help="'absorb' (a runbook lesson) or 'no-new-lesson' (explicit ack)",
    )
    gate_p.add_argument(
        "--class",
        dest="class_id",
        default=None,
        help="existing registry class for an 'absorb' decision",
    )
    gate_p.add_argument("--lesson", default="", help="proposed lesson text (absorb)")
    gate_p.add_argument(
        "--reason", default="", help="why no new lesson (no-new-lesson)"
    )
    gate_p.add_argument("--ref", default=None, help="board row / incident id")
    gate_p.add_argument(
        "--decided-at",
        dest="decided_at",
        default=None,
        help="optional ISO-8601 timestamp (never invented when omitted)",
    )
    gate_p.set_defaults(func=_cmd_gate)

    absorb_p = sub.add_parser(
        "absorb",
        help=(
            "build the runbook-update PROPOSAL for an absorb decision "
            "(stdout only — propose-not-write, nothing is written)"
        ),
    )
    absorb_p.add_argument(
        "--class",
        dest="class_id",
        required=True,
        help="existing registry class to propose an update for",
    )
    absorb_p.add_argument("--lesson", required=True, help="the lesson text")
    absorb_p.set_defaults(func=_cmd_absorb)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
