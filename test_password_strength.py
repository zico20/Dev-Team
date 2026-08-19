"""Harness-owned acceptance tests for password_strength.py.

Written from requirements.md acceptance_criteria and architecture.md's
public API contract (check_password_strength(password: str) -> dict with
keys "rating" and "reasons"). Not authored by coder per CLAUDE.md rules.
"""
import pytest

from password_strength import check_password_strength


def test_strong_password_all_rules_satisfied():
    result = check_password_strength("Abcdef1!")
    assert result["rating"] == "strong"
    assert result["reasons"] == []


def test_medium_password_missing_two_rules():
    # 8 chars, has upper/lower/digit, no special -> 4/5 rules -> medium
    result = check_password_strength("Abcdefg1")
    assert result["rating"] == "medium"
    assert len(result["reasons"]) == 1


def test_medium_password_exactly_three_rules():
    # "abcdefg1" -> lower + digit + length = 3/5 -> medium
    result = check_password_strength("abcdefg1")
    assert result["rating"] == "medium"
    assert len(result["reasons"]) == 2


def test_weak_password_few_rules_satisfied():
    # "abc" -> only lowercase satisfied (1/5) -> weak
    result = check_password_strength("abc")
    assert result["rating"] == "weak"
    assert len(result["reasons"]) == 4


def test_empty_string_does_not_crash():
    result = check_password_strength("")
    assert result["rating"] == "weak"
    assert len(result["reasons"]) == 5


def test_very_short_password_does_not_crash():
    result = check_password_strength("a1")
    assert result["rating"] == "weak"
    assert isinstance(result["reasons"], list)


def test_reasons_reflect_only_unmet_rules():
    # Missing only the special character rule.
    result = check_password_strength("Abcdefg1")
    reasons_text = " ".join(result["reasons"]).lower()
    assert "special character" in reasons_text
    assert "uppercase" not in reasons_text
    assert "lowercase" not in reasons_text
    assert "digit" not in reasons_text
    assert "8 characters" not in reasons_text


def test_importable_and_callable_directly():
    import password_strength
    assert callable(password_strength.check_password_strength)
