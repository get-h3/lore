# Traceability doctrine — the `ch:trace` marker

Rows close in this repo the same way everywhere: one `ch:trace` line that names the row,
the requirement it is judged against, the evidence a reader can re-walk, and the witness
that observed the claim. The marker is already used in `docs/qa/evidence/`, in
`docs/dogfood/`, pinned into two test files, and carried as commit
footers — but until this document no file defined its grammar, so a reader could not
verify a marker and a writer had to imitate one by example.

The grammar below was harvested from the markers that exist, not designed for them: 59
marker lines in the last 400 commit messages and 9 marker lines in the working tree (7
under `docs/`, 2 in `tests/`). Where the corpus disagrees with the intent, the corpus is
documented and the disagreement is listed under **Legacy and drift**. Nothing in this
document rewrites an existing marker.

## Where markers live

Two carriers, one grammar:

- a line in a document — an evidence summary, a dogfood report, a pinned test docstring;
- a line in a commit message footer, naming the row that commit closes.

A marker is a single line. It is not prose — a reader greps it and a checker parses it,
neither reads it as a sentence.

## The shape

```text
ch:trace row=<id> spec=<ref> wave=<ref> test=<ref> doc=<ref> prompt=<ref> evidence=<ref> witness=<form> verdict=<result> commit=<sha> memory=<key>
```

`ch:trace`, then space-separated `field=value` pairs. Value rules:

- A value never contains a space. A space ends the value — the rest of the line is read
  as the next field (one real witness was truncated exactly there).
- `+` joins the parts of one field: `evidence=/tmp/a.jsonl+/tmp/b.jsonl`.
- `:` scopes a part: `none:<reason>`, `live:<endpoint>`, `tests/test_x.py::test_y`.
- `#` anchors inside a path: `docs/PRD.md#US-2`, `README.md#L149`.
- Absence is stated, never implied: `none:<reason>`. An omitted field and a bare `none`
  are both defects, for the same reason — the reader cannot tell absence from oversight.

Canonical field order — write them in this order, `row=` first:

```text
row spec wave test doc prompt evidence witness verdict commit memory
```

Field name is what identifies a field; the order is for readers and greps.

## Fields

| field | required | carries | examples from the corpus |
|---|---|---|---|
| `row` | yes | the board row this marker closes or claims | `LORE-048`, `QA-LORE-FOREMAN-1`, `LORE-070:reproof` (a reproof pass on the same row) |
| `spec` | no | the requirement the row is judged against | `docs/PRD.md#US-2`, `README.md#status-sec`, `none:board-finding` |
| `wave` | no | the dispatch that produced the work | `.coding-hermes/waves/lore-foreman-2026-11-03-20-34-57.json#QA-LORE-FOREMAN-1`, `none:serial-doc-lane` |
| `test` | no | the test that would fail if the claim were false | `tests/test_count_guard.py::test_regression_no_venv_on_path_still_collects`, `none:docs-only-no-test-owned-surface` |
| `doc` | no | the document the row changed | `docs/INSTALL.md#L294`, `README.md,docs/INSTALL.md,CONTRIBUTING.md,skills/lore-usage/SKILL.md` |
| `prompt` | no | the brief the work was dispatched with | `/tmp/lore-20261020-202948-LORE-057-brief.txt` |
| `evidence` | no | artifacts a reader can open and re-walk | `docs/qa/evidence/run-QA-LORE-FOREMAN-1/battery-r2.jsonl`, `.gitreins/history/2026-11-03/181eac7d/verdict.json` |
| `witness` | no | an independent observation of the claim | see **Witness forms** |
| `verdict` | no | the judge result, under the binding rule below | a judge run id (`1e4c0570`) |
| `commit` | no | the commit that landed the row | `a390fe1`, or `none:worker-commit` |
| `memory` | no | the DuckBrain key that records the closure | `/project/lore/status/2026-11-03-1357`, or `none:not-written` |

