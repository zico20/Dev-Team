"""
password_generator.py

A small, self-contained, dependency-free utility for generating random
passwords that are guaranteed to satisfy all five rules enforced by
password_strength.check_password_strength(): minimum length, at least
one uppercase letter, at least one lowercase letter, at least one digit,
and at least one special character.

Public API:
    generate_password(length: int = 12) -> str
        Returns a randomly generated password string of the requested
        length.
    MIN_LENGTH
        Smallest length accepted by generate_password().
    MAX_LENGTH
        Largest length accepted by generate_password().

Only the Python standard library is used (`secrets` and `string`). All
randomness -- both character selection and final ordering -- comes
exclusively from the `secrets` module; the `random` module is not
imported anywhere, not even random.SystemRandom. The function is pure:
no I/O, no logging, no global mutable state, no storage of the generated
password anywhere in this module, and no dependency on
password_strength.py.
"""

import secrets
import string

__all__ = ["MIN_LENGTH", "MAX_LENGTH", "generate_password"]

# ---------------------------------------------------------------------------
# Length bounds
# ---------------------------------------------------------------------------
MIN_LENGTH = 8
MAX_LENGTH = 1024

# ---------------------------------------------------------------------------
# Character pool constants -- frozen at import, never mutated or rebuilt.
# ---------------------------------------------------------------------------
_UPPER = string.ascii_uppercase
_LOWER = string.ascii_lowercase
_DIGITS = string.digits
_SPECIAL = string.punctuation
_ALL = _UPPER + _LOWER + _DIGITS + _SPECIAL

# Number of required character classes (one guaranteed character each).
_REQUIRED_CLASSES = (_UPPER, _LOWER, _DIGITS, _SPECIAL)


def _validate_length(length):
    """
    Validate a requested password length.

    bool is rejected explicitly (checked before the int check, since
    bool is a subclass of int in Python) and any other non-int is
    rejected with TypeError. Ints outside [MIN_LENGTH, MAX_LENGTH] are
    rejected with ValueError. Returns nothing; callers proceed only if
    no exception is raised.

    Raises:
        TypeError: if `length` is not an int, or is a bool.
        ValueError: if `length` is an int outside [MIN_LENGTH, MAX_LENGTH].
    """
    if isinstance(length, bool):
        raise TypeError(
            "generate_password() expects an int argument, got bool"
        )
    if not isinstance(length, int):
        raise TypeError(
            "generate_password() expects an int argument, got "
            "{!r}".format(type(length).__name__)
        )
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(
            "generate_password() length must be between {} and {} "
            "(inclusive), got {}".format(MIN_LENGTH, MAX_LENGTH, length)
        )


def _secure_shuffle(chars):
    """
    Shuffle a list of characters in place using a cryptographically
    secure Fisher-Yates algorithm. Every swap index is drawn from
    secrets.randbelow, so no character occupies a fixed or predictable
    position. Does not use the `random` module.

    Args:
        chars: list of single-character strings to shuffle in place.

    Returns:
        None. `chars` is mutated in place.
    """
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]


def generate_password(length=12):
    """
    Generate a random password that satisfies all five rules enforced
    by password_strength.check_password_strength(): at least `length`
    characters, and at least one uppercase letter, one lowercase
    letter, one digit, and one special character.

    One guarantee character is drawn from each of the four required
    character classes, the remaining positions are filled from the
    combined pool of all four classes, and the full buffer is shuffled
    with a cryptographically secure Fisher-Yates before being joined
    into the returned string. All randomness comes from the `secrets`
    module.

    Args:
        length: target password length, defaults to 12. Must be an int
            in the inclusive range [MIN_LENGTH, MAX_LENGTH].

    Returns:
        str: a randomly generated password of exactly `length`
        characters.

    Raises:
        TypeError: if `length` is not an int (including bool).
        ValueError: if `length` is an int outside
            [MIN_LENGTH, MAX_LENGTH].
    """
    _validate_length(length)

    chars = [secrets.choice(pool) for pool in _REQUIRED_CLASSES]

    for _ in range(length - len(_REQUIRED_CLASSES)):
        chars.append(secrets.choice(_ALL))

    _secure_shuffle(chars)

    return "".join(chars)
