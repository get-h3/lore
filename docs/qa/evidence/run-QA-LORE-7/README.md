# QA-LORE-7 — verification-only closeout evidence (2026-11-25)

Row: QA-LORE-7 — `.gitignore *.log` shadowing 10 tracked `docs/qa/evidence` log files.
Fix landed by sibling tick `lore-foreman-2026-11-23-04-28-28` (wave manifest
`.coding-hermes/waves/lore-foreman-2026-11-23-04-28-28.json`, worker branch `wt/QA-LORE-7`):

- fix commit `75ca51a` 2026-11-22 23:41:18 -0500 — "fix: unshadow tracked QA evidence logs from the *.log scratch rule. Addresses QA-LORE-7." (touches .gitignore, CONTRIBUTING.md, README.md, docs/INSTALL.md, scripts/test-count.txt, skills/lore-usage/SKILL.md)
- merge commit `2b59ca0` 2026-11-22 23:44:55 -0500 — "Merge wt/QA-LORE-7: stop .gitignore *.log from shadowing tracked QA evidence logs"

This tick (`lore-foreman-2026-11-25-05-35-00`) verified the landed fix against the published
tip `3e8e3497b44ef172f192e21d505114cc79450994` (= `origin/main` at verification time;
`git merge-base --is-ancestor 75ca51a origin/main` rc=0; `2b59ca0` rc=0) and closed the row.

## The landed rule (.gitignore lines 19-24)

```
# local scratch
/tmp/
*.log
# tracked QA evidence logs are product evidence, not scratch (QA-LORE-7)
!docs/qa/evidence/**/*.log
```

## AC probes (all run 2026-11-25T05:35-05:43Z, tree at 3e8e349)

AC clause: after the fix `git ls-files -i -c --exclude-standard` lists none of the 10 logs,
and a fresh `git archive` tree equals HEAD tree.

1. Tracked-but-ignored census — EMPTY (was the 10-run delta at filing):

```
$ git ls-files -i -c --exclude-standard
$                       # (no output; rc=0)
```

2. The 10 evidence logs remain TRACKED (not untracked):

```
$ git ls-files 'docs/qa/evidence/*.log' 'docs/qa/evidence/**/*.log' | wc -l
10
```

3. Future evidence logs are addable again (behavioral add probe; file touched, dry-run,
   then removed — tree clean after):

```
$ touch docs/qa/evidence/run99-probe.log
$ git status --porcelain docs/qa/evidence/run99-probe.log
?? docs/qa/evidence/run99-probe.log
$ git add -n docs/qa/evidence/run99-probe.log
add 'docs/qa/evidence/run99-probe.log'
$ rm docs/qa/evidence/run99-probe.log
```

4. Scratch `*.log` outside evidence is STILL ignored (no collateral scope break):

```
$ git check-ignore -v scratch-run.log
.gitignore:22:*.log	scratch-run.log
```

5. Fresh git archive tree equals HEAD tree (the QA sync binding:

```
$ diff <(git ls-tree -r --name-only HEAD | sort) \
       <(git archive HEAD | tar -tf - | grep -v '/$' | sort)
ARCHIVE TREE EQUALS HEAD TREE
```

## Gates at 3e8e349 (before the close; full suite finished BEFORE the judge)

```
$ uv run pytest -q tests/test_qalore7_gitignore_evidence.py
2 passed in 0.85s
$ bash scripts/check-test-count.sh
PASS: test-count guard: canonical=586 matches live=586; class-count=13; no stale count literals in living docs
$ uv run ruff check .
All checks passed!
$ uv run pytest -q
586 passed in 14.97s
```

## GitReins lifecycle state at close

- `.gitreins/tasks.yaml` carried task `QA-LORE-7` created `2026-11-23T04:35:01Z`
  by the sibling wave with status `in_progress` — completion never ran.
- No verdict artifact under `.gitreins/history/` names task_id QA-LORE-7 (grep empty).
- This tick completed the stalled lifecycle: `gitreins task complete QA-LORE-7` graded the
  tree at this evidence commit; the verdict run is recorded in the board row's evidence.
