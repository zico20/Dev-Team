"""
password_strength.py

A small, self-contained, dependency-free utility for evaluating the
strength of a password string against five fixed rules.

Public API:
    check_password_strength(password: str) -> dict
        Returns {"rating": "weak" | "medium" | "strong", "reasons": [str]}

No imports beyond the Python standard library (in fact, no imports at
all are needed). The function is pure: no I/O, no logging, no global
mutable state, no storage of the password argument.
"""

# ---------------------------------------------------------------------------
# Rating constants
# ---------------------------------------------------------------------------
RATING_WEAK = "weak"
RATING_MEDIUM = "medium"
RATING_STRONG = "strong"

# ---------------------------------------------------------------------------
# Reason message constants (fixed, human-readable, one per rule)
# ---------------------------------------------------------------------------
MSG_MIN_LENGTH = "Password must be at least 8 characters long."
MSG_UPPERCASE = "Password must contain at least one uppercase letter."
MSG_LOWERCASE = "Password must contain at least one lowercase letter."
MSG_DIGIT = "Password must contain at least one digit."
MSG_SPECIAL = "Password must contain at least one special character."

# Minimum length threshold for rule 1.
_MIN_LENGTH = 8

# Threshold (count of satisfied rules) required for the 'medium' rating.
_MEDIUM_THRESHOLD = 3

# Total number of rules; all must be satisfied for 'strong'.
_TOTAL_RULES = 5


def _scan_character_classes(password):
    """
    Single left-to-right pass over the password producing boolean flags
    for the character-class rules (2-5). An empty string yields all-False
    flags with zero iterations, so empty/short inputs need no special case.

    Classification is Unicode-aware via built-in str methods (isupper,
    islower, isdigit, isalnum, isspace).
    """
    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False

    for ch in password:
        if ch.isupper():
            has_upper = True
        if ch.islower():
            has_lower = True
        if ch.isdigit():
            has_digit = True
        if not ch.isalnum() and not ch.isspace():
            has_special = True

    return has_upper, has_lower, has_digit, has_special


def _resolve_rating(satisfied_count):
    """Map the count of satisfied rules to a rating string."""
    if satisfied_count == _TOTAL_RULES:
        return RATING_STRONG
    if satisfied_count >= _MEDIUM_THRESHOLD:
        return RATING_MEDIUM
    return RATING_WEAK


def check_password_strength(password):
    """
    Evaluate a password against five fixed rules:
        1. at least 8 characters long
        2. contains at least one uppercase letter
        3. contains at least one lowercase letter
        4. contains at least one digit
        5. contains at least one special character

    Args:
        password: the password string to evaluate.

    Returns:
        dict: {"rating": "weak" | "medium" | "strong", "reasons": [str, ...]}
        `reasons` lists the fixed failure message for each unsatisfied
        rule, in rule order (length, uppercase, lowercase, digit,
        special). `reasons` is empty exactly when rating is "strong".

    Raises:
        TypeError: if `password` is not a str.
    """
    if not isinstance(password, str):
        raise TypeError(
            "check_password_strength() expects a str argument, got "
            "{!r}".format(type(password).__name__)
        )

    has_upper, has_lower, has_digit, has_special = _scan_character_classes(password)

    # Ordered rule table: (satisfied, failure_message)
    rules = [
        (len(password) >= _MIN_LENGTH, MSG_MIN_LENGTH),
        (has_upper, MSG_UPPERCASE),
        (has_lower, MSG_LOWERCASE),
        (has_digit, MSG_DIGIT),
        (has_special, MSG_SPECIAL),
    ]

    satisfied_count = sum(1 for satisfied, _ in rules if satisfied)
    reasons = [message for satisfied, message in rules if not satisfied]
    rating = _resolve_rating(satisfied_count)

    return {"rating": rating, "reasons": reasons}
