# Backend Deployment — Wave D

## Overview

Member 3 is responsible for deploying the CSPM backend API to an Oracle Cloud VM with a managed Neon PostgreSQL database.

## Production Architecture

```text
Frontend (Vercel)
       |
       | HTTPS
       v
Oracle Cloud VM
       |
       +-- FastAPI Backend
       |
       +-- LocalStack
       |
       v
Neon PostgreSQL
```

- Production authentication cookies are configured with the `Secure` flag.

## Production secrets

`infra/docker-compose.prod.yml` loads the backend's environment from
`.env.production` on the deployment host via `env_file` — this file is never
committed (see `.env.production.example` for its required shape). It must
exist at the repo root on the Oracle VM before `docker compose -f
infra/docker-compose.prod.yml up --build -d` is run; if it's missing or
incomplete, Compose fails the run outright rather than silently shipping
blank secrets (verified: `docker compose ... config` errors with "env file
... not found" when it's absent).

Required variables (names only):

| Variable | Source |
| --- | --- |
| `DATABASE_URL` | Neon connection string (`postgresql+psycopg2://...?sslmode=require`) |
| `JWT_SECRET` | A real random value, 32+ characters — the app refuses to start auth on anything shorter or on the Phase 0 placeholder |
| `ADMIN_EMAIL` | The address that becomes Admin on signup |
| `CORS_ALLOW_ORIGINS` | The deployed frontend's exact origin (M2's Vercel URL) — never a wildcard |

`CSPM_ENV=production` and `SECURE_COOKIES=true` are forced directly in
`docker-compose.prod.yml` itself (not read from `.env.production`), so
production mode can't be accidentally left off by an incomplete secrets
file. AWS/LocalStack credentials default to LocalStack's dummy `test`/`test`
values and don't need to be set unless pointing at a different target.

## Deploy command

```bash
cd <repo root on the VM>
git pull origin main
docker compose -f infra/docker-compose.prod.yml up --build -d
```

This is exactly what `.github/workflows/deploy-backend.yml` runs over SSH on
every push to `main` that touches `backend/**` or the compose file.