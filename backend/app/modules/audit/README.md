# Audit Logging System

This module provides zero-boilerplate audit logging using Python's `contextvars.ContextVar`. It allows any code in the request lifecycle to emit audit events via a single `audit_event_stub()` call, without passing the DB session or auth context through every function signature.

## Architecture

The audit logging system consists of three main components:

### 1. Context Management (`context.py`)

- **`AuditRuntimeContext`**: A dataclass that holds request-scoped state needed to emit audit log entries
- **`set_audit_runtime_context()`**: Sets the audit runtime context for the current request (called by middleware)
- **`get_audit_runtime_context()`**: Gets the audit runtime context for the current request
- **`clear_audit_runtime_context()`**: Clears the audit runtime context (called at end of request)

### 2. Audit Event Stub (`hooks.py`)

- **`audit_event_stub()`**: The primary audit API. Call this from anywhere in the request lifecycle to emit an audit log entry.

### 3. Service Layer (`service.py`)

- **`append_audit_log()`**: Inserts a single audit log row into the database
- **`list_audit_logs()`**: Queries audit logs with optional filters

## Usage

### Basic Usage

From anywhere in your application code (route handlers, services, utilities), simply call:

```python
from app.modules.audit.hooks import audit_event_stub

async def create_user(session, email: str, ...):
    # Create the user
    user = User(email=email, ...)
    session.add(user)
    await session.flush()
    
    # Emit audit event - context fields auto-populated!
    await audit_event_stub(
        session=session,  # Pass session explicitly
        action="user.created",
        metadata={"email": email},
        resource_type="user",
        resource_id=str(user.id),
    )
    
    return user
```

### Auto-Populated Fields

The following fields are automatically populated from the request context:
- `tenant_id` - From JWT token
- `actor_user_id` - From JWT token (the user performing the action)
- `acting_as_user_id` - From JWT token (if impersonating another user)
- `ip_address` - From request client
- `user_agent` - From request headers

You can override any of these by passing them explicitly to `audit_event_stub()`.

### Middleware Setup

The middleware (`backend/app/middleware/auth.py`) automatically sets up and clears the audit context for each request:

```python
class JwtPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract auth info from JWT
        token_payload = decode_access_token(token) if token else None
        
        # Set up audit context
        audit_ctx = AuditRuntimeContext(
            session=None,  # Session passed explicitly in routes
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            acting_as_user_id=acting_as_user_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        set_audit_runtime_context(audit_ctx)
        
        try:
            response = await call_next(request)
            return response
        finally:
            clear_audit_runtime_context()
```

### Field Name Mapping

The audit module uses AuthModule-style field names but maps them to HMS's current model:

| API Field Name     | Model Column Name  | Description                           |
|--------------------|--------------------|---------------------------------------|
| `actor_user_id`    | `user_id`          | The user performing the action        |
| `acting_as_user_id`| `impersonated_by`  | The admin user when impersonating     |
| `metadata`         | `changes`          | JSON object with audit metadata       |

This mapping allows the new audit API to work with the existing database schema while preparing for future migrations.

## Testing

The module includes comprehensive unit tests:

- `test_audit_context.py` - Tests for context management (ContextVar operations)
- `test_audit_hooks.py` - Tests for `audit_event_stub()` with various scenarios
- `test_audit_integration.py` - End-to-end integration tests

Run tests with:

```bash
cd backend
DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test" \
JWT_SECRET="test_secret_key_for_testing" \
python -m pytest tests/unit/test_audit*.py -v
```

## Benefits

1. **Zero Boilerplate**: No need to pass `session`, `request`, or `current_user` through every function
2. **Consistent Audit Entries**: All audit fields are automatically populated correctly
3. **No Crashes**: Silently skips when called outside request context (tests, CLI, background jobs)
4. **Thread-Safe**: Uses `ContextVar` for async-safe context isolation
5. **Impersonation Support**: Automatically tracks `acting_as_user_id` during impersonation
6. **Flexible**: Can override any auto-populated field when needed

## Future Enhancements

When PR 5's database migration is applied, the model will use the new column names directly:
- `user_id` → `actor_user_id`
- `impersonated_by` → `acting_as_user_id`  
- `changes` → `metadata`

At that point, the field name mapping in `service.py` can be removed.
