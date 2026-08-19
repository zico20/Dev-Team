# Autonomous Software Development Team — Project Rules

## Purpose
Take a feature request from idea to reviewed, working code: a Product Owner
defines requirements, a System Architect designs the system, a Coder
implements it, a QA/Tester checks for logic and security issues, and a Code
Reviewer makes the final approve/reject call. Rejections loop back to the
Coder until the code is approved or a retry limit is reached.

## Team
- `product-owner` — turns a raw feature request into `requirements.md`.
- `system-architect` — turns requirements into `architecture.md` (a design
  proposal, not code).
- `coder` — implements the architecture as code, and fixes it on rejection.
- `qa-tester` — searches the code for logic/security issues (read-only).
- `code-reviewer` — approves or rejects the code (read-only, final gate).

## Rules that apply to every agent
1. Never fabricate requirements, design decisions, or findings that weren't
   actually derived from the previous agent's actual output.
2. Each agent stays inside its own stage: the Coder does not redesign the
   architecture, QA does not rewrite code, the Reviewer does not fix bugs
   itself — it only reports what must change.
3. Tool access is least-privilege, matched to what each role actually needs:
   - `product-owner`, `system-architect`: `Read, Write` (their own document only).
   - `coder`: `Read, Write` (source files only, never test files).
   - `qa-tester`: `Read, Grep` — read-only, cannot modify anything.
   - `code-reviewer`: `Read` only — cannot modify or search, only reads the
     code and QA's report and decides.

## Workflow
1. **Linear build phase** (each step strictly depends on the previous
   output): `product-owner` → `system-architect` → `coder`.
2. **Design-before-code discipline:** `architecture.md` is a proposal.
   Coding does not start until the architecture is accepted — architecture
   mistakes are expensive to fix once code is built on top of them.
3. **Automated test verification:** after `coder` submits, run
   `scripts/run_tests.sh` before any agent judges the code. It produces
   `test-results.json` (see `schemas/test_results.schema.json`) — a
   ground-truth pass/fail signal that does not depend on any agent's
   opinion.
4. **Bounded review loop:** `coder` → test runner → `qa-tester` →
   `code-reviewer`. If rejected, feedback goes back to `coder`, which fixes
   and resubmits.
   - **Stopping condition:** the loop ends when `code-reviewer` approves,
     OR after **3 rejected attempts**, at which point the system escalates
     to a human instead of retrying again. An unbounded retry loop is a bug.
   - **Automatic reject rule:** any failing test in `test-results.json`
     (`status: "fail"`) is treated exactly like a "high" security severity
     finding — `code-reviewer` must reject, no judgment call needed.

## Output validation (schema gate) — and fail-fast at every boundary
Every agent's JSON output is validated against its schema in `schemas/`
**before** it is handed to the next agent:

| Agent output | Schema |
|---|---|
| `requirements.md` | `schemas/requirements.schema.json` |
| `architecture.md` | `schemas/architecture.schema.json` |
| coder result | `schemas/coder.schema.json` |
| `test-results.json` | `schemas/test_results.schema.json` |
| qa-tester result | `schemas/qa.schema.json` |
| code-reviewer result | `schemas/review.schema.json` |

Run with: `python3 scripts/validate_schema.py <schema_file> <json_file>`.

**Fail-fast rule:** a schema-validation failure is a permanent boundary
error, not a normal rejection and not something to retry. Stop the pipeline
at that exact boundary immediately, build a structured error
(`schemas/error.schema.json`, `type: "schema_invalid"`, `retriable: false`)
and escalate — never forward malformed output to the next agent, and never
let a later stage work around bad input from an earlier one. Catching this
one step late is far more expensive than catching it here.

## Structured errors and bounded infra retries
Two different kinds of failure can happen in this system, and they must be
handled differently:

- **A code rejection** (`code-reviewer` says "rejected") is a normal,
  expected outcome of the review loop — it counts toward the 3-attempt
  limit above.
- **An infrastructure/tool failure** (the test runner crashes, a script
  errors before producing output) is a different kind of problem and uses
  its own, separate structured error:
  ```
  { "type": "...", "message": "...", "retriable": true|false, "hint": "..." }
  ```
  Wrap steps that touch the environment (currently: the test runner) with:
  ```
  python3 scripts/run_with_retry.py <stage-name> <max-infra-retries> -- <command...>
  ```
  - **Retriable** types (`timeout`, `network`, `unknown`) get retried with
    exponential backoff, up to the given limit — and this does **not**
    consume one of the 3 review-loop attempts.
  - **Non-retriable** types (`schema_invalid`, `permission_denied`,
    `not_found`) must not be retried at all — retrying a permanent error
    just wastes time and cost. Escalate immediately instead.

## Confidence and graceful degradation (fallback)
`code-reviewer` reports a `confidence` alongside its verdict:
- **High/medium confidence:** proceed normally — approved means approved,
  rejected feeds back into the loop.
- **Low confidence** (on either verdict): `requires_human_spotcheck` must be
  `true`. This does not block the loop by itself, but the result must be
  visibly flagged downstream (e.g. in CI) rather than merged silently.

If `code-reviewer` itself fails to produce a schema-valid result (an agent
failure, not a rejection), the system does not crash — it degrades
gracefully:
```
python3 scripts/fallback_gate.py <test-results-file>
```
This produces a same-shaped `review-result.json` gated purely on the real
test results, always with `confidence: "low"` and
`requires_human_spotcheck: true`, so every downstream step keeps working
unchanged.

## Escalation — structured hand-off, not a raw log dump
When the system needs a human (3 rejected attempts, a permanent infra
error, or a pattern of low-confidence approvals worth a look), build a
compact, structured escalation instead of handing over the entire audit
log:
```
python3 scripts/build_escalation.py <reason> <boundary> <attempt> <confidence> <summary>
```
This writes `escalation.json` (`schemas/escalation.schema.json`): who it
goes to, why, at which boundary, and a one-line summary — with
`details_ref` pointing at the full audit log for anyone who needs to dig
deeper. The summary is what a human reads first; the log is what they read
only if they need to.

## Context passing — do not accumulate history into every prompt
Each agent reads only what its current step needs, not the full run
history:
- `coder`, on a retry, reads only the latest `rejection_feedback` and the
  specific files it names — not every prior attempt's feedback.
- `qa-tester` and `code-reviewer` read only the current attempt's code,
  report, and test results — not earlier versions or earlier reports.
- The full history still exists (in `logs/dev-team-audit.jsonl`) for a
  human or an escalation to consult — it is just not stuffed into every
  agent's working context by default. Piling on history makes the
  important, current information harder to find and burns budget for no
  benefit.

## Observability (audit log)
After every stage — including every rejected loop attempt, every infra
retry, and every escalation, not just the final result — append the
stage's output to an append-only log:

```
python3 scripts/log_event.py <stage-name> <attempt-number> <json-file>
```

This writes one line per event to `logs/dev-team-audit.jsonl`, each with a
timestamp, stage name, attempt number, and the full payload. This is the
source of truth an escalation's `details_ref` points to, and what lets a
human reconstruct exactly what happened without re-running anything.
