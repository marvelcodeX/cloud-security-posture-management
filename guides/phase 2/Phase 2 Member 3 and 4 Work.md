# Phase 2 Work — Member 3 & Member 4 


Members 1 (database) and 2 (API contract) are documented separately in
`Phase 2 Fixes.md`. Member 3 builds the HTTP endpoints on top of Member 1's
models and Member 2's schemas; Member 4 proves the whole thing works and guards
it with CI. Per the plan, **one file per owner** — Member 3 owns the routes file,
Member 4 owns the tests + workflow.

---

## Member 3 — Endpoints

### Files created / touched
| File | What it is |
| --- | --- |
| `backend/src/routes.py` | **New.** The FastAPI router with all four scan endpoints. |
| `backend/main.py` | Wires the router into the app (`app.include_router(...)`) and keeps `/health`. |

### What Member 3 implemented

**A single `APIRouter`** (`backend/src/routes.py`) that wraps the Phase 1
`SecureParser` + `RuleEngine` over HTTP and stores the results using Member 1's
SQLModel models and Member 2's Pydantic schemas.

**Module-level setup (loaded once at import):**
- `RULES_DIR` — resolves the Phase 1 `/rules` directory, with a `RULES_DIR` env
  override so the API can run from any layout.
- `_engine = RuleEngine(rules_directory=RULES_DIR)` and `_parser = SecureParser()`
  are created once (rules are read-only) instead of per request.

**Placeholder identity — `get_current_user` dependency:**
- Real authentication arrives in Phase 8. Until then, every query is scoped to a
  placeholder development user (`dev@local`). Building user-scoping in now means
  the IDOR hole never exists later.
- Tests override this dependency to simulate multiple users.

**The four endpoints:**

1. **`POST /scans/upload`** — the core flow:
   - Reads the upload filename and its extension.
   - Rejects any extension not in Member 2's `ALLOWED_EXTENSIONS`
     (`.json/.yaml/.yml`) with **400**.
   - Reads the body and rejects anything over `MAX_FILE_SIZE` (2 MB) with **400**.
   - Writes the bytes to a temporary file (preserving the extension) and parses
     it with the Phase 1 `SecureParser` — reusing its size/depth/alias defences.
     The temp file is always cleaned up in a `finally`.
   - Any parse failure becomes a clean **400** (never a 500 stack trace).
   - Runs the parsed config through the Phase 1 `RuleEngine`.
   - Persists **one `scans` row** (`scan_type = STATIC`, `status = COMPLETED`)
     plus **one `findings` row per finding**.
   - Returns Member 2's `UploadResponse` (`scan_id`, `status`, `findings_count`).

2. **`GET /scans`** — lists the caller's scans, newest first
   (`response_model=list[ScanSummary]`).

3. **`GET /scans/{scan_id}`** — one scan with its findings
   (`response_model=ScanDetail`).

4. **`GET /scans/{scan_id}/findings`** — the findings for one scan
   (`response_model=list[FindingResponse]`).

**Access control (IDOR defence) — `_load_owned_scan` helper:**
- Every read is scoped to `user.user_id`. A scan that does not belong to the
  caller returns **404** (not 403), so the existence of other users' scans is not
  leaked. All three read endpoints go through this helper.

**Wiring — `backend/main.py`:**
- Puts `backend/src` on `sys.path` (mirroring the test harness) so the modules
  import cleanly whether the app is run from `backend/` or elsewhere.
- `app.include_router(scans_router)` and keeps the Phase 0 `/health` probe.

### How it was verified
- Uploading a known-bad fixture creates a scan + the correct findings and reads
  back via GET.
- Bad extension / oversized / unparseable input all return **400**.
- Another user's scan returns **404** (IDOR check), and listings are user-scoped.

---

## Member 4 — Tests & CI

### Files created / touched
| File | What it is |
| --- | --- |
| `backend/tests/test_api.py` | **New.** The full Phase 2 API test suite (httpx / `TestClient`). |
| `.github/workflows/phase2-tests.yml` | **New.** CI that runs migrations + the test suite on every push/PR. |
| `backend/requirements-dev.txt` | Added `httpx` and `python-multipart` (needed by `TestClient` and file uploads). |

