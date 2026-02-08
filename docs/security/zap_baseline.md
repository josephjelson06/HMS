# OWASP ZAP Baseline (Phase 4.4)

## What This Covers
Unauthenticated DAST baseline scans against the running local backend, using the OpenAPI spec to import endpoints.

Outputs (HTML/JSON) are written to `docs/security/reports/` and are intentionally gitignored.

## How To Run (Local)
Backend must be running on `http://127.0.0.1:8000`.

API baseline (safe mode, OpenAPI import):

```powershell
docker run --rm -t --user 0 `
  -v ${PWD}:/zap/wrk/:rw `
  zaproxy/zap-weekly zap-api-scan.py `
  -t http://host.docker.internal:8000/openapi.json `
  -f openapi -S -a -I `
  -r docs/security/reports/zap-api-baseline.html `
  -J docs/security/reports/zap-api-baseline.json
```

Docs/UI baseline (optional, crawls `/docs`):

```powershell
docker run --rm -t --user 0 `
  -v ${PWD}:/zap/wrk/:rw `
  zaproxy/zap-weekly zap-baseline.py `
  -t http://host.docker.internal:8000/docs `
  -m 5 -a -I `
  -r docs/security/reports/zap-baseline.html `
  -J docs/security/reports/zap-baseline.json
```

Note: `zaproxy/zap-stable` is currently unusable in this environment (container system files are 0 bytes, Python fails to start).
We use `zaproxy/zap-weekly` for repeatability.

## Latest Results (2026-02-09)
### API Baseline (OpenAPI, safe mode)
- `FAIL`: 0
- `WARN`: 1
- `PASS`: 144

Remaining warning:
- `Cookie No HttpOnly Flag [10010]`
  - Cause: our CSRF cookie (`csrf_token`) is intentionally **not** `HttpOnly` because the frontend must read it and echo it via `X-CSRF-Token` (double-submit CSRF protection).
  - Reference: `backend/app/middleware/csrf.py`
  - Risk tradeoff: if you have an XSS, the CSRF token can be read. We rely on the XSS posture of the frontend + standard mitigations. This is expected for this CSRF approach.

### Fixes Applied During Phase 4.4
To address missing security headers flagged by the API scan, we added a baseline headers middleware:
- `backend/app/middleware/security_headers.py`
- wired in `backend/app/main.py`

Headers now included on responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Cross-Origin-Resource-Policy: same-origin`

