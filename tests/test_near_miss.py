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
    classify,
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
    assert nm.n_keywords == 8, "shared-checkout-collision has 8 curated keywords"
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
    assert "score=0.25" in out_text
    assert "(2/8 keywords:" in out_text
    assert "worktree" in out_text and "checkout" in out_text


# ---------------------------------------------------------------- LORE-023 seeds
# Dogfood 2026-09-25 run 3: real incident vocabulary still missed the seeded
# classes. The registry stays CLOSED — these phrases must be matched by the
# EXISTING classes (keyword/signature additions), never by new class ids.
LORE023_PROBES = (
    (
        "empty commit landed with my message but zero files",
        "shared-checkout-collision",
    ),
    (
        "core.bare got flipped on the main repo and pushes fail",
        "shared-checkout-collision",
    ),
    ("env clobber", "secret-env-clobber"),
)


def test_lore023_empty_commit_phrase_lands_on_shared_checkout_collision():
    result = classify("empty commit landed with my message but zero files")
    assert result.class_id == "shared-checkout-collision"
    assert result.matched_signature == "empty commit"
    assert result.confidence >= 0.8, "signature strength, not the keyword band"


def test_lore023_core_bare_flip_phrase_lands_on_shared_checkout_collision():
    result = classify("core.bare got flipped on the main repo and pushes fail")
    assert result.class_id == "shared-checkout-collision"
    assert result.matched_signature == "core.bare"


def test_lore023_bare_env_clobber_lands_on_secret_env_clobber():
    # Pre-fix this was a 0.17 near-miss: the bigram "env clobber" does not
    # contain the seeded ".env clobber" shape. Signature-level now.
    result = classify("env clobber")
    assert result.class_id == "secret-env-clobber"
    assert result.matched_signature == "env clobber"


def test_lore023_dotted_env_clobber_signature_stays_token_exact():
    # The normalization must not widen the dotted form's echo: ".env.example
    # twins" still matches and matched_signature keeps the ".env" prefix —
    # the dot-less branch must never swallow the dotted token.
    result = classify("the .env.example twins overwrote the live secrets")
    assert result.class_id == "secret-env-clobber"
    assert result.matched_signature == ".env.example twins"


def test_lore023_cli_explain_labels_every_probe(capsys):
    for text, expected in LORE023_PROBES:
        code, out = _run_match(["match", "--explain", text], capsys)
        assert code == 0
        assert f"{expected}\tconfidence=" in out.out, f"{text!r} must label {expected}"
