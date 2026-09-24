"""Minimal lore CLI.

Subcommands (LORE-010 completes the PRD interface block):

    python -m lore match "<symptoms>" [--explain]
    python -m lore compile [--class <class_id>] [--format json|md]
    python -m lore show <class_id> [--evidence] [--format json|md]
    python -m lore audit [--format table|json|md]
    python -m lore absorb --class <id> --lesson <text>   # one proposal
    python -m lore absorb --window <dur> [--trail-file P] [--ns N] [--board B]
    python -m lore consult <title> [--detail ...] [--json]
    python -m lore validate [--class <id>] [--format json|md] [--execute]
    python -m lore gate --decision ... [--class ...] ...

``compile``/``show``/``audit``/``absorb`` print PROPOSALS to stdout. They
never write a runbook to disk anywhere (propose-not-write): the only side
effect is stdout. Unknown --class exits non-zero via the registry (closed,
curated). The ``--window`` sweep classifies a prior evidence trail into
per-class proposals; an empty trail is an explicit empty result, exit 0.
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
    absorb_sweep,
    gate_close,
    parse_duration,
)
from lore.classifier import classify_all, near_misses
from lore.compiler import NO_VALID_EVIDENCE, compile_all, compile_class
from lore.consult import ConsultResult, consult, consult_failure
from lore.evidence import (
    EvidenceBlock,
    LogseyExportParseError,
    attach_evidence,
    parse_logsey_export,
)
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
    that ref instead of crashing the caller's tick.

    LORE-009: ``--failure <text>`` switches to the guard-failure mode —
    classify a guard-failure output (e.g. a gitreins guard log tail) and, on
    a class match, print the matching runbook's ORDERED checks under the
    "this class has a runbook" heading so the failure output can carry them.
    Still fail-open: no match = exit 0, never an error.
    """
    if getattr(args, "failure", None):
        result = consult_failure(args.failure)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
            return 0
        if not result.matched:
            print("no matching runbook")
            return 0
        for s in result.suggestions:
            lv = s["last_validated"] if s["last_validated"] else "never"
            print(
                f"this class has a runbook: {s['class_id']} ({s['name']}) "
                f"status={s['status']} last_validated={lv} checks={s['check_count']}"
            )
            for c in s["checks"]:
                print(f"  check {c['order']}: {c['command']}")
        return 0
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
        source=args.source,
    )
    verdict = gate_close(d)
    print(verdict.summary())
    for err in verdict.errors:
        print(f"error: {err}")
    return 0 if verdict.allowed else 1


def _cmd_absorb(args: argparse.Namespace) -> int:
    """LORE-008: absorb half of the gate — print the proposal payload JSON.

    Propose-not-write: stdout only; the registry is never mutated.

    LORE-010 sweep: when ``--window`` is given, stdin (or --trail-file) is
    parsed as a PRIOR EVIDENCE TRAIL; every parseable block is classified and
    grouped into per-class absorb PROPOSALS. Still propose-not-write: stdout
    only, nothing is ever written. An empty trail is an explicit empty result
    (exit 0), not an error.
    """
    if not args.window:
        if not args.class_id or not args.lesson:
            print(
                "error: absorb requires --class and --lesson (or --window for the sweep)",
                file=sys.stderr,
            )
            return 2
        print(
            json.dumps(
                absorb_proposal(args.class_id, args.lesson, source=args.source),
                indent=2,
            )
        )
        return 0

    try:
        parse_duration(args.window)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.trail_file:
        try:
            with open(args.trail_file, encoding="utf-8") as fh:
                trail_text = fh.read()
        except OSError as exc:
            print(f"error: cannot read trail file: {exc}", file=sys.stderr)
            return 2
    else:
        trail_text = sys.stdin.read()

    try:
        blocks: list[EvidenceBlock] = parse_logsey_export(trail_text)
    except LogseyExportParseError as exc:
        print(
            f"error: trail claims to be an export but does not parse: {exc}",
            file=sys.stderr,
        )
        return 2

    proposals = absorb_sweep(blocks, window=args.window, ns=args.ns, board=args.board)
    if not proposals:
        print(
            "no classifiable evidence blocks in the trail "
            "(no blocks found — nothing proposed, nothing written)"
        )
        return 0

    print(json.dumps(proposals, indent=2))
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    """LORE-010: print the compiled runbook for ONE class (human-md default).

    --evidence adds the class's evidence/provenance detail: the registry
    entry's provenance line plus the evidence blocks ``attach_evidence`` can
    attach for the class (the compiled seed trail rendered per-check and as
    the runbook trail). Output is stdout only — propose-not-write holds.
    """
    try:
        rb = compile_class(args.class_id)
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2

    if args.evidence:
        rb = attach_evidence(
            rb,
            [
                EvidenceBlock(kind=e["kind"], detail=e["detail"])
                for e in rb.evidence_trail
            ],
        )

    if args.format == "json":
        print(json.dumps(rb.to_dict(), indent=2))
    else:
        print(rb.to_markdown().rstrip("\n"))
        if args.evidence:
            print()
            print("## Evidence / provenance detail")
            print()
            print(f"- Provenance: {rb.provenance or 'no data'}")
            trail = [
                e
                for e in rb.evidence_trail
                if e.get("detail") and e.get("kind") not in ("lint",)
            ]
            if trail:
                for e in trail:
                    print(f"- {e['kind']}: {e['detail']}")
            else:
                print("- Evidence trail: no data")
    return 0


