#!/usr/bin/env bash
# QA-LORE-5 — the real chaos-corruption premise for lore.
#
# WHY THIS FILE EXISTS: bunker-qa.sh's generic chaos-corruption cell builds its
# candidate set from *.db / *.sqlite / *.sqlite3 files under the repo. lore's
# durable state is not a database — it is the per-box JSONL ledger
# `.lore/validate-history.jsonl` (lore/validate.py HISTORY_FILE, relative to the
# CURRENT working directory, git-ignored). The generic cell can therefore only
# ever grade N/A "no db/state files in repo", and the torn-state read path is
# never exercised on a clean machine. The harness supports a repo-owned probe
# that REPLACES the generic cell logic (.qa/chaos-probes/corruption.sh, opt-in,
# executable) — this script is that probe.
#
# Self-contained, offline, writes nothing outside its mktemp dir, sub-second.
#
# EXIT CONTRACT (bunker-qa.sh project-probe hook):
#   0   = OK   — both rungs survived (the first stdout line is the cell detail)
#   1   = FAIL — the product misbehaved: a rung raised, or the corruption hid
#                records that are still well-formed
#   2   = INFO — genuine environment gap: no interpreter that imports the
#                checkout under test, no mktemp/timeout, or the probe's symptom
#                text no longer classifies (probe/registry premise drift —
#                reported, never blamed on the product)
#   124 = the harness maps a probe hang to FAIL; every CLI call here is also
#         bounded by an inner `timeout`, so a hung read fails as rc=1 with the
#         hung call named instead of consuming the harness budget.
#
# RUNGS
#  1. TORN LEDGER. A ledger in a throwaway dir is damaged the way a real
#     interrupted write damages it: two well-formed records, a line TRUNCATED
#     MID-RECORD (no trailing newline), one non-JSON garbage line, and then one
#     more well-formed record written AFTER the damage. Both public readers must
#     scan PAST the two malformed lines and report the newest readable record
#     instead of "never validated":
#       `lore consult "<symptoms>"` -> the local-history line names the
#           post-damage timestamp and its executed X/Y clause
#       `lore audit --format json`  -> the post-damage record's drift still
#           surfaces (exactly one stale class, reason "lint drift: check 2")
#     HONESTY NOTE: the post-damage record is the assertion that matters. A
#     reader that stopped at the torn line would still print the older record,
#     so only the newest-record pin proves the scan continued.
#  2. UNREADABLE LEDGER. The same path is replaced by a DIRECTORY (this works as
#     root, unlike chmod 000) and, when the probe is not root, by a chmod-000
#     file. `lore consult` / `lore audit` must degrade with a clean message and
#     never a traceback.
#
# The probe drives the checkout under test — never a globally installed `lore`:
# every call is `PYTHONPATH=<repo root> <python> -m lore …` from a temp cwd, and
# the interpreter's `lore.__file__` is required to live under the repo root.
# PYTHONDONTWRITEBYTECODE keeps the run from dropping __pycache__ into the tree.
set -uo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd) || exit 2

# The class + symptom text this probe exercises (class id is DERIVED from the
# product's own classifier below, never hardcoded: a registry rename must not
# turn into a false FAIL).
SYMPTOMS='gateway drain window: scheduler restarting, 503s killing ticks'
# Second, unrelated record so the ledger holds several classes' worth of data.
SYMPTOMS2='secret .env clobbered by a token rotation overwrite'
LABEL='lint-verified: commands parse and answer on the live system; this does NOT prove recovery succeeds'
TS_OLD='2026-11-16T10:00:00Z'
TS_MID='2026-11-16T11:00:00Z'
TS_NEW='2026-11-16T12:00:00Z'
CLI_TIMEOUT=30

diag=()

note() { diag+=("$1"); }
squash() { printf '%s' "$1" | tr '\n' ' ' | tr -s ' ' | cut -c1-240; }

# emit <rc> <one-line detail> — the detail MUST be the first stdout line: the
# harness uses it verbatim as the cell detail and merges stderr into stdout.
emit() {
  printf '%s\n' "$2"
  if [ "${#diag[@]}" -gt 0 ]; then
    printf '%s\n' "${diag[@]}"
  fi
  exit "$1"
}
gap() { emit 2 "environment gap: $1"; }
fail() { emit 1 "$1"; }

timeout_bin=$(command -v timeout 2>/dev/null || true)

