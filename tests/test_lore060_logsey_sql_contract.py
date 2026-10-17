"""LORE-060: gateway-drain-window's logsey checks ride logsey's REAL contract.

Dogfood run 10 proved the seeded check commands exit 2 on the actual logsey
CLI: `logsey query --pattern X --since <wd>` is not a shipped interface —
logsey takes ONE quoted SQL string (`logsey query "<sql>"`). These tests pin
the repaired shape so a future edit that re-introduces the fiction fails the
suite instead of the operator mid-incident.

Contract (verified live on HEAD 9b97fa2, corpus at
~/.local/share/logsey): a healthy invocation is ONE positional SQL argument
over the ``logs`` table (message/ts columns); healthy stdout ends with
``0 rows`` on a quiet corpus, never an ``error:`` line.
"""

from __future__ import annotations

import re

from lore.compiler import compile_all, compile_class
from lore.validate import is_read_only_command

# The two rewritten checks, derived — never duplicated by hand beyond the
# intent markers the tests assert on.
_BY_ORDER: dict[str, dict[int, str]] = {
    rb.class_id: {c.order: c.command for c in rb.checks} for rb in compile_all()
}
DRAIN = _BY_ORDER["gateway-drain-window"]

# LORE-060's defect shape: logsey flags that do not exist on the real CLI.
_FORBIDDEN_FLAGS = ("--pattern", "--since")


def _logsey_checks() -> list[tuple[int, str]]:
    return [
        (order, cmd)
        for order, cmd in sorted(DRAIN.items())
        if cmd.startswith("logsey ")
    ]


def test_drain_logsey_checks_are_exactly_orders_1_and_7():
    assert [o for o, _ in _logsey_checks()] == [1, 7], _logsey_checks()


def test_drain_logsey_checks_carry_no_fictional_flags():
    """The runbook text must not re-introduce `--pattern` / `--since`."""
    for order, cmd in _logsey_checks():
        for flag in _FORBIDDEN_FLAGS:
            assert flag not in cmd, (
                f"check {order} uses the unshipped flag {flag}: {cmd!r}"
            )


def test_drain_logsey_checks_are_single_quoted_sql_argument():
    """One positional SQL string in double quotes — logsey's real contract."""
    for order, cmd in _logsey_checks():
        argv = cmd.split()
        assert argv[0] == "logsey" and argv[1] == "query", cmd
        rest = cmd[len("logsey query ") :]
        assert rest.startswith('"') and rest.endswith('"'), (
            f"check {order} must pass ONE double-quoted SQL string: {cmd!r}"
        )
        # No second (unquoted) argument after the SQL string closes.
        assert not rest[1:-1].count('"') % 2, f"unbalanced quotes: {cmd!r}"
        assert re.fullmatch(r'"[^"]+"', rest), (
            f"check {order} must be a single quoted argument: {cmd!r}"
        )


def test_drain_logsey_sql_targets_the_real_schema():
    """SQL selects over logsey's actual `logs` table (message/ts columns)."""
    for order, cmd in _logsey_checks():
        sql = cmd[len("logsey query ") :].strip('"')
        assert re.match(r"(?i)\s*SELECT\b", sql), f"check {order}: {sql!r}"
        assert re.search(r"\bFROM\s+logs\b", sql, re.IGNORECASE), (
            f"check {order} must query the logs table: {sql!r}"
        )
        assert re.search(r"\bmessage\b", sql, re.IGNORECASE), (
            f"check {order} must match on message: {sql!r}"
        )


def test_drain_logsey_sql_preserves_the_intent():
    """Order 1 hunts drain-503s in a 30-min window; order 7 SIGKILL/503 in 60."""
    sql1 = DRAIN[1][len("logsey query ") :].strip('"')
    sql7 = DRAIN[7][len("logsey query ") :].strip('"')
    assert "%drain 503%" in sql1, sql1
    assert "INTERVAL 30 MINUTE" in sql1, sql1
    assert "%SIGKILL%" in sql7 and "%503%" in sql7, sql7
    assert "INTERVAL 60 MINUTE" in sql7, sql7
    # Order 7 broadens the original single alternation into OR'd LIKEs — the
    # SQL string cannot carry the bare `|` form.
    assert "'SIGKILL|503'" not in sql7, sql7


def test_drain_logsey_checks_are_gate_approved_read_only():
    for order, cmd in _logsey_checks():
        assert is_read_only_command(cmd), f"check {order} refused by the gate: {cmd}"


def test_other_classes_keep_no_fictional_logsey_flags():
    """The repair is repo-wide: no compiled logsey command anywhere ships
    the fiction. (A `grep ... --since-marker` placeholder flag in another
    class is a grep argument, not a logsey claim — out of scope.)"""
    for class_id, by_order in _BY_ORDER.items():
        for order, cmd in by_order.items():
            if not cmd.startswith("logsey "):
                continue
            for flag in _FORBIDDEN_FLAGS:
                assert flag not in cmd, (
                    f"{class_id} check {order} still carries {flag}: {cmd!r}"
                )


def test_compiled_runbook_renders_the_single_arg_form_markdown():
    """The markdown render surfaces the same single-arg SQL shape."""
    text = compile_class("gateway-drain-window").to_markdown()
    assert "--pattern" not in text and "--since" not in text, (
        "rendered runbook still surfaces the fictional flags"
    )
    for _, cmd in _logsey_checks():
        assert cmd in text, f"rendered runbook lost check command: {cmd!r}"
