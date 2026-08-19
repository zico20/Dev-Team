#!/usr/bin/env python3
"""
Run a command with bounded retries for TRANSIENT infrastructure failures
(e.g. a flaky test-runner environment). This is deliberately separate from
the review loop's 3-attempt limit — that counter is for real code
rejections, this one is for tooling that broke before it could even produce
a verdict.

On final failure, writes error.json (schemas/error.schema.json) so the
caller can decide what to do next: a permanent error (retriable: false)
should stop the pipeline and escalate immediately, never be retried
blindly.

Usage:
    python3 scripts/run_with_retry.py <stage-name> <max-retries> -- <command...>

Exit codes:
    0 -> command succeeded (possibly after retries)
    1 -> command failed permanently, or retries were exhausted; error.json written
"""
import json
import platform
import subprocess
import sys
import time


def resolve(command: list[str]) -> list[str]:
    """On Windows, a bare `foo.sh` can't be exec'd (no shebang support) —
    run it through bash explicitly. No-op everywhere else, since `bash
    foo.sh` behaves identically to `./foo.sh` on a real Unix shell."""
    if platform.system() == "Windows" and command and command[0].endswith(".sh"):
        return ["bash"] + command
    return command


def classify(returncode: int, stderr: str):
    """Best-effort classification of a failure into a (type, retriable, hint) triple."""
    text = stderr.lower()

    if "schema_invalid" in text:
        # A boundary-validation failure is permanent: retrying the exact same
        # command will fail the exact same way. The fix belongs upstream, in
        # whichever agent produced the bad output.
        return (
            "schema_invalid",
            False,
            "Upstream output did not match its schema. Fix the producing "
            "agent's output — retrying this step will not help.",
        )
    if "permission denied" in text or "forbidden" in text:
        return "permission_denied", False, "Check the credentials/scope for this step. Escalate — do not retry."
    if "no such file" in text or "not found" in text:
        return "not_found", False, "A required file or dependency is missing. Escalate — retrying will not create it."
    if returncode == 124 or "timeout" in text or "timed out" in text:
        return "timeout", True, "Likely transient. Safe to retry with backoff."
    if "connection" in text or "network" in text or "temporarily unavailable" in text:
        return "network", True, "Likely transient. Safe to retry with backoff."
    return "unknown", True, "Unclassified failure. Retry once with backoff, then escalate if it repeats."


def main() -> None:
    if len(sys.argv) < 5 or sys.argv[3] != "--":
        print("usage: run_with_retry.py <stage-name> <max-retries> -- <command...>")
        sys.exit(2)

    stage = sys.argv[1]
    max_retries = int(sys.argv[2])
    command = resolve(sys.argv[4:])

    attempt = 0
    last_type, last_retriable, last_hint, last_stderr = "unknown", True, "", ""

    while attempt <= max_retries:
        attempt += 1
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            if attempt > 1:
                print(f"INFRA_RECOVERED: '{stage}' succeeded on attempt {attempt}")
            sys.exit(0)

        last_stderr = (result.stderr or result.stdout or "").strip()
        last_type, last_retriable, last_hint = classify(result.returncode, last_stderr)

        if not last_retriable or attempt > max_retries:
            break

        backoff = 2 ** (attempt - 1)
        print(f"INFRA_RETRY: '{stage}' attempt {attempt} failed ({last_type}), retrying in {backoff}s")
        time.sleep(backoff)

    error = {
        "type": last_type,
        "message": (last_stderr[:500] if last_stderr else f"'{stage}' failed with no output"),
        "retriable": last_retriable,
        "hint": last_hint,
        "stage": stage,
        "infra_attempts": attempt,
    }
    with open("error.json", "w") as f:
        json.dump(error, f, indent=2)

    print(f"INFRA_FAILED: '{stage}' -> {last_type} (retriable={last_retriable}) after {attempt} attempt(s)")
    sys.exit(1)


if __name__ == "__main__":
    main()
