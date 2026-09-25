"""lore.validate — the read-only command lint (LORE-006, the anti-rot loop).

PRD §"The re-validation loop": every command in every runbook re-runs in
read-only/verify mode on a schedule; any drift flips the runbook to
``stale``. This module is the mechanism. Scheduling (relay B6) will wrap
``lint_all`` in a weekly fleet timer; v1 ships the unit/timer-shaped entry
point only — this module installs NO cron job and NO systemd timer.

SAFETY CORE — the default-deny command gate
===========================================

``is_read_only_command`` is an ALLOW-LIST predicate, not a denylist: a
command that cannot be POSITIVELY recognized as read-only is REFUSED
(default-deny). The detection rule, stated so it can be audited:

1. Not-a-command: the compiler's honest-absence sentinel ``"no data"`` (and
   any empty/whitespace command) is NOT a command. The lint reports it as
   the outcome ``absent`` — never executed, never a pass or a failure.
2. Shell-shape gate (quote-aware): the command must not contain newlines,
   backticks, command substitution ``$()``, backgrounding ``&``, or input
   redirection ``< file``. Output redirection is allowed ONLY to
   ``/dev/null`` (``2>/dev/null`` and friends — never to a real path).
   Chaining (``&&``, ``;``) and piping (``|``) are allowed, but EVERY
   resulting segment must independently pass the program allow-list below.
   Process substitution ``<( ... )`` recurses into the same gate.
3. Program allow-list (each first word must be one of):
   ``grep ls cat wc df tail head stat ps jq sort diff sed logsey`` (plain
   readers), plus the curated shapes:
   - ``git`` only read-only subcommands (status/log/diff/rev-parse/show/
     ls-files/ls-remote/blame/shortlog/describe, ``worktree list``,
     ``branch`` with no destructive flag, ``config`` read flags,
     ``remote -v``). commit/push/reset/clean/checkout are refused.
   - ``curl`` only GET-shaped probes: no -d/--data*/-F/-T/--upload-file;
     ``-o``/``--output`` only to ``/dev/null``; ``-X``/``--request`` only
     ``GET``; unknown long flags refused.
   - ``systemctl`` only status/is-active/is-enabled/show/cat/list-units/
     list-unit-files. restart/stop/start refused.
   - ``docker`` only ``inspect``/``ps`` (read-only inspection).
   - ``sqlite3`` only when the SQL argument starts with SELECT/PRAGMA/
     EXPLAIN (read-only query, never UPDATE/DELETE/DDL).
   - ``python3``/``python`` only ``-c`` one-liners whose body matches the
     stdin-parse shape (no ``os.``, ``open(``, ``subprocess``, ``shutil``,
     ``write``, ``exec(``, ``eval(``, file removal ...).
   - a ``<placeholder>`` binary (runbook template slot, e.g.
     ``<scheduler-cli>``) is recognized ONLY when the command carries a
     positive read-only marker flag (``--verify``/``--dry-run``/``--check``).
   Anything else — ``rm``, ``mv``, ``kill``, package installs, ``sed -i``,
   unknown binaries — is REFUSED and reported as ``refused``, never
   silently skipped.

HONESTY LABEL (README "Design laws this repo inherits" — the
verify-harness honesty law applied to ops):

    lint-verified: commands parse and answer on the live system; this does
    NOT prove recovery succeeds.

A green lint is NOT operator attestation: ``apply_lint`` never sets
``last_validated`` and never moves status to ``validated`` — only an
operator attestation may do that (PRD propose-not-write; human-in-the-loop
on write).

OUTCOME VOCABULARY (small and closed)::

    ok       ran, exit 0 — command parsed and answered
    error    ran, non-zero exit — DRIFT
    refused  the gate refused it (not positively read-only) — DRIFT
    absent   no sourced command (the ``no data`` sentinel) — honest absence
    template unfilled ``<placeholder>`` slots — reported, NEVER executed;
             not drift (fill the runbook, then re-lint)
    timeout  ran past the bounded timeout — DRIFT
    unknown  the runner returned something unclassifiable — DRIFT

``error``/``timeout``/``refused``/``unknown`` are DRIFT outcomes; any drift
flips the runbook to ``stale`` (see ``apply_lint``). ``template`` is NOT
drift: a runbook whose lint shows only ``ok``/``absent``/``template`` is
NOT stale — its real checks were linted honestly and its unfilled slots
are reported visibly rather than poisoning the whole class (a bare
``<token>`` parses as shell input redirection and would shell-error every
such check as a phantom ``error``).

--execute CONTRACT — it expects a FILLED runbook
------------------------------------------------

``--execute`` re-runs each check as a live read-only command. A runbook
still carrying ``<placeholder>`` template slots (e.g. ``git -C <main-tree>
status``) is INCOMPLETE INPUT, not a broken system: before executing
anything the lint detects unfilled ``<token>`` slots (quote-aware — a
``<...>`` inside quotes is literal text such as a grep pattern, not a
slot) and reports those checks as ``template`` with a fill-me detail
line on ``stderr``, WITHOUT running them. Template checks stay visible in
every render (never hidden — an operator must know what to fill) but are
neither drift nor passes. The default-deny gate is untouched: a command
that is BOTH unfilled and not positively read-only still reports
``refused`` (the safety verdict wins over the template note).

PLAN-ONLY CHECKS (LORE-026 — compiler/validator agreement)
----------------------------------------------------------

The class registry can seed a check the default-deny gate can never run:
a genuinely write-shaped diagnostic (``git worktree add`` — the
guard-degradation control-worktree proof). Such checks are marked
``read_only=False`` (rendered MUTATING) at the source, and the lint
honors that mark: a ``read_only=False`` check reports ``template`` —
never executed, never drift — the same honest incompleteness as an
unfilled slot, because the refusal is the check's PLANNED state, not
rot. This keeps the compiler and the validator in agreement (everything
emitted is either executable or plan-only) WITHOUT loosening the gate:
``is_read_only_command`` still refuses every write-shaped command
(worktree add, commit, push...), and a check that claims
``read_only=True`` while carrying a write shape still reports ``refused``
as drift — only the registry's explicit plan-only mark gets the
never-executed/not-drift treatment.
"""

