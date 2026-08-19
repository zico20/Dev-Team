#!/usr/bin/env python3
"""
Fallback decision used only when code-reviewer fails to produce a valid,
schema-conformant result (an agent failure, not a normal rejection). The
pipeline degrades instead of crashing: gate on the real test results alone,
and always flag the result for a human spot-check since the normal review
never actually ran.

Usage:
    python3 scripts/fallback_gate.py <test-results-file>

Writes review-result.json in the same shape code-reviewer would have
produced, so every downstream step (validation, logging, the CI gate)
keeps working unchanged.
"""
import json
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: fallback_gate.py <test-results-file>")
        sys.exit(2)

    with open(sys.argv[1]) as f:
        tests = json.load(f)

    passed = tests.get("status") == "pass"

    result = {
        "status": "approved" if passed else "rejected",
        "agent": "fallback-gate",
        "reasoning": (
            "code-reviewer failed to produce a valid result; the pipeline "
            "fell back to gating on real test results only."
        ),
        "rejection_feedback": [] if passed else [
            f"{failure['test_name']}: {failure['message']}" for failure in tests.get("failures", [])
        ],
        "confidence": "low",
        "requires_human_spotcheck": True,
    }

    with open("review-result.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"FALLBACK_GATE: {result['status']} (confidence=low, human spot-check required)")


if __name__ == "__main__":
    main()
