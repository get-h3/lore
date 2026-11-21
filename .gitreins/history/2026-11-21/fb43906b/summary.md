# Verdict: LORE-HYGIENE-20261121

**Task:** Release clean-tree gate broken by untracked .gitreins/verdicts residue
**Evaluated:** 2026-11-21T03:53:51.249337
**Result:** ✓ PASS

## Criteria

- ✓ **.gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.**
  - All four sub-parts verified live. (1) With .gitreins/verdicts/verdict.json created: `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit 0 — the single-path snapshot matches the rule at .gitignore:47. (2) .gitreins/history/ stays tracked: `git ls-files .gitreins/history/ | wc -l` = 667 tracked files; `git check-ignore -v .gitreins/history/` exits 1 (not ignored). (3) `scripts/release.sh --dry-run` with the untracked verdict.json present printed `ok: working tree clean` — the clean-tree gate (scripts/release.sh:28-31) passes; the run stops later at the CI gate (`REFUSE: latest CI on HEAD sha 75c094b... is not success (got: none)`), which is unrelated to the residue. (4) RED-proven pre-fix: `git show fada9ed^:.gitignore | grep verdicts` exits 1 (no rule before the fix), and fix commit fada9ed's message documents the RED run on the real gate: `?? .gitreins/verdicts/` in porcelain, check-ignore exit 1, `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty`, exit 1. Test fixture cleaned up afterward; tree clean.
- ✓ **Derived: with .gitreins/verdicts/verdict.json present on disk, `git status --porcelain` is empty so the release.sh step-1 gate (scripts/release.sh:28-31) is actually reached and passes — the ignore rule removes the residue from the gate's input, not just from check-ignore.**
  - Created .gitreins/verdicts/verdict.json, then `git status --porcelain` produced no output (exit 0) — the residue is invisible to the exact command the gate runs at scripts/release.sh:28. Confirmed end-to-end by the live `scripts/release.sh --dry-run` run printing `ok: working tree clean`. Other pre-existing residue (.gitreins/rescued-20261105, .digest) is covered by .gitignore:44-45, so the empty porcelain is not an artifact of a clean test environment.

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10
- ✓ **tier2**
  - COMPLETE
  ✓ .gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.: All four sub-parts verified live. (1) With .gitreins/verdicts/verdict.json created: `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit 0 — the single-path snapshot matches the rule at .gitignore:47. (2) .gitreins/history/ stays tracked: `git ls-files .gitreins/history/ | wc -l` = 667 tracked files; `git check-ignore -v .gitreins/history/` exits 1 (not ignored). (3) `scripts/release.sh --dry-run` with the untracked verdict.json present printed `ok: working tree clean` — the clean-tree gate (scripts/release.sh:28-31) passes; the run stops later at the CI gate (`REFUSE: latest CI on HEAD sha 75c094b... is not success (got: none)`), which is unrelated to the residue. (4) RED-proven pre-fix: `git show fada9ed^:.gitignore | grep verdicts` exits 1 (no rule before the fix), and fix commit fada9ed's message documents the RED run on the real gate: `?? .gitreins/verdicts/` in porcelain, check-ignore exit 1, `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty`, exit 1. Test fixture cleaned up afterward; tree clean.
  ✓ Derived: with .gitreins/verdicts/verdict.json present on disk, `git status --porcelain` is empty so the release.sh step-1 gate (scripts/release.sh:28-31) is actually reached and passes — the ignore rule removes the residue from the gate's input, not just from check-ignore.: Created .gitreins/verdicts/verdict.json, then `git status --porcelain` produced no output (exit 0) — the residue is invisible to the exact command the gate runs at scripts/release.sh:28. Confirmed end-to-end by the live `scripts/release.sh --dry-run` run printing `ok: working tree clean`. Other pre-existing residue (.gitreins/rescued-20261105, .digest) is covered by .gitignore:44-45, so the empty porcelain is not an artifact of a clean test environment.
The one-line .gitignore rule (.gitignore:47) ignores the .gitreins/verdicts/ snapshot while 667 .gitreins/history/ files stay tracked; the release.sh clean-tree gate passes with the residue present, and the pre-fix RED state is proven both by the empty parent-commit .gitignore and the fix commit's documented RED run.

## Summary

Stage tier1: PASS
    ✓ lint: scanners: nice=nice -n 10
  ✓ secrets: secrets: scanners=gitleaks+builtin cross-check
  ✓ tests: scanners: nice=nice -n 10

Stage tier2: PASS
  COMPLETE
  ✓ .gitignore ignores .gitreins/verdicts/ (git check-ignore -v matches the single-path snapshot) while .gitreins/history/ stays tracked; scripts/release.sh --dry-run passes its clean-tree gate with an untracked .gitreins/verdicts/verdict.json present; RED-proven on the real gate pre-fix.: All four sub-parts verified live. (1) With .gitreins/verdicts/verdict.json created: `git check-ignore -v .gitreins/verdicts/verdict.json` -> `.gitignore:47:.gitreins/verdicts/  .gitreins/verdicts/verdict.json`, exit 0 — the single-path snapshot matches the rule at .gitignore:47. (2) .gitreins/history/ stays tracked: `git ls-files .gitreins/history/ | wc -l` = 667 tracked files; `git check-ignore -v .gitreins/history/` exits 1 (not ignored). (3) `scripts/release.sh --dry-run` with the untracked verdict.json present printed `ok: working tree clean` — the clean-tree gate (scripts/release.sh:28-31) passes; the run stops later at the CI gate (`REFUSE: latest CI on HEAD sha 75c094b... is not success (got: none)`), which is unrelated to the residue. (4) RED-proven pre-fix: `git show fada9ed^:.gitignore | grep verdicts` exits 1 (no rule before the fix), and fix commit fada9ed's message documents the RED run on the real gate: `?? .gitreins/verdicts/` in porcelain, check-ignore exit 1, `scripts/release.sh --dry-run` -> `REFUSE: working tree is dirty`, exit 1. Test fixture cleaned up afterward; tree clean.
  ✓ Derived: with .gitreins/verdicts/verdict.json present on disk, `git status --porcelain` is empty so the release.sh step-1 gate (scripts/release.sh:28-31) is actually reached and passes — the ignore rule removes the residue from the gate's input, not just from check-ignore.: Created .gitreins/verdicts/verdict.json, then `git status --porcelain` produced no output (exit 0) — the residue is invisible to the exact command the gate runs at scripts/release.sh:28. Confirmed end-to-end by the live `scripts/release.sh --dry-run` run printing `ok: working tree clean`. Other pre-existing residue (.gitreins/rescued-20261105, .digest) is covered by .gitignore:44-45, so the empty porcelain is not an artifact of a clean test environment.
The one-line .gitignore rule (.gitignore:47) ignores the .gitreins/verdicts/ snapshot while 667 .gitreins/history/ files stay tracked; the release.sh clean-tree gate passes with the residue present, and the pre-fix RED state is proven both by the empty parent-commit .gitignore and the fix commit's documented RED run.

Overall: PASS ✓
