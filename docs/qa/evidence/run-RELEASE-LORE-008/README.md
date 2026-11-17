# RELEASE-LORE-008 — deployed CLI upgraded to the released tag

Evidence run: `lore-foreman-2026-11-17-05-00-08` (foreman-direct, host `kara`).
Row: `RELEASE-LORE-008` — "deployed CLI lags the release — host uv tool get-h3-lore
reports 0.1.2 while v0.2.0 is published, and the install floats on the default branch".

## Before (measured, not inferred)

| Witness | Value |
|---|---|
| `command -v lore` | `/home/kara/.local/bin/lore` → `~/.local/share/uv/tools/get-h3-lore/bin/lore` |
| installed dist-info | `get_h3_lore-0.1.2.dist-info` (only dist present) |
| `site-packages/get_h3_lore-0.1.2.dist-info/METADATA` | `Version: 0.1.2` |
| `site-packages/lore/__init__.py` | `__version__ = "0.1.2"` |
| `uv-receipt.toml` requirement | `{ name = "get-h3-lore", git = "https://github.com/get-h3/lore" }` — **no ref: floats on the default branch** |

## Action — the exact, reproducible install command

```
uv tool install --force "git+https://github.com/get-h3/lore@v0.2.0"
```

Output (tail):

```
Building get-h3-lore @ git+https://github.com/get-h3/lore@165cc8f6d354d9ed57d58635c1ad482d0e755cf2
Installed 1 package in 23ms
 + get-h3-lore==0.2.0 (from git+https://github.com/get-h3/lore@165cc8f6d354d9ed57d58635c1ad482d0e755cf2)
Installed 1 executable: lore
```

`git -C /home/kara/get-h3/lore rev-parse v0.2.0^{commit}` → `165cc8f6d354d9ed57d58635c1ad482d0e755cf2`,
i.e. the install resolved the released tag to the released commit.

## After (verified live)

| Witness | Value |
|---|---|
| `uv-receipt.toml` requirement | `{ name = "get-h3-lore", git = "https://github.com/get-h3/lore?rev=v0.2.0" }` — **names the released tag** |
| dist-info present | `get_h3_lore-0.2.0.dist-info` (the 0.1.2 dist is gone; no duplicate install) |
| `get_h3_lore-0.2.0.dist-info/METADATA` | `Version: 0.2.0` |
| `site-packages/lore/__init__.py` | `__version__ = "0.2.0"` |
| `command -v lore` | `/home/kara/.local/bin/lore` (the uv tool install) |

Live exercise (not metadata-only), run from `/tmp` so no checkout can shadow site-packages:

```
$ lore audit --format json          # rc=0, prints the 14-class registry JSON
$ lore match "tests flaked on a stale toolchain on the shared runner"   # rc=0
$ lore consult "shared runner rebuilt its toolchain mid-wave" --json    # rc=0
```

## Residuals / notes

- `lore match` has no `--json` flag (a first probe passed `--json` and got rc=2 from
  argparse). That is shipped-surface behaviour, not a deployment defect; the live
  exercise above uses the flags the installed CLI actually accepts.
- `lore match` returned `unclassified` for the toolchain-drift phrasing. That is a
  classifier-coverage observation, out of scope for this deployment row and not filed here
  (the board already carries the taxonomy work; filing a duplicate would be noise).
- The pin is per-host state (`~/.local/share/uv/tools/get-h3-lore/uv-receipt.toml`), not
  repository content — it is recorded here because the receipt is the only proof of the
  install's provenance.
