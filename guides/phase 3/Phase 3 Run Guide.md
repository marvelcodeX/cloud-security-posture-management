# Phase 3 — Run Guide (fresh laptop)

How to install, run, build, and test the Phase 3 frontend on another machine,
including the full end-to-end run against the real Phase 2 backend.

This procedure has been run through successfully end-to-end — the notes and
troubleshooting below reflect the exact issues that came up and how they were
fixed. Sections 3–4 cover the mock-backed UI + tests (Node only); Section 5 is
the real backend (Docker); Section 6 is troubleshooting.

---

## 0. Prerequisites

Install these first:

- **Node.js LTS** — version **20 or 22** recommended. Check: `node -v`
- **npm** (ships with Node). Check: `npm -v`
- **Git** (if cloning). Check: `git --version`
- Working **internet** connection (the first `npm install` downloads packages).

> Docker/Python are only needed later, for running against the *real* backend
> (Section 5). For the mock-backed UI (Section 3) you need **only Node**.

---

## 1. Get the code onto the laptop

Either clone the repo, or copy the whole project folder over (USB / cloud). If
you copy it, **do not copy `frontend/node_modules`** — it's stale and
platform-specific; a fresh `npm install` rebuilds it correctly.

```bash
cd cloud-security-posture-management/frontend
```

---

## 2. Create the local env file

`frontend/.env` is git-ignored, so after a clone it won't exist. Create it from
the example:

```bash
cp .env.example .env
```

Confirm it contains:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=true
```

`VITE_USE_MOCKS=true` means the app runs against the built-in **mock backend**
(MSW) — no real server needed.

---

## 3. Install dependencies and run the UI (mock mode)

```bash
npm install
npm run dev
```

- `npm install` should finish without an `ERESOLVE`/peer-dependency error.
- `npm run dev` prints a local URL (usually **http://localhost:5173**). Open it.

**What you should see:**
- A top nav: **Dashboard · Upload · Scans**.
- **Dashboard** → two charts (findings by severity pie, by resource type bar)
  plus a text summary like "4 findings across 2 scans".
- **Upload** → drag-drop / browse box; dropping a `.json` file and clicking
  "Upload & Scan" shows "Upload successful! Findings: 3" and a "View scan
  details" link.
- **Scans** → a table of two mock scans; clicking one opens its findings table
  (with a severity filter). Visiting a bad URL like `/scans/nope` shows a
  friendly "Scan not found".

Stop the dev server with `Ctrl+C`.

---

## 4. Build, test, and lint (the CI gates)

Run these three — they're exactly what the GitHub Action runs:

```bash
npm run lint     # expect: 0 errors (a warning in mockServiceWorker.js is fine)
npm run build    # expect: "built in ..."; creates a dist/ folder
npm run test     # expect: all test files pass (5 files, ~11 tests)
```

Optional coverage report:

```bash
npm run coverage
```

---

## 5. Run against the REAL Phase 2 backend (full end-to-end)

Needs **Docker Desktop** running. Do the steps in order — the CORS step (5.2)
is the one that silently breaks the UI if you get it wrong.

### 5.1 — Set CORS in the ROOT `.env` (do this BEFORE starting the backend)

The backend containers read the **repo-root** `.env` (not `frontend/.env`).
Create it if missing (`cp .env.example .env` from the repo root), then set —
**exactly**, plural with the trailing `S`, no quotes, no trailing slash:

```
CORS_ALLOW_ORIGINS=http://localhost:5173
CSPM_ENV=development
```

> ⚠️ The #1 gotcha: `CORS_ALLOW_ORIGIN` (missing `S`) is silently ignored and the
> browser blocks every call. It must be `CORS_ALLOW_ORIGINS`.
> `CSPM_ENV=development` lets the backend auto-create a dev user (no login yet).

### 5.2 — Start the backend stack

```bash
cd infra
docker compose up --build -d
docker compose ps            # wait until backend shows "Up ... (healthy)"
```

Confirm the API is up **and** that CORS is actually on:

```bash
curl --fail http://localhost:8000/health
# -> {"status":"ok"}

