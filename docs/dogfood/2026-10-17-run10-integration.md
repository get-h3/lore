# Dogfood run 10 — fix-verification second angle + fresh-machine install envelope (2026-10-17)

**Target:** lore at HEAD `9b97fa2` (same HEAD as sibling run 9 of this tick).
**Angle:** run 9 (earlier this same tick, same lane) drove the four foreman fixes on a
fresh bunker agent + the fleet QA battery. Run 10 is the SECOND same-tick angle, not a
re-sweep: (a) the install envelope measured end-to-end by hand on a fresh bunker agent
(run 9 rode the battery's wheel-based fresh-install flow), (b) the same five closed fixes
re-driven live from an independent tarball + clean-clone context, and (c) reading the
runbook TEXT the battery never parses — which surfaced the run's one P1.

**Verdict: SHIPPABLE.** All five closed fixes hold; the documented install path is proven
fresh end-to-end; the new defects are in the runbook TEXT against a sibling tool's real
flag contract, not in lore's code.

## The promise, re-stated

*"The five fixes runs 7-8 filed (LORE-049/050/054/055/056 + PERF-1) hold their
contracts when a real user drives them at HEAD, and a fresh bunker box still clears
the documented install path."*

## Fresh machine install envelope (hand-driven, not the battery's wheel flow)

Host `bunker-mvp` (las-01..04 offline; sibling-host substitution per the ephemeral-install
rule; `bunkerd` confirmed active before spawn). Agent `26678b35`, ttl 2h, destroyed after.

| leg | result |
|---|---|
| anonymous `git clone https://github.com/get-h3/lore` | rc=0, HEAD `9b97fa2` |
| bootstrap uv from astral-sh release tarball (uv absent on the box) | rc=0 each step |
| `uv venv` + `uv pip install -e ".[dev]"` (documented `uv sync --extra dev` equivalent) | rc=0, 34 packages, 2-4s |
| `python -m lore match "drain 503"` | 0.90 gateway-drain-window, rc=0 |
| `python -m lore consult --failure "gitleaks gate rejected commit"` | full runbook + fill-ins, rc=0 |
| `ruff check .` | clean |
| `validate --execute` from a brand-new clone (no `.lore/` yet) | rc=0, creates `.lore/validate-history.jsonl` 14/14 rows, `env-absent` outcomes on the tool-less box, honesty_label intact |

Total in-box wall for clone→sync→match: 3s (uv tarball download ~2m dominates any
first-touch run; once uv is present or cached, the whole thing is seconds).

## The five closed fixes, driven as real use (all at HEAD)

| fix | contract | result |
|---|---|---|
| LORE-054 `match --class` | valid 0.90 / mismatch 0.00 rc 0 / unknown rc 2 | holds |
| LORE-055 `consult` no input | rc 2 + usage error; valid no-match stays rc 0 | holds |
| LORE-049 guard-fail signatures | verbatim guard text AND bare tails (`gitleaks gate rejected commit`, `lint failed`) → gateway-guard-violation | holds |
| LORE-050 fill-in hints + executed-ratio | compile `--format md` carries per-slot fill-ins; validate-history/executed separation live | holds |
| LORE-056 `gate --record` missing parent | rc 0, ALLOW + parent auto-created + exactly one JSONL record | holds (mkdir at __main__.py:411) |
| PERF-1 compile_all | bench.py: compile_all_registry 78.68 µs/op; full `lore compile` 0.057s wall | holds, nothing user-noticeable |

## The two new findings (details on the board, rows LORE-060/061)

1. **LORE-060 (P1):** gateway-drain-window's runbook executes `logsey query --pattern X
   --since <window>` as checks 1 and 7 — but the real logsey CLI takes ONE quoted SQL
   string (`logsey query "<sql>"`); both orders exit 2 on the live CLI. The acceptance
   replay for this class quiet-fails on the tool it is written against.
2. **LORE-061 (P3):** env_absent ("tool not installed") and drifted are two different
   freshness stories at the data layer, but the plain-text runbook and the audit table
   name both "stale". A fresh-box user reading the runbook cannot tell "the box is
   missing logsey" from "the runbook violates the current tool".

## Negative arms and edges

- Clean committed clone + shared-checkout-collision: `validate --execute` → stale:no,
  env_absent clean. (Discriminating bisect: the classifier is sound; only the
  logsey-angled runbook text is broken.)
- Clean committed clones of 3 sibling classes (fast-forward-push-reject,
  docs-count-drift, worktree-reap-data-loss): all stale:no, env_absent empty. (Confirms
  the class-3 clean-clone shape.)
- `.lore/` is gitignored — a fresh clone + full validate leaves `git status` clean.
- Bare fresh box + first validate: `.lore/validate-history.jsonl` lands 14/14 rows
  honestly, env-absent outcomes, honesty_label intact.

## Residue

Ephemeral agent 26678b35 destroyed with its SSH key; residue census on bunker-mvp
unchanged (4 pre-existing agents untouched). The mtime-confusion note on the first
scripted leg (clone-tax included vs ms-only printed stamps) is a probe artifact, not a
lore defect.
