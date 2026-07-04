# Phase 2 — Work Summary

#files created newly

### Application code
| Path | Purpose |
| --- | --- |
| `backend/src/models.py` | SQLModel ORM — 5 tables + enums (Member 1, fixed). |
| `backend/src/db.py` | Engine + session helper; SQLite FK-enforcement listener (Member 1). |
| `backend/src/schemas.py` | Pydantic request/response contract (Member 2, fixed). |
| `backend/src/routes.py` | FastAPI router — the 4 scan endpoints (Member 3). |

### Database migrations
| Path | Purpose |
| --- | --- |
| `backend/alembic.ini` | Alembic configuration. |
| `backend/alembic/env.py` | Alembic environment (points at the models' metadata). |
| `backend/alembic/script.py.mako` | Migration template. |
| `backend/alembic/versions/2f5602bdb143_initial_schema.py` | Creates all 5 tables. |
| `backend/alembic/versions/b2c3d4e5f6a7_seed_compliance_map.py` | Seeds 5 `compliance_map` rows (CIS-AWS-001..005). |

### Tests & CI
| Path | Purpose |
| --- | --- |
| `backend/tests/test_api.py` | Phase 2 API test suite — 14 tests (Member 4 + 2 security regressions). |
| `.github/workflows/phase2-tests.yml` | CI: `alembic upgrade head` + full pytest suite on push/PR (Member 4). |

---

## 3. Existing files modified this session

| Path | Change |
| --- | --- |
| `backend/main.py` | Wires in the router; added request-size (413) middleware and env-gated CORS; keeps `/health`. |
| `backend/src/parser.py` | Hardened the parse timeout (non-blocking executor shutdown). |
| `backend/requirements.txt` | Added `sqlmodel`, `alembic`, `python-dotenv`. |
| `backend/requirements-dev.txt` | Added `httpx`, `python-multipart`. |
| `.env.example` | Added `CSPM_ENV`, `CORS_ALLOW_ORIGINS`, `RULES_DIR`, and SQLite/Neon `DATABASE_URL` guidance. |

---

## 4. Where to read more

- **What was broken and fixed:** `guides/Phase 2/Phase 2 Fixes.md`
- **What Members 3 & 4 built:** `guides/Phase 2/Phase 2 Member 3 and 4 Work.md`
- **Is it ready for the next phases:** `guides/Phase 2/Phase 2 Forward-Compatibility Review.md`
- **Numbers:** `docs/phase2-metrics.md`
- **The plan being implemented:** `guides/Phase 2/Phase 2 Plan.md`
- **The schema contract:** `docs/schema.md`

---

## 5. How to reproduce the verification

```bash
# From the repository root, using the Python 3.11 venv created this session:
.venv/Scripts/python.exe -m pytest backend/tests -q          # -> 28 passed

# Build the schema + seed on a clean SQLite DB:
cd backend
set DATABASE_URL=sqlite:///./check.db
python -m alembic upgrade head                                # 5 tables + 5 seed rows
```


