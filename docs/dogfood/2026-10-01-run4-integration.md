# Dogfood integration report — lore, 2026-10-01 (run 4)

Tick: lore-review stand-in lane (real repo `/home/kara/lore`) · HEAD at run:
`f60974c` · verdict: **per-surface — install/library/docs surfaces SHIPPABLE;
classifier recall PROMISING-BUT-ROUGH** (one seeded class misses its own
canonical error text; everything else hit or was honest about missing).

## Why a fourth run, and the angle

Runs 1–3 covered: responder entry (`match`/`compile`/`validate`, 09-24),
scribe/auditor surface (`show`/`audit`/`absorb`/`gate`/`consult`, 09-25 am),
re-validation + user-install path (09-25 run 3). Prior runs fed the tool tidy
symptom phrases. Run 4 takes the angle none touched: **the real 3 a.m.
drill** — raw log tails pasted the way an incident actually arrives — plus
the **library consumer** surface (never exercised from outside the repo) and
a **content-quality read of the flagship runbook**. The fresh-machine
install leg was repeated (skill mandates it) and extended to ALL THREE
documented install paths.

Promise under test (README): *"paste the symptom line you just saw and get
the failure class the fleet has seen before — with the evidence that
identifies it — instead of searching chat archives by memory."*

## The 3 a.m. drill (real inputs, not tidy phrases)

Three synthetic-but-realistic log tails (in `/tmp/dogfood-lore/`, not the
repo): a gateway-drain 503 tail, a git checkout-collision error tail (the
exact canonical git output), a cooldown pin-drift tail.

| input | result | verdict |
|---|---|---|
| drain tail (`503 … drain window … drain 503s kill ticks`) | `gateway-drain-window confidence=0.90`, evidence: signature + 5 keywords, **65 ms** | ✅ HIT |
| cooldown tail (`pin outranks DB write … pin drift again`) | `cooldown-pin-drift confidence=0.90` | ✅ HIT |
| git canonical collision error (`error: Your local changes … would be overwritten by checkout / Aborting`) | `unclassified 0.00`; near-miss **secret-env-clobber ranked FIRST** (0.17, "overwritten"), the true class second (0.12, "checkout") | ❌ MISS + wrong-family ranking → **LORE-041** |

The miss is sharp: the class's own description names this incident ("Two
agents operate the same checkout … staged files get swept by a sibling"),
but its keyword set (`index.lock/worktree/reap/sibling/collision/checkout/
empty commit/core.bare`) has zero overlap with git's canonical error text,
and no signature matches "would be overwritten by checkout". Worse, the
near-miss echo's top line points the responder at the *env-clobber* family.
`--explain` saves it from silence — but the first line it prints is the
wrong family.

## Consult title-mode blind spot (LORE-043)

The fleet integration feeds task titles. `"worker worktree checkout
collision during merge"` carries **3 of the class's 8 keywords** and still
returns `matched:false` — `KEYWORD_THRESHOLD = 0.6`
(`lore/classifier.py:27`) demands 5/8. The near-miss echo sees it
(`score=0.38`); the contract just refuses. Pairing the title with the
canonical git error via `--detail` (the documented integration shape:
title+detail are concatenated, `lore/__main__.py:132`) still misses. Fail-open
exit 0 means the integration silently gets nothing — no error to notice.

Contrast: `consult --failure` fed the same drain **tail** HIT with the full
7-check runbook appended. The guard-failure path (raw output text) is the
strong integration; the title path is the weak one.

## Runbook content quality (the flagship, read as a user)

`lore show gateway-drain-window`: 7 ordered checks, each with healthy vs
incident output, a decision, and **dated incident evidence** (2026-08-14
SIGKILL/214 in-flight, 2026-09-05 queue_depth=14 loss, 2026-09-16 drain
window 25–30 min). Recovery ladder matches the fleet's real doctrine
(batch config, pause-first, announce the window, never SIGKILL). This is
the artifact the README promises and it holds up. One blemish: check 2
carries `<gateway-log-path>` — the known LORE-024 placeholder class; run 4
adds cross-evidence that `consult --failure` prints that placeholder to the
operator as the literal command to run.

## Library consumer (first external consumer)

`/tmp/dogfood-lore/consumer.py` — imports `lore`, triages the tail folder,
compiles runbooks for hits, prints near-misses for misses. Whole folder:
**6 ms**; classify 0.1–5 ms/call; `compile_class` 0.1 ms warm.

