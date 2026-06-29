# Phase 2 — Backend API & Database

Goal: take the Phase 1 rule engine and (a) expose it over HTTP with **FastAPI**,
and (b) **save the results to a database** (SQLModel + Alembic + Postgres/SQLite).
By the end, you can upload a config to an API endpoint and the scan + findings are
stored and can be read back. Team: 4 members. Replace "Member 1/2/3/4" with names.

## How the work is divided (and why this way)

To keep things **simple and conflict-free, each person owns their own files** —
no two people edit the same file. The four areas are clean layers:

| Member | Owns | In plain words |
| ------ | ---- | -------------- |
| **1** | Database (`models.py`, `db.py`, migrations, seed) | The filing cabinet |
| **2** | API contract (`schemas.py`, Swagger docs, `.env.example`) | The agreed shapes of the data |
| **3** | Endpoints (the FastAPI router / routes) | The buttons people press |
| **4** | Tests + CI | Proves it all works |

**Order of work (so nobody is blocked):** Member 1 and Member 2 go first (they
produce the database + the data shapes everyone else needs). Member 3 builds the
endpoints on top of them. Member 4 tests the result. Members 3 and 4 can start
against a SQLite database and stub data while 1 and 2 finish.

## High-level workflow
- All work on a feature branch per task; PR required to merge to main.
- Every task has a Lead (implements), Reviewer (code review + QA), and Tester
  (writes/maintains tests). Roles rotate so everyone learns every step.
- **The API contract (Swagger/OpenAPI) is the source of truth** — Phase 3
  (frontend) builds against it, so keep it current.
- **Every database query must be user-scoped** (filter by `user_id`). Login
  arrives in Phase 8, but building scoping in now prevents the IDOR hole later.
- **Parameterized queries only** (SQLModel does this) — never string-built SQL.
- Daily 30m sync during Phase 2 (Weeks 3–4 suggested timeline).

---

## Deliverables (phase)
- `/backend/src/db.py`, `/backend/src/models.py` (5 tables).
- `/backend/alembic/` + `alembic.ini` (migrations create all tables) + seeded
  `compliance_map`.
- `/backend/src/schemas.py` (Pydantic request/response models).
- `/backend/src/routes.py` (or `main.py`) with `POST /scans/upload`, `GET /scans`,
  `GET /scans/{scan_id}`, `GET /scans/{scan_id}/findings`.
- Swagger/OpenAPI docs live at `/docs`.
- `/backend/tests/test_api.py` (httpx) — all tests passing.

---

## Member 1 — Database (Lead)

What to do
- Own everything that touches the database: the tables, the connection, the
  migrations, and the seed data. Nobody else writes DB code.

How (step-by-step)
1. `backend/src/db.py`: create the SQLModel engine + a session helper. Read the
   connection string from `DATABASE_URL` in the environment — **SQLite** for local
   dev, **Neon Postgres** in production. Never hard-code credentials.
2. `backend/src/models.py`: one SQLModel class per table from planning doc §10 —
   `users`, `scans`, `findings`, `compliance_map`, `audit_log`. Use enums for
   `role`, `scan_type`, `status`, `severity`; UUID primary keys; foreign keys.
3. Set up **Alembic**, point it at the models, and generate the initial migration
   that creates all tables. Document `alembic upgrade head`.
4. Seed `compliance_map` with the CIS ID, NIST ID, and remediation for each of the
   5 Phase-1 rules (copy from `/rules`).

Tools & tech
- SQLModel, SQLAlchemy, Alembic, python-dotenv.

Tests & measurement
- `alembic upgrade head` builds all 5 tables on a clean database.
- The seed inserts exactly 5 `compliance_map` rows.
- A smoke test inserts a `scan` row and reads it back.

Deliverables & checklist
- [ ] `db.py` (env-based connection)
- [ ] `models.py` (5 tables + enums + keys)
- [ ] Alembic migration creates all tables
- [ ] `compliance_map` seeded for CIS-AWS-001..005

---

## Member 2 — API Contract: Schemas & Docs (Lead)

What to do
- Own the "shapes" of the data the API accepts and returns, plus the public docs.
- This is the agreement Members 3 and 4 build against, so it comes early.

How (step-by-step)
1. `backend/src/schemas.py`: write **all** the Pydantic request/response models —
   the upload response, a scan summary, a scan-with-findings, a single finding,
   and a shared error model. One file, one owner.
2. Define the shared input rules as constants other code imports: the file
   extension allowlist (`.json/.yaml/.yml`) and the standard error shape.
3. Make sure Swagger/OpenAPI at `/docs` renders cleanly — add example values to
   the models so the page is self-explanatory — then **share the link with the
   team** as the contract.
4. Update `.env.example` with `DATABASE_URL` and document SQLite-vs-Neon setup.

Tools & tech
- Pydantic v2, FastAPI (for the auto-docs), python-dotenv.

Tests & measurement
- Every model has an example and validates a sample payload.
- `/docs` loads and shows all four endpoints once Member 3 wires them.

Deliverables & checklist
- [ ] `schemas.py` with all request/response + error models
- [ ] Extension allowlist + error shape as importable constants
- [ ] Swagger `/docs` clean and shared with the team
- [ ] `.env.example` updated

