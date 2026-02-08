# HMS Auth Threat Model (Tokens, CSRF, Impersonation)

Last updated: 2026-02-08

## Scope
This document focuses on the security posture of HMS authentication and session management after the AuthModule integration:
- Access tokens (JWT) and refresh tokens
- Refresh token families (rotation + reuse detection)
- CSRF protection (double-submit cookie + Origin/Referer allowlist)
- Impersonation (platform admin acting as hotel user)
- Password reset / forced reset flows
- Tenant boundary enforcement (platform vs hotel)

Out of scope (for now):
- Infrastructure hardening (WAF, reverse proxy, TLS termination)
- OS/container hardening
- Advanced DAST with authenticated crawling

## Assets (What We Protect)
- `access_token` JWT (authn/authz claims)
- `refresh_token` (session continuity)
- Refresh token families + token rows (reuse detection + revocation controls)
- CSRF token (`csrf_token` cookie) used as header echo
- User accounts, roles, permissions, and tenant IDs
- Impersonation sessions (who acted as whom, for which tenant, and why)
- Audit logs (security visibility + forensics)

## Entry Points
- Browser -> API (cookie-based auth)
- Public endpoints:
  - `POST /api/auth/login`
  - `POST /api/auth/refresh`
  - `GET /api/auth/csrf`
  - `GET /api/health`
- Authenticated endpoints (selected):
  - `GET /api/auth/me`
  - `POST /api/auth/password/change`
  - `POST /api/auth/password/reset` (admin-only)
  - `POST /api/auth/impersonation/start` (admin-only)
  - `POST /api/auth/impersonation/stop`
- DB (Postgres) storing users/tokens/families/audits/impersonation sessions

## Trust Boundaries
- User agent (untrusted) vs backend API (trusted)
- Platform tenant scope (no `tenant_id`) vs hotel tenant scope (`tenant_id` required)
- Normal session vs impersonation session (separate refresh family lineage)
- Application code vs database integrity constraints/migrations

## Threats (STRIDE) and Mitigations

### Spoofing
- Threat: stolen refresh token reused to mint new sessions.
  - Mitigation: refresh token rotation + reuse detection revokes entire family.
- Threat: forging JWTs (weak secret).
  - Mitigation: startup guard rejects weak `JWT_SECRET` (< 32 chars or known weak values).

### Tampering
- Threat: tampering with CSRF token (header/cookie mismatch).
  - Mitigation: timing-safe `hmac.compare_digest` for cookie/header comparison.
- Threat: impersonation context lost/forged across refresh.
  - Mitigation: impersonation sessions are linked to a dedicated refresh family (`refresh_token_family_id`); refresh decides impersonation by family linkage, not by arbitrary client claims.

### Repudiation
- Threat: privileged actions without audit trace.
  - Mitigation: audit logs for sensitive auth actions (password reset/change/invite) and impersonation start/stop.
  - Residual risk: ensure commits occur after audit writes for all audited routes; treat missing audit commits as a defect.

### Information Disclosure
- Threat: cookies exposed over insecure transport.
  - Mitigation: `COOKIE_SECURE=true` is enforced in production via startup guard.
- Threat: CSRF token readable by JS (required for double-submit) combined with XSS.
  - Mitigation: CSRF is not an XSS defense; reduce XSS risk via CSP + output encoding and keep tokens out of DOM/logs.

### Denial of Service
- Threat: login/refresh brute forcing or refresh storms.
  - Mitigations (recommended next): rate limiting on `/login` and `/refresh`, plus anomaly alerts on 401/403 spikes.

### Elevation of Privilege
- Threat: hotel users calling platform endpoints.
  - Mitigation: permission checks (`require_permission`) + tenant context enforcement for hotel users.
- Threat: legacy `user_type="admin"` tokens interpreted incorrectly.
  - Mitigation: transitional mapping treats `admin` as platform until all DBs are migrated.
- Threat: impersonation used to cross tenant boundaries.
  - Mitigation: impersonation session binds `tenant_id` and `acting_as_user_id`; admin-only permission is required to start impersonation.

## Residual Risks / Follow-ups
1. Add explicit rate limiting and lockout policy for `/login` and sensitive admin endpoints.
2. Add CSP and security headers at the edge (and/or in FastAPI) to reduce XSS risk.
3. Expand DAST to authenticated flows (ZAP context + scripted login) for deeper coverage.
4. Expand browser matrix beyond Chromium if required by deployment constraints.

## Monitoring Recommendations
- Alert on:
  - refresh token reuse detections (family revoke spikes)
  - sustained increases in 401/403 and 5xx
  - password reset volume spikes
  - impersonation start/stop anomalies (frequency, duration)
- Log/metric cardinality controls:
  - never log raw refresh tokens; log family_id/token_id only.
