# Phase 9 — CI/CD Security Pipeline

## 1. Objective

Turn "tests pass" into "tests pass *and* nothing scanned comes back
dangerous," and make that actually block a merge instead of only reporting on
one. This closes the gap where `gitleaks` (secret scanning) was the only
scanner running in CI.

The new workflow is `.github/workflows/security-scan.yml`. It runs on every
pull request, every push to `main`, and on demand (`workflow_dispatch`).
`.github/workflows/gitleaks.yml` is untouched — it already runs and isn't
duplicated here.

## 2. Scanners

| Job | Tool | Scope | Required? |
| --- | --- | --- | --- |
| `bandit` | Bandit (Python SAST) | `backend/src`, excluding `*/tests/*` | Yes |
| `pip-audit` | pip-audit | `backend/requirements.txt` (shipped deps only, not `-dev`) | Yes |
| `npm-audit` | `npm audit` | `frontend/`, `--audit-level=high --omit=dev` | Yes |
| `trivy` | Trivy | the backend image M1's Dockerfile builds | Yes |
| `semgrep` | Semgrep, `p/ci` ruleset | `backend/src`, `frontend/src` | No (advisory for now) |

CodeQL is **not** a job in this workflow. This repo already has GitHub's
**Default Setup** code scanning enabled (visible as a separate `CodeQL` check
with `Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze
(python)`, pre-dating this PR). A custom `codeql-action/init` +
`codeql-action/analyze` job for the same languages was tried here first and
failed outright — GitHub refuses to run an "advanced configuration" CodeQL
workflow alongside Default Setup for languages Default Setup already covers,
by design, not a misconfiguration to fix. Since Default Setup already scans
Python and JS/TS (plus GitHub Actions workflows, which this project wasn't
separately covering), duplicating it here would only re-create the conflict.
Treat `Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze
(python)` as this project's advisory CodeQL checks going forward.

### Why pip-audit only scans `requirements.txt`, not `requirements-dev.txt`

A vulnerable dev-only tool (test runner, linter) never ships to production and
never reaches an attacker. A vulnerable production dependency does. Scanning
only what ships keeps the gate meaningful instead of noisy.

### Why `npm audit` uses `--audit-level=high --omit=dev`

Running `npm install` in `frontend/` already surfaces moderate-severity
advisories in transitive graph-library dependencies. Gating on every
moderate finding would make the check fail on day one for issues nobody can
act on immediately, which is how required checks quietly get disabled later.
`--audit-level=high` keeps the gate on what's actually actionable; moderate
findings are still visible in the job log, just not blocking.

