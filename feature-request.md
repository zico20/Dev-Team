# Feature Request: Random Password Generator

We need a small, self-contained Python utility function that generates a
random password meeting a set of strength rules — a natural companion to
the existing password_strength.py checker.

## What it should do
- Take an optional target length (default 12) as input.
- Generate a random password of that length that is guaranteed to satisfy
  all 5 rules used by the existing password strength checker:
  - at least 8 characters long
  - contains at least one uppercase letter
  - contains at least one lowercase letter
  - contains at least one digit
  - contains at least one special character
- Return the generated password as a string.

## Requirements
- The requested length must be at least 8 (the minimum needed to satisfy
  all 5 rules); reject or clearly error on invalid/too-short lengths
  rather than silently producing a weak password.
- The randomness must be cryptographically secure — this is a password
  generator, not a general-purpose random string generator, so predictable
  or weak randomness (e.g. Python's standard `random` module) is not
  acceptable.
- Every character position should be drawn from a reasonable full
  character set (uppercase, lowercase, digits, and special characters),
  not just the minimum one character per required class padded with
  something predictable.
- The output should not follow an easily-guessable pattern (e.g. always
  putting the uppercase letter first, the digit second, etc.) — character
  positions should be shuffled/randomized.

## Notes
- Should reuse or stay consistent with the existing password_strength.py
  module's rule definitions where practical (e.g. the same definition of
  "special character"), rather than inventing a different one.
- No external dependencies needed — pure Python standard library only.
- This will be used as a reusable function other parts of the app can
  import, not a CLI or web endpoint.
