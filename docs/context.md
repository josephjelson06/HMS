# HMS AuthModule Integration Context

## Current Snapshot
- Timestamp: 2026-02-09T01:51:36+05:30
- Current branch: `master`
- Current commit: `0d108413af74a9fd889143988c4300c85d935ab1`
- Note: git history was rewritten to purge leaked artifacts. Any commit SHAs captured before the rewrite are no longer valid.

## Merged / Open PRs

### Merged
- PR #1: Replace unmaintained auth dependencies and fix login timing attack
- PR #2: Add startup configuration guards
- PR #3: Hardened CSRF middleware
- PR #4: Typed access token claims
- PR #5: Alembic + schema alignment
- PR #6: Refresh token family system
- PR #7: RBAC enhancements
- PR #8: AuthContext + tenant middleware
- PR #9: Audit system
- PR #10: Password management endpoints
- PR #11: Family-linked impersonation refactor
  - URL: https://github.com/josephjelson06/HMS/pull/11
  - Merged at: 2026-02-08T13:18:37Z
- PR #12: Frontend auth hardening (CSRF preflight + forced reset flow)
  - URL: https://github.com/josephjelson06/HMS/pull/12
  - Merged at: 2026-02-08T13:25:47Z
- PR #13: Context handoff document
  - URL: https://github.com/josephjelson06/HMS/pull/13
  - Merged at: 2026-02-08T13:28:39Z
- PR #14: Refresh context handoff snapshot after PR13
  - URL: https://github.com/josephjelson06/HMS/pull/14
  - Merged at: 2026-02-08T13:30:10Z
- PR #15: Phase 4.3: Secrets rotation runbook
  - URL: https://github.com/josephjelson06/HMS/pull/15
  - Merged at: 2026-02-08T18:45:09Z
- PR #16: Phase 4.4: OWASP ZAP baseline + security headers
  - URL: https://github.com/josephjelson06/HMS/pull/16
  - Merged at: 2026-02-08T19:16:54Z
- PR #17: Phase 4.5: Auth-negative regression automation
  - URL: https://github.com/josephjelson06/HMS/pull/17
  - Merged at: 2026-02-08T19:27:26Z
- PR #18: Next.js 16.1.6 upgrade (fix npm audit HIGH)
  - URL: https://github.com/josephjelson06/HMS/pull/18
  - Merged at: 2026-02-08T19:56:10Z
- PR #20: Phase 5.1: performance env readiness
  - URL: https://github.com/josephjelson06/HMS/pull/20
  - Merged at: 2026-02-08T20:20:36Z

### Open
- None

## Locked Decisions
1. PR sequence executed strictly: PR11 then PR12.
2. PR12 scope was repurposed to frontend auth hardening.
3. Context persistence location is `docs/context.md`.
4. Canonical password flow is `/api/auth/password/change`.
5. Profile pages no longer provide password-edit fields in frontend UX.

## PR11 Checklist Status (Completed)
- [x] Family-linked impersonation repository methods added:
  - `find_active_impersonation_for_refresh_family()`
  - `set_refresh_token_family_id()`
- [x] `start_impersonation()` updated:
  - actor refresh token accepted
  - parent family linkage applied
  - impersonation session stores `refresh_token_family_id`
- [x] `refresh()` updated to resolve impersonation by refresh family linkage.
- [x] `stop_impersonation()` updated to revoke linked impersonation family by family id first.
- [x] Canonical impersonation claims (`actor_user_id`, `acting_as_user_id`) emitted with legacy aliases preserved.
- [x] Router passes actor refresh cookie into impersonation start.
- [x] Refresh token helper added: `revoke_refresh_token_family()`.
- [x] Unit tests added/extended:
  - `backend/tests/unit/test_auth_impersonation_service.py`
  - `backend/tests/unit/test_impersonation_context.py`
  - `backend/tests/unit/test_refresh_token_family.py`

## PR12 Checklist Status (Completed)
- [x] PR metadata repurposed to frontend auth hardening.
- [x] CSRF preflight dedupe implemented in `frontend/lib/api/client.ts` (`ensureCsrfCookie()`).
- [x] `AuthResponse` type extended with `must_reset_password`.
- [x] Auth provider tracks `mustResetPassword`.
- [x] Login redirects to `/change-password` when reset is required.
- [x] New forced reset UI route added: `frontend/app/(auth)/change-password/page.tsx`.
- [x] `authApi.changePassword()` added for `/auth/password/change`.
- [x] Workspace guard redirects users with `mustResetPassword` to `/change-password`.
- [x] Admin/hotel profile pages now edit only first/last name (no password fields in UI).

## Validation Commands and Latest Results

### Backend
- Command (ensure env vars are set: `DATABASE_URL`, `JWT_SECRET` (>=32 chars), `SEED_DATA=false`):
  - `cd backend`
  - `python -m pytest -q`
