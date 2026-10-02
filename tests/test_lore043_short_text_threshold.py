"""LORE-043: short-text (title-mode) keyword threshold — consult must not go
silent on realistic board-row TITLES.

Dogfood 2026-10-01 run 4 measured the gap: the tick-start consult (LORE-007)
is fed task TITLES, which are short. A realistic title

    worker worktree checkout collision

carries 3 of the 8 shared-checkout-collision keywords (worktree, checkout,
collision) = raw score 0.375 — below the long-text KEYWORD_THRESHOLD of 0.6,
so ``consult`` returned ``matched:false`` for the fleet's most recurring
collision class. LORE-041 absorbed the canonical git error text, which fixed
the title+detail path where the detail carries the paste — this row targets
the TITLE-ONLY path, which carries only the title.

Fix shape (deliberate band, not a blanket threshold drop — the honesty rule
stays: a specific label must still carry its keyword evidence):

- SHORT texts (<= :data:`SHORT_TEXT_WORD_LIMIT` words) accept keyword
  evidence at a lower gate, :data:`SHORT_KEYWORD_THRESHOLD` (>= 0.3 = a
  2-3 keyword hit on a short title like the LORE-043 one).
- LONG texts keep the exact pre-change gate (:data:`KEYWORD_THRESHOLD` =
  0.6): a near-miss score of 0.17 must refuse exactly as before.
- Confidence stays capped at KEYWORD_CONFIDENCE_MAX (keyword evidence never
  reads as signature strength) and the evidence kind stays ``keyword``.

The cutoff is principled, not vibes: the board census shows a median title
of 14 words with a 25th percentile of 8, so titles cluster at or below ~8
words; the longest REFUSED paraphrase pinned by the near-miss tests ("two
foremen committed to the same worktree checkout", 8 words; "container env
lost the API key after .env got clobbered", 10 words) must stay on the long
path — 9 or 12 would flip the 10-word one, so 8 is the ceiling that keeps
every existing refusal pin intact.
"""

import json

from lore.classes import SEED_CLASSES, UNCLASSIFIED_ID, get_registry
from lore.classifier import (
    KEYWORD_CONFIDENCE_MAX,
    KEYWORD_THRESHOLD,
    SHORT_KEYWORD_THRESHOLD,
    SHORT_TEXT_WORD_LIMIT,
    classify,
    classify_all,
    near_misses,
)
from lore.consult import consult, consult_task

# The exact LORE-043 board-row title (dogfood run 4, docs/dogfood/
# 2026-10-01-run4-integration.md) — title-only, no detail, no paste.
LORE043_TITLE = "worker worktree checkout collision"

# The longest paraphrase the near-miss tests refuse today; 10 words — the
# reason the short cutoff cannot be 9 or 12 without flipping this refusal.
LONG_REFUSED_PARAPHRASE = "container env lost the API key after .env got clobbered"

# Canonical git error text (LORE-041 shape) used as the title+detail paste.
CANONICAL_DETAIL = (
    "error: Your local changes to the following files would be overwritten\n"
    "by checkout:\n\ttests/test_x.py\n"
    "Please commit your changes or stash them before you switch branches."
)


# ---------------------------------------------------------------- constants
def test_short_text_constants_exist_and_keep_the_shape():
    assert SHORT_KEYWORD_THRESHOLD < KEYWORD_THRESHOLD
    # A raw score of exactly SHORT_KEYWORD_THRESHOLD (e.g. 2/8 = 0.25 hits)
    # must NOT clear a 0.3 gate in the WRONG direction: the gate accepts
    # scores AT or above it. The title's 0.375 clears both 0.3 and the long
    # path stays strict at 0.6.
    assert SHORT_TEXT_WORD_LIMIT >= 8, "the LORE-043 title itself must fit"
    assert SHORT_TEXT_WORD_LIMIT < 10, (
        "the 10-word refused paraphrase must stay on the LONG path"
    )
    assert KEYWORD_CONFIDENCE_MAX == 0.5, "keyword cap survives the band"


def test_long_text_threshold_constant_is_unchanged():
    assert KEYWORD_THRESHOLD == 0.6


