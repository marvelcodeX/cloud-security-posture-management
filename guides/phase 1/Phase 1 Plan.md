# Phase 1 — Core Rule-Based Detection Engine

Goal: build a standalone Python module that securely parses uploaded cloud configs (JSON/YAML) and emits findings via a declarative YAML rule set. Team: 3 members. Replace "Member 1/2/3" with real names.

## High-level workflow
- All work on a feature branch per task; PR required to merge to main.
- Every task has a Lead (implements), Reviewer (code review + QA), and Tester (writes/maintains fixtures & tests). Roles rotate per rule to ensure each member learns every step.
- Daily 30m sync during Phase 1 (Weeks 2–3 suggested timeline).

---

## Deliverables (phase):
- `/rules/` with 5–8 starter YAML rule files.
- `/backend/src/rule_engine.py` (importable module: loader, evaluator).
- `/backend/src/parser.py` (secure parser with limits).
- `/backend/tests/fixtures/` good/bad configs.
- `/backend/tests/test_rules.py` (pytest) — all tests passing.

---

## Member 1 — Rule Format, Starter Rules & Documentation (Lead)

What to do
- Design rule YAML schema and author 2–3 starter rules.
- Document rule fields, condition operators, and examples in `/rules/README.md`.

How (step-by-step)
1. Create `/rules/spec.yaml` documenting fields: rule_id, name, severity, compliance, condition (resource_type, eval_path, equals/contains/regex, numeric comparisons), remediation.
2. Write 2–3 rules (e.g., S3 public read, SG ingress 0.0.0.0/0, IAM wildcard action) as YAML files in `/rules`.
3. Add examples and edge-case notes.

Tools & tech
- Editor (VS Code), YAML lint (`yamllint`), git + PRs.

Tests & measurement
- Each rule must have a paired bad fixture that triggers it and a good fixture that does not.
- Measure by test pass rate (target 100% for fixtures) and code review feedback count (<=2 iterative rounds).

Deliverables & checklist
- [ ] `/rules/spec.yaml` created
- [ ] 2–3 rule YAML files
- [ ] Examples and mapping to CIS IDs in `/rules/README.md`

---

## Member 2 — Secure Parser & Rule Evaluator (Lead)

What to do
- Build secure YAML/JSON parser and the rule evaluation engine that loads rule YAML and runs conditions against resources.

How (step-by-step)
1. Implement `/backend/src/parser.py`:
   - Enforce max file size (e.g., 2MB) before reading.
   - Use `yaml.safe_load` for YAML; wrap parse in `concurrent.futures.ThreadPoolExecutor` with timeout or use `signal` timeout pattern for CLI tests.
   - Limit nesting depth and reject aliases/anchors if detected.
2. Implement `/backend/src/rule_engine.py`:
   - Loader: read all YAML rules from `/rules`.
   - Evaluator: for each resource, do path lookups (dot/bracket path), apply operators (`equals`, `contains`, `regex`, `gte`, `lte`).
   - Emit finding dict: resource_id, resource_type, severity, rule_id, message.
3. Add logging (not secrets) and clear exceptions for invalid input.

Tools & tech
- Python 3.11, PyYAML, pytest for unit tests, `jsonschema` optional for parsed structure checks.

Tests & measurement
- Unit tests: parser rejects malicious/deep payloads; engine flags expected findings for provided fixtures.
- Performance: parse + evaluate on a 100-resource fixture should complete < 1s locally. Measure with `time` in tests; add a pytest marker to assert time threshold.

Deliverables & checklist
- [ ] `/backend/src/parser.py` with size/depth/timeout protections
- [ ] `/backend/src/rule_engine.py` that loads rules and returns findings
- [ ] Logging + clear error messages

---

## Member 3 — Fixtures, Unit Tests & CI Integration (Lead)

What to do
- Write good/bad fixtures for each starter rule; write pytest tests; add a minimal CI job to run tests locally/preview.

How (step-by-step)
1. Create `/backend/tests/fixtures/good/` and `/backend/tests/fixtures/bad/` with JSON/YAML files matching each rule.
2. Implement `/backend/tests/test_rules.py`:
   - Parametrized tests: for each bad fixture assert engine returns the expected rule_id; for each good fixture assert no findings.
   - Add parser edge-case tests: huge file, deep-nested YAML, YAML alias abuse.
3. Add a simple GitHub Actions workflow skeleton (or local run script) that runs `pytest -q`.