- Result: `152 passed, 1 skipped`

- Command (ensure env vars are set: `DATABASE_URL`, `JWT_SECRET` (>=32 chars)):
  - `cd backend`
  - `python -m alembic heads`
- Result: single head `0021_backfill_refresh_token_families (head)`

- Command (live API smoke gate; requires backend running with seeded data):
  - `python backend/scripts/smoke_api.py --base-url http://127.0.0.1:8000/api`
- Result: `OK` (0 failures)

### Frontend
- Command: `cd frontend && npm run lint`
- Result: no ESLint warnings/errors

- Command: `cd frontend && npm run build`
- Result: success, includes `/change-password` route

- Command: `cd frontend && npm run test:e2e`
- Result: `2 passed` (Chromium)

- Command: `cd frontend && npm audit --omit=dev`
- Result: `found 0 vulnerabilities`

### Performance (Phase 5)
- Baseline k6 run (disposable DB: `hms_perf_20260209_083359`):
  - `docker run --rm --network hms_default -e HMS_PERF_BASE_URL=http://hms-perf-backend:8000/api -e HMS_PERF_ORIGIN=http://localhost:3000 -e HMS_PERF_DURATION=30s -e HMS_PERF_VUS_ADMIN=1 -e HMS_PERF_VUS_HOTEL_REFRESH=1 -e HMS_PERF_VUS_HOTEL_CRUD=1 -v \"${PWD}\\scripts\\perf\\k6:/scripts\" grafana/k6 run /scripts/hms_phase5.js`
- Result: PASS (http_req_failed=0%)
  - p95 `POST /auth/refresh`: `40.9ms`
  - p95 `POST /hotel/rooms/` (create): `46.44ms`
  - p95 `GET /hotel/rooms/` (list): `18.31ms`

## Hardening Phase Status (Auth + Security)
- Phase 1 (migrations): completed
- Phase 2 (automated regression gates): completed
- Phase 3A (API smoke gate): completed (`backend/scripts/smoke_api.py`)
- Phase 3B (frontend E2E, Chromium): completed (Playwright)
- Phase 4.1 (reduce scan noise): completed (cleaned build artifacts; working-tree gitleaks clean)
- Phase 4.2 (rewrite git history; purge leaks): completed (gitleaks git/history clean; remote branches pointing to old history deleted)
- Phase 4.3 (secrets rotation runbook): completed (`docs/runbooks/secrets.md`, updated `.env.example` guidance)
- Phase 4.4 (DAST baseline): completed (OWASP ZAP baseline; summary in `docs/security/zap_baseline.md`)
- Phase 4.5 (auth-negative regression automation): completed (`backend/tests/system/test_auth_negative_regressions.py`)
- Phase 4.6 (Next.js upgrade to address npm audit HIGH): completed (upgraded to Next 16.x; `npm audit --omit=dev` clean)
- Phase 5.1 (perf env readiness): completed (`docs/runbooks/performance.md`, `scripts/perf/New-HmsPerfDb.ps1`)
- Phase 5.2 (k6 suite): completed (`scripts/perf/k6/hms_phase5.js`)
- Phase 5.3 (baseline run): completed (k6 baseline run at 3 VUs total / 30s)
- Phase 5.4 (steady-state load): pending
- Phase 5.5 (spike test): pending
- Phase 5.6 (endurance soak): pending
- Phase 5.7 (recovery / restart checks): pending
- Phase 5.8 (perf report + thresholds): pending
- Phase 6 (release readiness): pending

## Known Risks / Follow-ups
1. Ensure CI uses a Node version compatible with Next 16 (Next 16.1.6 requires Node `>=20.9.0`).
2. System auth-negative regression tests require a running backend (set `SMOKE_BASE_URL`). Prefer running them against a disposable DB for repeatability.
3. Backend profile update endpoints still accept password fields; frontend no longer uses them. If desired, enforce backend-level canonicalization later by deprecating password fields in profile schemas/services.

## Next-Session Start Instructions
1. If you cloned before the history rewrite:
   - Prefer a fresh clone.
   - If you must keep your clone, back up local work and then realign to `origin/master`.
2. Start from `master` and pull latest:
   - `git checkout master`
   - `git pull --ff-only`
2. Re-run quality gates:
   - backend: `python -m pytest -q`, `python -m alembic heads`
   - frontend: `npm run lint`, `npm run build`, `npm run test:e2e`
3. Re-run live API smoke gate against a disposable DB:
   - `python backend/scripts/smoke_api.py --base-url http://127.0.0.1:8000/api`
4. Continue security phase:
   - re-run OWASP ZAP baseline as needed (see `docs/security/zap_baseline.md`)
   - run auth-negative system gate: `cd backend && SMOKE_BASE_URL=http://127.0.0.1:8000/api python -m pytest -q -m system`
   - upgrade Next to remove HIGH audit findings
