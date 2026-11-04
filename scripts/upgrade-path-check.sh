#!/usr/bin/env bash
# Upgrade-path check — the `lore` -> `get-h3-lore` distribution rename.
#
# Why this exists (QA-LORE-RELENG-1): the project renamed its PyPI
# *distribution* to `get-h3-lore` while the import package and the console
# script stay `lore`. A rename changes the distribution identity, so a plain
# install over an older release does not upgrade it — the old `lore`
# distribution is never removed, and the operator is left with two installed
# distributions and no way to tell which code the `lore` executable runs.
# Nothing else in the gate set exercises that path, and the index-based
# upgrade cell cannot (the project does not publish to PyPI by design), so
# this script exercises the only supported channel: installs built from this
# repository, offline, with no PyPI access.
#
# Rungs, each printed as `rung <name> OK|FAIL <detail>`:
#   v0.1.0-install          tag v0.1.0 installs as distribution `lore` 0.1.0
#   naive-upgrade-leftover  installing the current tree over it is classified
#                           (leftover-confirmed = the hazard; clean-rename = fine)
#   rename-migration        uninstall `lore`, install current tree => exactly
#                           one distribution, at the current version
#   post-upgrade-verify     the CLI works AND the installed code really swapped
#                           (version marker, not just the version string pip reports)
#
# Exit: 0 = every rung observed, 1 = a rung failed, 2 = guard misconfigured.
#
# Usage: scripts/upgrade-path-check.sh [tag]      (default tag: v0.1.0)
#        KEEP=1 scripts/upgrade-path-check.sh    (keep the scratch venv)

set -uo pipefail

ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null)" || {
    echo "GUARD: not inside a git checkout" >&2
    exit 2
}
TAG="${1:-v0.1.0}"
OLD_DIST="lore"
NEW_DIST_MATCH="get_h3_lore"

for bin in git uv; do
    command -v "$bin" >/dev/null 2>&1 || {
        echo "GUARD: $bin not on PATH" >&2
        exit 2
    }
done
[ -f "$ROOT/pyproject.toml" ] || {
    echo "GUARD: no pyproject.toml at $ROOT" >&2
    exit 2
}
git -C "$ROOT" rev-parse -q --verify "refs/tags/$TAG" >/dev/null || {
    echo "GUARD: tag $TAG not found in $ROOT" >&2
    exit 2
}

head_version="$(
    sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$ROOT/pyproject.toml" | head -1
)"
tag_version="$(
    git -C "$ROOT" show "$TAG:pyproject.toml" |
        sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' | head -1
)"
[ -n "$head_version" ] && [ -n "$tag_version" ] || {
    echo "GUARD: could not read project version from pyproject.toml" >&2
    exit 2
}

BASE="${TMPDIR:-/tmp}"
WORK="$(mktemp -d "$BASE/lore-upgrade-path-XXXXXX")" || exit 2
SRC="$WORK/src-at-tag"
VENV="$WORK/venv"
PY="$VENV/bin/python"
LOG="$WORK/install.log"
fails=0

