# INFRA-LORE-045 — boardctl close gate now validates the stored verdict's task_id and commit

Fix commit (product): `cca45c81457ab22caff3bc108b3ea63755bf39be` on coding-hermes/boardctl
(`fix(evidence-gate): read the stored verdict at completion -- refuse runs graded for another task or commit. Addresses INFRA-LORE-045.`),
pushed to origin/main (parity 0), installed at ~/.local/bin/boardctl (go version -m vcs.revision=cca45c81457ab22caff3bc108b3ea63755bf39be, built 2026-11-22T10:37:35Z).

## Defect premise (re-verified 2026-11-22)
`.gitreins/history/2026-11-21/d46cce23/verdict.json` in this repo names task_id `LORE-EXPORT-1` at commit
eda0c96f9a09a37361b4eebd11356300fcd66699, while board row RELEASE-LORE-009 had bound that run at close time with exit 0 —
the old gate proved only that the run DIRECTORY existed (boardctl internal/board/evidence_gate.go validateCompletionProvenance).

## Acceptance arms (installed binary cca45c8, scratch board at /tmp/lore-fm-arm built from this repo's board + the real d46cce23 verdict)
1. FOREIGN RUN — `boardctl update INFRA-LORE-045 --status complete --commit-hash 75c094b91ef8bd5837a7c4f94887c87d7ec4fcb9 --evidence-run-id d46cce23`
   -> exit 1:
   `boardctl: completion REFUSED: evidence run d46cce23 graded task LORE-EXPORT-1 at commit eda0c96f9a09a37361b4eebd11356300fcd66699; completion of INFRA-LORE-045 requires a run graded for task INFRA-LORE-045`
   Row stayed `pending`. (Exactly the required "names the task_id mismatch" behaviour.)
2. MATCHING RUN — verdict fixture `{"task_id": "INFRA-LORE-045", "commit": <scratch HEAD>, "passed": true}` in .gitreins/history/2026-11-22/fm-verify-match/
   `boardctl update INFRA-LORE-045 --status complete --commit-hash <scratch HEAD> --evidence-run-id fm-verify-match`
   -> exit 0: `updated task INFRA-LORE-045: status, commit_hash, detail, updated_at`; row reads status=complete with that commit_hash.
3. MISSING VERDICT — `--evidence-run-id fm-noverdict` with a run dir that carries no verdict.json
   -> exit 1: `completion REFUSED: evidence run "fm-noverdict" carries no verdict.json (expected .../.gitreins/history/fm-noverdict/verdict.json); a bound run must store its verdict at .gitreins/history/<date>/<run-id>/verdict.json`
   -> the same call with `--force` exits 0 (documented deliberate bypass).

## Gates
- go test ./... -count=1: all packages ok, rc=0 (full suite; the new verdict-gate tests include a RED-proven foreign-task refusal pinned pre-fix).
- go vet ./internal/board ./cmd/boardctl: clean; gofmt -l: empty.
- CI on cca45c8: Build & Test 1.26 success. Pre-existing unrelated arm64 Multi-Arch failure (gzip threshold test) predates this commit (also failed on 97567d4, 4f70f21) — filed separately on the boardctl board.

## Worker
glm-5.3-flash @ ollama-cloud, dispatched from lore tick lore-foreman-2026-11-22-10-22-47, serial (WAVE_BUDGET=1), one worktree commit on the boardctl repo main.