from __future__ import annotations

import dataclasses
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from lore.compiler import NO_VALID_EVIDENCE, compile_all
from lore.runbook import STATUS_STALE, Runbook

__all__ = [
    "COMMAND_TIMEOUT_SECONDS",
    "DRIFT_OUTCOMES",
    "HONESTY_LABEL",
    "OUTCOME_TEMPLATE",
    "OUTCOME_VOCABULARY",
    "CheckResult",
    "CommandResult",
    "LintReport",
    "apply_lint",
    "is_read_only_command",
    "lint_all",
    "lint_runbook",
]

# The machine-checkable honesty label. Carried on every report. A green
# lint means commands PARSE AND ANSWER — nothing more. Never render a green
# lint as "the recovery works".
HONESTY_LABEL = (
    "lint-verified: commands parse and answer on the live system; "
    "this does NOT prove recovery succeeds"
)

# The closed outcome vocabulary (documented in the module docstring).
OUTCOME_VOCABULARY = (
    "ok",
    "error",
    "refused",
    "absent",
    "template",
    "timeout",
    "unknown",
)

# Outcomes that constitute drift and flip a runbook to ``stale``.
DRIFT_OUTCOMES = ("error", "timeout", "refused", "unknown")

# Outcome for "no sourced command" (the honest-absence sentinel).
OUTCOME_ABSENT = "absent"

# Outcome for a check still carrying unfilled ``<placeholder>`` slots:
# reported visibly, never executed, never drift (see module docstring).
OUTCOME_TEMPLATE = "template"

# Bounded execution for the default runner: no interactive terminal, no
# unbounded waits.
COMMAND_TIMEOUT_SECONDS = 30

_CLIP = 2000  # keep captured stdout/stderr tails small in the report

_PLACEHOLDER_RE = re.compile(r"<[A-Za-z0-9_.\-]+>")


# ---------------------------------------------------------------- runner
@dataclass(frozen=True)
class CommandResult:
    """What a runner records for one executed command."""

    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


def _clip(text: object) -> str:
    return str(text or "")[:_CLIP]


