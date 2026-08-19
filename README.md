# Autonomous Software Development Team

A working project you can drop into an agent-capable environment that reads
project-level and agent-level markdown configuration.

## How to run it
1. Place this folder where your environment reads project config
   (`CLAUDE.md`, `.claude/agents/`, `.claude/commands/`).
2. Write your feature request into a file (e.g. `feature-request.md`).
3. Run: `/build-feature feature-request.md`
4. Watch the linear build phase run (Product Owner → Architect → Coder),
   then the bounded review loop (QA → Reviewer → back to Coder if
   rejected, up to 3 times).
5. (Optional) Push to a `feature/**` branch to trigger
   `.github/workflows/dev-team-pipeline.yml` and run the same team
   headlessly, with the review result gating the merge.

## Why the loop is bounded
The fix/resubmit step is a real feedback loop, not a straight pipeline.
Every agentic loop needs an explicit stopping condition — here that's
"approved, OR 3 rejected attempts, then escalate to a human." Leaving this
unbounded is a real bug: without a cap, a stubborn disagreement between the
Coder and the Reviewer could loop forever and burn cost with no output.

## What keeps this loop trustworthy, not just "agents talking to agents"

1. **Real test runner** (`scripts/run_tests.sh` + `scripts/junit_to_json.py`)
   — runs the actual `pytest` suite, converts the JUnit report into
   `test-results.json`. A failing test is an automatic reject for
   `code-reviewer` — a ground-truth signal, not an agent's opinion.

2. **Schema validation, fail-fast at every boundary**
   (`scripts/validate_schema.py`) — every agent's JSON output is checked
   against its schema in `schemas/` before being handed to the next agent.
   A validation failure stops the run at that exact boundary immediately —
   it never gets forwarded, worked around, or silently patched downstream.

3. **Structured errors + bounded infra retries**
   (`scripts/run_with_retry.py`) — separates a normal code rejection from
   an infrastructure failure (e.g. the test runner itself crashing).
   Transient failures (`timeout`, `network`) retry with exponential
   backoff on their own counter, without spending one of the Coder's 3
   review attempts. Permanent failures (`schema_invalid`,
   `permission_denied`, `not_found`) are never retried — they escalate
   immediately, since retrying them would just waste time and cost.

4. **Confidence + graceful degradation**
   (`scripts/fallback_gate.py`) — `code-reviewer` reports a confidence
   level alongside its verdict; low confidence always sets
   `requires_human_spotcheck: true` so a shaky approval never merges
   silently. If `code-reviewer` fails outright (invalid output, not a
   rejection), the system doesn't crash — it falls back to gating on the
   real test results alone, always flagged for a human to check.

5. **Structured escalation, not a raw log dump**
   (`scripts/build_escalation.py`) — when a human is needed (3 rejected
   attempts, a permanent infra error), the system builds one compact
   `escalation.json`: who, why, at which boundary, and a one-line summary
   — with a pointer to the full audit log for anyone who wants to dig
   deeper, instead of handing over the entire run history by default.

6. **Trimmed context on every retry** — `coder` on a retry reads only the
   latest `rejection_feedback` and the files it names, not every prior
   attempt's history. Same for `qa-tester` and `code-reviewer`: they see
   the current attempt only. The full history still lives in the audit
   log for anyone who needs it — it just isn't stuffed into every agent's
   working context by default, which would bury the one thing that
   actually matters (what changed *this* time) under everything that came
   before it.

7. **Observability** (`scripts/log_event.py`) — every stage, including
   every rejected attempt, every infra retry, and every escalation, is
   appended as one line to `logs/dev-team-audit.jsonl` with a timestamp
   and attempt number. This is what an escalation's `details_ref` points
   to, and what lets a human reconstruct exactly what happened without
   re-running anything. In CI, it's uploaded as a build artifact on every
   run — along with `escalation.json` when one was produced.

## File map
- `CLAUDE.md` — project-wide rules every agent must follow: workflow,
  least privilege, schema/fail-fast, structured errors, confidence/
  fallback, escalation, context passing, and observability.
- `.claude/agents/*.md` — one identity file per role.
- `.claude/commands/build-feature.md` — the single entry point;
  orchestrates the full pipeline including validation, infra retry,
  fallback, and escalation at each stage.
- `schemas/*.schema.json` — one schema per agent output, plus
  `test_results.schema.json`, `error.schema.json`, and
  `escalation.schema.json`.
- `scripts/run_tests.sh`, `scripts/junit_to_json.py` — real test execution.
- `scripts/validate_schema.py` — generic output validator.
- `scripts/run_with_retry.py` — bounded retry + backoff for infra
  failures, with error classification.
- `scripts/fallback_gate.py` — graceful degradation when the reviewer's
  output isn't usable.
- `scripts/build_escalation.py` — compact structured hand-off to a human.
- `scripts/log_event.py` — appends one audit event per stage.
- `logs/dev-team-audit.jsonl` — the append-only run history.
- `requirements-dev.txt` — Python deps (`jsonschema`, `pytest`).
- `.github/workflows/dev-team-pipeline.yml` — headless automation with
  infra-retry, schema/fallback/escalation handling, and a review + test
  gate that also surfaces low-confidence approvals instead of hiding them.
