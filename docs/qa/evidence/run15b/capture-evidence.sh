#!/usr/bin/env bash
# run15b evidence capture — reproduces every probe cited in the run-15b addendum.
# Scratch tree: /tmp/lore-df23 (clean clone of da91c1e). Never touches the repo under test.
set -u
SRC=/tmp/lore-df23/src
BIN=$SRC/.venv/bin/lore
OUT=/home/kara/get-h3/lore/docs/qa/evidence/run15b
mkdir -p "$OUT"

{
  echo "# audit from an EMPTY dir (no .coding-hermes/board): \$HOME isolated, cwd=/tmp/lore-df23/empty"
  echo "# binary: $BIN  (clean clone of HEAD da91c1e via uv sync --extra dev)"
  cd /tmp/lore-df23/empty && "$BIN" audit 2>&1; echo "rc=$?"
} > "$OUT/audit-empty-dir.txt" 2>&1

{
  echo "# the contradiction: same binary, same cwd, a class whose 'compiled' column says False"
  cd /tmp/lore-df23/empty && "$BIN" show secret-env-clobber 2>&1; echo "rc=$?"
} > "$OUT/show-vs-compiled-contradiction.txt" 2>&1

{
  echo "# json: runbook_compiled == incident_seen on every row (empty dir)"
  cd /tmp/lore-df23/empty && "$BIN" audit --format json | jq -c '.classes[] | {class_id,runbook_compiled,incident_seen,coverage_note}'
} > "$OUT/audit-empty-json-rows.txt" 2>&1

{
  echo "# fleet-shaped scratch board: .coding-hermes/board/{events,tasks}.jsonl"
  echo "#   evt-2 detail = {\"class_id\": \"disk-full-on-host\"}  <- NOT a registry class"
  echo "#   evt-3 timestamp 2026-06-01 (outside the 90d window)"
  cat /tmp/lore-df23/fleet/.coding-hermes/board/events.jsonl
  echo "# --- tasks ---"
  cat /tmp/lore-df23/fleet/.coding-hermes/board/tasks.jsonl
} > "$OUT/fleet-scratch-board.txt" 2>&1

cd /tmp/lore-df23/fleet && "$BIN" audit --format json > "$OUT/audit-fleet.json" 2>&1
cd /tmp/lore-df23/fleet && "$BIN" audit --format md > "$OUT/audit-fleet.md" 2>&1
cd /tmp/lore-df23/fleet && "$BIN" audit > "$OUT/audit-fleet-table.txt" 2>&1

{
  echo "# US-3 gap: a class WITH incidents and NO runbook is unrepresentable"
  echo "grep -c disk-full-on-host audit-fleet.json  -> $(grep -c 'disk-full-on-host' "$OUT/audit-fleet.json")"
  echo "grep -c disk-full-on-host audit-fleet.md    -> $(grep -c 'disk-full-on-host' "$OUT/audit-fleet.md")"
  echo "grep -c disk-full-on-host audit-fleet-table.txt -> $(grep -c 'disk-full-on-host' "$OUT/audit-fleet-table.txt")"
  echo "grep -c incident audit-fleet.md             -> $(grep -c 'incident' "$OUT/audit-fleet.md")  (md renders no incident column)"
  echo "# rows whose incident_seen=true:"
  jq -c '.classes[] | select(.incident_seen) | {class_id,runbook_compiled,coverage_note}' "$OUT/audit-fleet.json"
  echo "# a row with incident_seen=false still gets coverage_note=\"\":"
  jq -c '.classes[] | select(.class_id=="cooldown-pin-drift") | {incident_seen,coverage_note,status}' "$OUT/audit-fleet.json"
} > "$OUT/us3-novel-class-gap.txt" 2>&1

{
  echo "# exit ladder for an unknown class, four verbs, same HEAD"
  for v in "match --class nope" "show nope" "compile --class nope"; do
    printf '%-22s -> ' "$v"
    ( cd /tmp/lore-df23/empty && "$BIN" $v >/dev/null 2>&1 ); echo "rc=$?"
  done
  printf '%-22s -> ' "absorb --class nope"
  ( cd /tmp/lore-df23/empty && "$BIN" absorb --class nope --lesson x >/dev/null 2>&1 ); echo "rc=$?"
  echo "# absorb's own stderr/stdout on the same call:"
  ( cd /tmp/lore-df23/empty && "$BIN" absorb --class nope --lesson x 2>&1 ); echo "rc=$?"
} > "$OUT/absorb-exit-ladder.txt" 2>&1

{
  echo "# LORE-069 RE-PROOF — documented window mode, real prior trail"
  ( cd "$SRC" && "$BIN" absorb --window 2h --trail-file docs/qa/evidence/run14c/trail-real.txt --source dogfood-run15b ) \
    | tee "$OUT/absorb-window-update.json" \
    | jq -c '.[] | {class_id,action,added:(.added|length),changed:(.changed|length),removed:(.removed|length)}'
  echo "# single path (--class/--lesson) for contrast:"
  ( cd "$SRC" && "$BIN" absorb --class gateway-drain-window --lesson "logsey checks need a fresh index" ) \
    | jq -c '{class_id,action,added:(.added|length),changed:(.changed|length),blocks:(.blocks|length),lesson}'
} > "$OUT/absorb-lore069-reproof.txt" 2>&1

{
  echo "# PERF-2 RE-PROOF at the GROWN ledger (5,127 rows / 1.4 MB; run 14 measured 144ms at 3,161 rows)"
  echo "## single-pass: opens of the ledger during ONE audit (14 before the fix)"
  ( cd /home/kara/get-h3/lore && strace -f -e trace=openat -o /tmp/lore-df23/strace.txt .venv/bin/lore audit --format json >/dev/null 2>&1
    echo "opens(5127-row ledger) = $(grep -c 'validate-history.jsonl' /tmp/lore-df23/strace.txt)" )
  ( cd /tmp/lore-df23/scale10 && strace -f -e trace=openat -o /tmp/lore-df23/strace10.txt "$BIN" audit --format json >/dev/null 2>&1
    echo "opens(51270-row ledger) = $(grep -c 'validate-history.jsonl' /tmp/lore-df23/strace10.txt)" )
  echo "## warm timings (hyperfine, this box)"
  ( cd /home/kara/get-h3/lore && hyperfine -w 3 -r 12 '.venv/bin/lore audit --format json > /dev/null' 2>&1 | grep -E 'Time \(mean' | sed 's/^/5127rows  /' )
  ( cd /tmp/lore-df23/scale10 && hyperfine -w 2 -r 6 "$BIN audit --format json > /dev/null" 2>&1 | grep -E 'Time \(mean' | sed 's/^/51270rows /' )
  ( cd /tmp/lore-df23/empty && hyperfine -w 2 -r 6 "$BIN audit --format json > /dev/null" 2>&1 | grep -E 'Time \(mean' | sed 's/^/no-ledger /' )
} > "$OUT/perf-perf2-reproof.txt" 2>&1

ls -l "$OUT"
