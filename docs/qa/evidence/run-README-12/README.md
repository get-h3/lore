# README-12 evidence — lore README health sweep 2026-11-24

Lane: lore-readme (scheduler tick lore-readme-2026-11-24-20-44-23)
Audited tip: 377baa0d93dfa020cc738ca4cd7527a5d5876bc8 (origin/main parity verified pre-sweep)
README.md content sha256: c40222d1a0df7206bcd9c169970bd8a912b47ada8b16b48640727c6cb97494bd

## Finding (P5)

README.md:27 promises "Every command below was run and its output pasted
verbatim" and README.md:103 calls the compile sample "Abridged real output",
but the compile `--format md` sample at README.md:116-121 renders Check 1's
command as a 4-space-indented line, while the binary prints the command inside
a ```sh fenced block (lore/runbook.py:128 prints "```sh" for every rendered
check; fence introduced 7cbdb70 2026-09-23, so the sample never matched
current output).

Exact probes (full transcripts below, frozen byte-for-byte this sweep):

- `uv run python -m lore compile --class gateway-drain-window --format md`
  prints:

      ### Check 1 (read-only)

      ```sh
      logsey query "SELECT message, ts FROM logs WHERE message LIKE '%drain 503%' AND ts >= now() - INTERVAL 30 MINUTE"
      ```

  (transcript 2026-11-24-sweep.txt:79-84)

- README.md:116-121 in the same tree prints:

      ### Check 1 (read-only)

          logsey query "SELECT message, ts FROM logs WHERE message LIKE '%drain 503%' AND ts >= now() - INTERVAL 30 MINUTE"

  — the fence lines are gone and the command is indented. The healthy/
  incident/decision lines match live output; only the check-command rendering
  drifted. Severity P5: presentation fidelity of a pasted sample under an
  explicit verbatim promise (doc severity P5 by ruling 2026-09-30).

Not filed here (covered elsewhere this sweep): README.md Status / docs/RELEASE.md
version staleness at the v0.3.0 cut is DOC-10-R2's premise; re-probed live this
sweep (README.md:381-390 still says stamp 0.2.0 / "Two tags exist" / "7 commits
past v0.2.0"; measured now: stamps 0.3.0 pyproject.toml:7 lore/__init__.py:3,
tags v0.1.0/v0.2.0/v0.3.0, `git rev-list --count v0.2.0..HEAD` = 90, v0.3.0..HEAD = 36)
and recorded ON that row as a still-live note.

## Everything else measured this sweep (all claims held)

- Freshness/executed matrix: `lore --help`, 4 match arms, compile md + unknown
  class (exit 2), pytest (586 passed — matches README.md:396), ruff (All checks
  passed!), consult --json + failure fail-open + title mode + LORE-055 exit 2,
  show / show --evidence / audit table+json / validate plan+md / gate ALLOW+DENY,
  absorb propose-only ("nothing proposed, nothing written", exit 0). All exit
  codes and outputs quoted in the transcripts.
- Stranger tool install: `env HOME=<fresh> uv tool install --force
  git+https://github.com/get-h3/lore` → get-h3-lore==0.3.0, `lore match`
  works (README-11-R2's --force path holds); `uv tool upgrade get-h3-lore`
  → "Nothing to upgrade".
- Links: readme-link-check → local_missing=0 external_non_200=0 (12 local, 1
  external). Anchors: check-md-anchors → anchors_checked=1 broken=0.
- README audit docs (bucket column, `[bucket] unclassified`, `bucket: true`
  JSON key) match live `lore audit` output — README-3's fix holds.
- CI: `gh run list` top three on main all completed/success (2026-11-24).

## Files

- sweep.txt — sha256 e6df324b4096370fbab22c6aa98cba976ef70d688dcddce2d365c44dbab03d85
- sweep-supp.txt — sha256 bb5f41e21ebd8c6a3165652b62bc530216f65f22fd7d7320ea5fb8ae42446744
- The single marker token inside sweep-supp.txt is README.md's own prose
  quoting its marker-grammar link (README.md:526), not an authored marker.

ch:trace row=README-12 spec=README.md#quickstart wave=none:serial-docs-tick test=none:no-arm-guards-sample-output-fidelity doc=README.md evidence=docs/qa/evidence/run-README-12/README.md witness=none:repo-local-doc-claims-no-external-endpoint verdict=none:open-finding commit=none:open memory=none:not-written
