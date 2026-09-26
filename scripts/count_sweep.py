#!/usr/bin/env python3
"""count_sweep.py — shared doc sweep for the count-sync guard (LORE-029/036).

Sweeps living Markdown for stale count literals in two families:

  test counts:  '<N> passed' / '<N> tests'      vs scripts/test-count.txt
  class counts: '<N> failure classes' /          vs len(SEED_CLASSES) derived
                '<N> curated classes'              from lore/classes.py (LORE-036)

The class count is DERIVED by loading lore/classes.py from the repo root —
never a second hand-maintained literal (LORE-032 precedent).

Exit contract (used by scripts/check-test-count.sh):
  0 = clean, 1 = drift found, 2 = misconfigured (cannot derive a count).

Usage:
  python3 scripts/count_sweep.py <test-count> [repo-root]

The shell guard passes its canonical test count; this script derives the
class count, prints one line per drift hit ('path:line: text') on stdout,
and prints an ERROR line on stderr when misconfigured.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

# Dated records — a number there was true when written, never flagged.
# Mirrors the allowlist in scripts/check-test-count.sh.
ALLOWLISTED_PATTERNS: tuple[str, ...] = (
    "CHANGELOG.md",
    "docs/dogfood/*",
    ".gitreins/*",
    ".coding-hermes/*",
    "docs/acceptance/*",
)

# A line quoting the canonical count file itself is a sync instruction, not
# a claim about the current count.
SELF_REFERENCE = "scripts/test-count.txt"

# Test-count literal family (LORE-029): '<N> passed' / '<N> tests'.
TEST_COUNT_RE = re.compile(r"(?<![\w])(\d{2,4}) (passed|tests)(?![\w])")

# Class-count literal family (LORE-036): '<N> failure classes' /
# '<N> curated classes'. Singular forms ('1 failure class') are excluded
# from the numeric match on purpose: the registry never holds one class.
# Threshold phrasing ('≥N', 'at least N', '>= N') is not a claim about the
# current count and is skipped.
CLASS_COUNT_RE = re.compile(
    r"(?<![\w])(\d{1,4}) (failure classes|curated classes)(?![\w])"
)

THRESHOLD_PREFIX_RE = re.compile(r"(≥|>=|>\+?|at least|no fewer than)\s*([.,]?)\s*$")


def _allowlisted(rel: str) -> bool:
    """True when the tracked path is a dated record (never flagged)."""
    for pattern in ALLOWLISTED_PATTERNS:
        if pattern.endswith("/*"):
            if rel.startswith(pattern[:-1]):
                return True
        elif rel == pattern:
            return True
    return False


def derive_class_count(repo_root: Path) -> int | None:
    """Load lore/classes.py from repo_root and return len(SEED_CLASSES).

    Loads the module fresh from its path (the repo root's `lore` package is
    not always importable — e.g. the guard runs from any cwd) so the count
    is derived from the seed table itself, never a hand-maintained literal.
    Returns None when the module or SEED_CLASSES cannot be resolved (the
    caller must treat that as misconfiguration, not as drift).
    """
    classes_py = repo_root / "lore" / "classes.py"
    if not classes_py.is_file():
        return None
    spec = importlib.util.spec_from_file_location("lore_classes_guard", classes_py)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves its annotations through
    # sys.modules[cls.__module__] and fails with AttributeError otherwise.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 — any load failure = misconfigured, not drift
        return None
    seeds = getattr(module, "SEED_CLASSES", None)
    if not isinstance(seeds, tuple):
        return None
    return len(seeds)


def _line_hits(line: str, canonical_test_count: int, class_count: int) -> bool:
    """True when the line carries a stale count literal of either family."""
    if SELF_REFERENCE in line:
        return False
    for match in TEST_COUNT_RE.finditer(line):
        if int(match.group(1)) != canonical_test_count:
            return True
    for match in CLASS_COUNT_RE.finditer(line):
        prefix = line[: match.start()]
        if THRESHOLD_PREFIX_RE.search(prefix):
            continue
        if int(match.group(1)) != class_count:
            return True
    return False


def sweep(
    root: Path,
    files: list[str],
    canonical_test_count: int,
    class_count: int,
) -> list[str]:
    """Sweep the given (tracked, living) Markdown files under ``root``.

    Returns drift hits as 'path:line: text' (one per stale literal line);
    empty list = clean. ``class_count`` must come from derive_class_count().
    """
    hits: list[str] = []
    for rel in files:
        if not rel.endswith(".md"):
            continue
        if _allowlisted(rel):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _line_hits(line, canonical_test_count, class_count):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "--class-count":
        # Helper mode: print only the derived class count (guard banner).
        repo_root = Path(argv[2]) if len(argv) > 2 else Path.cwd()
        count = derive_class_count(repo_root)
        if count is None:
            print(
                "ERROR: could not derive the class count from lore/classes.py SEED_CLASSES",
                file=sys.stderr,
            )
            return 2
        print(count)
        return 0
    if len(argv) < 2:
        print(
            "ERROR: usage: count_sweep.py <canonical-test-count> [repo-root]",
            file=sys.stderr,
        )
        return 2
    if not re.fullmatch(r"\d+", argv[1]):
        print(
            f"ERROR: canonical test count {argv[1]!r} is not a number", file=sys.stderr
        )
        return 2
    canonical = int(argv[1])
    repo_root = Path(argv[2]) if len(argv) > 2 else Path.cwd()

    class_count = derive_class_count(repo_root)
    if class_count is None:
        print(
            "ERROR: could not derive the class count from lore/classes.py SEED_CLASSES "
            "(guard misconfigured, not drift)",
            file=sys.stderr,
        )
        return 2

    ls = _git_ls_files_md(repo_root)
    if ls is None:
        print("ERROR: git ls-files failed (not a git checkout?)", file=sys.stderr)
        return 2

    hits = sweep(repo_root, ls, canonical, class_count)
    for hit in hits:
        print(hit)
    if hits:
        print(
            f"FAIL: stale count literal(s) above (canonical test count {canonical}, "
            f"derived class count {class_count}); fix them or the wave ships stale docs",
            file=sys.stderr,
        )
        return 1
    return 0


def _git_ls_files_md(repo_root: Path) -> list[str] | None:
    import subprocess

    proc = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