Tools & tech
- Pytest, httpx not needed here, GitHub Actions skeleton (optional) or `./infra/test-runner.sh`.

Tests & measurement
- Goal: 100% tests passing. Also track test coverage for the engine module (target >=80% lines).
- Track failing CI runs: zero failing PRs allowed to merge.

Deliverables & checklist
- [ ] fixtures for each rule (good + bad)
- [ ] `test_rules.py` passing locally
- [ ] CI/test-runner to run pytest

---

## Collaboration & Rotation Plan (ensures everyone learns every step)
- For each starter rule (5–8 total), rotate roles: Lead → Reviewer → Tester. Example for 5 rules:
  - Rule 1: Member1 lead, Member2 review, Member3 test
  - Rule 2: Member2 lead, Member3 review, Member1 test
  - Rule 3: Member3 lead, Member1 review, Member2 test
  - Continue rotation for remaining rules.
- Every PR must include: feature branch, unit tests, reviewer assigned, and a short PR checklist (parser safety, rule mapping, fixture added, tests pass).
- Pair-program session: once per week, do a 90-min pairing where the lead codes and others ask questions; the reviewer runs test coverage and suggests improvements.

---

## How to test & measure overall Phase 1 success
- Acceptance criteria (all must pass):
  1. `pytest` passes for all fixtures (0 failures).
  2. Parser rejects malformed / malicious payloads (tested via fixtures).
  3. Starter rules correctly map to CIS IDs and remediation exists.
  4. Performance: parse + evaluate <=1s for 100-resource fixture.
  5. Code review: each PR reviewed by at least one teammate and merged only after tests pass.

Metrics to record (in `/docs/phase1-metrics.md`):
- Number of rules implemented.
- Tests passed/failed.
- Average PR review iterations per PR.
- Parser parse time on standard fixture (ms).

---

## Suggested schedule (2 weeks)
- Day 1: Kickoff, agree rule set, create branches.
- Days 2–4: Member leads implement first rule components + fixtures.
- Days 5–7: Finish remaining rules, parser improvements, testing.
- Days 8–10: Cleanup, docs, and merge to main.

---

## Notes
- Keep secrets out of repo; use `.env` for local testing and `.env.example` committed.
- Keep PRs small (<300 lines) for faster reviews.

---

## What We Actually Did in Phase 1

Phase 1 is **done and working** — all tests pass. Here is the whole thing in
simple words.

**The goal:** build the part of the tool that reads a cloud config file and points
out the security mistakes in it.

**What we built:**

1. **The rules** (`/rules/`) — 5 security checks written as simple YAML files
   (not code), so anyone can add a new check by adding a file:
   - S3 bucket open to the public
   - S3 bucket with no encryption
   - Security group open to the whole internet (`0.0.0.0/0`)
   - IAM policy with a wildcard action (`*`)
   - IAM policy with a wildcard principal (`*`)
   Each check is tagged with its CIS and NIST compliance ID and a fix tip.

2. **The safe file reader** (`backend/src/parser.py`) — opens uploaded JSON/YAML
   files safely. It blocks files that are too big, too deeply nested, or try
   YAML "bomb" tricks — but still allows normal files (including ones that
   legitimately contain `*`).

3. **The rule engine** (`backend/src/rule_engine.py`) — takes the file, runs every
   rule against every resource, and returns a list of findings (what's wrong,
   how serious, which rule, and how to fix it).

4. **The tests** (`backend/tests/`) — example "good" and "bad" config files plus an
   automatic test suite that proves: bad files get flagged, good files don't, and
   the safety limits work. **All 14 tests pass.**

5. **Automation** — `scripts/run_tests.sh` runs the tests with one command, and a
   GitHub Action runs them automatically on every pull request.

**How the work was split (and reviewed):**

- **Member 1** wrote the rules + their format.
- **Member 2** wrote the safe file reader + the rule engine.
- **Member 3** wrote the test files, the test suite, and the CI, and reviewed
  Members 1 & 2's work — fixing a critical bug (the reader was throwing away any
  file containing `*`, which would have broken the wildcard checks) and filling in
  the missing compliance IDs and rules.

Full details of what was fixed are in `guides/Phase 1 Review and Fixes.md`.

**Result:** you can hand the engine a cloud config and it correctly reports the
security problems in it. This is the foundation the API (Phase 2), the dashboard
(Phase 3), and live cloud scanning (Phase 4) all build on.

---
