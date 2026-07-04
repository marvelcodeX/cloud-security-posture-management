# Phase 2 Fixes — Member 1 & Member 2 Work

This document records everything that was wrong in the **Member 1** (database:
`models.py`, `db.py`, migrations, seed) and **Member 2** (API contract:
`schemas.py`, `.env.example`) deliverables, and how each item was fixed.

The original draft code lived as text in `phase 2 member work/` (it had not been
committed because the authors were unsure it was correct). It has now been
corrected and placed in its real home under `backend/`. **Members 3 (endpoints)
and 4 (tests/CI) are not yet done** — none of their work was required to fix or
verify Members 1 & 2; the two layers are self-contained.

Source of truth for the schema is `docs/schema.md` (the agreed logical schema),
reconciled with two additive fields the application genuinely needs
(`scans.filename`, `findings.message`).

---

## Summary of verification (fixed system)

All of the following now pass with a clean database:

| Check | Result |
| --- | --- |
| `alembic upgrade head` builds all 5 tables | ✅ |
| Seed inserts exactly 5 `compliance_map` rows (CIS-AWS-001..005) | ✅ |
| ORM insert/read across all 5 tables (relationships + FK join) | ✅ |
| `findings.rule_id` FK rejects an unknown rule | ✅ |
| Pydantic schemas build directly from ORM objects (`from_attributes`) | ✅ |
| Phase 1 rule-engine finding → `FindingResponse` + `Finding` model | ✅ |
| Phase 1 test suite still green | ✅ 14 passed |

---

## Member 1 — `backend/src/models.py`

### 1. BLOCKING: `from __future__ import annotations` broke all ORM usage
- **Wrong:** the module started with `from __future__ import annotations`.
  Combined with SQLModel's `Relationship(List["Scan"])` declarations, PEP 563
  stringized annotations cause SQLAlchemy 2.x mapper initialization to fail:
  `InvalidRequestError: ... "relationship("List['C']")" seems to be using a
  generic class as the argument to relationship()`. Tables could be *created*,
  but the first `session.add()/select()` raised — i.e. the DB was unusable.
  Confirmed with an isolated two-model repro (identical code failed **with** the
  future import and passed **without** it).
- **Fix:** removed `from __future__ import annotations` from `models.py`. The
  relationships (`List["Scan"]`, `List["Finding"]`, `List["AuditLog"]`) now
  resolve at mapper-configuration time.

### 2. Enum labels did not match the agreed contract
- **Wrong:** `UserRole` = ADMIN/**USER**, `ScanType` = STATIC/**DYNAMIC**,
  `ScanStatus` = **PENDING**/COMPLETED/FAILED.
- **Fix (per `docs/schema.md`):** `UserRole` = ADMIN/**VIEWER**,
  `ScanType` = STATIC/**LIVE**, `ScanStatus` = **IN_PROGRESS**/COMPLETED/FAILED.
- **Severity** kept intentionally as title-case **values** (`"Low"`,`"High"`,…)
  even though the contract lists uppercase labels, because the Phase 1 rule
  engine emits `"High"`/`"Critical"` (from the rule YAML). This lets engine
  output validate straight into the model/schema and keeps the Phase 1 tests
  green. The enum member *names* are still `LOW/MEDIUM/HIGH/CRITICAL`.

### 3. Primary-key / column names did not match the contract
- **Wrong:** every table used a generic `id` PK; `scans` used `created_at`.
- **Fix:** contract names — `users.user_id`, `scans.scan_id`,
  `findings.finding_id`, `audit_log.event_id`, and `scans.timestamp`. This also
  makes 1:1 mapping into the Member 2 response schemas trivial.

### 4. `findings.rule_id` was not a foreign key
- **Wrong:** `rule_id` was a plain `str` with no relationship to
  `compliance_map`, so findings could reference non-existent rules.
- **Fix:** `rule_id` is now `Field(foreign_key="compliance_map.rule_id")` and a
  `Relationship` to `ComplianceMap` was added. Verified: inserting a finding with
  an unknown `rule_id` now raises `IntegrityError` (with FK enforcement on).

### 5. `compliance_map` had the wrong shape
- **Wrong:** used a surrogate `id: UUID` PK with fields `cis_id`, `nist_id`,
  `remediation`, so there was no `rule_id` for findings to reference.
- **Fix (per contract):** `rule_id` (VARCHAR) is the primary key, with
  `cis_control_id`, `nist_id`, and `remediation_steps`.

### 6. `findings` was missing contract fields
- **Wrong:** no `risk_score`, no `is_anomaly`.
- **Fix:** added `risk_score: Optional[int]` (nullable, ML phase populates it)
  and `is_anomaly: bool` (default `False`).

### 7. `audit_log` had the wrong shape
- **Wrong:** had a `description` column, no `ip_address`, and a **non-nullable**
  `user_id`.
- **Fix (per contract):** added `ip_address` (Optional; INET in Postgres, stored
  as text for SQLite dev), made `user_id` nullable (system events have no user),
  and dropped `description`.

### 8. Non-contract `username` on `users`
- **Wrong:** `users` carried a `username` column not present in the contract.
- **Fix:** removed; `email` is the unique identifier (login arrives in Phase 8).