cleanup() {
    if [ "${KEEP:-0}" = "1" ]; then
        echo "scratch: $WORK"
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

pass() { printf 'rung %-22s OK   %s\n' "$1" "$2"; }
fail() { printf 'rung %-22s FAIL %s\n' "$1" "$2"; fails=$((fails + 1)); }

site_packages() {
    ls -d "$VENV"/lib/python*/site-packages 2>/dev/null | head -1
}
dist_list() {
    local sp; sp="$(site_packages)"
    [ -n "$sp" ] || return 0
    find "$sp" -maxdepth 1 -name '*.dist-info' -printf '%f\n' 2>/dev/null |
        sed 's/\.dist-info$//' | sort
}
has_dist() { # $1 = distribution name prefix (dist-info stems are `<name>-<version>`)
    dist_list | grep -q "^$1-" 2>/dev/null
}
dist_version() { # $1 = dist-info stem
    local sp; sp="$(site_packages)"
    grep -h -m1 '^Version:' "$sp/$1.dist-info/METADATA" 2>/dev/null | awk '{print $2}'
}
installed_code_version() {
    sed -n 's/^__version__[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
        "$(site_packages)/lore/__init__.py" 2>/dev/null | head -1
}
install_tree() { # $1 = install source; quiet, log captured
    uv pip install -q --python "$PY" "$1" >>"$LOG" 2>&1
}

echo "upgrade-path-check: tag=$TAG tag_version=$tag_version head_version=$head_version"

# ---------------------------------------------------------------- rung 1
git clone -q --branch "$TAG" --depth 1 "file://$ROOT" "$SRC" >>"$LOG" 2>&1 ||
    git clone -q --branch "$TAG" "$ROOT" "$SRC" >>"$LOG" 2>&1
if [ ! -d "$SRC" ]; then
    fail v0.1.0-install "clone of $TAG failed (see log below)"
else
    uv venv -q "$VENV" >>"$LOG" 2>&1
    if install_tree "$SRC"; then
        d1="$(dist_list)"
        v1="$(dist_version "$(echo "$d1" | grep "^$OLD_DIST-" | head -1)")"
        if [ "$(echo "$d1" | wc -l)" = "1" ] && [ "$v1" = "$tag_version" ] && [ -x "$VENV/bin/lore" ]; then
            pass v0.1.0-install "dist=$OLD_DIST version=$v1 script=lore"
        else
            fail v0.1.0-install "dists=[$(echo "$d1" | tr '\n' ' ')] version=${v1:-none}"
        fi
    else
        fail v0.1.0-install "install of $TAG tree failed (see log below)"
    fi
fi

# ---------------------------------------------------------------- rung 2
# Naive upgrade: install the current tree without removing the old distribution.
# This is what a user does after reading "upgrade" as a version bump. It is a
# CLASSIFICATION, not an assertion: a tool that cleans the rename up is fine,
# a leftover is the hazard this script exists to name.
if [ "$fails" -eq 0 ]; then
    if install_tree "$ROOT"; then
        have_old=0; have_new=0
        has_dist "$OLD_DIST" && have_old=1
        has_dist "$NEW_DIST_MATCH" && have_new=1
        count="$(dist_list | wc -l)"
        if [ "$have_old" = 1 ] && [ "$have_new" = 1 ]; then
            pass naive-upgrade-leftover "leftover-confirmed: $count dists installed ($(dist_list | tr '\n' ' '))-> migration required"
        elif [ "$have_new" = 1 ]; then
            pass naive-upgrade-leftover "clean-rename: $count dist ($(dist_list | tr '\n' ' '))"
        else
            fail naive-upgrade-leftover "neither distribution present after install: [$(dist_list | tr '\n' ' ')]"
        fi
    else
        fail naive-upgrade-leftover "install of current tree failed (see log below)"
    fi
fi

# ---------------------------------------------------------------- rung 3
# The supported migration: drop the old distribution, then install the new one.
if [ "$fails" -eq 0 ]; then
    uv pip uninstall -q --python "$PY" "$OLD_DIST" >>"$LOG" 2>&1
    if has_dist "$OLD_DIST"; then
        fail rename-migration "uninstall of $OLD_DIST did not remove it"
    elif ! install_tree "$ROOT"; then
        fail rename-migration "install of current tree failed after uninstall (see log below)"
    else
        d3="$(dist_list)"
        count3="$(echo "$d3" | wc -l)"
        new3="$(echo "$d3" | grep "^$NEW_DIST_MATCH-" | head -1)"
        v3="$(dist_version "${new3:-missing}")"
        if [ "$count3" = "1" ] && [ -n "$new3" ] && [ "$v3" = "$head_version" ]; then
            pass rename-migration "dists=1 ($new3) version=$v3"
        else
            fail rename-migration "dists=$count3 [$(echo "$d3" | tr '\n' ' ')] version=${v3:-none}"
        fi
    fi
fi

# ---------------------------------------------------------------- rung 4
# The version string is not proof: prove the installed CODE swapped, and that
# the console script still runs the new build.
if [ "$fails" -eq 0 ]; then
    code_v="$(installed_code_version)"
    smoke="$("$VENV/bin/lore" match "key rotation expired" 2>&1 | head -1 || true)"
    if [ "$code_v" = "$head_version" ] && [ "$code_v" != "$tag_version" ]; then
        case "$smoke" in
            key-rotation-expiry*)
                pass post-upgrade-verify "code_version=$code_v smoke=key-rotation-expiry"
                ;;
            *)
                fail post-upgrade-verify "CLI smoke unexpected: ${smoke:-<empty>}"
                ;;
        esac
    else
        fail post-upgrade-verify "installed code version=${code_v:-none} expected=$head_version (tag was $tag_version)"
    fi
fi

if [ "$fails" -gt 0 ]; then
    echo "--- install log (tail) ---"
    tail -20 "$LOG" 2>/dev/null
    echo "RESULT: FAIL rungs_failed=$fails"
    exit 1
fi
echo "RESULT: PASS rungs=4 tag=$TAG head_version=$head_version"
exit 0