Presence in the harvested corpus (68 markers): `row` 68, `evidence` 63, `witness` 60,
`spec` 38, `test` 36, `commit` 33, `verdict` 31, `memory` 26, `wave` 25, `doc` 25,
`prompt` 3. A frequently empty field is not an optional fact: `test=none:<reason>` and
`witness=none:<reason>` are statements, and they are the statements a reader most needs.

One field appears in the corpus and is not part of the canonical order:
`candidate=<sha>`, used once (RELEASE-LORE-006) in place of `spec`/`wave` — a release
candidate under consideration, not a landed fact.

## Hard rules

1. **`row=` is mandatory.** Every one of the 68 harvested markers carries it. The value
   is a board row id, `none:<reason>` for a read-only run that closes no row, or a comma
   list for rows closed together. The row id appears verbatim — a decoration a grep of
   the id would miss makes the marker untraceable.
2. **Nothing closes by reference.** "See the board row" or "see commit X" is not a close.
   The marker that closes a row carries the evidence and the witness on its own line.
   A cross-reference is a pointer; a marker is the record.
3. **`witness=none:<reason>` when no witness exists.** The reason is required. An
   omitted witness is unverifiable; `witness=none` without a reason is the same defect
   wearing a label.
4. **Memory never carries a claim alone.** `memory=` records where the closure was
   written down; the claim itself is still carried by `evidence=` and `witness=`. A
   marker whose only content is a memory key is a note about a memory, not a trace of
   work.
5. **`verdict=` counts only when bound to a commit reachable from the published tip.**
   A verdict names a judge run or a verdict label; it is evidence only if the `commit=`
   on the same marker — or the commit the marker is a footer of — is an ancestor of the
   published branch. A verdict against an unreachable commit describes abandoned work.
6. **The checker is never the author.** Whoever ran the check writes `witness=`. The
   agent that produced the change cannot witness it: its own re-run is not an
   independent observation, and the honest marker says so (`witness=none:worker-local`,
   `none:cli-output-is-our-own`) rather than dressing self-verification as a witness.
7. **One `ch:trace` line per closed row.** Two rows closed by one commit get two lines,
   each naming its own row and its own facts.

## Witness forms

| form | means | in the corpus |
|---|---|---|
| `tag:<v>@origin` | the release tag exists at the remote | `tag:v0.1.0@origin` (4) |
| `release:<v>` | a release object or artifact at that version | `release:v0.2.0` (1) |
| `http:<code>+sha256:<digest>` | an HTTP fact plus the digest of the body read | declared; real markers use `http:<code>+<ref>` (12) — see drift |
| `path@origin:<path>` | a file read at the published tip, not the local tree | declared, no occurrences |
| `ledger:<predicate>` | a query against a board or store that returned true | declared, no occurrences — carried instead by `evidence=` plus `boardctl-validate:OK` |
| `provider:<usage-page>` | a provider console reading (plan, quota, usage) | declared, no occurrences |
| `live:<endpoint>` | the running system, named precisely enough to re-probe | `live:bunker-mvp:df`, `live:CLI+fresh-bunker`, `live:pip-install-get-h3-lore==0.1.0-404` (4) |
| `none:<reason>` | no independent witness exists, and this is why | `none:docs-only-no-runtime-surface`, `none:bunker-mvp-control-endpoint-unreachable` (25 of 60) |

A witness is an observation someone other than the author could repeat: a tag at the
remote, a status code and a digest, a file at origin, a live endpoint, a ledger
predicate. "It worked on my machine" is `none:` with the reason written out.

## The one-grep verification

A row is traceable when one recursive grep for its id finds every marker for it. Two
commands, because the two carriers live in different stores:

```sh
grep -rn "<row id>" . --exclude-dir=.git     # document carriers
git log --format=%B | grep "<row id>"        # commit-footer carriers
```

Measured on this tree: `QA-LORE-FOREMAN-1` → 2 marker lines in the tree, 5 in the last
400 commit bodies; `LORE-057` → 1 and 2; `LORE-055` → 1 and 0.

