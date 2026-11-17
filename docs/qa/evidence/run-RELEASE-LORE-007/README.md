# RELEASE-LORE-007 — releng lane workdir is a real git work tree

Row: `RELEASE-LORE-007` (P3) · filed by `releng-lane lore-releng-2026-11-16-23-09-49`
Fix date: 2026-11-17 · Host: kara (local scheduler host)
Evidence owner: `lore-foreman-2026-11-17-16-40-16`

## Defect (repro before the fix)

The scheduler hands the `lore-releng` lane the workdir named in
`~/.hermes/fleet.toml` (`projects.workdir`), which was a *board-only stand-in*
directory — not a git work tree:

```
$ ls -la /home/kara/.hermes/stand-in/releng-lane/lore
drwxrwxr-x 3 kara kara 4096 Sep 23 02:21 .
drwxrwxr-x 3 kara kara 4096 Sep 23 02:21 .coding-hermes
drwxrwxr-x 2 kara kara 4096 Oct  1 21:27 .coding-hermes/board

$ cd /home/kara/.hermes/stand-in/releng-lane/lore && git rev-parse --show-toplevel
fatal: not a git repository (or any of the parent directories): .git
rc=128
```

A release tick needs history, tags and remote refs, so every releng tick had to
hunt for `/home/kara/get-h3/lore` before it could gather a single piece of
evidence, and could not tell from its own path whether its board mirrored the
repo board.

## Fix applied (host-level, outside the repository)

Option taken from the row: **make the stand-in a real worktree** (not a symlink,
so the release lane never shares the foreman's dirty checkout).

```
$ mv /home/kara/.hermes/stand-in/releng-lane/lore \
     /home/kara/.hermes/stand-in/releng-lane/lore-standin-archive-20261117
$ git -C /home/kara/get-h3/lore worktree add \
     /home/kara/.hermes/stand-in/releng-lane/lore -b lane/releng-workdir origin/main
Preparing worktree (new branch 'lane/releng-workdir')
branch 'lane/releng-workdir' set up to track 'origin/main'.
HEAD is now at 72adb69 board: close QA-LORE-5, DOC-10, DOC-12 — wave closeout ...
```

The archived stand-in board was byte-identical to the repository board on the
canonical `origin/main` tree at the moment of the swap:

```
$ diff <(cat <archived>/.coding-hermes/board/tasks.jsonl) \
       /home/kara/get-h3/lore/.coding-hermes/board/tasks.jsonl | wc -l
0
```

so nothing was lost by dropping the stand-in copy; the lane now reads the
canonical board from the worktree.

## Acceptance verification (from the lane workdir, no cd elsewhere)

AC1 — `git rev-parse --show-toplevel` exits 0 and resolves inside get-h3/lore:

```
$ cd /home/kara/.hermes/stand-in/releng-lane/lore && git rev-parse --show-toplevel
/home/kara/.hermes/stand-in/releng-lane/lore
rc=0

$ git remote -v
origin  https://github.com/get-h3/lore.git (fetch)
origin  https://github.com/get-h3/lore.git (push)
```

AC2 — the lane resolves to the same git object store used for the release cut
(a registered worktree of the same repository, not a copy):

```
$ git -C /home/kara/get-h3/lore worktree list
/home/kara/get-h3/lore                              72adb69 [main]
/home/kara/.hermes/stand-in/releng-lane/lore        72adb69 [lane/releng-workdir]
...
```

AC3 — `scripts/release.sh --dry-run` runs from the path the lane is given:

```
$ cd /home/kara/.hermes/stand-in/releng-lane/lore && bash scripts/release.sh --dry-run
ok: working tree clean
ok: CI success on HEAD sha 72adb69d57cee674893b6b2a5928b1e9eb493ef1
ok: version 0.2.0 -> tag v0.2.0
REFUSE: tag v0.2.0 already exists.
rc=1
```

The refusal is a *release-state* answer (v0.2.0 is already tagged), read from the
same object store — exactly the evidence a releng tick could not obtain before.
It is not a workdir failure: the script resolved the tree, the remote CI state,
the version and the tag from the lane path alone.

## Residual / notes

- The old stand-in directory is preserved at
  `/home/kara/.hermes/stand-in/releng-lane/lore-standin-archive-20261117`
  (board copy only, byte-identical and now redundant).
- `lane/releng-workdir` tracks `origin/main`; a releng tick must
  `git fetch && git reset --hard origin/main` (or re-point the branch) before a
  readiness probe, otherwise the worktree reports the state at fetch time.
- No scheduler config was edited: `fleet.toml` remains a generated mirror and
  the DB row still names the same workdir path — the path itself is now a real
  work tree, which is what the row asked for.
- The lane workdir is a *separate* worktree on purpose: release probes must not
  compete with the foreman's checkout, where untracked harness residue
  (`.digest/`, rescue copies) would make every dry-run stop at "working tree
  dirty".