# ---------------------------------------------------------------- a) title path
def test_lore043_title_returns_shared_checkout_collision():
    result = classify(LORE043_TITLE)
    assert result.class_id == "shared-checkout-collision"
    assert result.confidence > 0.0
    # Honest evidence: keyword-only, capped below signature strength, and it
    # names the three keywords that fired (worktree, checkout, collision).
    assert result.matched_signature is None
    assert all(ev["kind"] == "keyword" for ev in result.evidence)
    assert result.confidence <= KEYWORD_CONFIDENCE_MAX, (
        "keyword evidence never reads as signature strength"
    )
    assert {"worktree", "checkout", "collision"} <= set(result.matched_keywords)


def test_lore043_title_classify_all_keeps_fallback_and_ranking():
    results = classify_all(LORE043_TITLE)
    assert results[0].class_id == "shared-checkout-collision"
    assert results[0].confidence > 0.0
    confs = [c.confidence for c in results]
    assert confs == sorted(confs, reverse=True), "candidates stay best-first"
    assert results[-1].class_id == UNCLASSIFIED_ID, "fallback stays present"
    ids = [c.class_id for c in results]
    assert len(ids) == len(set(ids)), "no duplicate ids"


def test_lore043_title_consult_reports_matched_true():
    result = consult(LORE043_TITLE)
    assert result.matched is True
    assert "shared-checkout-collision" in result.matched_classes
    assert result.runbook_refs, "a matched consult must carry up-to-3 runbook refs"
    ref_ids = [r["class_id"] for r in result.runbook_refs]
    assert "shared-checkout-collision" in ref_ids
    assert result.elapsed_ms > 0.0


def test_lore043_title_consult_json_round_trip():
    result = consult(LORE043_TITLE)
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["matched"] is True
    assert payload["matched_classes"][0] == "shared-checkout-collision"
    assert isinstance(payload["elapsed_ms"], float)


