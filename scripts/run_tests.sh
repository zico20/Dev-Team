#!/usr/bin/env bash
# Runs the project's real test suite and produces test-results.xml (JUnit format),
# which junit_to_json.py then converts into the project's own test-results.json
# schema (schemas/test_results.schema.json).
#
# Usage: scripts/run_tests.sh [pytest args...]

set -uo pipefail

pytest --junitxml=test-results.xml "$@"
TEST_EXIT=$?

# pytest exit codes: 0 = all tests passed, 1 = some tests failed but pytest
# itself ran fine and produced a report. Both are a successful run of the
# test *runner* — the failing-tests case is ground truth for code-reviewer
# to reject on, not an infra problem for run_with_retry.py to retry.
# Codes 2-5 (usage error, internal error, no tests collected, ...) mean the
# runner itself didn't do its job, which is a real infra failure.
if [ "$TEST_EXIT" -gt 1 ]; then
    exit $TEST_EXIT
fi

python3 scripts/junit_to_json.py test-results.xml test-results.json
JSON_EXIT=$?

exit $JSON_EXIT