### What Member 4 implemented

**A throwaway test harness** (`backend/tests/test_api.py`) so tests never touch a
real database:
- An **in-memory SQLite** engine using `StaticPool` with a fresh schema built per
  test (`SQLModel.metadata.create_all` / `drop_all`).
- A `connect` listener enabling `PRAGMA foreign_keys=ON` so FK constraints (e.g.
  `findings.rule_id`) are actually enforced in tests.
- The `compliance_map` table seeded with the 5 Phase-1 rules, plus **two users**
  (A and B) so access-control can be tested.
- FastAPI **dependency overrides**: `get_session` points at the throwaway DB and
  `routes.get_current_user` returns a switchable current user (`env.current`),
  which lets a single test act as user A then user B.

**The test cases** (the original Member 4 suite — 12 tests):

*Happy path*
- `test_health` — `/health` returns `{"status": "ok"}`.
- `test_upload_bad_fixture_stored_and_readback` — upload a bad config → it is
  stored → read it back through list, detail, and findings endpoints.
- `test_findings_persisted_in_db` — the findings are actually written to the DB.
- `test_upload_good_fixture_zero_findings` — a clean config produces 0 findings.

*Validation failures (clean 400, never a 500)*
- `test_upload_rejects_bad_extension` — a `.txt` upload → 400.
- `test_upload_rejects_oversized` — a body over 2 MB → 400.
- `test_upload_rejects_deep_nesting` — deeply nested JSON → 400.
- `test_upload_rejects_yaml_alias_bomb` — a YAML alias/anchor bomb → 400.
- `test_upload_rejects_malformed_json` — broken JSON → 400.

*Access control (IDOR / scoping)*
- `test_idor_other_user_cannot_read_scan` — user B cannot read user A's scan (404).
- `test_scans_are_user_scoped` — each user only sees their own scans.
- `test_unknown_scan_id_returns_404` — an unknown scan id → 404.

> Two extra regression tests (`test_upload_rejects_recursion_bomb`,
> `test_oversized_request_rejected_at_edge`) were added later during the
> whole-system security review — those are documented in `Phase 2 Fixes.md`.

**Continuous Integration** (`.github/workflows/phase2-tests.yml`):
- Runs on every `push` to `main` and every `pull_request`.
- Sets up Python 3.11 and installs `backend/requirements-dev.txt`.
- **Verifies migrations**: runs `alembic upgrade head` against a fresh SQLite DB
  (so Member 1's migrations are checked too), then removes the DB file.
- **Runs the whole test suite**: `pytest backend/tests -q` (Phase 1 rules +
  Phase 2 API).

### How it was verified
- Full suite runs green locally and in the CI definition; `alembic upgrade head`
  builds the 5 tables + 5 seed rows before the tests run.

---

## In simple words

### What Member 3 did (the "buttons people press")
Member 3 built the **four web buttons** for the app:
- **Upload** a cloud config file → the app checks it's a safe, allowed file,
  scans it with the Phase 1 engine, and **saves the scan and every problem it
  found** into the database.
- **See my scans** → a list of everything you've uploaded.
- **Open one scan** → that scan and its problems.
- **See one scan's problems** → just the list of problems.

Two important safety rules followed: **bad files get a polite "400" error
instead of crashing the server**, and **you can only ever see your own scans** —
if you try to open someone else's, the app pretends it doesn't exist (returns
"404") so nobody can even tell it's there.

### What Member 4 did (the "proof it works")
Member 4 wrote the **automatic tests** that prove the whole thing works, using a
tiny fake database that's thrown away after each run so real data is never
touched. The tests check the good path (upload → save → read it back), that bad
files are rejected cleanly, and that one user can't peek at another user's data.

Member 4 also set up **CI (a robot on GitHub)** that re-runs all these tests every
time someone pushes code or opens a pull request, and also double-checks that the
database can be built from scratch. If anything is broken, the robot fails the
check — so broken code can't sneak into the project.