### 9. Deprecated timestamp default
- **Wrong:** `default_factory=datetime.utcnow` (deprecated in Python 3.12+ and
  timezone-naive).
- **Fix:** timezone-aware `datetime.now(timezone.utc)` via a small `_utcnow`
  helper.

### 10. Fix: Added Alembic migrations 

- added a real Alembic setup under `backend/`:
  - `backend/alembic.ini`
  - `backend/alembic/env.py` — resolves `DATABASE_URL` from the environment
    (SQLite locally, Postgres/Neon in prod), targets `SQLModel.metadata`, and
    uses `render_as_batch=True` for SQLite-safe migrations.
  - `backend/alembic/script.py.mako` — includes `import sqlmodel` so
    autogenerated `AutoString` columns render correctly.
  - `backend/alembic/versions/2f5602bdb143_initial_schema.py` — creates all
    five tables, enums, indexes, and foreign keys.

### 11. Missing `compliance_map` seed (deliverable)
- **Wrong:** no seed existed for the five Phase 1 rules.
- **Fix:** data migration
  `backend/alembic/versions/b2c3d4e5f6a7_seed_compliance_map.py` inserts exactly
  five rows (CIS-AWS-001..005) with the CIS control ID, NIST CSF ID, and
  remediation text copied from `/rules`. `alembic upgrade head` now both builds
  **and** seeds; `downgrade` removes the five rows.

### `backend/src/db.py`
- No bugs found. It reads `DATABASE_URL` (SQLite default), sets
  `check_same_thread=False` for SQLite, and exposes `get_session()` +
  `create_db_and_tables()`. Left as-is (production uses Alembic, not
  `create_db_and_tables`).

---

## Member 2 — `backend/src/schemas.py` and `.env.example`

