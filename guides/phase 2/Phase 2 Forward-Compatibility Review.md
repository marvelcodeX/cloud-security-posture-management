# Phase 2 — Forward-Compatibility Review

---

## What was checked

The whole assembled system was reviewed against the phase plan
(`Major Project Planning.md` §7) and the schema contract (`docs/schema.md`):

- Database models (`backend/src/models.py`)
- API schemas (`backend/src/schemas.py`)
- Endpoints (`backend/src/routes.py`) and app wiring (`backend/main.py`)
- Migrations + seed (`backend/alembic/`)
- Tests + CI (`backend/tests/test_api.py`, `.github/workflows/phase2-tests.yml`)

---

## Already forward-ready (no change needed)

| Future phase | What it will need | Why it already fits |
| --- | --- | --- |
| **3 — Frontend** | A stable, documented API contract | Swagger/OpenAPI is live at `/docs`; all responses are Pydantic models with examples. |
| **4 — Live cloud** | A way to mark non-upload scans | `ScanType.LIVE` already exists; the upload route sets `STATIC`. A future live-scan route just sets `LIVE` and reuses the same store logic. |
| **5 — ML risk scoring** | Somewhere to put scores/anomalies | `findings.risk_score` and `findings.is_anomaly` exist on the model **and** in `FindingResponse`; today they default to `None`/`False` and round-trip cleanly. |
| **7 — Compliance mapping** | Rule → CIS/NIST/remediation lookup | `compliance_map` table exists and is seeded; `findings.rule_id` is a FK to it. Compliance data can be joined into responses later without a migration. |
| **8 — Auth & RBAC** | A single place to swap in real identity | `get_current_user` is one dependency the whole router depends on; every query is already user-scoped (IDOR-safe). `UserRole` (ADMIN/VIEWER), `audit_log` (with `ip_address`, nullable `user_id`) are in place. In production the placeholder refuses to fabricate a user (401). |
| **9 — DevOps/CI** | Automated checks | `phase2-tests.yml` already runs migrations + the full suite on every push/PR; a `Dockerfile` exists under `backend/`. New security scanners slot in as extra steps. |

---

## Enabler added during this review

### CORS (unblocks Phase 3) — **secure by default**
- **Why:** the Phase 3 React dashboard runs on a different origin (e.g.
  `http://localhost:5173`, later Vercel). Browsers block cross-origin API calls
  unless the server sends CORS headers. Without this, Phase 3 hits a wall on day
  one.
- **What was added:** `backend/main.py` now reads `CORS_ALLOW_ORIGINS`
  (comma-separated). If it is **unset/empty, nothing changes** — no origins are
  allowed, identical to before. When set, a `CORSMiddleware` is added with
  `allow_credentials=True` (so Phase 8 httpOnly auth cookies work).
- **How Phase 3 uses it:** set `CORS_ALLOW_ORIGINS=http://localhost:5173` in
  `.env`. **Phase 8** later tightens this to the deployed frontend origin only.
- No new dependency (ships with FastAPI/Starlette); 28 tests still pass.

Also documented `CSPM_ENV` and `CORS_ALLOW_ORIGINS` in `.env.example`.

---

## Intentionally deferred to their owning phase (not blockers now)

1. **Rate limiting (`slowapi`)** — listed in the Phase 2 tech stack but is a
   cross-cutting hardening concern. It plugs in as app middleware later (Phase 8
   security hardening) without touching the endpoints. **Action:** add
   `slowapi` limits in Phase 8.
2. **Real authentication / RBAC enforcement** — `get_current_user` is a
   deliberate placeholder (Phase 8). No rework needed: swap the dependency body
   for JWT-cookie validation; the router and tests already treat it as the single
   identity source.
3. **Compliance/remediation in responses** — the data is stored and linked;
   surfacing it in the API and UI is Phase 7 work (additive, no migration).
4. **Live-scan endpoint** — Phase 4 adds a new route; the model and store path
   are ready.

---

## Compatibility rule to remember (applies from Phase 4 onward)

`findings.rule_id` is now a **hard foreign key** to `compliance_map`, and FKs are
enforced at runtime (Postgres natively; SQLite via the `PRAGMA foreign_keys=ON`
listener added in Phase 2 fixes). **Any new detection rule must also be seeded
into `compliance_map`** (add an Alembic seed row) or inserting its findings will
fail. This is intentional — it guarantees every finding is always mappable to a
CIS/NIST control for Phase 7.

---

## Verification snapshot

| Check | Result |
| --- | --- |
| Full test suite (`pytest backend/tests -q`) | ✅ 28 passed |
| `alembic upgrade head` on a clean DB | ✅ 5 tables + 5 seed rows |
| App imports with CORS **off** (default) | ✅ no behavior change |
| App imports with `CORS_ALLOW_ORIGINS` set | ✅ CORS middleware active |
| Swagger contract at `/docs` | ✅ present (Phase 3 source of truth) |

**Conclusion:** Phase 2 is a stable foundation. Phases 3–11 can proceed by
*adding* to it (new routes, a swapped auth dependency, ML score population,
compliance surfacing) rather than changing what exists.
