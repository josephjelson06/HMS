# Testing Checklist for Migration PR

This checklist should be completed to verify the migrations work correctly.

## Pre-Migration Verification

- [ ] Database backup completed
- [ ] Current alembic version is `0014_report_export_async_queue`
- [ ] No pending migrations (`alembic current` shows head)
- [ ] Application is running on current schema

## Run Migrations

```bash
# Start fresh database (if testing in dev)
docker compose down -v
docker compose up -d db

# Wait for database to be ready
sleep 5

# Run migrations
docker compose exec backend alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 0014_report_export_async_queue -> 0015_create_refresh_token_families, Create refresh_token_families table
INFO  [alembic.runtime.migration] Running upgrade 0015_create_refresh_token_families -> 0016_add_user_columns, Add username, domain, must_reset_password, invited_at to users
INFO  [alembic.runtime.migration] Running upgrade 0016_add_user_columns -> 0017_add_refresh_token_columns, Add family_id and rotated_at to refresh_tokens
INFO  [alembic.runtime.migration] Running upgrade 0017_add_refresh_token_columns -> 0018_rename_impersonation_columns, Rename impersonation_sessions columns and add refresh_token_family_id
INFO  [alembic.runtime.migration] Running upgrade 0018_rename_impersonation_columns -> 0019_rename_audit_columns, Rename audit_logs columns for AuthModule consistency
INFO  [alembic.runtime.migration] Running upgrade 0019_rename_audit_columns -> 0020_migrate_user_type, Migrate user_type 'admin' to 'platform'
```

## Schema Verification

### 1. Check refresh_token_families table exists
```sql
\d refresh_token_families
```
Expected columns:
- id (uuid, PK)
- tenant_id (uuid, FK to tenants)
- user_id (uuid, FK to users)
- parent_family_id (uuid, FK to refresh_token_families, nullable)
- created_by_user_id (uuid, FK to users, nullable)
- revoked_at (timestamp with timezone, nullable)
- revoke_reason (varchar(255), nullable)
- created_at (timestamp with timezone)
- updated_at (timestamp with timezone)

Indexes:
- ix_refresh_token_families_tenant_id
- ix_refresh_token_families_user_id

### 2. Check users table updates
```sql
\d users
```
Expected new columns:
- username (varchar(120), NOT NULL)
- domain (varchar(120), nullable)
- must_reset_password (boolean, NOT NULL, default false)
- invited_at (timestamp with timezone, NOT NULL)
- email should be varchar(320)

Constraints:
- uq_users_tenant_username (UNIQUE on tenant_id, username)

Verify username populated:
```sql
SELECT COUNT(*) as total, COUNT(username) as with_username FROM users;
-- total should equal with_username
```

### 3. Check refresh_tokens table updates
```sql
\d refresh_tokens
```
Expected new columns:
- family_id (uuid, FK to refresh_token_families, nullable)
- rotated_at (timestamp with timezone, nullable)

Index:
- ix_refresh_tokens_family_id

### 4. Check impersonation_sessions column renames
```sql
\d impersonation_sessions
```
Expected columns (renamed):
- actor_user_id (NOT admin_user_id)
- acting_as_user_id (NOT target_user_id)
- tenant_id (NOT target_tenant_id)
- refresh_token_family_id (new, nullable, FK to refresh_token_families)

### 5. Check audit_logs column renames
```sql
\d audit_logs
```
Expected columns (renamed):
- actor_user_id (NOT user_id)
- metadata (NOT changes)
- acting_as_user_id (new, nullable, FK to users)

Index:
- ix_audit_logs_acting_as_user_id

### 6. Check user_type migration
```sql
SELECT user_type, COUNT(*) FROM users GROUP BY user_type;
```
Expected: Should show 'platform' and 'hotel', NOT 'admin'

Check constraint:
```sql
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'ck_users_user_type';
```
Should show: `CHECK ((user_type)::text = ANY ((ARRAY['platform'::character varying, 'hotel'::character varying])::text[]))`

## Application Testing

### 1. Start application
```bash
docker compose up -d
```

### 2. Run seed data
```bash
docker compose exec backend python -c "
import asyncio
from app.core.database import async_session_maker
from app.core.seed import seed_database

async def main():
    async with async_session_maker() as session:
        await seed_database(session)

asyncio.run(main())
"
```

Expected: No errors, admin and hotel users created with username field

### 3. Test admin login
- Navigate to http://localhost:3000
- Login with admin@demo.com / Admin123!
- Should succeed

Verify in database:
```sql
SELECT id, email, username, user_type, first_name, last_name FROM users WHERE email = 'admin@demo.com';
```
Should show:
- username: 'admin'
- user_type: 'platform' (NOT 'admin')

### 4. Test hotel login
- Login with manager@demo.com / Manager123!
- Should succeed

### 5. Test impersonation (if accessible)
- Login as admin
- Start impersonation of hotel user
- Should work without errors

Verify impersonation session:
```sql
SELECT actor_user_id, acting_as_user_id, tenant_id, started_at, ended_at 
FROM impersonation_sessions 
ORDER BY started_at DESC LIMIT 1;
```
Columns should exist with correct names (not admin_user_id, target_user_id, etc.)

### 6. Test audit logs
Create some actions (login, create user, etc.) and verify:
```sql
SELECT actor_user_id, acting_as_user_id, action, metadata 
FROM audit_logs 
ORDER BY created_at DESC LIMIT 5;
```
Columns should exist with correct names (not user_id, changes)

### 7. Test user creation
Try creating a new admin user via API/UI
- Should require username field
- Username should be unique per tenant

## Rollback Testing (Optional but Recommended)

### Test downgrade
```bash
docker compose exec backend alembic downgrade 0014_report_export_async_queue
```

Verify:
- [ ] All 6 migrations rolled back successfully
- [ ] Schema matches pre-migration state
- [ ] Data preserved (except user_type reverted to 'admin')

### Test upgrade again
```bash
docker compose exec backend alembic upgrade head
```

Verify:
- [ ] All migrations reapplied successfully
- [ ] Schema matches expected state

## Issues to Watch For

### Potential Issues
1. **Username conflicts**: If multiple users have same email prefix in same tenant
   - Migration handles this by backfilling from email
   - New user creation might fail if username not provided

2. **Column renames**: Old code referencing old column names will fail
   - All code in this PR updated
   - Check for any custom queries or scripts

3. **User type checks**: Code checking for `user_type == 'admin'` will fail
   - All code in this PR updated to use 'platform'

4. **Foreign key constraints**: New FKs might cause issues with orphaned data
   - family_id is nullable, shouldn't cause issues
   - All FKs have proper ondelete actions

## Sign-off

- [ ] All migrations completed successfully
- [ ] Schema verification passed
- [ ] Application starts without errors
- [ ] Seed data works
- [ ] Login works for both admin and hotel users
- [ ] Impersonation works (if tested)
- [ ] Audit logs work
- [ ] User creation works with new schema
- [ ] No errors in application logs
- [ ] No errors in database logs

Date: ________________
Tested by: ________________
Environment: ________________
Database version: ________________