---

## Member 3 — Endpoints (Lead)

What to do
- Own the FastAPI router. Build all four endpoints using Member 1's models and
  Member 2's schemas. Nobody else edits the routes file.

How (step-by-step)
1. `POST /scans/upload`:
   - Check `Content-Type` + the extension allowlist (from Member 2's constants).
   - Reuse the Phase 1 `SecureParser` (size/depth limits + safe parse).
   - Run the parsed config through the Phase 1 `RuleEngine`.
   - Save one `scans` row (`scan_type = Static`) + one `findings` row per finding,
     then return Member 2's response model.
   - Turn bad input into a clean `400` (never a 500 stack trace).
2. `GET /scans` — list the caller's scans.
3. `GET /scans/{scan_id}` — one scan with its findings.
4. `GET /scans/{scan_id}/findings` — findings detail.
5. **Scope every query to the current user** with a placeholder `current_user`
   dependency (real auth in Phase 8). If a scan isn't the caller's, return `404`.

Tools & tech
- FastAPI, SQLModel, the Phase 1 `parser.py` + `rule_engine.py`.

Tests & measurement
- Uploading a known-bad fixture creates a scan + the right findings.
- Read endpoints return stored data, scoped to the caller.
- Another user's scan returns `404` (IDOR check).

Deliverables & checklist
- [ ] `POST /scans/upload` (parse → evaluate → store)
- [ ] Three read endpoints, all user-scoped
- [ ] Clean `400`/`404` handling

---

## Member 4 — Tests & CI (Lead)

What to do
- Own the testing of the whole API and the CI that runs it. Stop broken code from
  merging.

How (step-by-step)
1. Build a test harness: a throwaway **SQLite** database with a FastAPI dependency
   override so tests never touch the real DB; fresh schema per test run.
2. `backend/tests/test_api.py` with **httpx** / `TestClient`:
   - Happy path: upload a bad fixture → it's stored → read it back via GET.
   - Validation failures (wrong type, oversized) return `400`.
   - IDOR test: user A cannot read user B's scan.
3. Extend CI (the Phase 1 GitHub Actions workflow, or a new `phase2` one) to run
   the API tests and `alembic upgrade head` (so migrations are checked too).

Tools & tech
- pytest, httpx, FastAPI `TestClient`, SQLite, GitHub Actions.

Tests & measurement
- Full upload→retrieve flow passes in CI.
- Coverage for the API/DB layer >= 80% lines.
- Zero failing PRs allowed to merge.

Deliverables & checklist
- [ ] Test DB harness with dependency override
- [ ] `test_api.py` (happy path + validation + IDOR) passing
- [ ] CI runs API tests + migrations

---

## Collaboration & Rotation Plan (ensures everyone learns every step)
- Four work items (database, contract, endpoints, tests). Rotate so each person
  leads one and reviews/tests the others:
  - Database: M1 lead, M2 review, M3 test, M4 second-review
  - Contract: M2 lead, M3 review, M4 test, M1 second-review
  - Endpoints: M3 lead, M4 review, M1 test, M2 second-review
  - Tests & CI: M4 lead, M1 review, M2 test, M3 second-review
- Every PR includes: feature branch, tests, an assigned reviewer, and a short
  checklist (schema used, query is user-scoped, migration updated if models
  changed, tests pass).
- One 90-min pairing session per week: the lead codes while others ask questions.

---

## How to test & measure overall Phase 2 success
- Acceptance criteria (all must pass — these match the phase Definition of Done):
  1. Uploading a bad config via the API creates `scan` + `findings` rows in the DB.
  2. The read endpoints return the stored findings.
  3. All request/response bodies are validated by Pydantic.
  4. All queries are parameterized and **user-scoped** (no IDOR).
  5. `alembic upgrade head` builds the schema on a clean database.
  6. Swagger docs are live at `/docs` and shared with the team.
  7. Every PR reviewed by a teammate and merged only after tests pass.

Metrics to record (in `/docs/phase2-metrics.md`):
- Number of endpoints implemented.
- Tests passed/failed and coverage %.
- Average PR review iterations per PR.
- Upload→store→retrieve round-trip time on the standard fixture (ms).

---

## Suggested schedule (2 weeks)
- Day 1: Kickoff; agree the API contract + table shapes together; create branches.
- Days 2–3: Member 1 lands models + db + first migration; Member 2 lands schemas +
  Swagger; Member 4 starts the test harness.
- Days 4–7: Member 3 builds all four endpoints against SQLite.
- Days 8–9: Wire up Neon, seed `compliance_map`, finish API tests + CI.
- Day 10: Cleanup, Swagger published, docs, and merge to main.

---

## Notes
- Keep secrets out of repo; use `.env` for local testing and `.env.example`
  committed (now includes `DATABASE_URL`).
- Keep PRs small (<300 lines) for faster reviews.
- The same rule engine from Phase 1 is reused unchanged — the API just wraps it
  and stores the results.
- One file per owner is the whole point: if you find yourself needing to edit
  someone else's file, raise it at the daily sync instead.

---