The property those numbers serve: if the row id alone does not find a marker, the marker
is not traceable. A marker that only surfaces once you already know the commit sha has
told the reader nothing they did not arrive with. This is also why the row id is written
verbatim in `row=` and why a marker is a line of its own rather than a clause in a
sentence.

## Commit footers

- One `ch:trace` line per closed row, in the footer of the commit that closes it.
- The line starts at column 0, after the body, with no wrapping and no continuation
  line. A wrapped marker is two lines, and the second one is not a marker.
- Do not append a marker to the subject line. History contains commits that do; it is
  readable, but it breaks the subject's own grammar and it puts a field list where a
  log reader expects a summary.
- Do not escape the newline. Markers written into structured payloads appear in history
  as one physical line holding two markers (`memory=none:not-written\nch:trace row=…`);
  write one line per marker instead.

## Writing one

1. Close the row once, in the commit that lands the work, in the footer.
2. Copy the field order above and state every field a reader needs, using
   `none:<reason>` where a field does not apply.
3. Name a witness you did not produce yourself, or write out why none exists.
4. Check it with the one-grep: `git log -1 --format=%B | grep "<row id>"`, then
   `grep -rn "<row id>" . --exclude-dir=.git`.

## Legacy and drift

Existing markers are not rewritten — the doctrine states the grammar and reports
disagreement as legacy. Each item below is measured on the 68-marker corpus, so a reader
who meets one of these shapes knows what it is and does not mistake it for a rule.

- **Undeclared witness schemes.** `ssh:` (2, `ssh:bunker-mvp:df`), `gh:` (3,
  `gh:run+b0d759e-success`), `ci:` (1, `ci:queued-head-fb48c4d`), `boardctl-validate:`
  (1, `boardctl-validate:OK`). These are real witnesses that the accepted-forms list does
  not name, so a checker validating the scheme would reject healthy markers. Read them as
  witnesses; prefer a declared form when writing a new one.
- **Bare-token witnesses (7).** `gitreins-tier2`, `apply_lint`,
  `clean-agent-battery-2292c09c`, `lore-dogfood-2026-10-26-12-43-59` (twice),
  `lore-dogfood-run14c-local-leg`, `scripted-A-B-`. They name what was observed but not
  the form. The last is also truncated: the value ended at a space.
- **`http:` without a digest (12).** The markers carry `http:<code>+<url-or-ref>`, e.g.
  `http:404+pypi.org/pypi/get-h3-lore/json`, and one wrote the literal placeholder
  `http:200+sha256:not-recomputed`. The declared form asks for the digest of the body
  actually read; the placeholder states that a digest was not computed, which is honest
  and is not a digest.
- **Declared but unused:** `path@origin:`, `ledger:`, `provider:` — zero occurrences. The
  ledger fact these were meant to carry appears as an `evidence=` path plus
  `boardctl-validate:OK`, which is readable but not machine-checkable.
- **`candidate=` (1).** RELEASE-LORE-006 used a release-candidate sha in place of
  `spec=`/`wave=`. The marker still names its row and its witness, so it is traceable;
  the field is not part of the canonical order.
- **`verdict=` carries four kinds of value:** a judge run id (`1e4c0570`), a row id with
  a pass suffix (`QA-LORE-FOREMAN-1-R1`), a lane run id
  (`lore-qa-2026-10-07-09-11-11`), and a free-form verdict label
  (`PROMISING-BUT-ROUGH:LORE-070-reproof`). Only the first is machine-checkable. Write
  the judge run id.
- **`memory=` variants:** bare `not-written` with no `none:` prefix, and DuckBrain key
  paths (`/project/lore/status/2026-11-03-1357`). Both are readable; the absence form is
  `none:<reason>`.
- **`row=` variants:** comma lists (`LORE-060,LORE-061`; `LORE-049,LORE-050,LORE-051`)
  stay traceable by a grep for any one id; `none:read-only-dogfood` (2) is an honest
  pseudo-row for a read-only run that closes nothing, but a checker expecting an id-shaped
  value will reject it.
- **Markers in subjects and escaped newlines:** both described under **Commit footers**.
  They are counted here because those commits stay as they are.
