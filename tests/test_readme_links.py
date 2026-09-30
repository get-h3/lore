"""README-1 guard: README.md must not link to non-public get-h3 sibling repos.

Hermetic and offline: asserts over the README text against an explicit
allowlist of known-public repos. No network I/O.
"""

from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"

# Repos under github.com/get-h3 that are verified public and may be linked.
KNOWN_PUBLIC = {"lore"}


def test_readme_does_not_link_private_get_h3_repos() -> None:
    text = README.read_text(encoding="utf-8")
    bad = [
        line
        for line in text.splitlines()
        if "https://github.com/get-h3/" in line
        and line.split("https://github.com/get-h3/", 1)[1]
        .split("/", 1)[0]
        .split(")", 1)[0]
        .split(" ", 1)[0]
        not in KNOWN_PUBLIC
    ]
    assert not bad, (
        "README.md links to get-h3 repos not in the known-public allowlist "
        f"{sorted(KNOWN_PUBLIC)}: {bad}"
    )
