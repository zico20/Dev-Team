"""
Harness-owned acceptance tests for password_generator.py.

Written from requirements.md acceptance_criteria and architecture.md's
public API contract (generate_password(length: int = 12) -> str,
MIN_LENGTH = 8, MAX_LENGTH = 1024, TypeError on non-int, ValueError on
out-of-range int). Not authored by coder per CLAUDE.md rules.
"""
import inspect

import pytest

import password_generator
from password_generator import generate_password, MIN_LENGTH, MAX_LENGTH
from password_strength import check_password_strength


def test_default_length_is_strong():
    password = generate_password()
    assert len(password) == 12
    result = check_password_strength(password)
    assert result["rating"] == "strong"
    assert result["reasons"] == []


@pytest.mark.parametrize("length", [8, 16, 40])
def test_explicit_valid_lengths_are_strong(length):
    password = generate_password(length)
    assert len(password) == length
    result = check_password_strength(password)
    assert result["rating"] == "strong"
    assert result["reasons"] == []


@pytest.mark.parametrize("length", [0, 1, 7, -1, -100])
def test_too_short_length_raises_value_error(length):
    with pytest.raises(ValueError):
        generate_password(length)


@pytest.mark.parametrize("length", [8.0, "12", None, 12.5, [12]])
def test_non_integer_length_raises_type_error(length):
    with pytest.raises(TypeError):
        generate_password(length)


@pytest.mark.parametrize("length", [True, False])
def test_bool_length_raises_type_error(length):
    # bool is a subclass of int in Python; must still be rejected as a type error.
    with pytest.raises(TypeError):
        generate_password(length)


def test_length_above_max_raises_value_error():
    with pytest.raises(ValueError):
        generate_password(MAX_LENGTH + 1)


def test_min_and_max_constants_match_spec():
    assert MIN_LENGTH == 8


def test_repeated_calls_produce_different_passwords():
    passwords = {generate_password(12) for _ in range(50)}
    assert len(passwords) > 1


def test_does_not_use_random_module():
    source = inspect.getsource(password_generator)
    assert "import random" not in source
    assert "from random" not in source


@pytest.mark.parametrize("length", [8, 12, 20, 50, 100])
def test_sweep_of_lengths_always_satisfies_all_rules(length):
    for _ in range(5):
        password = generate_password(length)
        result = check_password_strength(password)
        assert result["rating"] == "strong", (length, password, result)
        assert result["reasons"] == []
