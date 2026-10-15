"""LORE-054: match --class filter validates and filters results."""

import subprocess
import sys


def test_match_class_filter_valid_class():
    """--class with a valid class returns only that class."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "match",
            "drain 503",
            "--class",
            "gateway-drain-window",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "gateway-drain-window" in result.stdout
    assert "confidence=0.90" in result.stdout


def test_match_class_filter_unknown_class():
    """--class with unknown class exits 2 with error."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "match",
            "drain 503",
            "--class",
            "nonexistent-class",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown class" in result.stderr


def test_match_class_filter_no_match():
    """--class with valid class but no match returns confidence=0.00."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lore",
            "match",
            "completely unrelated",
            "--class",
            "gateway-drain-window",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "gateway-drain-window" in result.stdout
    assert "confidence=0.00" in result.stdout


def test_match_without_class_unchanged():
    """match without --class still works normally."""
    result = subprocess.run(
        [sys.executable, "-m", "lore", "match", "drain 503"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "gateway-drain-window" in result.stdout
