#!/usr/bin/env bash
# release.sh — cut a lore release from the current tree.
#
# Usage:
#   scripts/release.sh --dry-run            # run every check, mutate nothing
#   scripts/release.sh --authorized         # owner-authorized cut (board RELEASE-cut row required)
#   scripts/release.sh --authorized --skip-ci-check   # tolerate missing gh auth
#
# Safety: without --authorized the script is inert — a release cut needs a
# board-authorized RELEASE-cut row. Without --dry-run and WITH --authorized it
# mutates: creates an annotated tag, pushes it, and opens a GitHub Release.
set -euo pipefail

DRY_RUN=0
AUTHORIZED=0
SKIP_CI=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)      DRY_RUN=1 ;;
    --authorized)   AUTHORIZED=1 ;;
    --skip-ci-check) SKIP_CI=1 ;;
    *) echo "release.sh: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# --- 1. clean tree -----------------------------------------------------------
if [ -n "$(git status --porcelain)" ]; then
  echo "REFUSE: working tree is dirty — commit or stash before cutting." >&2
  exit 1
fi
echo "ok: working tree clean"

HEAD_SHA="$(git rev-parse HEAD)"

# --- 2. CI green on HEAD sha -------------------------------------------------
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  CI_CONCLUSION="$(gh run list --limit 20 --json headSha,conclusion \
    --jq "[.[] | select(.headSha == \"$HEAD_SHA\")][0].conclusion // \"none\"" 2>/dev/null || echo "error")"
  if [ "$CI_CONCLUSION" != "success" ]; then
    if [ "$SKIP_CI" -eq 1 ]; then
      echo "WARN: CI on HEAD sha $HEAD_SHA is '$CI_CONCLUSION' — skipping check (--skip-ci-check)." >&2
    else
      echo "REFUSE: latest CI on HEAD sha $HEAD_SHA is not success (got: $CI_CONCLUSION)." >&2
      echo "        Use --skip-ci-check only when gh CI data is unavailable." >&2
      exit 1
    fi
  else
    echo "ok: CI success on HEAD sha $HEAD_SHA"
  fi
else
  if [ "$SKIP_CI" -eq 1 ]; then
    echo "WARN: gh auth unavailable — skipping CI check (--skip-ci-check)." >&2
  else
    echo "REFUSE: cannot verify CI status (gh missing or unauthenticated)." >&2
    echo "        Pass --skip-ci-check to tolerate this." >&2
    exit 1
  fi
fi

# --- 3. derive tag from version stamp ----------------------------------------
VERSION="$(sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml | head -1)"
if [ -z "$VERSION" ]; then
  echo "REFUSE: could not read version from pyproject.toml." >&2
  exit 1
fi
TAG="v$VERSION"
echo "ok: version $VERSION -> tag $TAG"

if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  echo "REFUSE: tag $TAG already exists." >&2
  exit 1
fi
echo "ok: tag $TAG does not exist"

# --- 4. changelog section for this version, not marked "Not released" --------
CHANGELOG_BLOCK="$(awk -v pat="^## \\[$VERSION\\]" '
  $0 ~ pat {inblk=1}
  inblk && /^## \[/ && $0 !~ pat {exit}
  inblk {print}
' CHANGELOG.md)"
if [ -z "$CHANGELOG_BLOCK" ]; then
  echo "REFUSE: CHANGELOG.md has no '## [$VERSION]' section." >&2
  exit 1
fi
if printf '%s\n' "$CHANGELOG_BLOCK" | grep -qi "Not released"; then
  echo "REFUSE: CHANGELOG.md section [$VERSION] is still marked 'Not released'." >&2
  echo "        Promote it first (see docs/RELEASE.md)." >&2
  exit 1
fi
echo "ok: CHANGELOG.md has a promoted [$VERSION] section"

# --- 5. explicit authorization ----------------------------------------------
if [ "$AUTHORIZED" -ne 1 ]; then
  echo "REFUSE: a release cut needs a board-authorized RELEASE-cut row." >&2
  echo "        Re-run with --authorized once the owner authorizes the cut." >&2
  exit 1
fi
echo "ok: cut authorized"

# --- 6. mutation phase -------------------------------------------------------
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY-RUN: all checks passed — would now: git tag -a $TAG, push origin $TAG, gh release create $TAG --generate-notes"
  exit 0
fi

git tag -a "$TAG" -m "lore $TAG"
git push origin "$TAG"
gh release create "$TAG" --generate-notes --verify-tag

# --- 7. verify ---------------------------------------------------------------
gh release view "$TAG" >/dev/null
echo "DONE: release $TAG created and verified (gh release view $TAG)."
echo "Rollback: gh release delete $TAG --yes && git push origin :refs/tags/$TAG"
