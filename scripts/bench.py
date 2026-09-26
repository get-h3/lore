#!/usr/bin/env python3
"""bench.py — focused offline benchmarks for lore's hot paths (LORE-042).

Measures, with the stdlib ``timeit`` module only (no new runtime/dev
dependency), the representative core paths a responder's run touches:

  classify (signature hit / keyword hit / full-miss worst case),
  classify_all (ranked candidates over the whole registry),
  compile_class / compile_all (runbook compiler), and
  is_read_only_command (the validator's default-deny gate).

Contract:

- Inputs are DETERMINISTIC module constants (mirroring the classifier test
  fixtures) — every run measures the same work, so numbers are comparable
  across runs on the same machine.
- The harness is ``timeit.Timer(...).repeat(repeats, number)``; the reported
  per-call time is the MINIMUM of ``repeats`` batches (best-case stable
  estimate, standard timeit practice — never an average that hides outliers).
- Numbers are MEASURED wall-clock, not thresholds: this script asserts
  nothing about how fast the code is and never fails on a slow number.
  What it DOES fail on is invalid setup (exit 2): every operation is first
  executed and its behaviour validated against the package's contract
  (expected class ids, statuses, gate verdicts). A benchmark run over code
  whose behaviour changed is worse than no benchmark, so it refuses to run.
- Fully offline: imports ``lore`` only, no network, no filesystem writes.

Usage (from a clean checkout with ``uv sync --extra dev`` done)::

    uv run python scripts/bench.py               # full measured run
    uv run python scripts/bench.py --check-only  # validate setup, exit fast
    uv run python scripts/bench.py --number 500 --repeats 7

Exit codes: 0 = measured (or setup valid with --check-only), 2 = invalid
setup, 1 = usage error (argparse).
"""

from __future__ import annotations

import argparse
import sys
import timeit
from collections.abc import Callable

from lore import classifier, validate
from lore.compiler import compile_all, compile_class

# ------------------------------------------------------- deterministic inputs
# Frozen symptom texts (NOT randomly generated): the signature fixture and
# keyword fixture mirror tests/test_classifier.py so benchmark work is stable
# across runs and machines.

SIGNATURE_HIT_TEXT = (
    "hermes gateway restart: batch config change applied, expect up to 30 min "
    "of drain 503s while in-flight requests finish"
)
KEYWORD_HIT_TEXT = (
    "gateway maintenance: drain window planned, 503s expected, "
    "reload afterwards, restart if needed"
)
FULL_MISS_TEXT = "purple elephant unicycle parade"
GATE_COMMAND = "git -C <main-tree> rev-parse HEAD && git -C <worktree> rev-parse HEAD"

DEFAULT_NUMBER = 200
DEFAULT_REPEATS = 5


class SetupError(RuntimeError):
    """Benchmark setup is invalid (behaviour contract broken) — exit 2."""


class Operation:
    """One named benchmark operation plus its behaviour check."""

    def __init__(
        self, name: str, what: str, fn: Callable[[], object], check: Callable[[], None]
    ) -> None:
        self.name = name
        self.what = what
        self.fn = fn
        self.check = check


def _validate_setup() -> None:
    """Assert every measured path still behaves per its contract.

    Raises SetupError on the FIRST mismatch; a benchmark whose subject changed
    behaviour must not print measured numbers (they would be numbers for code
    that no longer does what the name says).
    """
    checks: list[tuple[str, Callable[[], None]]] = [
        (
            "classify signature hit -> gateway-drain-window (0.9)",
            lambda: _require(
                classifier.classify(SIGNATURE_HIT_TEXT).class_id
                == "gateway-drain-window"
                and classifier.classify(SIGNATURE_HIT_TEXT).confidence == 0.9,
                "classify(SIGNATURE_HIT_TEXT) must label gateway-drain-window at 0.9",
            ),
        ),
        (
            "classify keyword hit -> gateway-drain-window (keyword path)",
            lambda: _require(
                classifier.classify(KEYWORD_HIT_TEXT).class_id == "gateway-drain-window"
                and classifier.classify(KEYWORD_HIT_TEXT).matched_signature is None,
                "classify(KEYWORD_HIT_TEXT) must be a keyword match (no signature)",
            ),
        ),
        (
            "classify full miss -> unclassified (0.0)",
            lambda: _require(
                classifier.classify(FULL_MISS_TEXT).is_unclassified,
                "classify(FULL_MISS_TEXT) must return unclassified",
            ),
        ),
        (
            "compile_class(gateway-drain-window) -> proposal runbook",
            lambda: _require(
                compile_class("gateway-drain-window").status == "proposal"
                and compile_class("gateway-drain-window").class_id
                == "gateway-drain-window",
                "compile_class('gateway-drain-window') must compile a proposal",
            ),
        ),
        (
            "is_read_only_command(gate command) -> True",
            lambda: _require(
                validate.is_read_only_command(GATE_COMMAND) is True,
                "is_read_only_command(GATE_COMMAND) must be True",
            ),
        ),
    ]
    for label, check in checks:
        try:
            check()
        except SetupError:
            raise
        except Exception as exc:
            raise SetupError(f"{label}: unexpected error: {exc}") from exc


