# Secrets and Rotation Runbook

## Scope
This runbook covers:
- How to generate/store/rotate secrets for HMS.
- What to expect when rotating auth secrets (token invalidation).

It intentionally does not include any real secret values.

## Non-Negotiables
- Never commit secrets to git (even for "dev").
- Assume any secret previously present in git history is compromised and must be rotated.
- Store production secrets in a secret manager (not `.env` files on disk).

## Backend Secrets / Sensitive Config
- `JWT_SECRET`
  - Required.
  - Must be high entropy and at least 32 characters.
  - Rotation impact: invalidates all existing access/refresh tokens; users will need to log in again.
- Database credentials (for the DB user referenced by `DATABASE_URL`)
  - Treat as secrets even in non-prod if the DB is reachable by others.

## Generating a Strong JWT Secret
Use any cryptographically secure generator. Examples:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Notes:
- Do not paste generated values into docs or tickets.
- Prefer rotating secrets during a maintenance window (token invalidation is expected).

## Where To Store Secrets
- Local development:
  - Use environment variables or your local `.env` (which must be gitignored).
- Production:
  - Use a secret manager and inject env vars at runtime.
  - Do not bake secrets into Docker images.

## Rotation Procedure (JWT_SECRET)
1. Generate a new secret (see above).
2. Update the runtime secret source (secret manager / env var injection).
3. Deploy the new configuration and restart the backend.
4. Verify:
   - logins work
   - refresh works
   - impersonation start/stop works
5. Expect all existing sessions/tokens to become invalid.

## Incident Note (Leak Suspected)
If you suspect `JWT_SECRET` (or DB creds) leaked:
1. Rotate immediately.
2. Audit recent auth/audit logs for anomalies around:
   - refresh token reuse detections
   - impersonation usage
   - elevated 401/403/5xx spikes
3. If DB creds leaked, rotate DB user password and invalidate active sessions.