Friction found: `Classification` has no `near_misses` attribute — the
CLI's `--explain` section is powered by a **separate** `near_misses(text)`
function. A first-time consumer guesses wrong exactly where the CLI looks
richest (AttributeError, same naming-split family as LORE-021's
`raw_score` vs `score=`; cross-evidence noted on that row).

## Scribe surface re-verified on synthetic trail

`absorb --window 3h --trail-file` on a 6-line logsey-contract export:
3 per-class proposals (drain ×3, cooldown ×2) + 1 honest `unclassified`
group for the line that matched nothing; `--source dogfood-run4` threaded
into every payload (LORE-020's fix verified live). `lore audit`: 14 rows,
honest `no data` freshness everywhere, summary names the lint as today's
only freshness signal.

## Install leg (fresh machine, bunker-las-03, agent de336287, destroyed)

Agent: uid 1003, Debian 12, Python 3.13.5, git 2.47.3, **no uv, no unzip**.

| step | result |
|---|---|
| anonymous clone `https://github.com/get-h3/lore` | 4 s, HEAD `f60974c` — **LORE-018 fix proven: repo is public, docs truthful** |
| uv bootstrap (GitHub release tarball, no pipe-to-shell) | 4 s |
| `uv sync --extra dev` | 5 s |
| documented pip fallback (`venv` + `pip install -e ".[dev]"`) | 15 s ✅ (fallback not rotted) |
| `uv tool install git+https://github.com/get-h3/lore` | 2 s, `lore match` live |
| smoke: `uv run pytest -q` | **353 passed in 2.0 s** |
| smoke: `uv run ruff check .` | clean |
| headline on fresh box | drain 0.90 / coffee-machine honest `unclassified` / cooldown 0.90 / unknown class exit 2 with known-classes list |

Gap → **LORE-044**: INSTALL.md presumes uv but never says how to get it;
the uv docs' own installer is a curl-piped-to-shell one-liner (unusable on
security-gated surfaces — the tarball route worked), and bare Debian lacks
`unzip`, which `uv self update` needs. One Prerequisites bullet closes it.

Environment notes (not lore defects, recorded for follow-up): `/tmp` on the
bunker host is multi-tenant — a sibling agent's `/tmp/pip.log` redirected my
first fallback attempt (Permission denied + wrong log tail). All scratch now
in `$HOME`. Separately, kara-level ssh to all bunker boxes currently fails
(`id_ed25519_bunker` regenerated Sep 30 22:29, new pubkey never installed
host-side) — the agent leg is unaffected (per-spawn keys), but the
root-rescue path documented in the bunker skills is dead until the key is
re-installed.

## Measurement (Step 2b)

`hyperfine`, warm repo: cold CLI `match` **48.1 ms ± 1.8** (20 runs),
`compile --format md` **49.2 ms ± 5.6**, `audit --format md` **41.5 ms ± 1.8**;
warm in-process classify < 0.01 ms (registry compiled once at import).
Install leg: clone 4 s → first match well under 15 s on a bare box.
**Nothing here is slow enough to be worth a PERF row** — consistent with
runs 1–3.

## Verdict

- **Install / packaging: SHIPPABLE.** All three documented paths pass fresh;
  repo public; docs truthful; test-count literals (353) match HEAD.
- **Library API: SHIPPABLE** with one naming wart (near-misses reach).
- **Classifier recall: PROMISING-BUT-ROUGH.** Signature-carrying input is
  near-instant and well-evidenced; but the fleet's most recurring collision
  class misses its own canonical error text (LORE-041) and title-mode
  integration misses at 3/8 keywords (LORE-043). Both are registry-vocabulary
  fixes, not threshold-loosening.

Maintainer's 1-hour list: (1) absorb "would be overwritten by checkout" +
"Please commit your changes or stash" as `shared-checkout-collision`
signatures (LORE-041); (2) one uv-acquisition bullet in INSTALL.md (LORE-044);
(3) decide a title-mode threshold or document that consult wants raw output
text, not titles (LORE-043).

Artifacts: this file · `docs/dogfood/diagnostics.md` §run 4 ·
`skills/lore-usage/SKILL.md` (count sync + install + near-misses + consult
caveats) · board rows LORE-041/043/044 + cross-evidence notes on
LORE-021/LORE-024 · `.coding-hermes/dogfood-log.md` entry.
