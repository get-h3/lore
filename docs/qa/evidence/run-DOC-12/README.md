# DOC-12 — `ch:trace` traceability doctrine

Run: `lore-foreman-2026-11-17-05-00-08`. Merged at `70229d8` (worker commit `d75e18b`,
merge `70229d8`). Tier-1 gitreins verdict `f4e67dd7` (passed:true, commit `70229d8`).

## What shipped

`docs/traceability-doctrine.md` (198 lines) — the marker grammar that was already in use but
never defined:

- **shape** — `ch:trace row= spec= wave= test= doc= prompt= evidence= witness= verdict= commit= memory=`,
  canonical order, `row=` first;
- **value rules** — no spaces inside a value, `+` joins parts, `:` scopes (`none:<reason>`,
  `live:<endpoint>`, `path::test`), `#` anchors, and absence is always stated (`none:<reason>`),
  never implied by an omitted field;
- **hard rules** — `row=` mandatory; nothing closes by reference; `memory=` never carries a
  claim alone; `verdict=` counts only when bound to a commit reachable from the published tip;
  the checker is never the author;
- **witness forms** — the seven shapes that actually appear in this repo's corpus;
- **commit-footer rule** — one `ch:trace` line per closed row;
- **one-grep verification** — a recursive grep for the row id must find every marker for it;
- **Legacy and drift** — the places where the live corpus disagrees with the canonical order or
  uses an unlisted witness scheme, reported as legacy rather than rewritten.

The grammar was harvested, not designed: 59 marker lines in the last 400 commit bodies and 9 in
the working tree (7 under `docs/`, 2 in `tests/`), with witness schemes tallied as
`none:25 http:12 bare:7 live:4 tag:4 gh:3 ssh:2 boardctl-validate:1 release:1 ci:1` across the 60
that carry `witness=`. No existing marker was edited (`docs/qa/evidence`, `docs/dogfood`
untouched).

Linked from `README.md:475` in the per-topic docs list:

```
- Marker grammar: [docs/traceability-doctrine.md](docs/traceability-doctrine.md)
  (the `ch:trace` fields, witness forms and commit-footer rule).
```

## Acceptance status — one item deliberately not met

Item 3 asked for a link from **both** `AGENTS.md` Git conventions **and** the README. Only the
README link exists:

- The worker's write to `AGENTS.md` was blocked by the harness ("write to protected
  agent-instruction file(s) (AGENTS.md) approval prompt timed out without a user response") and
  the harness refuses a retry.
- An unattended tick cannot supply that consent, and the owner's standing rule is that
  `AGENTS.md` edits are his call — a tick must not propose or file them. The row is therefore
  closed on its core intent (the doctrine exists, is discoverable, and is authoritative) with
  this residual **owner-gated** item named rather than worked around.
- `AGENTS.md:23-24` keeps no doctrine bullet until the owner wants one. Nothing else in the row
  depends on it.

## Verification

```
$ ls -l docs/traceability-doctrine.md      # 12257 bytes, tracked
$ grep -n traceability README.md
475:- Marker grammar: [docs/traceability-doctrine.md](docs/traceability-doctrine.md)
$ grep -c ch:trace docs/traceability-doctrine.md   # grammar defined once, in the author's words
```

| Gate (merged tree `70229d8`) | Result |
|---|---|
| `python -m pytest -q` | `572 passed in 8.37s` |
| `bash scripts/check-test-count.sh` | PASS canonical=572 live=572; class-count=13; no stale literals |
| `pytest tests/test_readme_links.py -q` | 1 passed |
| `ruff check .` | All checks passed |