def _default_runner(command: str) -> CommandResult:
    """Default runner: bounded, non-interactive, captures output.

    NEVER inherits an interactive terminal (stdin=DEVNULL) and never runs
    without a timeout. Used only when the caller passes no runner.
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            returncode=None,
            stdout=_clip(exc.stdout),
            stderr=_clip(exc.stderr),
            timed_out=True,
        )
    except OSError as exc:
        return CommandResult(
            returncode=None,
            stdout="",
            stderr=f"runner error: {exc}",
            timed_out=False,
        )
    return CommandResult(
        returncode=proc.returncode,
        stdout=_clip(proc.stdout),
        stderr=_clip(proc.stderr),
        timed_out=False,
    )


# ---------------------------------------------------------------- gate
def _unquoted(cmd: str) -> str:
    """Blank out quoted spans so metachar scanning sees only shell syntax."""
    out: list[str] = []
    quote: str | None = None
    for ch in cmd:
        if quote is None and ch in "'\"":
            quote = ch
            out.append(" ")
        elif quote is not None:
            if ch == quote:
                quote = None
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _extract_process_subs(cmd: str) -> tuple[str, list[str]] | None:
    """Replace top-level ``<( ... )`` with a token; return (text, inners).

    Returns None on unbalanced parentheses. Inner commands are raw (their
    own quotes intact) and get re-checked by the full gate.
    """
    out: list[str] = []
    subs: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if quote is None and ch in "'\"":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if quote is not None:
            if ch == quote:
                quote = None
            out.append(ch)
            i += 1
            continue
        if ch == "<" and cmd.startswith("<(", i):
            depth = 1
            j = i + 2
            inner: list[str] = []
            while j < len(cmd) and depth:
                c2 = cmd[j]
                if c2 == "(":
                    depth += 1
                elif c2 == ")":
                    depth -= 1
                    if depth == 0:
                        break
                inner.append(c2)
                j += 1
            if depth:
                return None
            subs.append("".join(inner))
            out.append(" _PS_ ")
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out), subs


_SEPARATORS = ("&&", "||", ";", "|")


def _split_top_level(cmd: str) -> list[str]:
    """Split on top-level ``&&``/``||``/``;``/``|`` (quote-aware)."""
    segments: list[str] = []
    cur: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if quote is None and ch in "'\"":
            quote = ch
        elif quote is not None and ch == quote:
            quote = None
        elif quote is None:
            for sep in _SEPARATORS:
                if cmd.startswith(sep, i):
                    segments.append("".join(cur))
                    cur = []
                    i += len(sep)
                    break
            else:
                cur.append(ch)
                i += 1
            continue
        cur.append(ch)
        i += 1
    segments.append("".join(cur))
    return segments


def _tokenize(segment: str) -> list[str] | None:
    """Split one segment into argv words; None on unterminated quotes."""
    words: list[str] = []
    cur: list[str] = []
    has = False
    i = 0
    while i < len(segment):
        ch = segment[i]
        if ch.isspace():
            if has:
                words.append("".join(cur))
                cur = []
                has = False
            i += 1
            continue
        if ch == "'":
            j = segment.find("'", i + 1)
            if j == -1:
                return None
            cur.append(segment[i + 1 : j])
            has = True
            i = j + 1
            continue
        if ch == '"':
            j = segment.find('"', i + 1)
            if j == -1:
                return None
            cur.append(segment[i + 1 : j])
            has = True
            i = j + 1
            continue
        if ch == "\\":
            if i + 1 >= len(segment):
                return None
            cur.append(segment[i + 1])
            has = True
            i += 2
            continue
        cur.append(ch)
        has = True
        i += 1
    if has:
        words.append("".join(cur))
    return words


def _redirects_ok(u: str) -> bool:
    """Only output redirects to /dev/null; any input redirect refused."""
    i = 0
    n = len(u)
    while i < n:
        ch = u[i]
        if ch == ">":
            j = i
            while j < n and u[j] == ">":
                j += 1
            while j < n and u[j] == " ":
                j += 1
            k = j
            while k < n and not (u[k].isspace() or u[k] in ";|&"):
                k += 1
            if u[j:k] != "/dev/null":
                return False
            i = k
            continue
        if ch == "<":
            return False
        i += 1
    return True


_GIT_READ_ONLY_VERBS = frozenset(
    {
        "status",
        "log",
        "diff",
        "rev-parse",
        "show",
        "ls-files",
        "ls-remote",
        "blame",
        "shortlog",
        "describe",
    }
)

_SYSTEMCTL_READ_ONLY_VERBS = frozenset(
    {
        "status",
        "is-active",
        "is-enabled",
        "show",
        "cat",
        "list-units",
        "list-unit-files",
    }
)

_CURL_VALUE_FLAGS = {
    "-H": "any",
    "--header": "any",
    "-w": "any",
    "--write-out": "any",
    "-X": "get-only",
    "--request": "get-only",
    "--max-time": "skip",
    "--connect-timeout": "skip",
}
_CURL_SAFE_SHORT_CLUSTER = frozenset("sSkLiq")
_CURL_SAFE_FLAGS = {
    "-s",
    "-S",
    "-k",
    "-q",
    "-L",
    "-i",
    "--silent",
    "--show-error",
    "--fail",
    "--location",
    "--head",
    "--insecure",
}

_PLAIN_READERS = frozenset(
    {
        "grep",
        "ls",
        "cat",
        "wc",
        "df",
        "tail",
        "head",
        "stat",
        "ps",
        "jq",
        "sort",
        "diff",
        "logsey",
    }
)

_PY_FORBIDDEN_SUBSTRINGS = (
    "import os",
    "import shutil",
    "import subprocess",
    "os.",
    "open(",
    "shutil",
    "subprocess",
    "system(",
    "popen",
    "Popen",
    "exec(",
    "eval(",
    "write",
    "remove(",
    "unlink",
    "rmdir",
    "rename(",
)

_READ_ONLY_MARKERS = ("--verify", "--dry-run", "--check")


def _git_read_only(argv: list[str]) -> bool:
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-C":  # global repo-path flag; skip its value
            i += 2
            continue
        if args[i].startswith("-"):
            i += 1
            continue
        verb = args[i]
        rest = args[i + 1 :]
        if verb in _GIT_READ_ONLY_VERBS:
            return True
        if verb == "worktree":
            return bool(rest) and rest[0] == "list"
        if verb == "branch":
            return not rest or all(a in ("-a", "-v", "--list") for a in rest)
        if verb == "config":
            return any(
                a in ("--list", "--get", "--get-regexp", "--get-all") for a in rest
            )
        if verb == "remote":
            return not rest or rest[0] == "-v"
        return False
    return False


def _curl_read_only(argv: list[str]) -> bool:
    args = argv[1:]
    i = 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("--"):
            name, eq, val = tok.partition("=")
            mode = _CURL_VALUE_FLAGS.get(name)
            if mode is None:
                return name in _CURL_SAFE_FLAGS and not eq
            if mode == "get-only":
                value = val if eq else (args[i + 1] if i + 1 < len(args) else None)
                if value is None or value.upper() != "GET":
                    return False
                i += 1 if eq else 2
                continue
            i += 1 if eq else 2  # any / skip: value consumed
            continue
        if tok.startswith("-") and len(tok) > 1:
            if tok == "-o":
                target = args[i + 1] if i + 1 < len(args) else None
                if target != "/dev/null":
                    return False
                i += 2
                continue
            if tok == "-w":  # write-out FORMAT string: a value flag, safe
                i += 2
                continue
            if tok == "-H":  # header: a value flag, safe for GET probes
                i += 2
                continue
            if set(tok[1:]) <= _CURL_SAFE_SHORT_CLUSTER:
                i += 1
                continue
            return False
        i += 1  # URL / operand
    return True


def _segment_read_only(argv: list[str]) -> bool:
    prog = argv[0]
    if prog.startswith("<"):  # template placeholder binary
        return any(a in _READ_ONLY_MARKERS for a in argv[1:])
    if prog in ("python3", "python"):
        body = None
        for idx, a in enumerate(argv[1:]):
            if a == "-c":
                body = argv[2 + idx] if 2 + idx < len(argv) else None
                break
        if body is None:
            return False
        return not any(bad in body for bad in _PY_FORBIDDEN_SUBSTRINGS)
    if prog == "git":
        return _git_read_only(argv)
    if prog == "curl":
        return _curl_read_only(argv)
    if prog == "systemctl":
        rest = argv[1:]
        return bool(rest) and rest[0] in _SYSTEMCTL_READ_ONLY_VERBS
    if prog == "docker":
        rest = argv[1:]
        if not rest:
            return False
        if rest[0] in ("inspect", "ps"):
            return True
        return rest[0] == "container" and len(rest) > 1 and rest[1] == "inspect"
    if prog == "sqlite3":
        sql = next(
            (
                a
                for a in argv[1:]
                if not a.startswith("-") and not _PLACEHOLDER_RE.fullmatch(a)
            ),
            None,
        )
        if sql is None:
            return False
        head = sql.split(None, 1)[0].upper() if sql.split() else ""
        return head in ("SELECT", "PRAGMA", "EXPLAIN", "WITH")
    if prog == "sed":
        return not any(
            a in ("-i", "--in-place")
            or (a.startswith("-") and not a.startswith("--") and "i" in a)
            for a in argv[1:]
        )
    return prog in _PLAIN_READERS


def is_read_only_command(command: str) -> bool:
    """Default-deny allow-list gate. See the module docstring for the rule.

    True ONLY for commands positively recognized as read-only/verify/
    dry-run/SELECT-only. The ``no data`` sentinel is not a command: False.
    """
    if not command or not command.strip():
        return False
    cmd = command.strip()
    if cmd == NO_VALID_EVIDENCE:
        return False
    if "\n" in cmd or "\r" in cmd:
        return False
    extracted = _extract_process_subs(cmd)
    if extracted is None:
        return False
    text, subs = extracted
    for sub in subs:
        if not is_read_only_command(sub):
            return False
    unquoted = _PLACEHOLDER_RE.sub("_PH_", _unquoted(text))
    if "`" in unquoted or "$(" in unquoted:
        return False
    if not _redirects_ok(unquoted):
        return False
    if "&" in unquoted.replace("&&", " "):
        return False
    for segment in _split_top_level(text):
        stripped = segment.strip()
        if not stripped:
            continue
        argv = _tokenize(stripped)
        if not argv:
            return False
        if not _segment_read_only(argv):
            return False
    return True


# ---------------------------------------------------------------- lint
def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _classify(result: object) -> str:
    """Map a runner result onto the closed outcome vocabulary."""
    if result is None:
        return "unknown"
    if getattr(result, "timed_out", False):
        return "timeout"
    rc = getattr(result, "returncode", None)
    if isinstance(rc, bool) or not isinstance(rc, int):
        return "unknown"
    return "ok" if rc == 0 else "error"


def _unfilled_placeholder_token(command: str) -> str | None:
    """Return the FIRST unfilled ``<placeholder>`` slot in the command.

    Quote-aware: ``<...>`` inside quoted spans is literal text (a grep
    pattern such as ``'<key-name>'`` or a jq filter), not a template slot —
    only placeholders the shell would see count. The runner shell would
    parse a bare ``<token>`` as input redirection, so an unfilled slot must
    never reach it (module docstring: --execute expects a FILLED runbook).
    """
    unquoted = _unquoted(command)
    match = _PLACEHOLDER_RE.search(unquoted)
    return match.group(0) if match else None


@dataclass(frozen=True)
class CheckResult:
    """One check's lint outcome (closed vocabulary, see module docstring).

    ``template`` results carry the offending ``<token>`` on ``stderr`` and
    are never executed (``exit_code`` stays ``None``).
    """

    class_id: str
    order: int
    command: str
    outcome: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    timestamp: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class LintReport:
    """Per-class lint report carrying the honesty label and drift reason."""

    class_id: str
    results: list[CheckResult] = field(default_factory=list)
    honesty_label: str = HONESTY_LABEL
    created_at: str = ""

    @property
    def drifted_orders(self) -> list[int]:
        return [r.order for r in self.results if r.outcome in DRIFT_OUTCOMES]

    @property
    def stale_reason(self) -> str | None:
        drift = [
            (r.order, r.outcome) for r in self.results if r.outcome in DRIFT_OUTCOMES
        ]
        if not drift:
            return None
        detail = ", ".join(f"check {o} ({out})" for o, out in drift)
        return f"lint drift: {detail}"

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "results": [r.to_dict() for r in self.results],
            "honesty_label": self.honesty_label,
            "created_at": self.created_at,
            "drifted_orders": self.drifted_orders,
            "stale_reason": self.stale_reason,
        }


def lint_runbook(
    runbook: Runbook,
    *,
    runner: Callable[..., object] | None = None,
) -> LintReport:
    """Lint every check of one runbook in read-only mode.

    ``runner`` is INJECTABLE: tests never execute a real command. The
    default runner (only when ``runner`` is None) runs the gate-approved
    command via ``subprocess.run(shell=True, capture_output=True,
    timeout=COMMAND_TIMEOUT_SECONDS, stdin=DEVNULL)`` — bounded and never
    interactive. The ``no data`` sentinel is reported as ``absent``: never
    executed, never counted as pass or failure. A check still carrying
    unfilled ``<placeholder>`` slots is reported as ``template`` (with the
    offending token on ``stderr``): never executed, never drift —
    --execute expects a FILLED runbook (see the module docstring).
    """
    run = runner if runner is not None else _default_runner
    ts = _utc_now()
    results: list[CheckResult] = []
    for check in sorted(runbook.checks, key=lambda c: c.order):
        cmd = check.command.strip()
        result: object = None
        exit_code: int | None = None
        stdout = stderr = ""
        timed_out = False
        if cmd == NO_VALID_EVIDENCE or not cmd:
            outcome = OUTCOME_ABSENT
        elif not check.read_only:
            # LORE-026 plan-only: the registry marked this check MUTATING
            # (e.g. the guard-degradation control-worktree git worktree
            # add). The default-deny gate CAN never approve it and must
            # never be loosened to: the mark itself is the honest statement
            # that this check is a plan, not an executable probe. Reported
            # as ``template`` — never executed, never drift — so the class
            # does not stale from its own diagnostic.
            outcome = OUTCOME_TEMPLATE
            stderr = (
                "plan-only check — the registry marks it MUTATING "
                "(read_only=False); the default-deny gate will never run it"
            )
        elif not is_read_only_command(check.command):
            outcome = "refused"
        elif (token := _unfilled_placeholder_token(check.command)) is not None:
            outcome = OUTCOME_TEMPLATE
            stderr = (
                "template check — fill <placeholder> args before "
                f"executing; {token} is not shell syntax"
            )
        else:
            try:
                result = run(check.command)
            except Exception as exc:  # noqa: BLE001 — drift, never a crash
                result = CommandResult(returncode=None, stderr=f"runner failure: {exc}")
            outcome = _classify(result)
            exit_code = getattr(result, "returncode", None)
            stdout = _clip(getattr(result, "stdout", ""))
            stderr = _clip(getattr(result, "stderr", ""))
            timed_out = bool(getattr(result, "timed_out", False))
        results.append(
            CheckResult(
                class_id=runbook.class_id,
                order=check.order,
                command=check.command,
                outcome=outcome,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                timed_out=timed_out,
                timestamp=ts,
            )
        )
    return LintReport(class_id=runbook.class_id, results=results, created_at=ts)


def lint_all(*, runner: Callable[..., object] | None = None) -> list[LintReport]:
    """Lint every registry class's runbook (curated first, unclassified last)."""
    return [lint_runbook(rb, runner=runner) for rb in compile_all()]


