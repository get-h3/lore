"""REVIEW-LORE-002: classifier recall on natural incident phrasings.

Measured misses (all returned unclassified with score 0.00 before the seed
widening): the three drain/503 phrasings and "env file got clobbered".
One assertion per phrase pins the exact class_id, plus negative guards so
widening one class's seeds cannot make the other win.
"""

import pytest

from lore.classifier import classify

DRAIN_PHRASES = {
    "seeing 503 errors during drain": "gateway-drain-window",
    "503s while draining": "gateway-drain-window",
    "drain-window 503s": "gateway-drain-window",
}


@pytest.mark.parametrize(("phrase", "expected"), sorted(DRAIN_PHRASES.items()))
def test_drain_phrasing_classifies_gateway_drain_window(phrase, expected):
    result = classify(phrase)
    assert result.class_id == expected
    assert result.confidence >= 0.9  # signature match, not a weak keyword score


def test_env_file_got_clobbered_classifies_secret_env_clobber():
    result = classify("env file got clobbered")
    assert result.class_id == "secret-env-clobber"
    assert result.confidence >= 0.9


def test_matched_signature_stays_token_exact():
    # matched_signature echoes the drift token, never the whole sentence.
    result = classify("seeing 503 errors during drain")
    assert result.matched_signature == "503 errors during drain"
    result = classify("env file got clobbered")
    assert result.matched_signature == "env file got clobbered"


# ---------------------------------------------------------------- near-miss guards
def test_drain_phrases_do_not_land_on_secret_env_clobber():
    # Cross-class guard: the drain family shares no vocabulary with the
    # secret-env-clobber seeds, but pin it anyway — widening must never make
    # the clobber class win a drain phrase.
    for phrase in DRAIN_PHRASES:
        assert classify(phrase).class_id != "secret-env-clobber"


def test_env_clobber_phrase_does_not_land_on_gateway_drain_window():
    assert classify("env file got clobbered").class_id != "gateway-drain-window"


def test_bare_503_and_bare_env_file_stay_unclassified():
    # The new patterns anchor on CO-OCCURRENCE; a bare "503" or a bare
    # "env file" (no clobber verb) must never fire either class.
    assert classify("503 errors").class_id == "unclassified"
    assert classify("env file").class_id == "unclassified"
