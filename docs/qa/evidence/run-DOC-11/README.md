# DOC-11 — the weekly validate timer is operator-armed, and the docs now say so

Row: `DOC-11` (P4) · measured 2026-11-16 at origin/main 7788fb4 · fixed at the merge of
`wt/DOC-11` (worker commit 0992413) · evidence owner `lore-foreman-2026-11-17-16-40-16`

## The rot

Five doc sites asserted, absolutely, that no weekly lint schedule exists. On this box it
does: a user systemd timer has been re-validating the checkout every Monday since
2026-11-15, and the lint history has been accumulating in `.lore/validate-history.jsonl`.

Sites (pre-fix text):

| file | pre-fix claim |
|---|---|
| README.md (Status, `lore validate` bullet) | "No schedule is installed yet (a separate task owns the weekly timer)." |
| README.md (Status, closing paragraph) | "Still planned: runbook-store materialization and the scheduled weekly lint." |
| docs/INSTALL.md (CLI coverage) | "the weekly *schedule* that would run it for you is not installed (that is a separate task)." |
| docs/INSTALL.md (What this tool is NOT) | "**No scheduled lint / re-validation yet.** … nothing runs on a schedule." |
| docs/RUNBOOK-STORE.md (re-validation contract) | "Only its weekly schedule is uninstalled: nothing runs the lint on a timer today …" |

## Live reality (probed at fix time)

```
$ systemctl --user list-timers --all | grep -i lore
Mon 2026-11-23 07:30:00 -05    5 days Mon 2026-11-16 07:30:00 -05       1 day 4h ago lore-validate.timer                           lore-validate.service

$ cat ~/.config/systemd/user/lore-validate.timer
[Unit]
Description=lore runbook re-validation every Monday 07:30

[Timer]
OnCalendar=Mon *-*-* 07:30:00
Persistent=true

[Install]
WantedBy=timers.target

$ cat ~/.config/systemd/user/lore-validate.service
[Unit]
Description=lore weekly runbook re-validation (validate --execute, proposal-only writes)
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/kara/get-h3/lore
ExecStart=/home/kara/.local/bin/lore validate --execute --format md
Environment=HOME=/home/kara
StandardOutput=append:/home/kara/.local/share/lore/weekly-validate.log
StandardError=inherit

$ wc -l ~/.local/share/lore/weekly-validate.log
138 /home/kara/.local/share/lore/weekly-validate.log

$ tail -4 ~/.local/share/lore/weekly-validate.log
  stale_reason: none
  honesty: lint-verified: commands parse and answer on the live system; this does NOT prove recovery succeeds

history: 13 record(s) appended to .lore/validate-history.jsonl (local lint history, not operator attestation)
```

Scope note that the docs must keep: the timer is **operator-armed, outside the repo**
(user units in `~/.config/systemd/user`); the 0.2.0 release ships no installer, timer or
service (`CHANGELOG.md:25`), so a fresh source install has none until an operator arms it.

## What the fix changed

- README.md: new Status bullet **"Weekly re-validation: the schedule is operator-armed,
  not shipped."** naming the unit files, `OnCalendar=Mon *-*-* 07:30:00`,
  `Persistent=true`, the `ExecStart` command and the log path; closing paragraph now says
  only runbook-store materialization is still planned.
- docs/INSTALL.md: CLI-coverage paragraph corrected; the "No scheduled lint" bullet
  becomes **"The weekly lint runs on a timer you arm, not one we ship."** with the same
  verified unit/cadence/log facts.
- docs/RUNBOOK-STORE.md: the re-validation contract states the schedule is operator-armed
  rather than shipped, and names this fleet's timer.

## Acceptance re-check (all commands run at the fix commit)

```
$ grep -rn "nothing runs on a schedule" README.md docs/            # (no output)
$ grep -rn "No schedule is installed yet" README.md docs/          # (no output)
$ grep -rn "not installed (that is a" README.md docs/              # (no output)
$ grep -rn "No scheduled lint / re-validation yet" README.md docs/ # (no output)

$ grep -rn "lore-validate.timer|OnCalendar=Mon|Persistent=true|weekly-validate.log" README.md docs/
README.md:433  `~/.config/systemd/user/lore-validate.timer` with
README.md:434  `OnCalendar=Mon *-*-* 07:30:00` and `Persistent=true`, plus
README.md:437  appended to `~/.local/share/lore/weekly-validate.log`. Arm it per box with
docs/INSTALL.md:447  `~/.config/systemd/user/lore-validate.timer` with
docs/INSTALL.md:448  `OnCalendar=Mon *-*-* 07:30:00` and `Persistent=true`, plus
docs/INSTALL.md:451  to `~/.local/share/lore/weekly-validate.log`. Arm it per box with
docs/RUNBOOK-STORE.md:134  runs a user systemd timer (`lore-validate.timer`, Mon 07:30,
docs/RUNBOOK-STORE.md:135  `Persistent=true`) that runs `lore validate --execute --format md` weekly and

$ uv run pytest -q
572 passed in 5.35s

$ PATH=<worktree>/.venv/bin:$PATH bash scripts/check-test-count.sh
PASS: test-count guard: canonical=572 matches live=572; class-count=13; no stale count literals in living docs
```

No README URL was added (the README link scanner is unchanged and green), and no
test/class count literal was introduced: every count above is derived by the guard.

## Residual

- The unit files stay outside the repository by design (release scope unchanged); the docs
  are the only repo-side carrier of the operator-armed fact.
- Nothing in this row arms the timer on a new box — that remains an operator step
  (`systemctl --user enable --now lore-validate.timer`), which the docs now spell out.
