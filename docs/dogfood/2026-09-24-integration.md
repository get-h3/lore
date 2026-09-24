# Dogfood integration report — lore, 2026-09-24

Tick: lore-dogfood-2026-09-24-14-06-54 · HEAD at run: `edeb898` · verdict: **PROMISING-BUT-ROUGH**

The run was a real responder session: a fresh clone, the documented install, 25+
symptom phrasings typed the way an operator types them (not the README's exact
strings), the compiled runbooks read as triage material, the anti-rot lint run
against the live box, and a library-consumer probe over the Python API.

## Promise under test

> "A user can paste a symptom line and get the failure class the fleet has seen
> before — with evidence — instead of searching chat archives; then compile the
> runbook for that class as a proposal."

## Install — every documented path works

| Path | Command | Result | Time (this box) |
|---|---|---|---|
| Quickstart | `git clone https://github.com/get-h3/lore && cd lore && uv sync --extra dev` | rc=0, 7 packages | **0.81 s** (warm uv cache) |
| Tool install | `uv tool install git+https://github.com/get-h3/lore` | rc=0, `lore` on PATH | seconds; also cleanly upgraded a pre-existing 1ab4df1 install to edeb898 |
| Fresh machine | ephemeral bunker (bunker-las-03, bare Debian user, no sudo) | `uv sync --extra dev` OK: "Successfully installed iniconfig-2.3.0 lore-0.1.0 pluggy-1.6.0 pygments-2.21.0 ruff-0.16.8" | see below |

Fresh-machine battery (bunker-qa.sh on bunker-las-03, agent destroyed after):
`fresh-install OK` · `ci-pass OK` (native suite; act had no triggerable workflow
file — expected, the repo's CI is GitHub Actions not local act) ·
`chaos-resource PASS` (suite survives a 3 GiB memory cap) ·
`chaos-errorpath OK` (missing config → clean rc=2) · honest `N/A` cells for
upgrade (no release tags), docker-deploy/chaos-shutdown (no compose file),
chaos-corruption (no db/state files), plus 2 INFO. **Zero FAIL cells.**

The docs promised Python 3.11+ only, zero runtime deps — both held on a bare box.

## Real use — what worked, with numbers

- `lore match` — canonical fleet phrasings ("drain 503s kill ticks", "worker
  spin, -Q log stuck at 0 bytes", "sqlite header wiped after disk pressure",
  "cooldown authority drift: DB pin vs fleet.toml pin", …): **6/6 → 0.90
  signature confidence**, each with its evidence printed.
- Multi-line pasted log (3 lines, real timestamp format) → correct class at
  0.90. Leading-dash symptoms (`-Q log stuck at 0 bytes`) work — argparse does
  not eat them (tested before assuming).
- `lore compile --class gateway-drain-window --format md` — reads as genuine
  triage material: ordered read-only checks with healthy-vs-incident expected
  outputs, per-check decisions, per-check evidence citations. **10 runbooks
  compile; all carry `Status: proposal` and `Last validated: no data`** — the
  honesty labels are real, not decorative.
- `lore validate` plan mode lists what would run, executes nothing (verified:
  no execution side effects). `--execute` mode on this box honestly reported
  `check 1: error (exit 127): logsey query …` — logsey is not installed here,
  and the lint said so instead of passing. `--class does-not-exist` → exit 2
  (closed registry, as documented).
- Library consumer (external script, public API only): `classify()` returns a
  typed Classification (class_id/confidence/matched_signature/evidence with
  kind+detail); `compile_class(...).to_dict()` has a stable 10-key shape;
  `compile_all()` → 10 runbooks, all `status == "proposal"`. No internal
  imports needed, zero deps to install.

## Real use — where it fell short (LORE-016)

25+ symptoms typed as a real 3 a.m. operator. Result split by phrasing
distance from the seed vocabulary:

- Canonical seed phrasings: **6/6 classified at 0.90.**
- Multi-line log paste with seed vocabulary: classified at 0.90.
- **Stranger paraphrases of the SAME seeded classes: 5/9 → unclassified.**
  e.g. "two foremen committed to the same worktree checkout" (2/6 keywords,
  below the 0.6 gate), "git push 403 on all repos since the key rotation"
  (1/6), "container env lost the API key after .env got clobbered" (2/6),
  "host disk pressure led to duckdb file corruption" (no 'disk pressure…
  corrupt' signature window hit), "tests keep degrading, guard reports
  DEGRADED PASS" (0 signatures match — guard-degradation's signatures are
  strictly worktree-vs-main gate equivalence).

The refusal itself is doctrine ("absence is a first-class answer") and is NOT
the bug. The gap: `classify_all()` already computes the below-threshold scores
and throws them away, so the user gets zero graded signal that the fleet HAS a
class almost matching. An evidence-echo (top-3 near-misses with keyword
scores) would keep the closed registry and the honest refusal while making the
tool teachable at incident time. Filed as **LORE-016** with the full mechanism
analysis; also flagged the missing defect-class ("banned command tripped the
gateway guard" has no home in the registry).

## Performance (measured, hyperfine, this box, warm unless stated)

- `lore match` via installed tool: mean 343 ms ± 158 ms over 20 runs — but the
  box was under ambient load; range 82–646 ms and the decomposition below
  shows the tool itself is ~94 ms.
- Raw `python -m lore` (project venv, no uv wrapper): **93.6 ms ± 13.5 ms**
  (30 runs). Decomposition: bare interpreter start 35.0 ms + import
  `lore.__main__` +28.2 ms + classify/print ≈ 30 ms.
- `lore compile --format md` (all 10 classes): 249.8 ms ± 250 ms (variance is
  ambient; import dominates).
- `uv run` wrapper adds ~80 ms over the raw venv path (varies with load).

Verdict: **nothing here is slow enough for a user to notice at 3 a.m.** — the
headline operation is a fraction of a second. No PERF row filed (a win nobody
can feel is not a finding); the numbers live here for the next measurement.

## Verdict

**PROMISING-BUT-ROUGH.** The core loop (match → compile → validate) works
end-to-end on a fresh machine in under two minutes, is honest by construction
(closed registry, proposal-only, evidence printed, "no data" over zero), and
installs with zero friction. The rough edge is recall: the classifier
recognizes the fleet's own vocabulary perfectly and a stranger's wording not
yet — fixable in one file (`lore/classifier.py` already has the data it needs
to echo near-misses), which is exactly what LORE-016 asks for.