curl -i -H "Origin: http://localhost:5173" http://localhost:8000/health | grep -i access-control-allow-origin
# -> access-control-allow-origin: http://localhost:5173
```

If the second command prints **nothing**, CORS is off — fix the env var name in
5.1, then reload it:

```bash
docker compose up -d --force-recreate backend
```

> A plain `docker compose restart` does **not** re-read `.env` — you must
> `--force-recreate` (or `down` then `up`) after editing the root `.env`.

If the backend never becomes healthy (`Restarting`), see the backend
troubleshooting in Section 6.

### 5.3 — Point the frontend at the backend

In `frontend/.env`:

```
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000
```

Restart the dev server (Vite only reads `.env` at startup):

```bash
cd ../frontend
npm run dev
```

### 5.4 — Do the end-to-end flow

Open http://localhost:5173 and upload `docs/sample-config.json` on the **Upload**
page. Expected: **Findings: 5** → the scan appears in **Scans** → its detail page
shows 5 findings (2 Critical, 2 High, 1 Medium) → **Dashboard** charts reflect
them. If the pages hang on "loading" or upload says "network error", it's
almost always CORS (5.1) — see Section 6.

---

## 6. What to send me if something breaks

### Likely first-run issues (and that they're normal to hit)

- **`npm install` peer/version conflict** (e.g. `vitest` vs `vite`, or
  `recharts` vs React). The versions in `package.json` are best-effort ranges
  I set offline. If install fails, paste the `ERESOLVE` block — I'll pin the
  right versions. As a quick unblock you can try `npm install --legacy-peer-deps`,
  but send me the original error either way so I fix it properly.
- **`vite build` native-binary error** (mentions `rolldown`): should be gone
  after a fresh `npm install` on your machine (it downloads the correct binary).
  If it persists, delete `node_modules` + `package-lock.json` and reinstall.
- **Tests: "Cannot find module 'recharts'/'vitest'/'@testing-library/...'"** →
  `npm install` didn't complete; re-run it and check it succeeded.
- **Blank page / no data in mock mode** → confirm `.env` exists with
  `VITE_USE_MOCKS=true`, then hard-refresh. Check the Console for MSW startup.

### Real-backend issues (Section 5)

- **Pages stuck on "loading" and/or upload says "Network Error"** (with mocks
  off) → **CORS.** The browser can't read the backend's responses. Check:
  1. `grep CORS ../.env` shows `CORS_ALLOW_ORIGINS=http://localhost:5173`
     (plural `S`, exact origin, no slash/quote).
  2. `curl -i -H "Origin: http://localhost:5173" http://localhost:8000/health`
     returns an `access-control-allow-origin` header. If not, fix the env and
     `docker compose up -d --force-recreate backend`.
  3. Then hard-refresh the browser. DevTools → Console will name the blocked URL.
- **Backend container keeps `Restarting`** → read the crash:
  `docker compose logs backend --tail=40`. Known causes (all fixed in the repo
  now, but listed in case you're on an older copy):
  - `FileNotFoundError: Rules directory '/rules' not found.` → the rule engine's
    `rules/` folder isn't in the container. Fix: `infra/docker-compose.yml` must
    mount it under the `backend` service's `volumes:` — `- ../rules:/rules:ro`.
  - `RuntimeError: Form data requires "python-multipart"` → the upload endpoint's
    dependency is missing. Fix: `python-multipart==0.0.32` must be in
    `backend/requirements.txt`, then rebuild: `docker compose up -d --build backend`.
- **`curl http://localhost:8000/health` "connection refused"** → the backend
  isn't up yet or crashed. `docker compose ps -a` shows each container's state;
  Postgres/LocalStack must be `healthy` before the backend starts.
- **Editing the root `.env` seems to have no effect** → containers read env at
  create time. After any `.env` change: `docker compose up -d --force-recreate
  backend` (a plain `restart` won't re-read it). Dependency changes in
  `requirements.txt` need `--build` instead.
- **`docker: cannot connect to the Docker daemon`** → Docker Desktop isn't
  running. Start it, wait for "running", retry.

---

## Quick reference

```bash
# --- Frontend (mock mode) ---
cd frontend
cp .env.example .env          # first time only (VITE_USE_MOCKS=true)
npm install                   # first time / after dependency changes
npm run dev                   # http://localhost:5173 (mock backend)
npm run lint && npm run build && npm run test   # the CI checks

# --- Real backend (from repo root) ---
cp .env.example .env          # first time only, then set:
#   CORS_ALLOW_ORIGINS=http://localhost:5173   (plural S!)
#   CSPM_ENV=development
cd infra && docker compose up --build -d
curl -i -H "Origin: http://localhost:5173" http://localhost:8000/health \
  | grep -i access-control-allow-origin        # must print the header
# then in frontend/.env set VITE_USE_MOCKS=false and re-run `npm run dev`
# upload docs/sample-config.json  ->  expect Findings: 5
```

