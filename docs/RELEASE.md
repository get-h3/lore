# Release process — lore

How to cut a release. **Nobody cuts without a board-authorized RELEASE-cut row.**

## Tag namespace

Releases are annotated git tags named `vX.Y.Z` (e.g. `v0.1.2`). The tag is always
derived from the version stamp — never invented by hand. Existing tags: `v0.1.0`.
Release artifacts are git tags only. The PyPI distribution name for this project
is `get-h3-lore`, and PyPI publishing is NOT enabled: releases never go to PyPI.
The bare name `lore` on PyPI is a foreign, unrelated package (instacart/lore)
and must never be used — installing `pip install lore` installs someone else's
software.

## Version-stamp files

The version lives in exactly two places and must always agree:

- `pyproject.toml:7` — `version = "X.Y.Z"` under `[project]`
- `lore/__init__.py:3` — `__version__ = "X.Y.Z"`

Bump both together. CI enforces agreement on every `v*` tag push
(`.github/workflows/release-check.yml`).

## Changelog promotion rule

`CHANGELOG.md` must contain a `## [X.Y.Z] — <date>` section for the version being
cut, and it must NOT be marked "Not released". Promotion means:

1. Bump the two version-stamp files.
2. Add (or fill in) the `## [X.Y.Z]` changelog section for the release.
3. If an `## [Unreleased]` section exists, fold its entries into the new section.
4. Remove any "Not released" wording from the section.

`scripts/release.sh` refuses to cut while the section is missing or still marked
"Not released".

## Cut authorization rule

A release cut requires a board-authorized RELEASE-cut row (`.coding-hermes/board/tasks.jsonl`,
`RELEASE-*` id) approved by the owner. The script enforces this: without the
explicit `--authorized` flag it prints the refusal and exits non-zero, no matter
how clean the tree is.

## Cutting

```sh
uv sync --extra dev && uv run pytest -q          # green locally first
scripts/release.sh --dry-run                     # all checks, no mutation
scripts/release.sh --authorized                  # real cut: tag + push + GitHub Release
```

The script refuses: dirty tree, HEAD sha without a passing CI run, an already
existing tag, a missing/unpromoted changelog section, and a missing
`--authorized` flag (`--skip-ci-check` tolerates gh auth being unavailable for
the CI-status check only).

## Rollback path

To undo a bad release, delete the Release object and the tag. The **previous
tag remains the last good release** — never rewrite or move an existing tag.

```sh
gh release delete vX.Y.Z --yes
git push origin :refs/tags/vX.Y.Z
```

Consumers should pin to the previous tag until the fixed version is cut.
