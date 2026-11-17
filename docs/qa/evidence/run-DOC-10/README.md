# DOC-10 — README Status + docs/RELEASE.md after the v0.2.0 cut

Run: `lore-foreman-2026-11-17-05-00-08`. Merged at `70229d8` (worker commit `4c363f2`,
merge `514287f`). Tier-1 gitreins verdict `d24425ea` (passed:true, commit `70229d8`).

## Premise (was live before the change)

`README.md` "## Status" claimed: version stamp **0.1.2 — not released**, tag **v0.1.0** as
"the repo's only tag", tree "**over 160 commits**" past it. `docs/RELEASE.md` listed only
`v0.1.0`. But v0.2.0 was tagged and released on 2026-11-16.

## Witnesses (command output, not prose)

```
$ git for-each-ref refs/tags --format='%(refname:short) %(objectname:short)'
v0.1.0 1713ab8
v0.2.0 9f605ba

$ git ls-remote --tags origin
1713ab8181bded87a8fe63ad8b1162117e6995db      refs/tags/v0.1.0
c6556662c93ba0db846dfe3edb68fca58f2a8a3c      refs/tags/v0.1.0^{}
9f605bae671ae0f688847b204db8e4fc3dce22ce      refs/tags/v0.2.0
165cc8f6d354d9ed57d58635c1ad482d0e755cf2      refs/tags/v0.2.0^{}

$ git log -1 --format='%h %ad %s' --date=short v0.2.0^{commit}
165cc8f 2026-11-16 chore(release): authorize and prepare the v0.2.0 cut

$ git rev-list --count v0.2.0..HEAD     # at the worker commit 4c363f2
7
$ grep -m1 '^version' pyproject.toml
version = "0.2.0"
$ grep -m1 '__version__' lore/__init__.py
__version__ = "0.2.0"
```

## Edited surfaces

- `README.md` "## Status" — stamp **0.2.0**, released **2026-11-16** as tag `v0.2.0`
  (commit `165cc8f`), link to the CHANGELOG 0.2.0 section, both tags listed with their dates,
  and `main` is **7 commits** past v0.2.0 *stated as a dated snapshot with the recompute
  command* ("counted 2026-11-17; run `git rev-list --count v0.2.0..HEAD` for the live figure")
  so the integer cannot silently rot. The PyPI honesty line is kept verbatim in meaning:
  nothing is published under any name, install channels are git only.
- `docs/RELEASE.md` tag-namespace paragraph — `Existing tags: v0.1.0, v0.2.0`, and the
  illustrative tag example no longer cites `v0.1.2`, a stamp that was never tagged. The
  "derived from the version stamp, never invented" rule is untouched.

## Verification

```
$ grep -n "not released\|only tag\|over 160" README.md docs/RELEASE.md
(no matches — exit 1)
```

| Gate (merged tree `70229d8`) | Result |
|---|---|
| `python -m pytest -q` | `572 passed in 8.37s` |
| `bash scripts/check-test-count.sh` | PASS canonical=572 live=572; class-count=13; no stale literals |
| `pytest tests/test_readme_links.py -q` | 1 passed |
| `ruff check .` | All checks passed |

Out of scope by design: `INSTALL.md`, `AGENTS.md`, the README per-topic docs list, the weekly
schedule/timer prose (DOC-11's region), CHANGELOG history, and the "572 tests passing" literal
(policed by `tests/test_count_guard.py` and `scripts/check-test-count.sh`).
