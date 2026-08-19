#!/usr/bin/env python3
"""
Append one structured event to logs/dev-team-audit.jsonl. Called once after
every agent stage and after the test runner, so the full run is reconstructable
after the fact — including every rejected attempt, not just the final result.

Usage:
    python3 scripts/log_event.py <stage> <attempt> <json_file>

Where <stage> is one of:
    product-owner | system-architect | coder | test-runner | qa-tester |
    code-reviewer | loop-end
"""
import json
import os
import sys
from datetime import datetime, timezone


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: log_event.py <stage> <attempt> <json_file>")
        sys.exit(2)

    stage, attempt_str, json_file = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        attempt = int(attempt_str)
    except ValueError:
        print(f"LOG_ERROR: attempt must be an integer, got '{attempt_str}'")
        sys.exit(2)

    try:
        with open(json_file) as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"LOG_ERROR: could not read/parse {json_file}: {e}")
        sys.exit(2)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "attempt": attempt,
        "payload": payload,
    }

    os.makedirs("logs", exist_ok=True)
    with open("logs/dev-team-audit.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

    print(f"LOGGED: stage={stage} attempt={attempt}")


if __name__ == "__main__":
    main()
