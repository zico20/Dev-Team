#!/usr/bin/env python3
"""
Build a compact, structured escalation payload (schemas/escalation.schema.json)
so a human gets one clear summary, not a raw dump of the audit log.

Usage:
    python3 scripts/build_escalation.py <reason> <boundary> <attempt> <confidence> <summary>

Where <reason> is one of:
    review_attempts_exhausted | infra_error_permanent | low_confidence_approval
"""
import json
import sys
from datetime import datetime, timezone


def main() -> None:
    if len(sys.argv) != 6:
        print("usage: build_escalation.py <reason> <boundary> <attempt> <confidence> <summary>")
        sys.exit(2)

    reason, boundary, attempt, confidence, summary = sys.argv[1:6]

    escalation = {
        "to": "human-engineering-lead",
        "reason": reason,
        "boundary": boundary,
        "attempt": int(attempt),
        "confidence": confidence,
        "summary": summary,
        "details_ref": "logs/dev-team-audit.jsonl",
        "escalated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open("escalation.json", "w") as f:
        json.dump(escalation, f, indent=2)

    print(f"ESCALATION_BUILT: {reason} at {boundary} (attempt {attempt}) -> escalation.json")


if __name__ == "__main__":
    main()
