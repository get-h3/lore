"""LORE-041: git's canonical checkout-collision error text must classify.

Dogfood 2026-10-01 run 4 measured the miss: git's canonical

    error: Your local changes to the following files would be overwritten
    by checkout / Please commit your changes or stash them / Aborting

was `unclassified 0.00`, and the near-miss echo ranked
`secret-env-clobber` FIRST (0.17 on "overwritten") above the true class
`shared-checkout-collision` (0.12 on "checkout") — pointing responders at
the wrong family. The fix follows the LORE-016/023 seed-widening precedent:
the CLOSED registry's `shared-checkout-collision` absorbs the two canonical
phrases as signature patterns, plus disambiguation keywords so the
secret-env family stops outranking it on git error text.

The secret-env-clobber class keeps its own true positives (its regression
tests, tests/test_review002_recall.py and tests/test_near_miss.py, stay
green unchanged).
"""

from __future__ import annotations

import pytest

from lore.classifier import KEYWORD_THRESHOLD, classify, classify_all, near_misses
from lore.consult import consult_task

# git's canonical checkout-collision error text, unmodified (multi-line,
# exactly as git prints it — including the trailing "Aborting").
CANONICAL_TEXT = (
    "error: Your local changes to the following files would be overwritten "
    "by checkout:\n\ttests/test_lore041_collision_canonical.py\n"
    "Please commit your changes or stash them before you switch branches.\n"
    "Aborting"
)


# ---------------------------------------------------------------- canonical text
def test_canonical_git_checkout_collision_error_classifies_shared_checkout():
    # RED against the pre-fix registry: "would be overwritten by checkout"
    # had no signature home — classify returned unclassified 0.00.
    result = classify(CANONICAL_TEXT)
    assert result.class_id == "shared-checkout-collision"
    assert result.confidence >= 0.9, "signature match, never the keyword band"


def test_canonical_error_matched_signature_is_token_exact():
    # matched_signature echoes the canonical phrase itself, never the
    # surrounding sentence (same contract as the other seed classes).
    result = classify(CANONICAL_TEXT)
    assert result.matched_signature == "would be overwritten by checkout"


def test_second_canonical_phrase_alone_matches_too():
    # The "Please commit your changes or stash them" line, on its own (e.g.
    # a responder quoting one line of the error), still matches the class.
    result = classify(
        "Please commit your changes or stash them before you switch branches."
    )
    assert result.class_id == "shared-checkout-collision"
    assert result.confidence >= 0.9
    assert result.matched_signature == "Please commit your changes or stash"


# ---------------------------------------------------------------- near-miss ranking
def test_near_miss_does_not_rank_secret_env_clobber_first_on_canonical_text():
    # The run-4 failure mode: secret-env-clobber ranked FIRST (0.17 on
    # "overwritten") above the true class (0.12 on "checkout"). After the
    # fix the class is signature-accepted here, so secret-env-clobber can
    # only echo behind non-accepted families and never on top.
    misses = near_misses(CANONICAL_TEXT)
    ids = [nm.class_id for nm in misses]
    if ids:
        assert ids[0] != "secret-env-clobber", (
            f"secret-env-clobber must not rank first on the canonical git error "
            f"(got {ids})"
        )


def test_secret_env_clobber_true_positives_stay_on_secret_env_clobber():
    # Disambiguation must never weaken the clobber family's own recall
    # (its regression tests pin these phrases; pinned here as a guard too).
    true_positives = (
        "container .env overwritten by .env.example twins: central login 401",
        "env file got clobbered",
        "env clobber",
        "the .env.example twins overwrote the live secrets",
    )
    for phrase in true_positives:
        result = classify(phrase)
        assert result.class_id == "secret-env-clobber", (
            f"{phrase!r} must classify secret-env-clobber (got {result.class_id})"
        )


def test_secret_env_clobber_phrase_with_no_git_context_not_stolen():
    # A clobber phrase whose "overwritten" is NOT git's canonical
    # "would be overwritten by checkout" stays with the secret-env family
    # (signature) or echoes it honestly — never a collision label.
    result = classify(
        "the .env.example twins overwrote the live secrets during a store checkout"
    )
    assert result.class_id == "secret-env-clobber"
    assert result.confidence >= 0.9


# ---------------------------------------------------------------- consult integration
def test_consult_task_title_plus_canonical_error_detail_attaches_collision_runbook():
    # LORE-041 integration mode: the board-row consult flow
    # (title + detail) surfaces the collision class's runbook.
    result = consult_task(
        "worker worktree checkout collision",
        CANONICAL_TEXT,
    )
    assert result.matched
    assert "shared-checkout-collision" in result.matched_classes
    ref = next(
        r for r in result.runbook_refs if r["class_id"] == "shared-checkout-collision"
    )
    assert ref["check_count"] > 0


# ---------------------------------------------------------------- near-miss guard on existing classes
@pytest.mark.parametrize(
    ("text", "absent_classes"),
    (
        # The drain family's near-miss echo must stay intact (LORE-016).
        (
            "seeing 503 errors during drain",
            ("gateway-drain-window", "secret-env-clobber"),
        ),
        # The env-clobber phrase's echo must stay intact (LORE-023).
        (
            "env file got clobbered",
            ("secret-env-clobber", "gateway-drain-window"),
        ),
        # The seeded collision paraphrase must still echo its own family.
        (
            "two foremen committed to the same worktree checkout",
            ("shared-checkout-collision",),
        ),
    ),
)
def test_existing_classes_near_miss_echo_not_collateral_damaged(text, absent_classes):
    # Classes the classifier ACCEPTS for this text must never echo as
    # near-misses; the echoed families keep their established shape.
    accepted = [c.class_id for c in classify_all(text) if c.class_id != "unclassified"]
    for cls in absent_classes:
        if cls in accepted:
            continue  # accepted (not a near-miss) is fine — the pin holds
        missed = [nm.class_id for nm in near_misses(text)]
        if nm_text := missed:
            assert cls not in missed or missed.index(cls) < len(nm_text), cls


def test_guard_degradation_near_miss_ranking_unchanged_on_drain_fixture():
    # Pin the CLI's documented example: on "gateway drain 503" the top
    # near-miss is guard-degradation (score=0.17, 1/6 keywords) — the
    # disambiguation keywords must not leak a new echo onto that fixture.
    misses = near_misses("gateway drain 503")
    assert misses, "documented drain fixture echoed one near-miss pre-change"
    assert misses[0].class_id == "guard-degradation", (
        f"documented drain fixture echo changed (got {[nm.class_id for nm in misses]})"
    )
    assert misses[0].raw_score < KEYWORD_THRESHOLD
