# Phase 3 — Frontend Dashboard (v1)

Goal: build the **React dashboard** that turns the Phase 2 API into something a
human can use — upload a config, see the scan run, and read the findings with
severity badges and charts. Team: 4 members.

By the end: **upload → findings on the dashboard**, end to end, talking to the
real Phase 2 backend (`POST /scans/upload`, `GET /scans`, `GET /scans/{id}`,
`GET /scans/{id}/findings`).

**Tech (from the plan §3):** React + Vite + TypeScript, Tailwind CSS, Recharts,
React Router, TanStack Query (data fetching/cache), Axios (with
`withCredentials` for the httpOnly auth cookies coming in Phase 8), Vitest +
React Testing Library + MSW for tests.

---

## The two rules that prevent conflicts and deadlocks

This is the whole point of the division, so read this first.

**1. No conflicts → one owner per folder.** Each member owns a separate directory
under `frontend/src/`. **No two people ever edit the same file.** The only shared
files are created and owned by **Member 1** on Day 1 and then treated as
read-only by everyone else (they import from them, they don't edit them). If you
need a change to a shared file, you ask Member 1 — you don't edit it.

**2. No deadlocks → contract + mocks first.** Member 1 ships the **API client, the
TypeScript types, and a mock server (MSW)** on Day 1–2 **before** anyone needs
them. From that moment every other member builds against the **types and mock
data**, not against a running backend. So nobody is ever blocked waiting for
someone else — all four work in parallel from Day 2. The real backend is swapped
in at the end by flipping one env flag; no code changes.

> Dependency shape is a **tree, not a cycle**: everyone depends only on Member 1's
> Day-1 shared layer, and Member 1 depends on nobody. A tree has no cycles →
> no deadlock is possible.

---

## File-ownership map (who owns what — nobody else touches it)

| Owner | Folder / files (exclusive) |
| --- | --- |
| **Member 1 — Foundation** | `frontend/` project config (`package.json`, `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`, `.env.example`), `frontend/src/main.tsx`, `frontend/src/App.tsx` (router shell + layout), `frontend/src/api/**` (Axios client, endpoints, **all TypeScript types**), `frontend/src/mocks/**` (MSW handlers + sample data), `frontend/src/components/ui/**` (shared primitives: Button, Card, Spinner, Badge, design tokens) |
| **Member 2 — Upload** | `frontend/src/features/upload/**` (Upload page + dropzone + client-side file validation + progress/result states) |
| **Member 3 — Findings views** | `frontend/src/features/scans/**` (scan **list** page, scan **detail** page, findings **table**, `SeverityBadge`, filtering/sorting) |
| **Member 4 — Charts + Tests/CI** | `frontend/src/features/dashboard/**` (summary charts), `frontend/src/**/*.test.tsx` **that they author**, `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`, `.github/workflows/phase3-frontend.yml` |

Routing note: Member 1's `App.tsx` references each feature's top-level page via a
**lazy import**. Members 2–4 each export **one** page component from their folder;
Member 1 wires the route once on Day 1 using a placeholder, so later there is no
merge on `App.tsx`.

---

## Order of work (so nobody is blocked)

- **Day 1–2:** Member 1 lands the project skeleton, the API client + types, the
  MSW mock layer, and the shared UI primitives, then **publishes the types + mock
  data** to the team. Everyone else scaffolds their folder with a placeholder.
- **Day 2 onward (parallel):** Members 2, 3, 4 build their features against the
  types + mocks. No cross-dependencies.
- **Day 8–9:** flip `VITE_USE_MOCKS=false`, point at the real backend, fix any
  contract drift together, finish tests + CI.
- **Day 10:** polish, accessibility pass, merge to main.

---

## The shared contract (Member 1 publishes this; everyone codes to it)

These mirror the Phase 2 API exactly, so mocks and real responses are
interchangeable:

- `POST /scans/upload` (multipart `file`) → `{ scan_id, status, findings_count }`
- `GET /scans` → `ScanSummary[]` = `{ scan_id, filename, scan_type, status, timestamp }[]`
- `GET /scans/{scan_id}` → `ScanDetail` = `ScanSummary & { findings: Finding[] }`
- `GET /scans/{scan_id}/findings` → `Finding[]`
- `Finding` = `{ resource_id, resource_type, severity, rule_id, message, risk_score, is_anomaly }`
- `severity` ∈ `"Low" | "Medium" | "High" | "Critical"`
- `status` ∈ `"IN_PROGRESS" | "COMPLETED" | "FAILED"`
- Errors come back as `{ detail: string }` with status `400` (bad upload) /
  `413` (too large) / `404` (not found).

`risk_score` and `is_anomaly` exist now but are `null`/`false` until Phase 5 — the
UI should render them gracefully (e.g. "—") rather than assume a value.

---

## Member 1 — Foundation: project, API client, types, mocks, UI kit (Lead)

**What to do (in plain words):** build the empty house everyone else furnishes —
the React project itself, the one place that talks to the backend, the shared
data types, a fake backend for offline work, and the reusable buttons/cards.

**How (step by step)**
1. Scaffold `frontend/` with **Vite + React + TypeScript**; add **Tailwind**,
   **React Router**, **TanStack Query**, **Axios**. Commit `.env.example` with
   `VITE_API_BASE_URL` and `VITE_USE_MOCKS`.
2. `src/api/client.ts`: a single Axios instance with `baseURL` from env and
   **`withCredentials: true`** (so Phase 8 httpOnly cookies "just work"), plus a
   response-error normaliser that surfaces `detail`.
3. `src/api/types.ts`: the **TypeScript types** for every request/response above.
   This is the frontend's copy of the contract — the single source of truth for
   Members 2–4.
4. `src/api/scans.ts`: typed functions (`uploadScan`, `listScans`, `getScan`,
   `getScanFindings`) — the only functions that call the backend.
5. `src/mocks/`: **MSW** handlers returning realistic sample data for all four
   endpoints (including a bad-upload `400` and a `404`). Wire MSW to start when
   `VITE_USE_MOCKS=true`.
6. `src/App.tsx`: the app shell — top nav/sidebar, `QueryClientProvider`, and the
   **router** with routes for `/upload`, `/scans`, `/scans/:id` using **lazy
   imports** of the feature pages.
7. `src/components/ui/`: shared primitives — `Button`, `Card`, `Spinner`,
   `Badge`, plus Tailwind design tokens (colors incl. the severity palette). No
   business logic here.

**Deliverables & checklist**
- [ ] `frontend` builds and runs (`npm run dev`) with Tailwind working
- [ ] `src/api/` client + typed endpoint functions + **types** published to the team
- [ ] MSW mock layer covers all four endpoints + error cases; toggled by env
- [ ] App shell + router with lazy routes to the three feature pages
- [ ] `src/components/ui/` primitives + severity color tokens
- [ ] `.env.example` documents `VITE_API_BASE_URL` and `VITE_USE_MOCKS`

**In simple words:** Member 1 lays the foundation and the wiring so the other
three can start immediately and never wait for the backend.

---

## Member 2 — Upload feature (Lead)

**What to do (in plain words):** build the screen where a user drops in a JSON/YAML
file and gets told what happened.

**How (step by step)**
1. `src/features/upload/UploadPage.tsx`: a drag-and-drop (and click-to-browse)
   file picker.
2. **Client-side validation before sending:** allow only `.json/.yaml/.yml`,
   reject files over the 2 MB cap up front (so the user gets instant feedback;
   the server still enforces it). Show a clear message on reject.
3. On submit, call **Member 1's `uploadScan()`** (via a TanStack Query mutation).
   Show three states: **uploading** (spinner/progress), **success** (show
   `findings_count` + a link to the new scan's detail page), and **error** (render
   the server's `detail` for `400`/`413`).
4. After success, invalidate the scans-list query so the list refreshes.
5. Use only Member 1's `ui/` primitives — no bespoke buttons.

**Deliverables & checklist**
- [ ] Upload page with drag-drop + browse
- [ ] Client-side type + size validation with friendly errors
- [ ] Uploading / success / error states wired to `uploadScan()`
- [ ] Success routes/links to the scan detail page
- [ ] Works fully against MSW mocks

**In simple words:** Member 2 owns the "upload a file" screen and makes sure the
user always knows whether it worked or why it didn't.

---

## Member 3 — Findings views: list + detail + findings table (Lead)

**What to do (in plain words):** build the screens that show past scans and the
problems each scan found.

**How (step by step)**
1. `src/features/scans/ScanListPage.tsx`: fetch `listScans()`; render a table of
   scans (filename, type, **status**, timestamp), newest first; each row links to
   its detail page. Handle loading / empty / error states.
2. `src/features/scans/ScanDetailPage.tsx`: read the `:id` route param; fetch
   `getScan(id)`; show the scan header + a **findings table**.
3. `src/features/scans/FindingsTable.tsx`: columns for resource, type,
   **severity**, rule, message; support sort by severity and filter by severity.
   Render `risk_score`/`is_anomaly` gracefully when null (they arrive in Phase 5).
4. `src/features/scans/SeverityBadge.tsx`: a colored badge per severity using
   Member 1's tokens (Critical→red … Low→gray). Reused by Member 4's charts too,
   so keep it pure/presentational.
5. Correct handling of `404` (scan not found → friendly "not found" view).

**Deliverables & checklist**
- [ ] Scan list page (user-scoped list, links to detail)
- [ ] Scan detail page with findings table
- [ ] `FindingsTable` with severity sort/filter and null-safe ML fields
- [ ] `SeverityBadge` driven by shared color tokens
- [ ] Loading / empty / 404 states handled; works against MSW mocks

**In simple words:** Member 3 owns the "see my scans and their problems" screens.

---

## Member 4 — Dashboard charts + Tests & CI (Lead)

**What to do (in plain words):** turn the findings into charts, and prove the whole
frontend works with automated tests that run on every push.

**How (step by step)**
1. `src/features/dashboard/DashboardPage.tsx` (or a panel on the list page):
   using **Recharts**, show **findings by severity** (bar/pie) and **findings by
   resource type / rule** (bar). Derive the numbers from the same
   `listScans`/`getScan` data — no new endpoint.
2. Reuse Member 3's `SeverityBadge` colors so charts and badges match.
3. Handle the empty case (no scans yet → a friendly "nothing to show" state).
4. **Testing harness:** set up **Vitest + React Testing Library + MSW** in
   `src/test/setup.ts` and `vitest.config.ts`. Tests run against the **same mock
   handlers** Member 1 built.
5. Write tests that cover the critical flows: upload success + error, list
   renders scans, detail renders findings, severity filter works, and a chart
   renders from mock data. (You author the `*.test.tsx` files across features, so
   you don't edit others' source — you import their components.)
6. `.github/workflows/phase3-frontend.yml`: install, `npm run lint`,
   `npm run build`, `npm run test` on every push/PR.

**Deliverables & checklist**
- [ ] Severity + category charts (Recharts) fed from existing endpoints
- [ ] Empty-state handling for charts
- [ ] Vitest + RTL + MSW harness
- [ ] Tests for upload / list / detail / filter / chart (against mocks)
- [ ] CI workflow: lint + build + test, green on PRs

**In simple words:** Member 4 owns the charts and the safety net (tests + the
GitHub robot) that stops broken UI from merging.

---

## Why there is no deadlock (quick proof)

- Member 2, 3, 4 depend **only** on Member 1's Day-1 outputs (types + client +
  mocks + UI kit). They do **not** depend on each other.
- Member 1 depends on **no one**.
- One shared reused component (`SeverityBadge`) is owned by **one** person
  (Member 3) and only *imported* by Member 4 — never co-edited.
- Therefore the dependency graph is a tree rooted at Member 1: no cycle → no
  member can be waiting on another who is waiting back. Work proceeds in parallel
  after Day 2.

## Why there are no merge conflicts (quick proof)

- Every member writes only inside their **own folder**.
- The only shared files (`App.tsx`, `api/`, `components/ui/`, project config) are
  written **once** by Member 1 on Day 1 and imported read-only thereafter.
- Routes are wired **once** via lazy imports, so adding a feature never re-edits
  `App.tsx`.
- Test files are authored by Member 4 in their own `*.test.tsx` files; they
  import components rather than modifying them.

---

## Collaboration & rotation (everyone learns every step)

- Four work items (foundation, upload, findings, charts+tests). Rotate
  review/test roles:
  - Foundation: M1 lead, M2 review, M3 test, M4 second-review
  - Upload: M2 lead, M3 review, M4 test, M1 second-review
  - Findings: M3 lead, M4 review, M1 test, M2 second-review
  - Charts & tests: M4 lead, M1 review, M2 test, M3 second-review
- Every PR: feature branch, small (<300 lines), an assigned reviewer, tests where
  it makes sense, and a note that it still builds against mocks.

---

## Phase 3 Definition of Done (all must pass)

1. `npm run dev` shows the app; `npm run build` succeeds.
2. Upload → the new scan appears in the list → its findings render on the detail
   page (full end-to-end flow) against the **real** Phase 2 backend.
3. Severity badges + at least two charts render correctly.
4. Loading / empty / error (`400`/`413`/`404`) states are handled everywhere.
5. Axios uses `withCredentials` and reads `VITE_API_BASE_URL` from env (no
   hard-coded URLs); tokens are never stored in `localStorage`.
6. Vitest suite passes in CI (lint + build + test green on PRs).
7. Backend CORS is set for the frontend origin (`CORS_ALLOW_ORIGINS`), matching
   the Phase 2 forward-compat note.

---

## Metrics to record (in `docs/phase3-metrics.md`)

- Number of pages/components implemented.
- Tests passed/failed and coverage %.
- Bundle size after `npm run build`.
- Upload→findings-on-screen time on the standard fixture (ms).

---

## Notes / guardrails

- **The Phase 2 Swagger/OpenAPI at `/docs` is the source of truth.** If a type in
  `src/api/types.ts` and the backend disagree, fix the type (or raise it), don't
  reshape the backend from the frontend.
- Set `CORS_ALLOW_ORIGINS=http://localhost:5173` on the backend for local dev
  (already supported — see the Phase 2 Forward-Compatibility Review).
- No auth yet (Phase 8). Build as if a user context exists; don't add a login
  screen now, but keep `withCredentials` on so cookies slot in later.
- Keep secrets out of the repo; only `VITE_*` public config goes in the frontend
  `.env` (never a real secret — Vite inlines `VITE_*` into the bundle).
