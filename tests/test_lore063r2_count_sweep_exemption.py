"""LORE-063-R2: count_sweep self-reference exemption no longer hides stale literals.

Fixes the recurrence where a line containing both ``scripts/test-count.txt``
and a stale ``<N> passed`` literal was silently skipped because the
``SELF_REFERENCE`` check ran first and returned ``False``.

Acceptance:
1. A line containing ``scripts/test-count.txt`` + stale literal -> flagged.
2. A line containing ``scripts/test-count.txt`` + canonical literal -> NOT flagged.
3. Lines without ``scripts/test-count.txt`` still check as before.
"""

import pytest
import test_count_guard

count_sweep = test_count_guard._load_sweep_module()


class TestLineHitsSelfReferenceExemption:
    """The self-reference exemption must NOT hide stale literals."""

    @pytest.fixture(autouse=True)
    def _counts(self) -> tuple[int, int | None]:
        """Return (canonical_test_count, class_count) for this repo."""
        canonical = test_count_guard._read_canonical()
        class_count = count_sweep.derive_class_count(test_count_guard.REPO_ROOT)
        # class_count may be None on a broken install; use a safe default
        return canonical, class_count if class_count is not None else 0

    def test_stale_literal_with_self_reference_is_flagged(self, _counts) -> None:
        """Line quoting the sync file but stating the wrong number must flag.

        This is the LORE-063-R2 recurrence: the guard returned True
        (clean) when the skill line read "510 passed" alongside a mention
        of ``scripts/test-count.txt``, because the exemption ran first.
        """
        canonical, class_count = _counts
        # A stale literal that differs from the canonical count
        line = f"uv run pytest -q    # expect: {canonical + 7} passed (count synced to scripts/test-count.txt, LORE-029)"
        assert count_sweep._line_hits(line, canonical, class_count) is True

    def test_canonical_literal_with_self_reference_is_clean(self, _counts) -> None:
        """When the line states the canonical count it stays clean."""
        canonical, class_count = _counts
        line = f"uv run pytest -q    # expect: {canonical} passed (count synced to scripts/test-count.txt, LORE-029)"
        assert count_sweep._line_hits(line, canonical, class_count) is False

    def test_stale_literal_without_self_reference_still_flags(self, _counts) -> None:
        """Non-self-reference lines with stale literals continue to flag."""
        canonical, class_count = _counts
        line = f"# expect: {canonical + 1} passed"
        assert count_sweep._line_hits(line, canonical, class_count) is True

    def test_threshold_prefix_skips_class_count(self, _counts) -> None:
        """Threshold-prefixed class counts (>=, >=, at least) are skipped."""
        canonical, class_count = _counts
        line = f">= {class_count + 1} classes"
        assert count_sweep._line_hits(line, canonical, class_count) is False

    def test_canonical_test_count_in_line_is_not_flagged(self, _counts) -> None:
        """A line with the canonical test count is clean."""
        canonical, class_count = _counts
        line = f"# expect: {canonical} tests"
        assert count_sweep._line_hits(line, canonical, class_count) is False
