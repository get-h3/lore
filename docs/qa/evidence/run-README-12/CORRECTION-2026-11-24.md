# CORRECTION 2026-11-24 — digest labels swapped in README.md "Files" section

File: docs/qa/evidence/run-README-12/2026-11-24-sweep.txt
Line: "- sweep.txt — sha256 e6df324b..."  — superseded, see below.

The frozen evidence README (docs/qa/evidence/run-README-12/README.md) and the
README-12 board row's reasoning label the two sweep transcripts with each
other's sha256. Cause: the digests were captured with `sha256sum *.txt | awk
'{print $1}'`, whose shell-glob order is `-supp.txt` before `.txt`, and the
printed pair was read as (sweep, supp) instead of (supp, sweep).

Corrected digest mapping, measured at origin/main 55420a1cac062e13585c4300a1182b721fd80169
(`git show origin/main:<path> | sha256sum`):

- docs/qa/evidence/run-README-12/2026-11-24-sweep.txt
  = bb5f41e21ebd8c6a3165652b62bc530216f65f22fd7d7320ea5fb8ae42446744
- docs/qa/evidence/run-README-12/2026-11-24-sweep-supp.txt
  = e6df324b4096370fbab22c6aa98cba976ef70d688dcddce2d365c44dbab03d85

The frozen README.md and the README-12 row's reasoning state the opposite
assignment; this file supersedes those two labelings. No transcript content
changed. (A separate probe confusion during verification — `git show
origin/main:.../run-README-12/sweep.txt` returning "path does not exist" — was
a wrong filename in the probe, not a repo defect; the real filenames are
2026-11-24-sweep.txt / 2026-11-24-sweep-supp.txt.)
