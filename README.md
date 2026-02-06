# HMS Foundation Module

This repo contains the foundation layer for the Hotel Management System (HMS):
- Shared authentication
- Permission-based RBAC
- Strict multi-tenancy enforcement
- Minimal admin/hotel shells

## Quick start

1. Create `.env`:

```
copy .env.example .env
```

2. Start services:

```
docker compose up --build
```

3. Run migrations:

```
cd backend
alembic upgrade head
```

4. Log in using seeded users:

- Admin: `admin@demo.com` / `Admin123!`
- Hotel: `manager@demo.com` / `Manager123!`

## Dev endpoints

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PgAdmin: http://localhost:5050

## Notes

- Auth is cookie-based (access + refresh). CSRF protection uses `X-CSRF-Token`.
- Tenant isolation is enforced in service/repository layers.
- To customize seed data, update `.env` values.