`--omit=dev` applies the same production-only principle as pip-audit above:
on the first real run, the only remaining high/critical findings
(`tinypool`/`vitest`'s prototype-pollution RCE) were in `vitest`, a
`devDependency` — the test runner, never shipped, never reachable by an
attacker. The genuinely production-relevant findings from that same run
(`react-router` CSRF bypass, `postcss` path traversal, `nanoid`,
`browserslist`, `source-map-js`) were fixed outright via `npm audit fix`
(non-breaking, within existing semver ranges) and verified with `npm run
build` and `npm run test` before merging — not suppressed.

### Why CodeQL and Semgrep start advisory, not required

Both are the two scanners most prone to noisy first-run false positives on an
existing codebase. They run on every PR and push, and genuine findings show
up in the GitHub Security tab (CodeQL, via Default Setup) or the job log
(Semgrep), but a red result here does **not** block a merge yet. Once a
baseline pass is clean (see the triage log below), add their check names to
branch protection and they become required the same as the other four.

### Trivy and the image build (Shared Contract 1)

Trivy scans the exact image M1's Dockerfile produces:

```bash
docker build -t cspm-backend:phase9 ./backend
```

No registry push is involved (per the Wave D decision to build-on-VM, not
registry-push) — CI builds the same image fresh in this job, scans it for
`CRITICAL`/`HIGH` severity vulnerabilities with known fixes
(`ignore-unfixed: true`), and discards it. The artifact that matters for
deployment is the Dockerfile and compose file in the repo, not a pushed
image.

## 3. Branch protection (Shared Contract 2)

Branch protection on `main` requires:

- `pytest` (Phase 1 Tests)
- `api` (Phase 2 Tests)
- `frontend` (Phase 3 Frontend)
- `Gitleaks` (Secret scan)
- `Bandit (Python SAST)`
- `pip-audit (production dependencies)`
- `npm audit (frontend dependencies)`
- `Trivy (backend image scan)`

`Semgrep (advisory)` and Default Setup's `Analyze (actions)` / `Analyze
(javascript-typescript)` / `Analyze (python)` checks are intentionally **not**
in this list yet — see above.

This is a GitHub repository-settings change (Settings → Branches → branch
protection rule for `main`), not a workflow file. A scanner workflow nobody's
required to pass is noise, not a gate — confirm this is configured, and
confirm it with a real test: open a PR with a failing required check and
verify GitHub blocks the merge button, don't just confirm the workflow runs.

M2 and M3's deploy workflows trigger only on push to `main`, which — once
branch protection above is in place — already implies every required check
passed. Neither needs its own redundant `needs:` gate on these job names as
long as that stays true.

## 4. Known suppressed findings (tracked, not ignored)

| Check | Finding | Why suppressed | Follow-up |
| --- | --- | --- | --- |
| `pip-audit`, `trivy` | `starlette 0.46.2` (transitive via `fastapi==0.115.14`): pip-audit's PYSEC-2026-1941/1942/161/2280/2281/248/249, Trivy's CVE-2025-62727/CVE-2026-48818/CVE-2026-54283 | Fix requires a starlette 0.46→1.x major bump via a ~35-minor-version `fastapi` bump — a real regression risk needing its own test pass, not a silent CI-config change | Open a dedicated fastapi/starlette upgrade task with full backend regression testing; remove the `--ignore-vuln` flags in `pip-audit` and the matching lines in `.trivyignore` once it lands |
| `trivy` | `jaraco.context` CVE-2026-23949, `msgpack` GHSA-6v7p-g79w-8964, `setuptools` CVE-2025-47273, `wheel` CVE-2026-24049, and `urllib3` CVE-2026-97687/97689 at version 2.7.0 | Confirmed by locating each inside the built image (`docker run --rm cspm-backend:phase9 find / -iname ...`): all five live under `pip/_vendor/` or `setuptools/_vendor/` — pip's and setuptools' own bundled copies, or botocore's legacy `vendored/requests/packages/urllib3` compat shim. None are invoked at runtime (the container's `CMD` never calls `pip` or `setuptools`); the real, top-level, importable `urllib3` the app and botocore actually use is pinned `>=2.8.0` in `backend/requirements.txt` and verified clean | Suppressed in `.trivyignore` at the repo root with this same reasoning; revisit if a future `python:3.11-slim` base image bump changes pip's bundled vendor versions |

See `.trivyignore` for the exact suppressed IDs.

## 5. How to triage a new finding

1. **Confirm it's real.** Reproduce locally with the same tool/flags shown in
   the job log before deciding whether to fix or suppress.
2. **Fix it if it's cheap and real** — upgrade the dependency, patch the
   pattern Bandit/Semgrep flagged, rebuild the image on a patched base layer
   for Trivy.
3. **If it's a false positive or an accepted risk, suppress it explicitly
   with a reason**, inline next to the finding (e.g. `# nosec` with a comment
   for Bandit, a `.semgrepignore` entry, an `--ignore` entry for pip-audit),
   never by disabling the whole check or widening `--audit-level`/severity
   thresholds to make noise disappear.
4. **Record genuinely-triaged findings** so the next run's diff is only new
   findings, not the same accepted one resurfacing every PR.
5. Never bypass a required check by merging without it passing, bypassing
   branch protection, or adding `continue-on-error: true` to make a required
   job always green — that defeats the gate.

## 6. Verification checklist

- [ ] Bandit, pip-audit, npm audit, Trivy all run in CI and produce a real
      result, not just "step completed." CodeQL runs via GitHub's Default
      Setup, already enabled separately from this workflow.
- [ ] A deliberately-introduced vulnerable dependency/pattern was caught at
      least once during setup, proving the gate actually gates.
- [ ] Each scanner's first real run triaged — genuine findings fixed or
      explicitly suppressed with a reason, not ignored.
- [ ] Branch protection configured on `main` with the required-check list
      above.
- [ ] Branch protection confirmed to block a PR with a failing required
      check (tested, not assumed).
- [ ] CodeQL and Semgrep run and are visible, but intentionally not yet
      required.

## 7. Handoffs

**Member 2 — Frontend Deployment** and **Member 3 — Backend + DB
Deployment:** the required-check list in section 3 is final; deploy
workflows can trigger on push to `main` without a redundant `needs:` gate.
