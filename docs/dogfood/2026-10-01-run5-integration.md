# Dogfood integration report — lore, 2026-10-01 (run 5)

Tick: lore-dogfood · HEAD at run: `4265973` · verdict: **SHIPPABLE**.

## Why a fifth run, and the angle

Runs 1–4 covered: responder entry (`match`/`compile`/`validate`, 09-24),
scribe/auditor surface (09-25 am), re-validation + user-install path (09-25
run 3), the 3 a.m. raw-log drill + library consumer + all three install paths
(run 4, same morning). Run 4's rows LORE-041/044 were fixed and merged at
07:21 today. Run 5 therefore takes two angles:

1. **Verify the just-landed fixes at HEAD as a user** (not as the test suite).
2. **The operator-approval surface** — `docs/RUNBOOK-STORE.md` (the two-homes
   proposal) and what happens to a `validate --execute` result afterward. No
   prior run chased the validation *result* after the command returned.

## Fix verification at HEAD

- **LORE-041 (canonical git collision text)** — pasted git's exact
  `error: Your local changes … would be overwritten by checkout` block:
  `shared-checkout-collision confidence=0.90, evidence: signature:would be
  overwritten by checkout; keyword:checkout`. `--explain` shows
  `near-misses: none`. Run 4's wrong-family ranking is gone. VERIFIED.
- **LORE-044 (INSTALL.md documents obtaining uv)** — the "Installing uv"
  section exists with the curl installer, gated-surface guidance, and
  self-update unzip note; followed verbatim on the fresh box below. VERIFIED.
- **Consult failure-mode** — `lore consult --failure <git collision error>`
  names the class and echoes all 3 checks. Works as documented.

## The validation result has no memory (LORE-045, P2)

Ran `lore validate --execute` on the live checkout: every check `outcome: ok`,
honesty label `lint-verified`. Then, seconds later on the same box:

- `lore consult --failure` → `last_validated=never`
- `lore compile --format md` → `Last validated: no data (never validated)`

The lint run printed to stdout and evaporated — the exact disease
RUNBOOK-STORE.md exists to cure, currently applied to lore's own output.
README:366 honestly discloses "no code path writes last_validated in v0.1";
the UX consequence is the tool's core promise ("does the fix still run?") has
no memory between invocations. Filed as LORE-045 with a persist-to-local-
history fix direction.

## Small papercut (LORE-046, P3)

A confident match (`gateway-drain-window confidence=0.90 …`) still prints the
`unclassified confidence=0.00` line right under it. Two answers on one screen;
a scripting consumer splitting on lines sees two class rows.

## Perf (Step 2b)

`uv run lore match` cold (fresh venv, per-invocation): ~60 ms wall
(5 sequential runs: 0.304 s total). Warm classify <0.01 ms (run 4). Fresh-box
pytest: 364 passed in 1.96 s. Nothing user-noticeable — no PERF row, per the
skill's law.

## Fresh-machine install leg

Designated host bunker-las-03 rejected the agent key (publickey refused for
both kara@ and root@ probes — SKIPPED-install-bunker evidence recorded);
substituted sibling **bunker-las-01** (registered, bunkerd active). Fresh
agent `23ada9bf` (destroyed after the run):

- `git clone https://github.com/get-h3/lore` — anonymous clone worked (repo
  public), HEAD `4265973` matching local.
- Fresh Debian 13, Python 3.13.5, no uv preinstalled. Followed INSTALL.md's
  documented path top-down: curl-to-shell uv installer, then
  `uv sync --extra dev` → **RC=0, 11 s** total.
- Smoke on the same fresh box: both headline matches 0.90 ✓, honest
  unclassified ✓, `uv run pytest -q` → 364 passed in 1.96 s ✓,
  `uv run ruff check .` → All checks passed ✓.
- Agent destroyed and verified gone from the server list.

## Value judgment

Does it work? Yes — the promised loop (symptom → class with evidence →
runbook proposal → live lint) completes end to end, and today's fixes hold at
HEAD. Is it usable? Yes — time-to-first-success on a truly fresh box is about
30 s (clone + uv bootstrap + sync + first match). Is it trustworthy? The
honesty labels say what they mean and mean what they say. The one real gap is
memory: a validated runbook still claims "never validated" a minute later.
That is polish on a system that is otherwise doing its job.

**Verdict: SHIPPABLE.**