# ------------------------------------------------------- stale transition
def apply_lint(report: LintReport, runbook: Runbook) -> Runbook:
    """The anti-rot transition: drift flips the runbook to ``stale``.

    Returns a NEW frozen Runbook (``dataclasses.replace`` — never mutate).
    The runbook flips to ``STATUS_STALE`` when the report shows ANY drift
    (``error``/``timeout``/``refused``/``unknown``). A report with nothing
    but ``ok``/``absent``/``template`` outcomes does NOT flip the runbook —
    honest absence and unfilled ``<placeholder>`` slots are not rot
    (template checks are reported visibly; fill them and re-lint).

    Honesty laws: this NEVER sets ``last_validated`` (a lint run is not
    operator attestation) and NEVER moves status to ``validated`` — only a
    human attestation may do that. WHY it went stale lives on the report:
    ``report.stale_reason`` names the drifted checks (e.g.
    ``"lint drift: check 2 (error)"``) so callers can render the reason.
    """
    reason = report.stale_reason
    if reason is None:
        return runbook  # no drift: nothing to flip, nothing to annotate
    new_checks = [
        dataclasses.replace(
            c,
            evidence=list(c.evidence)
            + [
                {
                    "kind": "lint",
                    "detail": f"{report.created_at}: {reason}",
                }
            ],
        )
        for c in runbook.checks
    ]
    return dataclasses.replace(runbook, checks=new_checks, status=STATUS_STALE)