def _audit_rows() -> list[dict]:
    """Coverage + freshness matrix rows, one per registry class (PRD US-3).

    HONESTY LAW: freshness comes from the runbook's own ``last_validated``
    state — which is ``no data`` for every class until a ``lore validate
    --execute``-backed attestation populates it. Never a fabricated date,
    never an invented status.
    """
    rows: list[dict] = []
    for rb in compile_all():
        real_commands = [
            c
            for c in rb.checks
            if c.command.strip() and c.command.strip() != NO_VALID_EVIDENCE
        ]
        rows.append(
            {
                "class_id": rb.class_id,
                "name": rb.name,
                "runbook_compiled": True,
                "check_count": len(rb.checks),
                "command_count": len(real_commands),
                "last_validated": rb.last_validated or NO_VALID_EVIDENCE,
                "status": rb.status,
            }
        )
    return rows


def _cmd_audit(args: argparse.Namespace) -> int:
    """LORE-010: the coverage + freshness matrix (PRD US-3).

    One row per registry class: is a runbook compiled, how many checks, how
    many of those carry a REAL command (vs the honest-absence ``no data``
    sentinel), and the freshness state. Read-only; stdout only.
    """
    rows = _audit_rows()
    zero_command = sum(1 for r in rows if r["command_count"] == 0)
    summary_note = (
        "last_validated is populated only by `lore validate --execute` runs; "
        "a compiled runbook with no executed lint honestly reports 'no data'"
    )

    if args.format == "json":
        print(
            json.dumps(
                {
                    "classes": rows,
                    "summary": {
                        "total_classes": len(rows),
                        "classes_with_zero_real_commands": zero_command,
                        "note": summary_note,
                    },
                },
                indent=2,
            )
        )
        return 0

    if args.format == "md":
        lines = [
            "| class_id | name | runbook-compiled | checks | real commands | last_validated | status |",
            "|---|---|---|---|---|---|---|",
        ]
        lines.extend(
            f"| {r['class_id']} | {r['name']} | {r['runbook_compiled']} | "
            f"{r['check_count']} | {r['command_count']} | "
            f"{r['last_validated']} | {r['status']} |"
            for r in rows
        )
        print("\n".join(lines))
        print()
        print(
            f"**Summary:** {len(rows)} classes; {zero_command} with zero real "
            f"commands; {summary_note}"
        )
        return 0

    # table (default)
    headers = (
        "class_id",
        "name",
        "compiled",
        "checks",
        "real-cmds",
        "last_validated",
        "status",
    )
    table_rows = [
        (
            r["class_id"],
            r["name"],
            str(r["runbook_compiled"]),
            str(r["check_count"]),
            str(r["command_count"]),
            r["last_validated"],
            r["status"],
        )
        for r in rows
    ]
    widths = [
        max(len(h), *(len(row[i]) for row in table_rows)) if table_rows else len(h)
        for i, h in enumerate(headers)
    ]

    def _fmt(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip()

    print(_fmt(headers))
    print("  ".join("-" * w for w in widths))
    for row in table_rows:
        print(_fmt(row))
    print()
    print(
        f"summary: {len(rows)} classes; {zero_command} with zero real commands; "
        f"{summary_note}"
    )
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
    consult_p.add_argument(
        "title",
        nargs="?",
        default=None,
        help="task title (symptom text); required unless --failure is given",
    )
    consult_p.add_argument(
        "--failure",
        default=None,
        help=(
            "LORE-009: guard-failure mode — treat the value as guard-failure "
            "OUTPUT text (e.g. a gitreins guard log tail) instead of a task "
            "title; on a class match prints the matching runbook's ordered "
            "checks ('this class has a runbook'). Fail-open: no match = exit 0"
        ),
    )
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
    gate_p.add_argument(
        "--source",
        default=None,
        help=(
            "LORE-009: provenance marker for this closure — e.g. "
            "'qa-dagger' or 'dogfood-dagger' (QA/dogfood findings close "
            "through the same absorb-gate as incidents). Omitted = default "
            "incident-closure behavior (no source printed)"
        ),
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
        default=None,
        help="existing registry class to propose an update for (required without --window)",
    )
    absorb_p.add_argument(
        "--lesson",
        default=None,
        help="the lesson text (required without --window)",
    )
    absorb_p.add_argument(
        "--window",
        default=None,
        help=(
            "LORE-010 sweep: sweep a PRIOR EVIDENCE TRAIL (stdin, or "
            "--trail-file) instead of taking --class/--lesson; parse a "
            "duration like 2h/45m/90 and group classifiable blocks into "
            "per-class absorb PROPOSALS (stdout only — nothing is written)"
        ),
    )
    absorb_p.add_argument(
        "--trail-file",
        dest="trail_file",
        default=None,
        help="read the evidence trail from PATH instead of stdin (with --window)",
    )
    absorb_p.add_argument(
        "--ns",
        default=None,
        help=(
            "optional namespace label recorded in the proposal provenance "
            "(no live lookups in this PR)"
        ),
    )
    absorb_p.add_argument(
        "--board",
        default=None,
        help=(
            "optional board path label recorded in the proposal provenance "
            "(no live lookups in this PR)"
        ),
    )
    absorb_p.add_argument(
        "--source",
        default=None,
        help=(
            "LORE-009: provenance marker recorded into the proposal payload "
            "(e.g. 'qa-dagger' or 'dogfood-dagger'). Omitted = the payload "
            "keeps its original shape (no 'source' key)"
        ),
    )
    absorb_p.set_defaults(func=_cmd_absorb)

    show_p = sub.add_parser(
        "show",
        help=(
            "print the compiled runbook for ONE class (LORE-010); "
            "human-markdown default, --format json optional"
        ),
    )
    show_p.add_argument("class_id", help="existing registry class to show")
    show_p.add_argument(
        "--evidence",
        action="store_true",
        help="add the class's evidence/provenance detail (registry provenance + evidence blocks)",
    )
    show_p.add_argument(
        "--format",
        choices=("json", "md"),
        default="md",
        help="output format (default: md)",
    )
    show_p.set_defaults(func=_cmd_show)

    audit_p = sub.add_parser(
        "audit",
        help=(
            "coverage + freshness matrix over every registry class (LORE-010, "
            "PRD US-3); honest 'no data' freshness — never fabricated dates"
        ),
    )
    audit_p.add_argument(
        "--format",
        choices=("table", "json", "md"),
        default="table",
        help="output format (default: table)",
    )
    audit_p.set_defaults(func=_cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
