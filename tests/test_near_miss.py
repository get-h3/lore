"""LORE-016: near-miss evidence echo on unclassified match.

The honesty rule is doctrine: below-threshold keyword evidence never labels a
class. The gap was that the raw below-threshold scores were computed and
thrown away, so an unclassified match gave the operator zero graded signal.
``near_misses`` echoes that signal; ``--explain`` prints it.
"""

from lore.classes import UNCLASSIFIED_ID
from lore.classifier import (
    KEYWORD_THRESHOLD,
    NearMiss,
    classify_all,
    near_misses,
)


# ---------------------------------------------------------------- library API
def test_dogfood_worktree_paraphrase_names_shared_checkout_collision():
    # The dogfood 2026-09-24 example: stranger phrasing of a SEEDED class.
    misses = near_misses("two foremen committed to the same worktree checkout")
    ids = [nm.class_id for nm in misses]
    assert "shared-checkout-collision" in ids, (
        f"dogfood example must name shared-checkout-collision as a near-miss "
        f"(got {ids})"
    )
    nm = next(nm for nm in misses if nm.class_id == "shared-checkout-collision")
    assert nm.n_hits == 2, "dogfood evidence says 2 of its keywords hit"
    assert nm.n_keywords == 6, "shared-checkout-collision has 6 curated keywords"
    assert len(nm.hit_keywords) == 2
    assert nm.raw_score < KEYWORD_THRESHOLD, "honest: below the acceptance gate"
    assert {"worktree", "checkout"} <= set(nm.hit_keywords)


def test_key_loss_paraphrase_names_key_or_secret_class_with_low_score():
    # Another real dogfood paraphrase: below threshold, class named honestly.
    misses = near_misses("container env lost the API key after .env got clobbered")
    ids = [nm.class_id for nm in misses]
    assert "key-rotation-expiry" in ids or "secret-env-clobber" in ids, (
        f"expected key-rotation-expiry or secret-env-clobber (got {ids})"
    )
    top = misses[0]
    assert top.raw_score < KEYWORD_THRESHOLD
    assert top.n_hits >= 1
    assert top.hit_keywords, "near-miss must always name which keywords hit"


def test_near_misses_never_contains_an_accepted_class():
    # Any class classify_all accepted (signature or above-threshold keywords)
    # must not appear as a near-miss — even when its keyword score is low.
    text = "drain 503s while requests drain during restart"  # signature fixture
    accepted = [c.class_id for c in classify_all(text) if c.class_id != UNCLASSIFIED_ID]
    assert accepted, "precondition: the fixture classifies a class"
    miss_ids = [nm.class_id for nm in near_misses(text)]
    assert not set(accepted) & set(miss_ids), (
        "a class the classifier accepted must never be echoed as a near-miss"
    )


def test_near_misses_returns_empty_when_nothing_hits():
    misses = near_misses("coffee machine broken")
    assert misses == []
    # The dogfood near-zero phrasing too.
    assert near_misses("lost the API key") == []


def test_near_misses_sorted_best_first_and_capped_at_three():
    misses = near_misses("container env lost the API key after .env got clobbered")
    scores = [nm.raw_score for nm in misses]
    assert scores == sorted(scores, reverse=True)
    assert len(misses) <= 3


def test_near_miss_is_frozen_typed_dataclass():
    nm = near_misses("two foremen committed to the same worktree checkout")[0]
    assert isinstance(nm, NearMiss)
    assert isinstance(nm.raw_score, float)
    assert isinstance(nm.hit_keywords, tuple)


# ---------------------------------------------------------------- CLI surface
def _run_match(argv, capsys):
    from lore.__main__ import main

    code = main(argv)
    return code, capsys.readouterr()


def test_cli_match_without_explain_output_unchanged(capsys):
    # Byte-identical to the pre-LORE-016 shape: candidate lines only, no
    # near-misses section, with or without a classification.
    code, out = _run_match(["match", "drain 503"], capsys)
    assert code == 0
    lines = out.out.strip().splitlines()
    assert all("\tnear-miss" not in ln and ln.strip() != "near-misses:" for ln in lines)
    assert "near-misses:" not in out.out
    assert lines[0].startswith("gateway-drain-window\tconfidence=")


def test_cli_match_canonical_symptom_explain_still_lists_honestly(capsys):
    # --explain on a CANONICAL seed symptom: the class is labeled at 0.90 and
    # the near-miss section still prints honestly (may be none).
    code, out = _run_match(
        ["match", "--explain", "drain 503s while requests drain during restart"], capsys
    )
    assert code == 0
    out_text = out.out
    assert "gateway-drain-window\tconfidence=" in out_text
    assert "near-misses:" in out_text  # section header always present


def test_cli_match_explain_dogfood_example_prints_honest_score(capsys):
    code, out = _run_match(
        ["match", "--explain", "two foremen committed to the same worktree checkout"],
        capsys,
    )
    assert code == 0
    out_text = out.out
    assert "unclassified" in out_text, "honest refusal stays the headline"
    assert "near-misses:" in out_text
    assert "shared-checkout-collision" in out_text
    # raw fraction + which keywords hit — never a bare number
    assert "score=0.33" in out_text
    assert "(2/6 keywords:" in out_text
    assert "worktree" in out_text and "checkout" in out_text
