You are a Senior Software Architect and Backend–Frontend System Designer.

Your task is to design and guide the implementation of a **production-grade Hotel Management System (HMS)** with **Role-Based Access Control (RBAC)** and **strict Multi-Tenancy isolation**.

This is a real SaaS system, not a tutorial project.

--------------------------------------------------
SYSTEM OVERVIEW
--------------------------------------------------

The HMS consists of **two panels sharing a single authentication system**:

1. Admin Panel (Platform Owner)
2. Hotel Panel (Tenant / Hotel Users)

Authentication:
- Single login page
- Email + Password
- Same authentication flow for both panels
- Post-login access is determined by:
  - User type (Admin or Hotel user)
  - Role
  - Tenant context

--------------------------------------------------
ROLES & RBAC
--------------------------------------------------

### Admin Roles (Platform-level)
Managed ONLY from Admin Panel:
- SuperAdmin (master role)
- Finance
- Operations
- Support
- System must support adding more admin roles in the future

### Hotel Roles (Tenant-level)
Managed ONLY from Hotel Panel:
- Hotel Manager (master role)
- House Keeping
- Hotel Finance
- Front Desk
- Hotel Maintenance
- System must support adding more hotel roles in the future

RBAC Design Requirements:
- Permission-based RBAC (no hard-coded role checks)
- Roles → Permissions → Actions
- Support:
  - Page-level permissions (navigation & UI visibility)
  - Action-level permissions (create, update, delete, export, etc.)
- Clear separation between Admin permissions and Hotel permissions

--------------------------------------------------
MULTI-TENANCY MODEL
--------------------------------------------------

- Multi-tenant SaaS
- **Single PostgreSQL database**
- **Shared tables with mandatory `tenant_id`**
- Every tenant-owned table MUST include `tenant_id`
- Tenant isolation enforced at:
  - API layer
  - Service layer
  - Query / repository layer

Admin users:
- Do not belong to a tenant by default
- Can access tenant data **only via explicit impersonation**

--------------------------------------------------
ADMIN IMPERSONATION
--------------------------------------------------

Admins can impersonate Hotel users via:
- “Login as Hotel Manager / Hotel Admin”

Impersonation rules:
- Explicit action (never silent)
- Clearly indicated in UI
- Logged in audit logs
- During impersonation:
  - Admin permissions are suspended
  - Only hotel role permissions apply
- Impersonation context is carried in auth tokens

--------------------------------------------------
USER MODEL CONSTRAINTS (V1)
--------------------------------------------------

For initial version:
- One user → one role → one hotel
- Admin users are admin-only (no hotel membership)
- Schema should be future-proof for many-to-many expansion

--------------------------------------------------
MODULES / PAGES
--------------------------------------------------

### Hotel Panel Modules
- Dashboard
- Guest Registry
- Room Management
- Incidents Record
- Users Management (Hotel Panel only)
- Roles Management (Hotel Panel only)
- Kiosk Settings
- Subscription & Billing
- Help & Support
- Audit Logs (Hotel Panel only)
- Reports (Hotel Panel only)
- My Profile
- Settings

### Admin Panel Modules
- Dashboard
- Hotel Registry
- Kiosk Fleet
- Plans
- Subscriptions
- Invoices
- Reports (Admin Panel only)
- Users Management (Admin Panel only)
- Roles Management (Admin Panel only)
- Audit Logs (Admin Panel only)
- HelpDesk
- My Profile
- Settings

--------------------------------------------------
AUDIT LOGGING
--------------------------------------------------

Audit logs must capture:
- Authentication events
- Impersonation events
- Data mutations (create/update/delete)
- Read access (designed but feature-flagged for later enablement)

Audit logs must be:
- Immutable
- Tenant-aware
- Queryable for reports

--------------------------------------------------
REPORTS
--------------------------------------------------

Reports system requirements:
- Card-based report previews
- Clicking a card opens a detailed report page
- Filters:
  - Date range
  - Entity-specific filters
- Export formats:
  - CSV
  - PDF
  - Excel

Execution strategy:
- Sync for small previews
- Async background jobs for exports
- File storage via abstraction layer:
  - Local storage for now
  - S3-compatible storage later without refactor

--------------------------------------------------
KIOSK (FUTURE MODULE)
--------------------------------------------------

- AI-based self-registration devices
- Not implemented now
- Design only:
  - Kiosk entity
  - Token-based authentication
  - Ownership mapping to hotel

--------------------------------------------------
TECH STACK (FIXED)
--------------------------------------------------

Frontend:
- Next.js (App Router)
- TypeScript
- Modular, reusable component architecture

Backend:
- FastAPI
- Clean architecture
- Dependency Injection
- Feature-based modules

Database:
- PostgreSQL
- PgAdmin
- Fully Dockerized

--------------------------------------------------
UI / UX REQUIREMENTS
--------------------------------------------------

- Reusable components:
  - Sidebar
  - Navbar
  - Cards
  - Tables
  - Pagination
  - Sorting
  - Filtering
  - Searching
- Card-first design for most data
- Tables primarily for:
  - Audit logs
  - Large exports
- Glassmorphism design
- Light / Dark mode
- Mobile responsive

--------------------------------------------------
DESIGN OBJECTIVES
--------------------------------------------------

- Build **module by module**
- Apply:
  - SOLID
  - DRY
  - KISS
  - Low coupling, high cohesion
  - Separation of concerns
- Production-ready code
- Dev-environment ready
- Minimal refactor needed for production

--------------------------------------------------
EXPECTED OUTPUT FORMAT
--------------------------------------------------

Respond in the following order:

1. High-Level System Architecture
2. Multi-Tenancy Enforcement Strategy
3. RBAC & Permission Model Design
4. Authentication & Authorization Flow
5. Database Schema (core + RBAC + tenancy)
6. Backend Folder Structure (FastAPI)
7. Frontend Folder Structure (Next.js App Router)
8. Module-wise Data Flow (examples)
9. Impersonation Flow
10. Reports & Audit Logs Design
11. Development Roadmap (Phase-wise)

Use diagrams (ASCII if needed), tables, and practical explanations.
Avoid generic theory.
Focus on **implementable architecture and clean design**.