lore_run() { # <cwd> <argv...> — combined output; caller reads $? for the rc
  local dir="$1"
  shift
  if [ -n "$timeout_bin" ]; then
    ( cd "$dir" && PYTHONPATH="$root" PYTHONDONTWRITEBYTECODE=1 \
        "$timeout_bin" "$CLI_TIMEOUT" "$@" ) 2>&1
  else
    ( cd "$dir" && PYTHONPATH="$root" PYTHONDONTWRITEBYTECODE=1 "$@" ) 2>&1
  fi
}

has_traceback() { printf '%s' "$1" | grep -q 'Traceback (most recent call last)'; }

# --- interpreter: prefer the checkout's own venv, then any python3 -----------
py=''
for cand in "$root/.venv/bin/python" "$root/venv/bin/python" \
            "$(command -v python3 2>/dev/null || true)" \
            "${HOME:-}/tools/venv/bin/python3"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then py="$cand"; break; fi
done
[ -n "$py" ] || gap "no python interpreter found (looked for .venv/bin/python, venv/bin/python, python3, ~/tools/venv/bin/python3)"

modfile=$(PYTHONPATH="$root" PYTHONDONTWRITEBYTECODE=1 "$py" -c \
  'import lore, sys; sys.stdout.write(getattr(lore, "__file__", "") or "")' 2>/dev/null)
