# Migration Guide: AuthModule Schema Integration

This PR introduces 6 new Alembic migrations (0015-0020) to align HMS's database schema with the AuthModule.

## Migrations Overview

### Migration 0015: Create `refresh_token_families` table
- New table for managing refresh token families
- Includes tenant_id, user_id, parent_family_id, created_by_user_id
- Tracks revocation status and reasons
- Indexed on tenant_id and user_id

### Migration 0016: Add columns to `users` table
- `username` (String(120), NOT NULL) - backfilled from email
- `domain` (String(120), nullable)
- `must_reset_password` (Boolean, default false)
- `invited_at` (DateTime with timezone, default now())
- Email widened from 255 to 320 characters (RFC 5321 max)
- Unique constraint on (tenant_id, username)

### Migration 0017: Add columns to `refresh_tokens` table
- `family_id` (UUID, nullable, FK to refresh_token_families)
- `rotated_at` (DateTime with timezone, nullable)

### Migration 0018: Rename `impersonation_sessions` columns
- `admin_user_id` → `actor_user_id`
- `target_user_id` → `acting_as_user_id`
- `target_tenant_id` → `tenant_id`
- Add `refresh_token_family_id` (UUID, nullable, FK to refresh_token_families)

### Migration 0019: Rename `audit_logs` columns
- `user_id` → `actor_user_id`
- `changes` → `metadata`
- Add `acting_as_user_id` (UUID, nullable, FK to users)

### Migration 0020: Data migration for `user_type`
- Update all users with `user_type = 'admin'` to `user_type = 'platform'`
- Update CHECK constraint to allow ('platform', 'hotel') instead of ('admin', 'hotel')

## Code Changes

### Models Updated
- `User`: Added username, domain, must_reset_password, invited_at
- `RefreshToken`: Added family_id, rotated_at
- `RefreshTokenFamily`: New model
- `ImpersonationSession`: Renamed columns, added refresh_token_family_id
- `AuditLog`: Renamed columns, added acting_as_user_id

### Services/Repositories Updated
- `ImpersonationSessionRepository`: Methods use new column names
- `AuthService`: Updated impersonation methods, user_type checks changed to 'platform'
- `AdminUserService`: user_type changed to 'platform'
- `AdminReportsService`: user_type changed to 'platform'
- `HotelUserService`: Added username field to user creation

### Routers Updated
- `AuthRouter`: user_type check changed to 'platform'
- `AdminUsersRouter`: user_type checks changed to 'platform'

### Seed Data Updated
- Admin user now has `user_type = 'platform'`
- Users created with username field

## Running Migrations

1. **Backup your database first**
   ```bash
   pg_dump -h localhost -U hms -d hms > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Verify migrations**
   ```bash
   alembic current
   # Should show: 0020_migrate_user_type
   ```

4. **Rollback if needed**
   ```bash
   alembic downgrade 0014_report_export_async_queue
   ```

## Verification Checklist

After running migrations, verify:

- [ ] All migrations completed successfully
- [ ] `refresh_token_families` table exists with correct schema
- [ ] `users` table has new columns (username, domain, must_reset_password, invited_at)
- [ ] `users.email` is VARCHAR(320)
- [ ] All existing users have username populated (from email)
- [ ] `refresh_tokens` has family_id and rotated_at columns
- [ ] `impersonation_sessions` columns renamed correctly
- [ ] `audit_logs` columns renamed correctly
- [ ] All users with old `user_type = 'admin'` now have `user_type = 'platform'`
- [ ] App starts without errors
- [ ] Login works (both admin and hotel users)
- [ ] Impersonation works
- [ ] Seed script creates users correctly

## Testing

```bash
# Start the services
docker compose up --build

# In another terminal, run migrations
docker compose exec backend alembic upgrade head

# Verify seed data
docker compose exec backend python -m app.core.seed

# Access the application
# - Admin: admin@demo.com / Admin123!
# - Hotel: manager@demo.com / Manager123!
```

## Backward Compatibility Notes

- **Breaking**: Code that directly references `admin_user_id`, `target_user_id`, `target_tenant_id` in ImpersonationSession will break
- **Breaking**: Code that references `user_id` in AuditLog will break
- **Breaking**: Code that references `.changes` on AuditLog will break
- **Breaking**: Code that checks `user_type == 'admin'` will no longer match users (use 'platform' instead)
- **Non-breaking**: The impersonation context dictionary still uses the old keys (admin_user_id, target_user_id) for frontend compatibility

## What's Next

This migration is a prerequisite for:
- PR 6: Refresh token family system implementation
- PR 7: RBAC enhancements
- PR 8: Tenant context improvements
- PR 11: Impersonation refactoring