def test_lore043_cli_consult_json_prints_matched_true(capsys):
    from lore.__main__ import main

    rc = main(["consult", LORE043_TITLE, "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["matched"] is True
    assert payload["matched_classes"][0] == "shared-checkout-collision"


def test_lore043_title_consult_task_title_only_matches():
    # consult_task with an EMPTY detail string is the title-only shape.
    result = consult_task(LORE043_TITLE, "")
    assert result.matched is True
    assert "shared-checkout-collision" in result.matched_classes


# ---------------------------------------------------------------- b) long-text guard
def test_long_refused_paraphrase_stays_refused():
    # The long path's gate is UNCHANGED: this 10-word paraphrase scored 0.5
    # (best class 3/6 keywords, below 0.6) and refused pre-change; it must
    # still refuse — the short band must not leak onto long texts.
    assert len(LONG_REFUSED_PARAPHRASE.split()) > SHORT_TEXT_WORD_LIMIT
    result = classify(LONG_REFUSED_PARAPHRASE)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0
    # The evidence echo stays available (LORE-016 contract).
    misses = near_misses(LONG_REFUSED_PARAPHRASE)
    assert "secret-env-clobber" in [nm.class_id for nm in misses]


def test_long_text_weak_evidence_consult_stays_false():
    # Criteria 4b: a LONG text with weak keyword evidence is still refused
    # through the consult path too — matched:false, no refs, no exception.
    result = consult(LONG_REFUSED_PARAPHRASE)
    assert result.matched is False
    assert result.matched_classes == []
    assert result.runbook_refs == []


def test_long_text_just_below_long_gate_stays_refused():
    # A genuinely LONG text whose best raw score (3/6 gateway keywords =
    # 0.5) sits just BELOW the long gate (0.6): refused before the change
    # and refused after it — the band is length-scoped, not a global drop.
    long_weak = (
        "the gateway came back after its restart and the drain of queued "
        "traffic finished; nothing failed for anyone"
    )
    assert len(long_weak.split()) > SHORT_TEXT_WORD_LIMIT
    result = classify(long_weak)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0


def test_quarter_score_collision_paraphrase_stays_refused_on_both_paths():
    # The symmetric guard: the dogfood "two foremen committed to the same
    # worktree checkout" paraphrase carried 2/8 keywords (0.25) and refused
    # pre-change. It is 8 words so it sits INSIDE the short band — but 0.25
    # is still below the short gate too, so it refuses on BOTH paths. The
    # pin: a quarter-score must never label, whichever gate applies.
    text = "two foremen committed to the same worktree checkout"
    result = classify(text)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0
    # ...and still echoes its own family as a near-miss (LORE-016 pin).
    assert "shared-checkout-collision" in [nm.class_id for nm in near_misses(text)]


def test_short_below_band_stays_refused_too():
    # A SHORT text whose best keyword evidence sits below the SHORT gate
    # never labels either: the honesty rule holds on both paths. One weak
    # 1/7 hit (0.143) must not label a class.
    text = "push rejected: permission denied (publickey)"
    assert len(text.split()) <= SHORT_TEXT_WORD_LIMIT
    result = classify(text)
    assert result.class_id == UNCLASSIFIED_ID, (
        "one weak keyword hit must never label a class"
    )
    assert "fast-forward-push-reject" in [nm.class_id for nm in near_misses(text)], (
        "the refusal still echoes what almost matched"
    )


def test_off_vocabulary_short_text_stays_unclassified():
    # Zero keyword hits: refused at any threshold, any length.
    text = "quarterly report widget sales spend"
    assert len(text.split()) <= SHORT_TEXT_WORD_LIMIT
    result = classify(text)
    assert result.class_id == UNCLASSIFIED_ID
    assert result.confidence == 0.0
    assert near_misses(text) == []


def test_short_band_does_not_change_registry_shape():
    # Criteria 3: no new failure classes, registry untouched.
    # Class count is DERIVED from SEED_CLASSES, never hardcoded (LORE-032/034
    # convention; tier-2 verdict flagged the hardcoded literal).
    curated = {c.id for c in get_registry().all_classes()} - {UNCLASSIFIED_ID}
    assert len(curated) == len(SEED_CLASSES)
    assert "shared-checkout-collision" in curated


def test_registry_count_pin_derived_from_seeds():
    # Guard the count the way the repo's own pins do (tests/test_lore034_
    # reap_and_push_classes.py::test_registry_counts_derived_from_seeds).
    assert len(get_registry()) == len(SEED_CLASSES) + 1


# ---------------------------------------------------------------- c) title+detail path
def test_title_plus_detail_path_still_matches():
    # LORE-041's integration cell, re-run here as the (c) pin: the paste in
    # the detail carries the signature and the class still lands.
    result = consult_task(LORE043_TITLE, CANONICAL_DETAIL)
    assert result.matched is True
    assert "shared-checkout-collision" in result.matched_classes
    ref = next(
        r for r in result.runbook_refs if r["class_id"] == "shared-checkout-collision"
    )
    assert ref["check_count"] > 0


def test_title_plus_detail_signature_evidence_still_dominates():
    # With the paste in the detail the class must still label at SIGNATURE
    # strength (0.9), not the short keyword band — the band only ever
    # lowers the acceptance GATE for keyword evidence, never the value
    # scaling, so signature evidence keeps its own strength.
    combined = f"{LORE043_TITLE}\n{CANONICAL_DETAIL}"
    result = classify(combined)
    assert result.matched_signature is not None
    assert result.confidence >= 0.9


# ---------------------------------------------------------------- sibling-class guard
def test_short_band_does_not_mislabel_drain_title():
    # A SHORT title with 2/6 drain keywords (0.333) now labels its OWN
    # class — fine under the band — but must never land on a sibling class.
    text = "503s while requests drain during restart"
    result = classify(text)
    assert result.class_id == "gateway-drain-window"
    assert result.matched_signature is None
    assert all(ev["kind"] == "keyword" for ev in result.evidence)


def test_short_env_paraphrase_lands_on_its_own_class_not_collision():
    # A SHORT text whose best class is secret-env-clobber must keep the
    # sibling boundary: clobber vocabulary cannot land on the collision
    # class just because the band lowered both gates.
    text = "env file secrets got clobbered"
    assert len(text.split()) <= SHORT_TEXT_WORD_LIMIT
    result = classify(text)
    assert result.class_id == "secret-env-clobber"
    assert result.matched_signature is None
    assert all(ev["kind"] == "keyword" for ev in result.evidence)
    assert result.class_id != "shared-checkout-collision"
