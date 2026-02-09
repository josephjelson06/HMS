# Performance + Reliability Runbook (Phase 5)

This runbook standardizes how we prepare an isolated, disposable database and run Phase 5 performance and reliability checks locally.

## Defaults (Current)
- Load target: `25-50` virtual users (VUs)
- Backend base URL: `http://127.0.0.1:8000/api`
- CSRF Origin header: `http://localhost:3000`
- Postgres (docker) host port: `5434` (see `docker-compose.yml`)

## Prereqs
- Docker is running
- Postgres container is up: `hms-db`
- Python can run backend tooling (`alembic`, seed script)

## 5.1 Environment Readiness (Disposable DB)

### 1) Start Postgres
```powershell
cd C:\Users\josep\Documents\AarkayTechnoConsultants\HMS
docker compose up -d db
```

### 2) Create + migrate + seed a disposable perf DB
This creates a DB named like `hms_perf_YYYYMMDD_HHMMSS`, runs `alembic upgrade head`, and seeds demo users/roles/permissions.

```powershell
.\scripts\perf\New-HmsPerfDb.ps1
```

The script prints two connection strings:
- `DATABASE_URL (host)`: use this when running backend locally (connects via `localhost:5434`)
- `DATABASE_URL (docker network)`: use this when running backend in Docker (connects via `db:5432`)

### 3) Start backend against the disposable DB (local)
Option A (recommended for Phase 5): run backend locally with explicit env vars:
```powershell
$env:DATABASE_URL="postgresql+asyncpg://hms:devpassword@localhost:5434/<DB_NAME>"
$env:JWT_SECRET="<at least 32 chars>"
$env:CORS_ORIGINS="http://localhost:3000"
$env:SEED_DATA="true"
cd .\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4) Sanity check
```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health
```

## Notes
- Most mutating endpoints require a CSRF double-submit cookie + matching `X-CSRF-Token` header + allowed `Origin`.
- Load tests must simulate browser-like headers/cookies for mutating requests (login, refresh, CRUD).
- Next.js 16.1.6 requires Node `>=20.9.0` (keep CI aligned).

## 5.2 k6 Load Suite

Suite location: `scripts/perf/k6/hms_phase5.js`

Environment variables:
- `K6_BASE_URL` (default `http://127.0.0.1:8000/api`)
- `K6_ORIGIN` (default `http://localhost:3000`)
- `K6_DURATION` (default `2m`)
- `K6_VUS_ADMIN` (default `5`)
- `K6_VUS_HOTEL_REFRESH` (default `10`)
- `K6_VUS_HOTEL_CRUD` (default `10`)
- `K6_THRESH_P95_REFRESH_MS` (default `250`)
- `K6_THRESH_P95_CRUD_MS` (default `400`)

### Option A: Run k6 installed on host
```powershell
$env:K6_BASE_URL="http://127.0.0.1:8000/api"
$env:K6_ORIGIN="http://localhost:3000"
k6 run .\scripts\perf\k6\hms_phase5.js
```

### Option B (recommended on Windows): Run k6 via Docker
This avoids installing k6. Note: use `host.docker.internal` to reach the host backend from inside Docker.
```powershell
$env:K6_BASE_URL="http://host.docker.internal:8000/api"
$env:K6_ORIGIN="http://localhost:3000"

docker run --rm `
  -e K6_BASE_URL=$env:K6_BASE_URL `
  -e K6_ORIGIN=$env:K6_ORIGIN `
  -e K6_DURATION=2m `
  -e K6_VUS_ADMIN=5 `
  -e K6_VUS_HOTEL_REFRESH=10 `
  -e K6_VUS_HOTEL_CRUD=10 `
  -v \"${PWD}\\scripts\\perf\\k6:/scripts\" `
  grafana/k6 run /scripts/hms_phase5.js
```


