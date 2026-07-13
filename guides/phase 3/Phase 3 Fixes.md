# Phase 3 — Fixes and Assembly

This document records the review and fixes applied to the Phase 3 frontend work
submitted by Members 1, 2, and 3. The gaps against the Phase 3 Plan have been fixed, 
and the result has been verified.


> **Structure note:** the members implemented their pages under `frontend/src/pages/`
> rather than the plan's `frontend/src/features/<name>/` layout, and all their
> imports are written for `pages/`. To avoid rewriting every import and risking
> breakage, the `pages/` layout was kept. This is a deviation from the plan's
> file-ownership map but does not affect the Definition of Done (which never
> requires `features/`). Member 4 can add `src/features/dashboard/` for charts.

---

## Verification (what was actually run)

| Gate | Command | Result |
| --- | --- | --- |
| Type + import check (all members' files) | `tsc -b` | **Pass — 0 errors** |
| Lint (CI gate) | `eslint .` | **Pass — 0 errors** (1 warning in the vendored `public/mockServiceWorker.js`, not our code) |
| Production bundle | `vite build` | Could not run **on macOS**: the submitted `node_modules` shipped only **Linux** rolldown binaries (`@rolldown/binding-linux-x64-*`), so the native bundler binary for this machine was missing. This is a packaging artifact of the zip, not a code issue. Run `npm install` locally to get the correct platform binary, then `npm run build`. |

`node_modules/` and `dist/` were removed from the assembled project (they are
gitignored and the bundled copy was Linux-only and had broken `.bin` symlinks
from the zip). Run `npm install` in `frontend/` before `npm run dev`/`build`.

---

## Member 1 — Foundation

**What was missing**

1. **MSW never actually started.** `mocks/browser.ts` created the worker, but
   `main.tsx` never called `worker.start()` and nothing read `VITE_USE_MOCKS`.
   The entire "build against mocks, flip one env flag for the real backend"
   premise the plan depends on did not function.
2. **Mock error cases absent.** The plan requires a bad-upload `400` and a `404`
   handler; `handlers.ts` had neither, so the upload error state and the
   "scan not found" view could not be exercised against mocks.
3. **Mock URL / baseURL mismatch.** Handlers matched relative paths (`/scans`),
   but the Axios client sends to `VITE_API_BASE_URL` (`http://localhost:8000`).
   MSW resolves relative paths against the page origin (`:5173`), so the handlers
   would never have intercepted the real requests even once started.
4. **Stray JSX in `App.tsx`.** A bare `<Badge severity="High" />` sat at module
   top level, outside any component — dead/erroneous code.
5. **No lazy route imports.** The plan requires lazy imports so `App.tsx` never
   needs re-editing when a feature page changes; it used static imports.
6. **Missing `vite-env.d.ts`.** Custom `VITE_*` env vars were untyped (latent
   type-safety gap on `import.meta.env`).

**What was updated**

- `main.tsx` — added an `enableMocking()` gate that dynamically imports and
  starts the MSW worker **only** when `VITE_USE_MOCKS === "true"`, before render.
- `mocks/handlers.ts` — rewrote with wildcard origins (`*/scans`) so they match
  the `:8000` baseURL; added a **404** (unknown scan id) on `GET /scans/:id` and
  `GET /scans/:id/findings`, and a **400** (unsupported file type) on
  `POST /scans/upload`. The 404 body uses the backend's exact `"Scan not found."`
  string so Member 3's not-found detection works.
- `mocks/data.ts` — replaced the single placeholder with two scans keyed by id,
  realistic backend `scan_type` values (`"STATIC"`), and findings across all four
  severities (so the 404 path and Member 4's future charts have real data).
- `App.tsx` — removed the stray `<Badge>`, switched to `lazy` + `Suspense`
  imports of the three pages, and moved the nav to Tailwind classes.
- `src/vite-env.d.ts` — **added**; references `vite/client` and types
  `VITE_API_BASE_URL` / `VITE_USE_MOCKS`.

**Left as-is (correct):** `api/types.ts` (matches the backend schema exactly),
`api/client.ts` (`withCredentials: true`, error normaliser surfacing `detail`),
`api/scans.ts`, and the `components/ui/` primitives + severity palette.

> Note on `api/client.ts`: it rejects with a plain **string** (the `detail`
> text), not an `Error`. This is unconventional but Members 2 and 3 already code
> to it (`typeof err === "string"`), so it was left unchanged to avoid churn.

---

## Member 2 — Upload feature

**What was missing**

1. **No drag-and-drop** — only a plain `<input type="file">`. The plan requires
   drag-drop *and* click-to-browse.
2. **No link to the scan detail page on success** — it printed the scan id as
   plain text; the plan requires a link to `/scans/:id`.
3. **Not a TanStack Query mutation** — used manual `useState`/`async`.
4. **Did not invalidate the scans list** after a successful upload, so the list
   would not refresh (a consequence of #3).

**What was updated** (`pages/UploadPage.tsx`, rewritten)

- Added a drag-and-drop zone (`onDragOver`/`onDragLeave`/`onDrop`) that also
  clicks a hidden file input for browse, with keyboard support (`Enter`/`Space`).
- Switched to a **`useMutation`** calling `uploadScan`, with `onSuccess`
  **invalidating the `["scans"]` query**.
- On success, renders findings count **and a `<Link>` to `/scans/{scan_id}`**.
- Kept the client-side validation (`.json/.yaml/.yml` + 2 MB cap) but factored it
  into a `validateFile()` helper shared by both drop and browse paths.
- Uploading / success / error states now derive from the mutation state.

**Duplicate removed:** Member 3's `scans.zip` also contained an identical
`UploadPage.tsx`; Upload belongs to Member 2, so only Member 2's (now fixed)
version was placed.

---

## Member 3 — Findings views

**Status: complete — no functional gaps.** Files were placed as-is:

- `pages/ScansPage.tsx` — list with newest-first sort, row links, loading /
  empty / error states.
- `pages/ScanDetailPage.tsx` — reads `:id`, header + findings table, graceful
  **404 "scan not found"** view.
- `pages/FindingsTable.tsx` — severity **sort** and **filter**, null-safe
  `risk_score` (renders `—`) and `is_anomaly`.
- `pages/SeverityBadge.tsx` — thin wrapper over Member 1's `Badge`, reusable by
  Member 4's charts.

The only adjustment was on Member 1's side: the mock 404 response now returns the
`"Scan not found."` detail string this page matches on, so its not-found path is
now reachable under mocks.

---

## Member 4 — Dashboard charts + Tests & CI


**Dashboard (`src/features/dashboard/DashboardPage.tsx`)**

- Two **Recharts** views fed only from the existing endpoints (no new API):
  a **pie** of *findings by severity* and a **bar** of *findings by resource
  type*. Data is aggregated client-side from `listScans()` + one `getScan()` per
  scan (`useQueries`, sharing the `["scan", id]` cache keys with the detail page).
- Chart colors mirror Member 1's `Badge` palette (same gray/yellow/orange/red
  hex values) so badges and charts match.
- **Empty state**: no scans → "Nothing to show yet — upload a config to see
  charts"; scans but zero findings → "No findings to chart yet".
- Each chart also renders an accessible text summary (e.g. `Critical: 1`), which
  doubles as a stable, jsdom-safe assertion target for the tests.
- Wired into routing: `/dashboard` (and `/` now lands on it) via a lazy import,
  plus a nav link in `App.tsx`.

**Test harness (Vitest + React Testing Library + MSW)**

- `vitest.config.ts` — jsdom environment, globals, coverage (v8), loads the setup
  file.
- `src/test/setup.ts` — a **Node MSW server built from Member 1's same handlers**,
  with `jest-dom` matchers; exported so tests can override a handler
  (`server.use(...)`) to force 400/404/empty responses.
- `src/test/utils.tsx` — `renderWithProviders` (React Query + MemoryRouter,
  `retry:false`).
- Tests authored across features (importing components, never editing them):
  - `UploadPage.test.tsx` — upload **success** (result + detail link), server
    **error** (400 detail), and client-side type rejection.
  - `ScansPage.test.tsx` — list renders newest-first; empty state.
  - `ScanDetailPage.test.tsx` — detail renders findings; **404** not-found view.
  - `FindingsTable.test.tsx` — **severity filter** works; null `risk_score` → `—`.
  - `DashboardPage.test.tsx` — charts aggregate from mock data; empty state.

**CI (`.github/workflows/phase3-frontend.yml`)**

- On push-to-main and every PR: `npm install` → `npm run lint` → `npm run build`
  → `npm run test`, on `ubuntu-latest` with Node 22 and npm cache.

**Build config touch:** `tsconfig.app.json` now **excludes `*.test.tsx` and
`src/test/`** so the production `tsc -b` build doesn't require test-only types;
Vitest type-handles the test files itself.

> **Verification status:** `npm install` succeeded, and after two fixes the
> suite is green: `npm run build` passes and **11/11 tests pass** (`vitest run`).
> The two fixes were (1) `DashboardPage` error-narrowing (`typeof` on a local,
> not the query object) and (2) forcing esbuild's automatic JSX runtime in
> `vitest.config.ts` (the `@vitejs/plugin-react` transform wasn't applying under
> vite 8 / rolldown, which surfaced as "React is not defined"). The upload tests
> also mock `uploadScan` directly because axios + multipart FormData hangs over
> MSW in jsdom.

---

## Real-backend end-to-end (integration fixes)

The full flow (upload → scan in list → findings on detail → charts) was verified
against the **real Phase 2 backend** with `VITE_USE_MOCKS=false`. Getting the
Docker stack to actually serve the API required three pre-existing backend/infra
fixes that only surface when the container runs (local `pytest` masked them):

1. **Rules not in the container** — the rule engine loads YAML from `/rules`, but
   `rules/` lives at the repo root, outside the backend build context, so it was
   never in the image (`FileNotFoundError: Rules directory '/rules' not found.`).
   **Fix:** mount it read-only in `infra/docker-compose.yml`
   (`- ../rules:/rules:ro`).
2. **`python-multipart` missing** — the upload endpoint uses `UploadFile`, which
   needs `python-multipart`; it was only in `requirements-dev.txt`, not the
   production `requirements.txt` the image installs (`RuntimeError: Form data
   requires "python-multipart"`). **Fix:** added `python-multipart==0.0.32` to
   `backend/requirements.txt`.
3. **CORS env var** — must be set as `CORS_ALLOW_ORIGINS=http://localhost:5173`
   in the **root** `.env` (note the trailing `S`; a `CORS_ALLOW_ORIGIN` typo
   silently disables CORS), and the backend recreated (`docker compose up -d
   --force-recreate backend`) so it re-reads the env file.

Verified with `docs/sample-config.json` → **5 findings** (2 Critical, 2 High,
1 Medium) rendered on the detail page and aggregated in the dashboard charts.

**Files touched:** `infra/docker-compose.yml`, `backend/requirements.txt`.
(The `.env` CORS value is per-environment and not committed; `.env.example`
already documents it.)

---

## Contract notes (frontend vs. real Phase 2 backend)

- Frontend types match the backend schemas. `scan_id` (UUID) and `timestamp`
  (datetime) serialize to strings over the wire, so the `string` typings are fine.
- **Oversized upload — both `413` and `400` exist.** `main.py` has a body-size
  middleware that returns **`413`** for a request body over `MAX_FILE_SIZE + 64 kB`;
  the upload route itself returns **`400`** for a file between the cap and that
  threshold. So the plan's `413` assumption is correct for genuinely large
  uploads. The frontend's 2 MB client-side check catches most cases first, and it
  renders whatever `detail` comes back, so either status is handled gracefully.
- **No-auth flow works:** `get_current_user` get-or-creates a dev user when
  `CSPM_ENV` isn't `production`, so the frontend (no login yet) can hit every
  endpoint. Ensure `CSPM_ENV=development` on the backend for local runs.
- **Upload field name matches:** backend expects multipart `file`; the client
  sends `file`. CORS allows credentials + the `:5173` origin, matching
  `withCredentials`.
- Backend `scan_type` enum is `"STATIC" | "LIVE"`; the mock now uses `"STATIC"`.

---

## Files changed / added

**Added**
- `frontend/` — Member 1's Vite + React + TS project assembled into the repo
  (was previously just `frontend/.gitkeep`, now removed).
- `frontend/src/vite-env.d.ts` — env var typings.
- `frontend/src/pages/FindingsTable.tsx`, `frontend/src/pages/SeverityBadge.tsx`
  — Member 3.
- `frontend/.env` — local dev config copied from `.env.example` (gitignored).
- `frontend/src/features/dashboard/DashboardPage.tsx` — Member 4 charts.
- `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`,
  `frontend/src/test/utils.tsx` — Member 4 test harness.
- `frontend/src/**/*.test.tsx` (Upload, Scans, ScanDetail, FindingsTable,
  Dashboard) — Member 4 tests.
- `.github/workflows/phase3-frontend.yml` — Member 4 CI (lint + build + test).
- `docs/phase3-metrics.md` — Phase 3 metrics record.
- `guides/phase 3/Phase 3 Fixes.md` — this document.

**Changed**
- `frontend/src/main.tsx` — MSW startup + `VITE_USE_MOCKS` toggle.
- `frontend/src/App.tsx` — lazy routes, removed stray `<Badge>`, Tailwind nav,
  and the `/dashboard` route + nav link (Member 4).
- `frontend/package.json` — added `recharts`, the Vitest/RTL/jsdom dev deps, and
  `test` / `test:watch` / `coverage` scripts (Member 4).
- `frontend/tsconfig.app.json` — excludes test files from the production build.
- `frontend/src/mocks/handlers.ts` — wildcard origins, 400 + 404 cases.
- `frontend/src/mocks/data.ts` — realistic multi-scan/multi-severity data.
- `frontend/src/pages/UploadPage.tsx` — drag-drop, mutation, invalidation,
  detail link (Member 2).
- `frontend/src/pages/ScansPage.tsx`, `frontend/src/pages/ScanDetailPage.tsx`
  — replaced Member 1's placeholders with Member 3's implementations.

**Removed**
- `frontend/.gitkeep`, and the bundled `frontend/node_modules` + `frontend/dist`
  (gitignored; Linux-only binaries with broken symlinks — reinstall with
  `npm install`).

---

## To run locally

```bash
cd frontend
npm install          # gets the correct platform binaries
npm run dev          # starts on :5173 with mocks (VITE_USE_MOCKS=true in .env)
```

To talk to the real backend instead: set `VITE_USE_MOCKS=false` in `frontend/.env`,
start the Phase 2 stack, and set `CORS_ALLOW_ORIGINS=http://localhost:5173` on the
backend.
