# Verdict: LORE-HYGIENE-20261121

**Task:** Release clean-tree gate broken by untracked .gitreins/verdicts residue
**Evaluated:** 2026-11-21T03:56:33.333602
**Result:** ✓ PASS

## Criteria

- ✓ **.gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.**
  - All four sub-claims verified live. (1) `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit=0 — the single-path snapshot matches the rule at .gitignore:47. (2) `.gitreins/history/` stays tracked: `git check-ignore .gitreins/history/2026-11-21` exit=1 (not ignored) and `git ls-files .gitreins/history | wc -l` = 667 tracked files. (3) Clean-tree gate: created untracked `.gitreins/verdicts/verdict.json`, then `git status --porcelain` produced 0 lines and `scripts/release.sh --dry-run` printed `ok: working tree clean` (scripts/release.sh:31-35), proceeding past gate 1 — it stopped only at later, unrelated gates (CI status 'none' on HEAD; with --skip-ci-check, `REFUSE: tag v0.2.0 already exists`), exactly as the task describes. (4) RED-proven pre-fix: commit fada9ed message records the pre-fix run at 8973116 — `git check-ignore` exit=1 and `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty` exit=1 — on the real gate (release.sh step 1), not a reproduction. Test suite: `uv run pytest -x --tb=short -q` exit=0, `572 passed in 5.61s`.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ .gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.: All four sub-claims verified live. (1) `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit=0 — the single-path snapshot matches the rule at .gitignore:47. (2) `.gitreins/history/` stays tracked: `git check-ignore .gitreins/history/2026-11-21` exit=1 (not ignored) and `git ls-files .gitreins/history | wc -l` = 667 tracked files. (3) Clean-tree gate: created untracked `.gitreins/verdicts/verdict.json`, then `git status --porcelain` produced 0 lines and `scripts/release.sh --dry-run` printed `ok: working tree clean` (scripts/release.sh:31-35), proceeding past gate 1 — it stopped only at later, unrelated gates (CI status 'none' on HEAD; with --skip-ci-check, `REFUSE: tag v0.2.0 already exists`), exactly as the task describes. (4) RED-proven pre-fix: commit fada9ed message records the pre-fix run at 8973116 — `git check-ignore` exit=1 and `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty` exit=1 — on the real gate (release.sh step 1), not a reproduction. Test suite: `uv run pytest -x --tb=short -q` exit=0, `572 passed in 5.61s`.
The one-line .gitignore rule (.gitignore:47) ignores .gitreins/verdicts/ while .gitreins/history/ (667 tracked files) stays tracked; verified live that release.sh --dry-run passes its clean-tree gate with the untracked verdict.json residue present, and the RED proof is recorded in commit fada9ed against the real gate.

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ .gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.: All four sub-claims verified live. (1) `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit=0 — the single-path snapshot matches the rule at .gitignore:47. (2) `.gitreins/history/` stays tracked: `git check-ignore .gitreins/history/2026-11-21` exit=1 (not ignored) and `git ls-files .gitreins/history | wc -l` = 667 tracked files. (3) Clean-tree gate: created untracked `.gitreins/verdicts/verdict.json`, then `git status --porcelain` produced 0 lines and `scripts/release.sh --dry-run` printed `ok: working tree clean` (scripts/release.sh:31-35), proceeding past gate 1 — it stopped only at later, unrelated gates (CI status 'none' on HEAD; with --skip-ci-check, `REFUSE: tag v0.2.0 already exists`), exactly as the task describes. (4) RED-proven pre-fix: commit fada9ed message records the pre-fix run at 8973116 — `git check-ignore` exit=1 and `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty` exit=1 — on the real gate (release.sh step 1), not a reproduction. Test suite: `uv run pytest -x --tb=short -q` exit=0, `572 passed in 5.61s`.
The one-line .gitignore rule (.gitignore:47) ignores .gitreins/verdicts/ while .gitreins/history/ (667 tracked files) stays tracked; verified live that release.sh --dry-run passes its clean-tree gate with the untracked verdict.json residue present, and the RED proof is recorded in commit fada9ed against the real gate.

Overall: PASS ✓