def _require(condition: object, message: str) -> None:
    if not condition:
        raise SetupError(f"invalid benchmark setup: {message}")


def build_operations() -> list[Operation]:
    """The named, offline benchmark operations (validated before timing)."""
    return [
        Operation(
            name="classify_signature_hit",
            what="classify() one text matched by a registry signature regex",
            fn=lambda: classifier.classify(SIGNATURE_HIT_TEXT),
            check=lambda: _require(
                classifier.classify(SIGNATURE_HIT_TEXT).class_id
                == "gateway-drain-window",
                "signature-hit fixture must classify gateway-drain-window",
            ),
        ),
        Operation(
            name="classify_keyword_hit",
            what="classify() one text matched only by keywords (threshold path)",
            fn=lambda: classifier.classify(KEYWORD_HIT_TEXT),
            check=lambda: _require(
                classifier.classify(KEYWORD_HIT_TEXT).class_id == "gateway-drain-window"
                and classifier.classify(KEYWORD_HIT_TEXT).matched_signature is None,
                "keyword-hit fixture must classify gateway-drain-window by keyword",
            ),
        ),
        Operation(
            name="classify_full_miss_scan",
            what="classify() worst case: no match, scans the entire registry",
            fn=lambda: classifier.classify(FULL_MISS_TEXT),
            check=lambda: _require(
                classifier.classify(FULL_MISS_TEXT).is_unclassified,
                "miss fixture must return unclassified",
            ),
        ),
        Operation(
            name="classify_all_rank",
            what="classify_all(): score + rank candidates across all classes",
            fn=lambda: classifier.classify_all(KEYWORD_HIT_TEXT),
            check=lambda: _require(
                len(classifier.classify_all(KEYWORD_HIT_TEXT)) >= 1,
                "classify_all must return candidates",
            ),
        ),
        Operation(
            name="compile_class_gateway",
            what="compile_class() for the doctrine class (checks + ladder)",
            fn=lambda: compile_class("gateway-drain-window"),
            check=lambda: _require(
                compile_class("gateway-drain-window").status == "proposal",
                "compile_class must produce a proposal runbook",
            ),
        ),
        Operation(
            name="compile_all_registry",
            what="compile_all(): one runbook per registry class",
            fn=lambda: compile_all(),
            check=lambda: _require(
                len(compile_all()) >= 1, "compile_all must compile the registry"
            ),
        ),
        Operation(
            name="validate_read_only_gate",
            what="is_read_only_command(): default-deny gate on a chained command",
            fn=lambda: validate.is_read_only_command(GATE_COMMAND),
            check=lambda: _require(
                validate.is_read_only_command(GATE_COMMAND) is True,
                "gate fixture must be recognized as read-only",
            ),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.py",
        description="Focused offline benchmarks for lore's core paths "
        "(stdlib timeit; measured numbers, no thresholds).",
    )
    parser.add_argument(
        "--number",
        type=int,
        default=DEFAULT_NUMBER,
        help=f"calls per timing batch (default {DEFAULT_NUMBER})",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=DEFAULT_REPEATS,
        help=f"timing batches; the MIN is reported (default {DEFAULT_REPEATS})",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the setup only (no timing loops), then exit",
    )
    args = parser.parse_args(argv)
    if args.number < 1 or args.repeats < 1:
        print("ERROR: --number and --repeats must be >= 1", file=sys.stderr)
        return 2

    try:
        ops = build_operations()
        # Validate every operation's behaviour contract BEFORE timing any of
        # them (the Operation.check lambdas re-assert per op).
        _validate_setup()
        for op in ops:
            op.check()
    except SetupError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.check_only:
        print(f"OK: benchmark setup valid ({len(ops)} operations); not timed")
        for op in ops:
            print(f"  {op.name}: {op.what}")
        return 0

    # Warm each operation once so first-call lazy compilation (the classifier's
    # _compiled() registry build) is not charged to the first timing batch.
    for op in ops:
        op.fn()

    print(
        "lore benchmarks (stdlib timeit; deterministic inputs; "
        "per-call = min of <repeats> batches x <number> calls; "
        "measured wall-clock, not thresholds)"
    )
    header = (
        f"{'operation':<28} {'us/op':>10} {'ops/sec':>12} {'number':>8} {'repeats':>8}"
    )
    print(header)
    for op in ops:
        timer = timeit.Timer(op.fn)
        best = min(timer.repeat(args.repeats, args.number)) / args.number
        print(
            f"{op.name:<28} {best * 1e6:>10.2f} {1 / best:>12.0f} "
            f"{args.number:>8} {args.repeats:>8}"
        )
        print(f"    # {op.what}")
    print(f"PASS: {len(ops)} operations measured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
