# QA-LORE-FOREMAN-1 — bunker-mvp disk block, verified live, remediation held for a foreground session

Row: `QA-LORE-FOREMAN-1` (P1, source `qa-dagger`, filed 2026-11-03T13:53:46Z)
Filed claim: `[run_battery] FAIL — launch refused: PREFLIGHT FAIL: target host bunker-mvp disk
usage 100% exceeds 94% launch threshold. No cells executed.`
Tick: `lore-foreman-2026-11-03-13-57-46`

## 1. Independent verification of the block (run by the foreman, not copied from the row)

Host: `bunker-mvp` = Hetzner CI/QA host `78.46.173.180` (ssh alias `bunker-mvp`, user `root`,
NOPASSWD sudo; `active_server: bunker-mvp` in `~/.bunker/config.yaml`).

```sh
ssh bunker-mvp 'hostname; df -h /'
# bunker-mvp
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       150G  141G  3.6G  98% /
```

The 94% preflight threshold is therefore still tripped. The block is LIVE, not stale, and the
row's premise is confirmed at tick time.

## 2. Host anatomy (why the disk is full)

```sh
ssh bunker-mvp 'du -xh --max-depth=1 / | sort -rh'
#   113G /home        <- per-agent bunker homes (rootless docker), 28 directories
#    14G /var         <- /var/lib 5.2G, /var/log 4.6G (journal 3.0G), /var/backups 4.0G
#   4.8G /root        <- go 2.5G, .cache 814M, qa-run-20261009 496M
```

This is the documented bunker failure shape: the bulk is agent homes, not logs. Log churn alone
(≈2.4G reclaimable by journal vacuum) would NOT clear the threshold with margin and would leave
the leak armed.

### Registry vs disk census

```sh
bunker list --server bunker-mvp --status all     # 8 agents, all "running"
```

Registered and writing within the last two hours (KEPT):

| agent id | disk | files < 2h | newest file |
|---|---|---|---|
| cc35ae03 | 3912M | 20684 | 2026-11-03 13:58 |
| 3743b57d | 4945M | 43573 | 2026-11-03 13:46 |
| 74baf031 | 3521M | 11242 | 2026-11-03 13:25 |
| e384a8c7 | 5446M | 43706 | 2026-11-03 12:29 |
| 272c7abb | 3380M | 6119 | 2026-11-03 13:13 |
| acaf858e | 4892M | 42392 | 2026-11-03 13:46 |
| 00a6ab6c | 3520M | 11242 | 2026-11-03 13:24 |
| ae196e40 | 6971M | 151430 | 2026-11-03 13:38 |

Total kept ≈ 35.8G.

Unregistered leftovers — present in `/home` but ABSENT from the bunkerd registry, zero processes
for the owning uid, no `/run/user/<uid>` (i.e. no live rootless dockerd), newest file ≥5h old
(DELETION CANDIDATES ≈ 75.7G):

| agent id | disk | newest file |
|---|---|---|
| 4160d972 | 11834M | 2026-11-03 07:07 |
| 4a63cded | 7507M | 2026-10-31 22:53 |
| 6046f72e | 7395M | 2026-10-31 06:10 |
| 2ecf416b | 6558M | 2026-11-01 01:31 |
| ac09623c | 6899M | 2026-11-02 20:35 |
| d5c1c615 | 5996M | 2026-11-02 16:02 |
| 9c7f0037 | 5408M | 2026-11-02 19:37 |
| 6282a0f5 | 5355M | 2026-11-02 23:52 |
| d24c8922 | 4816M | 2026-11-01 09:52 |
| 3a32e5eb | 4691M | 2026-11-02 16:30 |
| 08bc722c | 2781M | 2026-11-03 08:36 |
| 03ecf3b5 | 2363M | 2026-11-01 04:57 |
| 7f233985 | 1141M | 2026-10-31 13:20 |
| 3f3e8f96 | 1031M | 2026-11-01 00:26 |
| e3d0e434 | 825M | 2026-11-01 20:52 |
| fdb16e3b | 667M | 2026-11-01 19:54 |
| bed19365 | 663M | 2026-11-01 10:58 |
| 04235b51 | 600M | 2026-11-03 04:40 |
| a8a9be27 | 511M | 2026-11-03 01:14 |
| 28309542 | 448M | 2026-11-01 03:57 |

`08bc722c` and `04235b51` also have destroy archives in `/var/backups/bunker/`; the archive is
the only intact copy of those two homes, so the archive tier is retained (see below).

## 3. What this tick did NOT do, and why

The reclaim was staged as a single root script (delete the 20 unregistered homes, vacuum the
journal to 500M, prune dangling docker images) and refused by the unattended approval gate —
this tick is a scheduler/API-surface session, and a destructive remote `rm -rf` mass delete
cannot be authorized without the operator present. Silence is not consent, so nothing was
deleted, no space was freed, and the row stays PENDING.

State after this tick is byte-identical to the state before it: `df -h /` still reports
`141G used, 3.6G avail, 98%`, 28 homes still present, all 6 archives still present.

Retained deliberately: `/var/backups/bunker/*.tar.gz` (4.0G, six tarballs dated 2026-11-03) are
the documented backup-of-record for destroyed temp agents and the only intact copy of the two
homes that also survived on disk. Do not prune them as part of this reclaim.

## 4. Exact remediation for a foreground session (or an authorized tick)

```sh
ssh bunker-mvp
# 1. re-confirm the registry (8 running agents; NEVER delete a registered id)
bunker list --server bunker-mvp --status all

# 2. delete ONLY the unregistered, idle homes (the 20 ids in the table above)
for id in 4160d972 4a63cded 6046f72e 2ecf416b ac09623c d5c1c615 9c7f0037 6282a0f5 \
          d24c8922 3a32e5eb 08bc722c 03ecf3b5 7f233985 3f3e8f96 e3d0e434 fdb16e3b \
          bed19365 04235b51 a8a9be27 28309542; do
  d=/home/bunker-$id
  [ -d "$d" ] || { echo "absent $id"; continue; }
  uid=$(stat -c %u "$d")
  [ "$(pgrep -u "$uid" | wc -l)" -eq 0 ] || { echo "SKIP busy $id"; continue; }
  rm -rf "$d" && echo "deleted $id"
done

# 3. housekeeping (≈2.4G journal + ≈1.0G dangling images)
journalctl --vacuum-size=500M
docker image prune -f

# 4. prove the reclaim
df -h /          # expected ≈65G used / 150G ≈ 43%
```

Expected result: ~76G freed from homes + ~3.4G housekeeping → usage ≈43%, well under the 94%
preflight threshold and under the 80% band where the leak loop re-pins the disk within minutes.

## 5. Follow-up that belongs to the host, not this row

Twenty leaked homes at ~76G in ≤3 days means `bunkerd destroy` is not reaping agent homes
(archive written, home retained, or destroy never issued). That is a bunkerd retention defect
on the shared CI host, not a lore defect. It will re-fill the disk. File it against the bunker
lane if it recurs after this reclaim.