### 1. Enums inherited the same off-contract values
- **Wrong:** `ScanStatus` = **PENDING**/…, `ScanType` = STATIC/**DYNAMIC**
  (internally consistent with Member 1's draft, but off-contract).
- **Fix:** aligned to `IN_PROGRESS`/`COMPLETED`/`FAILED` and `STATIC`/`LIVE`, so
  the API enums match the model enums exactly (no serialization mismatch when a
  stored value is returned through a response model).

### 2. Time field name mismatched the model/contract
- **Wrong:** `ScanSummary`/`ScanDetail` exposed `created_at`, but the scans
  table's time column is `timestamp` (contract). A response built from the ORM
  object would not map.
- **Fix:** renamed the schema field to `timestamp` for direct 1:1 mapping.

### 3. Responses could not be built from ORM objects
- **Wrong:** no `from_attributes` config, so Member 3 could not do
  `ScanSummary.model_validate(scan_orm_object)`.
- **Fix:** added `model_config = ConfigDict(from_attributes=True)` to all
  response models. Verified end-to-end by validating `ScanSummary` and
  `FindingResponse` straight from ORM rows.

### 4. `FindingResponse` did not reflect the full finding row
- **Wrong:** omitted `risk_score` and `is_anomaly` (which now exist on the
  model per the contract).
- **Fix:** added `risk_score: Optional[int]` and `is_anomaly: bool` (with safe
  defaults) so a stored finding round-trips faithfully.

### 5. `.env.example` lacked Phase 2 database guidance
- **Wrong:** only the Docker Compose Postgres `DATABASE_URL` was present; no
  local-dev or production (Neon) guidance, which was a Member 2 deliverable.
- **Fix:** added commented examples for a zero-setup local SQLite URL and a
  managed Postgres/Neon URL, without altering the existing Compose line.

### Contract-consistent, kept as-is
- `FindingResponse` field set matches the Phase 1 engine output exactly
  (`resource_id, resource_type, severity, rule_id, message`) — no change needed
  there. `UploadResponse`, `ScanDetail`, and `ErrorResponse` shapes were sound.

---

## Additive fields kept on purpose (not in `docs/schema.md`)

These are required by the application and were retained (and documented in code):

- **`scans.filename`** — the uploaded configuration's original name, surfaced by
  `ScanSummary`/`ScanDetail`. `docs/schema.md` omits it; it is a genuine gap in
  the contract, not a mistake in the code.
- **`findings.message`** — the human-readable remediation/explanation the Phase 1
  rule engine already produces; surfaced by `FindingResponse`.

> Follow-up: update `docs/schema.md` to include `scans.filename` and
> `findings.message` so the written contract matches the implemented one.

---

## Dependencies added

`backend/requirements.txt` now pins the Phase 2 runtime deps:
`sqlmodel==0.0.39`, `alembic==1.18.5`, `python-dotenv==1.2.2`
(SQLAlchemy/Pydantic come transitively via SQLModel and FastAPI).

---

## How to reproduce the verification

```bash
# from repo root, with a Python 3.11 venv that has backend/requirements.txt
export DATABASE_URL="sqlite:///./cloud_security.db"   # PowerShell: $env:DATABASE_URL=...

cd backend
alembic upgrade head        # builds 5 tables + seeds 5 compliance_map rows
cd ..
python -m pytest backend/tests -q   # Phase 1 suite: 14 passed
```

Member 3 (endpoints) and Member 4 (API tests + CI) can now build directly on
this fixed database + contract.

---

## Whole-System Security Review & Fixes

After Members 3 (endpoints) and 4 (tests + CI) were implemented, the assembled
system was security-reviewed end to end. Six issues were found and **all six
were fixed**. None were injection/crypto/secret leaks; most were
denial-of-service / robustness / hardening gaps. Each fix ships with a
regression test where testable.

### S1. Unbounded request buffering before the size check (memory DoS)
- **Wrong:** the upload handler read the whole body (`await file.read()`)
  before checking the 2 MB cap, so a huge upload was buffered into memory first.
- **Fix:** added an ASGI middleware in `main.py` that rejects any request whose
  `Content-Length` exceeds `MAX_FILE_SIZE + 64 KB` with **413** before the body
  is buffered (and **400** on a malformed `Content-Length`).
- **Test:** `test_oversized_request_rejected_at_edge` (413).

### S2. Deeply-nested JSON/YAML returned HTTP 500 instead of 400
- **Wrong:** routes caught only `(ValueError, TimeoutError)`, so a
  `RecursionError` from the loader escaped as an unhandled **500** stack trace.
- **Fix:** broadened the parse `except` to include `RecursionError`, mapping it
  to a clean **400**.
- **Test:** `test_upload_rejects_recursion_bomb` (400).

### S3. Parse timeout could block on a runaway worker thread
- **Wrong:** `with ThreadPoolExecutor(...)` calls `shutdown(wait=True)` on exit
  and would block on an unkillable runaway thread, defeating the timeout.
- **Fix:** manage the executor manually and `shutdown(wait=False,
  cancel_futures=True)` in a `finally`; cancel the future on timeout. Size and
  depth limits remain the primary DoS defences.

### S4. SQLite foreign keys were never enforced at runtime
- **Wrong:** `db.py` never issued `PRAGMA foreign_keys=ON`, so on SQLite (local
  dev) FK constraints such as `findings.rule_id` were silently ignored and
  orphan rows could be written.
- **Fix:** a SQLAlchemy `connect` event listener enables the pragma per
  connection when the URL is SQLite (Postgres enforces FKs natively).
- **Verified:** inserting an orphan `Finding` now raises `IntegrityError`.

### S5. Untrusted upload filename reflected verbatim (stored-XSS vector)
- **Wrong:** `file.filename` was stored and returned in API JSON as-is,
  allowing path components / control chars / markup to be persisted and
  reflected to the frontend.
- **Fix:** `_safe_filename()` keeps only the basename (`Path(raw).name`), strips
  control characters, and caps length at 255. UI output-encoding remains the
  primary XSS control.

### S6. Placeholder dev user was over-privileged and prod-unsafe
- **Wrong:** the pre-auth placeholder user was auto-created with
  `role=ADMIN`, and it would be created even in production.
- **Fix:** default the placeholder to least-privilege `VIEWER`; when
  `CSPM_ENV=production` and no user exists, raise **401** instead of fabricating
  an identity.

### Result
Full suite: **28 passed** (26 prior + 2 new regression tests). `alembic upgrade
head` still builds 5 tables + 5 seed rows.

---

## In very simple words — who did what and what was fixed

### Member 1 — the database (the "filing cabinet")
- **What they did:** built the database tables (users, scans, findings,
  compliance_map, audit_log), the database connection, the migrations that create
  those tables, and the seed data for the 5 rules.
- **What was wrong / fixed:** one line at the top of the models file
  (`from __future__ import annotations`) quietly **broke the whole database** —
  tables could be created but the first read/write crashed; it was removed. The
  table labels (roles, scan types, statuses) didn't match the agreed plan, so
  they were corrected. The migrations and seed were rebuilt so
  `alembic upgrade head` cleanly creates all 5 tables and inserts exactly 5 rule
  rows. Foreign keys are now actually enforced.

### Member 2 — the API contract (the "agreed shapes of the data")
- **What they did:** wrote the request/response "shapes" (schemas) the API uses,
  the allowed file-type list, and the `.env.example` database guidance.
- **What was wrong / fixed:** the shapes didn't line up with the database (wrong
  field names, missing fields, mismatched labels), so they were realigned to the
  real model and the Phase 1 engine output. A small setting was added so the
  shapes can be built straight from database rows, and the missing fields
  (`risk_score`, `is_anomaly`, correct timestamps) were added. `.env.example` got
  clear local-SQLite and production-Postgres examples.

### The whole-system security review (after Members 3 & 4)
- **What was done:** once all four layers were assembled, the running system was
  security-reviewed end to end. **Six issues** were found and **all six fixed**
  (see the section above): oversized uploads now rejected early (413), deeply
  nested files return a clean 400 instead of a 500, the parse timeout can no
  longer be blocked by a runaway thread, SQLite foreign keys are enforced,
  untrusted filenames are sanitised, and the placeholder dev user is now
  least-privilege and refuses to be created in production.
- **Result:** full test suite **28 passed**, and the database still builds from
  scratch with `alembic upgrade head`.