case "$modfile" in
  "$root"/*) ;;
  *) gap "cannot import lore from the checkout under test ($root) with $py (imported: '${modfile:-<nothing>}')" ;;
esac

work=$(mktemp -d 2>/dev/null) || gap "mktemp -d unavailable"
trap 'rm -rf "$work"' EXIT

rec() { # <class_id> <timestamp> <outcomes-json> <drifted-json> <executed> <total>
  printf '{"class_id": "%s", "drifted_orders": %s, "executed_count": %s, "honesty_label": "%s", "outcomes": %s, "timestamp": "%s", "total_checks": %s}\n' \
    "$1" "$4" "$5" "$LABEL" "$3" "$2" "$6"
}

# ---------------------------------------------------------------- rung 1 -----
r1="$work/rung1"
mkdir -p "$r1/.lore" || fail "rung 1: could not create $r1/.lore"
hist="$r1/.lore/validate-history.jsonl"

# Derive the class id from the product's own classifier (offline, <1s).
match_out=$(lore_run "$r1" "$py" -m lore match "$SYMPTOMS")
match_rc=$?
if [ "$match_rc" -ne 0 ]; then
  fail "rung 1: 'lore match' exited $match_rc on the probe's symptom text: $(squash "$match_out")"
fi
class_id=$(printf '%s\n' "$match_out" | head -1 | cut -f1)
case "$class_id" in
  ''|unclassified) gap "probe premise drift: symptom text no longer classifies (match rc=$match_rc, first line: $(squash "$match_out"))" ;;
esac

# A second, unrelated class for bulk (best effort: if its text classifies to the
# same class or nothing, the ledger simply holds one class's records).
match2_out=$(lore_run "$r1" "$py" -m lore match "$SYMPTOMS2")
class2=$(printf '%s\n' "$match2_out" | head -1 | cut -f1)
if [ -z "$class2" ] || [ "$class2" = "$class_id" ] || [ "$class2" = "unclassified" ]; then
  class2="$class_id"
  note "note: second symptom text did not classify separately; ledger holds one class"
fi

{
  rec "$class2" "$TS_OLD" '["ok", "ok", "ok"]' '[]' 3 3
  rec "$class_id" "$TS_MID" '["ok", "ok", "ok", "ok", "ok", "ok", "ok"]' '[]' 7 7
  # Truncated MID-RECORD: no trailing newline, exactly what an interrupted
  # append leaves behind.
  printf '%s' "{\"class_id\": \"$class_id\", \"drifted_orders\": [1], \"outcomes\": [\"tim"
  # One non-JSON garbage line, then a well-formed record AFTER the damage.
  printf '\n%s\n' 'this line is not JSON at all: {{{ "unterminated'
  rec "$class_id" "$TS_NEW" '["ok", "error", "ok", "ok", "ok", "ok", "ok"]' '[2]' 6 7
} >>"$hist" || fail "rung 1: could not build the torn ledger at $hist"

consult_out=$(lore_run "$r1" "$py" -m lore consult "$SYMPTOMS")
consult_rc=$?
if has_traceback "$consult_out"; then
  fail "rung 1: 'lore consult' raised on a torn ledger: $(squash "$consult_out")"
fi
if [ "$consult_rc" -ne 0 ]; then
  fail "rung 1: 'lore consult' exited $consult_rc on a torn ledger: $(squash "$consult_out")"
fi
expect_consult="last lint-validated $TS_NEW"
case "$consult_out" in
  *"$expect_consult"*) ;;
  *) fail "rung 1: torn ledger hid the newest readable record — 'lore consult' output carries no '$expect_consult': $(squash "$consult_out")" ;;
esac
case "$consult_out" in
  *'(local history, not operator attestation)'*) ;;
  *) fail "rung 1: local-history line lost its honesty label: $(squash "$consult_out")" ;;
esac
case "$consult_out" in
  *'executed 6/7 checks'*) ;;
  *) fail "rung 1: local-history line lost its executed-ratio clause (expected 'executed 6/7 checks'): $(squash "$consult_out")" ;;
esac

audit_out=$(lore_run "$r1" "$py" -m lore audit --format json)
audit_rc=$?
if has_traceback "$audit_out"; then
  fail "rung 1: 'lore audit --format json' raised on a torn ledger: $(squash "$audit_out")"
fi
if [ "$audit_rc" -ne 0 ]; then
  fail "rung 1: 'lore audit --format json' exited $audit_rc on a torn ledger: $(squash "$audit_out")"
fi
case "$audit_out" in
  *'"stale_classes": 1'*) ;;
  *) fail "rung 1: torn ledger hid the post-damage record — audit reports no single stale class: $(squash "$audit_out")" ;;
esac
case "$audit_out" in
  *'"stale_reason": "lint drift: check 2 (error)"'*) ;;
  *) fail "rung 1: audit lost the post-damage record's drift reason: $(squash "$audit_out")" ;;
esac
case "$audit_out" in
  *'"status": "stale"'*) ;;
  *) fail "rung 1: audit did not flip the drifted class to stale: $(squash "$audit_out")" ;;
esac

# ---------------------------------------------------------------- rung 2 -----
# Arm A: replace the ledger with a DIRECTORY (unreadable as a file, and this
# arm also works when the probe runs as root, where chmod 000 means nothing).
r2="$work/rung2"
mkdir -p "$r2/.lore/validate-history.jsonl" || fail "rung 2: could not create the unreadable (directory) ledger path"

degrade_check() { # <label> <cwd> <output> <rc>
  local label="$1" out="$3" rc="$4"
  if has_traceback "$out"; then
    fail "rung 2 ($label): unreadable ledger produced a traceback: $(squash "$out")"
  fi
  case "$rc" in
    0) case "$out" in
         *"runbook: $class_id"*|*'"classes"'*|*'class_id'*) ;;
         *) fail "rung 2 ($label): clean rc=0 but no product output (silent no-op): $(squash "$out")" ;;
       esac ;;
    1|2) [ -n "$(printf '%s' "$out" | tr -d '[:space:]')" ] \
           || fail "rung 2 ($label): clean rc=$rc with no message at all" ;;
    *) fail "rung 2 ($label): unreadable ledger exited $rc (a traceback/abort, not a clean refusal): $(squash "$out")" ;;
  esac
}

for cmdname in consult audit; do
  if [ "$cmdname" = consult ]; then
    out=$(lore_run "$r2" "$py" -m lore consult "$SYMPTOMS")
  else
    out=$(lore_run "$r2" "$py" -m lore audit --format json)
  fi
  rc=$?
  degrade_check "directory ledger, $cmdname" "$r2" "$out" "$rc"
done

# Arm B: chmod 000 (only meaningful when NOT root — root reads it anyway).
if [ "$(id -u)" != "0" ]; then
  r3="$work/rung3"
  mkdir -p "$r3/.lore"
  rec "$class_id" "$TS_NEW" '["ok", "error", "ok", "ok", "ok", "ok", "ok"]' '[2]' 6 7 >"$r3/.lore/validate-history.jsonl"
  chmod 000 "$r3/.lore/validate-history.jsonl" || note "note: chmod 000 arm skipped (chmod failed)"
  if [ -f "$r3/.lore/validate-history.jsonl" ] && [ ! -r "$r3/.lore/validate-history.jsonl" ]; then
    out=$(lore_run "$r3" "$py" -m lore consult "$SYMPTOMS")
    rc=$?
    degrade_check "chmod 000 ledger, consult" "$r3" "$out" "$rc"
  else
    note "note: chmod 000 arm skipped (probe can still read the file)"
  fi
else
  note "note: chmod 000 arm skipped (probe runs as root; the directory arm covers unreadable)"
fi

emit 0 "torn ledger: read past 2 malformed lines, newest record still reported by consult+audit; unreadable ledger: clean degrade, no traceback"
