# HMS AuthModule Integration Context

## Current Snapshot
- Timestamp: 2026-02-08T19:00:00+05:30
- Current branch: `master`
- Current commit: `29c845df86e1fc530c21759c241fe86dc0c1ff68`
- Working tree note: untracked local planning file present (`CompletePlan.md`)

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
  - Merge commit: `fb8f31d9ce003b0c5673747647da9e646fbf0ed9`
- PR #12: Frontend auth hardening (CSRF preflight + forced reset flow)
  - URL: https://github.com/josephjelson06/HMS/pull/12
  - Merged at: 2026-02-08T13:25:47Z
  - Merge commit: `8729300d873c145c6303348522021e0cb21a6a90`
- PR #13: Context handoff document
  - URL: https://github.com/josephjelson06/HMS/pull/13
  - Merged at: 2026-02-08T13:28:39Z
  - Merge commit: `29c845df86e1fc530c21759c241fe86dc0c1ff68`

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
- Command:
  - `cd backend`
  - `$env:DATABASE_URL='postgresql+asyncpg://hms:devpassword@localhost:5432/hms'`
  - `$env:JWT_SECRET='<redacted>'`
  - `$env:SEED_DATA='false'`
  - `python -m pytest -q`
- Result: `149 passed, 1 skipped`

- Command:
  - `cd backend`
  - `$env:DATABASE_URL='postgresql+asyncpg://hms:devpassword@localhost:5432/hms'`
  - `$env:JWT_SECRET='<redacted>'`
  - `python -m alembic heads`
- Result: single head `0021_backfill_refresh_token_families (head)`

### Frontend
- Command: `cd frontend && npm run lint`
- Result: no ESLint warnings/errors

- Command: `cd frontend && npm run build`
- Result: success, includes `/change-password` route

## Known Risks / Follow-ups
1. End-to-end browser/API smoke tests for full login -> forced reset -> dashboard and full impersonation lifecycle should be run against a live environment with seeded data and cookie flows.
2. Backend profile update endpoints still accept password fields; frontend no longer uses them. If desired, enforce backend-level canonicalization later by deprecating password fields in profile schemas/services.
3. Existing local untracked file `CompletePlan.md` remains and is intentionally untouched.

## Next-Session Start Instructions
1. Start from `master` and pull latest:
   - `git checkout master`
   - `git pull --ff-only`
2. Verify PR state quickly:
   - `gh pr list --state open`
3. Re-run quality gates before additional auth changes:
   - backend pytest + alembic head check
   - frontend lint + build
4. If continuing hardening, prioritize live smoke scenarios:
   - impersonation start -> refresh rotations -> stop
   - forced reset login flow and workspace guard behavior
