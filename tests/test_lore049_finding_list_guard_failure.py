"""LORE-049 rework: the BARE finding-list shape of guard failures must classify.

Round 1 (commit 110e436) gave gateway-guard-violation the guarded
co-occurrence shape ("guard FAILED ... secrets detected"). Run 7's second
half stayed dead: the guard's DECISION word is often absent from what an
operator pastes — "secrets detected in diff: a sk-prefixed live token
leaked" measured `unclassified 0.00` with a 0.17/0.17/0.12 noise split
across secret-env-clobber / guard-degradation / gateway-guard-violation.
These tests pin the finding-list tail on the family that already owns
guard tripping, plus the non-regression pins the brief demands.
"""

from lore.classes import get_registry
from lore.classifier import classify, near_misses

CLASS_ID = "gateway-guard-violation"

# The two run-7 live probe strings, verbatim.
CONSULT_FAILURE_TEXT = (
    "guard FAILED: secrets detected a sk-prefixed test token in diff; "
    "gitleaks gate rejected commit"
)
BARE_FINDING_TEXT = "secrets detected in diff: a sk-prefixed live token leaked"


def _cls():
    return get_registry().get(CLASS_ID)


def test_bare_finding_list_secrets_diff_classifies():
    result = classify(BARE_FINDING_TEXT)
    assert result.class_id == CLASS_ID
    assert result.confidence >= 0.9


def test_consult_failure_example_string_classifies():
    result = classify(CONSULT_FAILURE_TEXT)
    assert result.class_id == CLASS_ID
    assert result.confidence >= 0.9


def test_gitleaks_gate_rejected_classifies():
    result = classify("gitleaks gate rejected commit")
    assert result.class_id == CLASS_ID
    assert result.confidence >= 0.9


def test_lint_failed_classifies():
    result = classify("lint failed")
    assert result.class_id == CLASS_ID
    assert result.confidence >= 0.9


def test_matched_signature_stays_token_exact():
    # matched_signature echoes the finding phrase, never the whole paste.
    result = classify(BARE_FINDING_TEXT)
    assert "secrets detected" in result.matched_signature
    assert "sk-prefixed" not in result.matched_signature


# ---------------------------------------------------------------- non-regression
def test_gate_equivalence_text_still_labels_guard_degradation():
    # The brief's near-miss regression pin: run-4-era gate-EQUIVALENCE
    # phrasing keeps its round-4 home; the finding-list widening must not
    # steal it.
    result = classify(
        "guard result PASS on worktree but not gate-equivalent on main tree same commit"
    )
    assert result.class_id == "guard-degradation"
    assert result.confidence >= 0.9


def test_bare_secrets_without_diff_context_stays_unclassified():
    # Round-1 co-occurrence rule preserved: a bare "secrets detected" with
    # no diff/commit/token finding context does not fire the class.
    result = classify("secrets detected somewhere in the repo")
    assert result.class_id != CLASS_ID


def test_no_false_positive_control_coffee_machine():
    # The brief's noise control: everyday unrelated text stays unclassified
    # with zero confidence, and no class echoes it as a near-miss either.
    result = classify("coffee machine broken")
    assert result.class_id == "unclassified"
    assert result.confidence == 0.0
    assert near_misses("coffee machine broken") == []


def test_finding_list_patterns_registered_on_curated_class():
    cls = _cls()
    patterns = "\n".join(cls.signature_patterns)
    assert "secrets?\\s+detected" in patterns  # round-1 shape still present
    assert "gitleaks" in patterns
    assert "lint\\s+failed" in patterns
    for kw in ("guard failed", "secrets detected", "lint failed", "gitleaks"):
        assert kw in cls.keywords


def test_near_miss_evidence_echo_keeps_raw_score_honesty():
    # Evidence-echo honesty (brief criterion 3): a below-gate echo still
    # reports the RAW keyword fraction as its score, never a fabricated
    # confidence. "secrets detected somewhere in the repo" hits exactly one
    # keyword of the widened class ("secrets detected"), so its raw score
    # must equal 1/len(keywords) exactly.
    misses = near_misses("secrets detected somewhere in the repo")
    mine = [nm for nm in misses if nm.class_id == CLASS_ID]
    assert mine, "widened class should echo as a near-miss on this text"
    assert mine[0].n_hits == 1
    assert mine[0].raw_score == mine[0].n_hits / mine[0].n_keywords
