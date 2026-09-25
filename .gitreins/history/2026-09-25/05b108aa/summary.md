# Verdict: LORE-021

**Task:** Library naming contract pin: NearMiss.raw_score vs CLI score=; evidence dict shape
**Evaluated:** 2026-09-25T09:00:54.844042
**Result:** ✓ PASS

## Pipeline Stages

- ✓ **tier1**
  -   ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================
- ✓ **tier2**
  - COMPLETE
  ✓ Docstrings state both names + dict shape; mechanical pin tests; zero behavior change: Docstrings: lore/classifier.py:60-72 NearMiss docstring names `raw_score` (raw fraction) AND the CLI's `score=` ('The CLI ``match --explain`` prints this SAME raw fraction as ``score=``'), contrasting it with the band-scaled `confidence=`; lore/classifier.py:36-43 Classification docstring states evidence is 'a list of PLAIN DICTS (``type(e) is dict``)... exactly the keys ``"kind"`` and ``"detail"``'. Pin tests: tests/test_lore021_naming_docs.py has 7 mechanical tests incl. test_docstrings_state_both_names (inspect.getdoc asserts 'raw_score', 'score=', '"kind"', '"detail"'), test_cli_explain_prints_the_raw_fraction_as_score, and two evidence-shape tests asserting type(e) is dict and set(keys)=={'kind','detail'}. Test evidence (fresh): `uv run pytest tests/test_lore021_naming_docs.py -v --tb=short` exit_code 0 -> '7 passed in 0.03s'; full config test_command `uv run pytest -x --tb=short` exit_code 0 -> '269 passed in 2.07s'. Zero behavior change: `git diff HEAD^1 HEAD -- lore/classifier.py` removes only 2 lines, both docstring/comment ('"""One candidate classification for a symptom text."""' and '# than a signature match.'), all 23 added lines are docstring/comment text — no executable statement altered. Runtime spot-check confirms claims: classify('drain 503s...').evidence == [{'kind':'signature','detail':'drain 503'},{'kind':'keyword','detail':'503'},...] all plain dicts; nm.raw_score == n_hits/n_keywords == 0.3333; CLI source lore/__main__.py:67 prints `score={nm.raw_score:.2f}` and :57 prints `confidence={c.confidence:.2f}`. LSP diagnostics: 0 findings.
LORE-021 fully satisfied: both naming contracts and the evidence dict shape are documented in docstrings, pinned by 7 passing mechanical tests (full suite 269 passed), with a docstring/comment-only diff proving zero behavior change.

## Summary

Judge Result: LORE-021

Stage tier1: PASS
    ✓ lint: ok (no output)
  ✓ secrets: secrets: harness state excluded from gitleaks scope (.gitreins/**)
  ✓ tests: ============================= test session starts ==============================

Stage tier2: PASS
  COMPLETE
  ✓ Docstrings state both names + dict shape; mechanical pin tests; zero behavior change: Docstrings: lore/classifier.py:60-72 NearMiss docstring names `raw_score` (raw fraction) AND the CLI's `score=` ('The CLI ``match --explain`` prints this SAME raw fraction as ``score=``'), contrasting it with the band-scaled `confidence=`; lore/classifier.py:36-43 Classification docstring states evidence is 'a list of PLAIN DICTS (``type(e) is dict``)... exactly the keys ``"kind"`` and ``"detail"``'. Pin tests: tests/test_lore021_naming_docs.py has 7 mechanical tests incl. test_docstrings_state_both_names (inspect.getdoc asserts 'raw_score', 'score=', '"kind"', '"detail"'), test_cli_explain_prints_the_raw_fraction_as_score, and two evidence-shape tests asserting type(e) is dict and set(keys)=={'kind','detail'}. Test evidence (fresh): `uv run pytest tests/test_lore021_naming_docs.py -v --tb=short` exit_code 0 -> '7 passed in 0.03s'; full config test_command `uv run pytest -x --tb=short` exit_code 0 -> '269 passed in 2.07s'. Zero behavior change: `git diff HEAD^1 HEAD -- lore/classifier.py` removes only 2 lines, both docstring/comment ('"""One candidate classification for a symptom text."""' and '# than a signature match.'), all 23 added lines are docstring/comment text — no executable statement altered. Runtime spot-check confirms claims: classify('drain 503s...').evidence == [{'kind':'signature','detail':'drain 503'},{'kind':'keyword','detail':'503'},...] all plain dicts; nm.raw_score == n_hits/n_keywords == 0.3333; CLI source lore/__main__.py:67 prints `score={nm.raw_score:.2f}` and :57 prints `confidence={c.confidence:.2f}`. LSP diagnostics: 0 findings.
LORE-021 fully satisfied: both naming contracts and the evidence dict shape are documented in docstrings, pinned by 7 passing mechanical tests (full suite 269 passed), with a docstring/comment-only diff proving zero behavior change.

Overall: PASS ✓
