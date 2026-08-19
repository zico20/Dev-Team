---
description: Run the full autonomous dev team workflow on a feature request, from requirements through a bounded, verified, and reliably-handled fix/review loop.
argument-hint: [feature-request-text-or-file]
---

Build the feature described in: $ARGUMENTS

## 1. Linear build phase
Each step needs only the previous step's output — do not carry forward
anything earlier than that.

a. `product-owner` reads the feature request, writes requirements.md.
   - Validate: `python3 scripts/validate_schema.py schemas/requirements.schema.json requirements.md`
     - If invalid: build a structured error (`type: schema_invalid`,
       `retriable: false`), then
       `python3 scripts/build_escalation.py infra_error_permanent product-owner 0 unknown "requirements.md failed schema validation"`,
       log it, and **stop the entire run here** — do not let
       `system-architect` work from unvalidated input.
   - Log: `python3 scripts/log_event.py product-owner 0 requirements.md`

b. `system-architect` reads requirements.md, writes architecture.md as a
   design proposal. Do not proceed to coding until this design is accepted.
   - Validate / on failure / log: same pattern as step (a), boundary
     `system-architect`.

c. `coder` reads requirements.md + architecture.md, implements the code.
   - Validate / on failure / log: same pattern as step (a), boundary
     `coder`. (This first invocation is attempt 1 of the review loop below.)

## 2. Bounded, verified review loop (max 3 review attempts)

a. Run the real test suite with bounded infra retries (separate from the
   review-attempt counter — a flaky test environment should not cost the
   Coder one of its 3 attempts):
   ```
   python3 scripts/run_with_retry.py test-runner 2 -- scripts/run_tests.sh
   ```
   - If this ultimately fails: it wrote `error.json`. If `retriable: false`,
     build an escalation (`reason: infra_error_permanent`,
     `boundary: test-runner`) and stop. If retries were simply exhausted on
     a transient error, also escalate the same way — do not let the loop
     spin forever on infrastructure.
   - On success: validate test-results.json against its schema, then log it
     under stage `test-runner`.

b. `qa-tester` reads only the current code + current test-results.json
   (not prior attempts), reports logic_issues and security_issues.
   - Validate / log: standard pattern, boundary `qa-tester`.

c. `code-reviewer` reads only the current qa-tester report, current
   test-results.json, and current code. Returns approved/rejected plus
   confidence and requires_human_spotcheck. Any failing test or high
   security severity is an automatic reject.
   - Validate: `python3 scripts/validate_schema.py schemas/review.schema.json review-result.json`
   - **If this validation fails** (code-reviewer produced an invalid or
     unusable result — an agent failure, not a rejection): do not retry
     the reviewer and do not stop the pipeline. Run
     `python3 scripts/fallback_gate.py test-results.json` to gracefully
     degrade to a tests-only decision (always low confidence, always
     flagged for a human spot-check), then continue to step (d) using that
     result.
   - Log the (real or fallback) result under stage `code-reviewer`.

d. Branch on the result:
   - **Approved, confidence high/medium:** stop the loop, feature complete.
   - **Approved, confidence low:** stop the loop, feature complete, but
     surface `requires_human_spotcheck: true` prominently (e.g. as a CI
     annotation) — do not merge it as if it were a clean approval.
   - **Rejected, attempt < 3:** send rejection_feedback (and any test
     failures) back to `coder` — and only that feedback, not the
     accumulated history of earlier attempts. Increment attempt, repeat
     step 2.
   - **Rejected, attempt == 3:** stop the loop. Build a structured
     escalation:
     ```
     python3 scripts/build_escalation.py review_attempts_exhausted code-reviewer 3 <confidence> "<one-line reason from the last rejection>"
     ```
     Log it under stage `loop-end`, and hand `escalation.json` to a human —
     do not attempt a 4th time.
