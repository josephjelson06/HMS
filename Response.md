I'll design a production-grade Hotel Management System with strict multi-tenancy and RBAC. Let me break this down into implementable architecture components.
1. High-Level System Architecture
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
├─────────────────────────┬───────────────────────────────────────┤
│      Admin Panel        │           Hotel Panel                  │
│   /admin/* routes       │        /hotel/* routes                │
└────────────┬────────────┴──────────────┬────────────────────────┘
             │                           │
             └──────────┬────────────────┘
                        │ HTTPS/JWT
┌───────────────────────▼─────────────────────────────────────────┐
│                    API GATEWAY / AUTH MIDDLEWARE                 │
│                  (JWT Validation, Tenant Context)                │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │Auth Service  │  │Admin Service │  │Hotel Service │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │RBAC Service  │  │Audit Service │  │Report Service│        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
├───────────────────────────────────────────────────────────────┤
│                    REPOSITORY LAYER                              │
│              (Tenant Isolation Enforcement)                      │
├───────────────────────────────────────────────────────────────┤
│                  DATABASE ABSTRACTION                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│                  (Single DB, Shared Tables)                      │
└─────────────────────────────────────────────────────────────────┘

2. Multi-Tenancy Enforcement Strategy
Three-Layer Defense Strategy:
pythonDownloadCopy code# Layer 1: API Middleware
class TenantContextMiddleware:
    """Extracts and validates tenant_id from JWT token"""
    async def __call__(self, request: Request, call_next):
        token_data = decode_jwt(request.headers.get("Authorization"))
        request.state.tenant_id = token_data.get("tenant_id")
        request.state.user_type = token_data.get("user_type")
        request.state.impersonation = token_data.get("impersonation")
        return await call_next(request)

# Layer 2: Service Layer
class BaseService:
    def __init__(self, tenant_id: Optional[UUID] = None):
        self.tenant_id = tenant_id
    
    def ensure_tenant_context(self):
        if not self.tenant_id and self.requires_tenant:
            raise TenantContextMissingError()

# Layer 3: Repository Layer
class TenantAwareRepository:
    def apply_tenant_filter(self, query: Query, tenant_id: UUID) -> Query:
        """Automatically inject tenant_id into all queries"""
        return query.filter(Model.tenant_id == tenant_id)
Tenant Isolation Rules:
User TypeDefault AccessTenant Data AccessMethodAdminPlatform data onlyVia impersonationExplicit tenant_id injectionHotel UserOwn tenant onlyAutomaticImplicit from token
3. RBAC & Permission Model Design
Permission Structure:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     Role     │────▶│ RolePermission│◀────│  Permission  │
└──────────────┘ 1:N └──────────────┘ N:1 └──────────────┘
       │                                          │
       ▼                                          ▼
┌──────────────┐                        ┌──────────────┐
│   UserRole   │                        │   Resource   │
└──────────────┘                        └──────────────┘
       │                                          │
       ▼                                          ▼
┌──────────────┐                        ┌──────────────┐
│     User     │                        │    Action    │
└──────────────┘                        └──────────────┘

Permission Naming Convention:
{scope}:{resource}:{action}

Examples:
- admin:hotels:read
- admin:hotels:impersonate
- hotel:guests:create
- hotel:rooms:update
- hotel:reports:export

Permission Check Implementation:
pythonDownloadCopy codeclass PermissionChecker:
    @staticmethod
    def has_permission(user_permissions: List[str], required: str) -> bool:
        # Direct match
        if required in user_permissions:
            return True
        
        # Wildcard support
        parts = required.split(':')
        for i in range(len(parts)):
            wildcard = ':'.join(parts[:i+1] + ['*'])
            if wildcard in user_permissions:
                return True
        return False

# Usage in endpoint
@router.get("/hotels/{hotel_id}/guests")
@require_permission("hotel:guests:read")
async def list_guests(hotel_id: UUID, current_user: User = Depends(get_current_user)):
    # Endpoint logic
4. Authentication & Authorization Flow
Authentication Flow:
User Login
    │
    ▼
Validate Credentials
    │
    ├─── Admin User ─────┐
    │                    │
    ▼                    ▼
Hotel User          Generate JWT with:
    │               - user_id
    │               - user_type: "admin"
    │               - roles: ["SuperAdmin"]
    │               - tenant_id: null
    │
    ▼
Generate JWT with:
- user_id
- user_type: "hotel"
- roles: ["Hotel Manager"]
- tenant_id: "uuid"
- hotel_id: "uuid"

Authorization Middleware:
pythonDownloadCopy codeclass AuthorizationMiddleware:
    async def __call__(self, request: Request, call_next):
        # 1. Extract JWT
        token = extract_token(request)
        
        # 2. Decode and validate
        payload = decode_jwt(token)
        
        # 3. Load user permissions
        permissions = await load_user_permissions(
            user_id=payload["user_id"],
            roles=payload["roles"],
            user_type=payload["user_type"]
        )
        
        # 4. Attach to request context
        request.state.user = {
            "id": payload["user_id"],
            "type": payload["user_type"],
            "tenant_id": payload.get("tenant_id"),
            "permissions": permissions,
            "impersonation": payload.get("impersonation")
        }
        
        return await call_next(request)
5. Database Schema (Core + RBAC + Tenancy)
Core Tables:
sqlDownloadCopy code-- Tenants (Hotels)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    user_type VARCHAR(20) NOT NULL, -- 'admin' or 'hotel'
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_tenant_for_hotel_user 
        CHECK (user_type != 'hotel' OR tenant_id IS NOT NULL)
);

-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    role_type VARCHAR(20) NOT NULL, -- 'admin' or 'hotel'
    is_system BOOLEAN DEFAULT false, -- Cannot be modified/deleted
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_role_per_context 
        UNIQUE(name, role_type, tenant_id)
);

-- Permissions
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'hotel:guests:create'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scope VARCHAR(20) NOT NULL, -- 'admin' or 'hotel'
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role-Permission Mapping
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

-- User-Role Assignment
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    UNIQUE(user_id, role_id)
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    impersonated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Impersonation Sessions
CREATE TABLE impersonation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    reason TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    ip_address INET
);
Hotel-Specific Tables (Examples):
sqlDownloadCopy code-- Guests
CREATE TABLE guests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    id_type VARCHAR(50),
    id_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_guests_tenant (tenant_id)
);

-- Rooms
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    floor INTEGER,
    room_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, room_number),
    INDEX idx_rooms_tenant (tenant_id)
);
6. Backend Folder Structure (FastAPI)
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── config.py                  # Settings and configuration
│   │
│   ├── core/                      # Core functionality
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection
│   │   ├── security.py            # JWT, password hashing
│   │   ├── dependencies.py        # Shared dependencies
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Authentication middleware
│   │   │   ├── tenant.py          # Tenant context middleware
│   │   │   └── audit.py           # Audit logging middleware
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pagination.py
│   │       └── filters.py
│   │
│   ├── modules/                   # Feature modules
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Auth endpoints
│   │   │   ├── service.py         # Auth business logic
│   │   │   ├── repository.py      # Auth data access
│   │   │   ├── schemas.py         # Pydantic models
│   │   │   └── dependencies.py    # Auth-specific deps
│   │   │
│   │   ├── rbac/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   ├── permissions.py     # Permission checker
│   │   │   └── decorators.py      # @require_permission
│   │   │
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── hotels/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   ├── impersonation/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   └── reports/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       └── generators.py
│   │   │
│   │   ├── hotel/
│   │   │   ├── __init__.py
│   │   │   ├── guests/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── schemas.py
│   │   │   ├── rooms/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   └── incidents/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       └── repository.py
│   │   │
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── schemas.py
│   │   │
│   │   └── reports/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── generators/
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── csv_generator.py
│   │       │   ├── pdf_generator.py
│   │       │   └── excel_generator.py
│   │       └── tasks.py           # Celery tasks for async
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                # Base model class
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── rbac.py
│   │   ├── audit.py
│   │   └── hotel/
│   │       ├── __init__.py
│   │       ├── guest.py
│   │       └── room.py
│   │
│   └── migrations/                # Alembic migrations
│       └── versions/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example

7. Frontend Folder Structure (Next.js App Router)
frontend/
├── app/
│   ├── (auth)/                    # Auth layout group
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   │
│   ├── admin/                     # Admin panel routes
│   │   ├── layout.tsx             # Admin layout with sidebar
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── hotels/
│   │   │   ├── page.tsx           # Hotels list
│   │   │   └── [id]/
│   │   │       ├── page.tsx       # Hotel details
│   │   │       └── impersonate/
│   │   │           └── page.tsx
│   │   ├── users/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── reports/
│   │       ├── page.tsx           # Reports cards
│   │       └── [reportId]/
│   │           └── page.tsx       # Report detail
│   │
│   ├── hotel/                     # Hotel panel routes
│   │   ├── layout.tsx             # Hotel layout with sidebar
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── guests/
│   │   │   ├── page.tsx
│   │   │   ├── new/
│   │   │   │   └── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── rooms/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── reports/
│   │       ├── page.tsx
│   │       └── [reportId]/
│   │           └── page.tsx
│   │
│   ├── api/                       # API route handlers (if needed)
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts
│   │
│   └── layout.tsx                 # Root layout
│
├── components/
│   ├── ui/                        # Reusable UI components
│   │   ├── card.tsx
│   │   ├── table/
│   │   │   ├── data-table.tsx
│   │   │   ├── pagination.tsx
│   │   │   └── filters.tsx
│   │   ├── forms/
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   └── date-picker.tsx
│   │   ├── modals/
│   │   │   ├── base-modal.tsx
│   │   │   └── confirm-modal.tsx
│   │   └── glassmorphism/
│   │       ├── glass-card.tsx
│   │       └── glass-panel.tsx
│   │
│   ├── layout/
│   │   ├── sidebar/
│   │   │   ├── sidebar.tsx
│   │   │   ├── sidebar-item.tsx
│   │   │   └── sidebar-context.tsx
│   │   ├── navbar/
│   │   │   ├── navbar.tsx
│   │   │   └── user-menu.tsx
│   │   └── breadcrumbs.tsx
│   │
│   ├── features/                  # Feature-specific components
│   │   ├── auth/
│   │   │   ├── login-form.tsx
│   │   │   └── permission-guard.tsx
│   │   ├── guests/
│   │   │   ├── guest-card.tsx
│   │   │   ├── guest-form.tsx
│   │   │   └── guest-list.tsx
│   │   └── reports/
│   │       ├── report-card.tsx
│   │       ├── report-filters.tsx
│   │       └── report-viewer.tsx
│   │
│   └── providers/
│       ├── auth-provider.tsx
│       ├── theme-provider.tsx
│       └── tenant-provider.tsx
│
├── lib/
│   ├── api/                       # API client
│   │   ├── client.ts              # Axios/Fetch wrapper
│   │   ├── auth.ts
│   │   ├── admin/
│   │   │   └── hotels.ts
│   │   └── hotel/
│   │       └── guests.ts
│   │
│   ├── hooks/                     # Custom hooks
│   │   ├── use-auth.ts
│   │   ├── use-permissions.ts
│   │   ├── use-tenant.ts
│   │   └── use-api.ts
│   │
│   ├── utils/
│   │   ├── permissions.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   │
│   └── types/                     # TypeScript types
│       ├── auth.ts
│       ├── tenant.ts
│       ├── user.ts
│       └── api.ts
│
├── styles/
│   ├── globals.css
│   └── themes/
│       ├── light.css
│       └── dark.css
│
├── public/
├── next.config.js
├── tailwind.config.js
└── tsconfig.json

8. Module-wise Data Flow (Examples)
Guest Registration Flow (Hotel Panel):
1. UI Component (guest-form.tsx)
   ↓
2. Form Validation (zod/yup)
   ↓
3. API Call (lib/api/hotel/guests.ts)
   POST /api/hotel/guests
   Headers: { Authorization: "Bearer JWT" }
   ↓
4. FastAPI Router (modules/hotel/guests/router.py)
   @require_permission("hotel:guests:create")
   ↓
5. Service Layer (modules/hotel/guests/service.py)
   - Business validation
   - Tenant context enforcement
   ↓
6. Repository Layer (modules/hotel/guests/repository.py)
   - Auto-inject tenant_id
   - Database transaction
   ↓
7. Audit Log (modules/audit/service.py)
   - Record creation event
   ↓
8. Response → UI Update

Admin Hotel List Flow:
1. Admin Dashboard (app/admin/hotels/page.tsx)
   ↓
2. API Call (lib/api/admin/hotels.ts)
   GET /api/admin/hotels?page=1&limit=20
   ↓
3. FastAPI Router (modules/admin/hotels/router.py)
   @require_permission("admin:hotels:read")
   ↓
4. Service Layer
   - No tenant filter (admin sees all)
   - Pagination applied
   ↓
5. Repository Layer
   - Query all tenants
   - Include subscription status
   ↓
6. Response with pagination metadata

9. Impersonation Flow
Impersonation Sequence:
Admin User → Clicks "Login as Hotel Manager"
    ↓
POST /api/admin/impersonation/start
{
    "target_tenant_id": "uuid",
    "reason": "Support ticket #1234"
}
    ↓
Backend validates:
- Admin has permission: "admin:hotels:impersonate"
- Target tenant exists
- Creates impersonation session
    ↓
Generate new JWT with:
{
    "user_id": "admin_uuid",
    "user_type": "admin",
    "impersonation": {
        "active": true,
        "tenant_id": "target_uuid",
        "tenant_name": "Hotel XYZ",
        "session_id": "session_uuid",
        "started_at": "2025-02-05T10:00:00Z"
    }
}
    ↓
Frontend receives new token
- Stores in context
- Redirects to /hotel/dashboard
- Shows impersonation banner
    ↓
All subsequent API calls:
- Include impersonation context
- Apply hotel permissions only
- Log with impersonation flag
    ↓
End Impersonation:
POST /api/admin/impersonation/end
- Closes session
- Returns regular admin JWT
- Redirects to /admin/dashboard

UI Indicators During Impersonation:
tsxDownloadCopy code// Impersonation Banner Component
function ImpersonationBanner() {
    const { impersonation, endImpersonation } = useAuth();
    
    if (!impersonation?.active) return null;
    
    return (
        <div className="bg-orange-500 text-white p-2 text-center">
            <span>Impersonating: {impersonation.tenant_name}</span>
            <button onClick={endImpersonation} className="ml-4">
                End Session
            </button>
        </div>
    );
}
10. Reports & Audit Logs Design
Reports Architecture:
Report Generation Pipeline:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Request   │────▶│  Validator  │────▶│  Generator  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                           ┌───────────────────┼───────────────────┐
                           ▼                   ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                    │     CSV     │    │     PDF     │    │    Excel    │
                    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           └───────────────────┼───────────────────┘
                                               ▼
                                        ┌─────────────┐
                                        │   Storage   │
                                        └─────────────┘

Report Service Implementation:
pythonDownloadCopy codeclass ReportService:
    def __init__(self, tenant_id: Optional[UUID] = None):
        self.tenant_id = tenant_id
        self.generators = {
            'csv': CSVGenerator(),
            'pdf': PDFGenerator(),
            'excel': ExcelGenerator()
        }
    
    async def generate_report(
        self,
        report_type: str,
        format: str,
        filters: dict,
        async_mode: bool = False
    ):
        # Small reports: Synchronous
        if not async_mode:
            data = await self.fetch_report_data(report_type, filters)
            return self.generators[format].generate(data)
        
        # Large reports: Background job
        task_id = str(uuid.uuid4())
        background_tasks.add_task(
            self._generate_async,
            task_id,
            report_type,
            format,
            filters
        )
        return {"task_id": task_id, "status": "processing"}
Audit Log Implementation:
pythonDownloadCopy codeclass AuditLogger:
    @staticmethod
    async def log(
        action: str,
        resource_type: str,
        resource_id: UUID,
        user_id: UUID,
        tenant_id: Optional[UUID],
        changes: Optional[dict] = None,
        impersonated_by: Optional[UUID] = None
    ):
        await AuditRepository.create({
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "changes": changes,
            "impersonated_by": impersonated_by,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent")
        })

# Decorator for automatic audit logging
def audit_action(action: str, resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await AuditLogger.log(
                action=action,
                resource_type=resource_type,
                resource_id=result.get("id"),
                # ... other params
            )
            return result
        return wrapper
    return decorator
11. Development Roadmap (Phase-wise)
Phase 1: Foundation (Weeks 1-2)

* Database setup with Docker
* Core tables (tenants, users, roles, permissions)
* Authentication service (login, JWT)
* Basic RBAC implementation
* Tenant context middleware
* Base repository pattern

Phase 2: Admin Panel Core (Weeks 3-4)

* Admin authentication flow
* Hotel registry (CRUD)
* Admin user management
* Admin role management
* Basic audit logging
* Impersonation framework

Phase 3: Hotel Panel Core (Weeks 5-6)

* Hotel authentication flow
* Guest registry
* Room management
* Hotel user management
* Hotel role management
* Tenant isolation verification

Phase 4: Advanced Features (Weeks 7-8)

* Incident management
* Reports framework
* Export functionality (CSV, PDF)
* Advanced audit logs with filters
* Dashboard analytics

Phase 5: Polish & Optimization (Weeks 9-10)

* UI/UX refinements
* Performance optimization
* Caching layer
* Error handling improvements
* Comprehensive testing
* Documentation

Phase 6: Production Readiness (Weeks 11-12)

* Security audit
* Load testing
* Monitoring setup
* CI/CD pipeline
* Deployment scripts
* Backup strategies

Module Implementation Priority:

1. 
Must Have (MVP):

Authentication
RBAC
Hotel Registry
Guest Management
Room Management
Basic Audit Logs


2. 
Should Have:

Impersonation
Reports
Incident Management
Advanced Filtering


3. 
Nice to Have:

Kiosk Preparation
Advanced Analytics
Email Notifications
Real-time Updates



This architecture provides a solid foundation for a production-grade HMS with clear separation of concerns, maintainability, and scalability in mind. Each component is designed to be testable and deployable independently while maintaining system integrity through well-defined interfaces.