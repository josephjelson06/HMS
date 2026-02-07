from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.tenant import Tenant
from app.models.user import User


ADMIN_PERMISSION_SEEDS = [
    ("admin:*:*", "Admin Wildcard", "All admin permissions", "*", "*"),
    ("admin:dashboard:read", "View Dashboard", "Read admin dashboard", "dashboard", "read"),
    ("admin:roles:read", "View Roles", "Read admin roles", "roles", "read"),
    ("admin:roles:create", "Create Roles", "Create admin roles", "roles", "create"),
    ("admin:roles:update", "Update Roles", "Update admin roles", "roles", "update"),
    ("admin:roles:delete", "Delete Roles", "Delete admin roles", "roles", "delete"),
    ("admin:users:read", "View Admin Users", "Read admin users", "users", "read"),
    ("admin:users:create", "Create Admin Users", "Create admin users", "users", "create"),
    ("admin:users:update", "Update Admin Users", "Update admin users", "users", "update"),
    ("admin:users:delete", "Delete Admin Users", "Delete admin users", "users", "delete"),
    ("admin:hotels:read", "View Hotels", "Read hotel registry", "hotels", "read"),
    ("admin:hotels:create", "Create Hotels", "Create hotel tenants", "hotels", "create"),
    ("admin:hotels:update", "Update Hotels", "Update hotel tenants", "hotels", "update"),
    ("admin:hotels:delete", "Delete Hotels", "Delete hotel tenants", "hotels", "delete"),
    ("admin:plans:read", "View Plans", "Read plans", "plans", "read"),
    ("admin:plans:create", "Create Plans", "Create plans", "plans", "create"),
    ("admin:plans:update", "Update Plans", "Update plans", "plans", "update"),
    ("admin:plans:delete", "Delete Plans", "Delete plans", "plans", "delete"),
    ("admin:subscriptions:read", "View Subscriptions", "Read subscriptions", "subscriptions", "read"),
    ("admin:subscriptions:create", "Create Subscriptions", "Create subscriptions", "subscriptions", "create"),
    ("admin:subscriptions:update", "Update Subscriptions", "Update subscriptions", "subscriptions", "update"),
    ("admin:subscriptions:delete", "Delete Subscriptions", "Delete subscriptions", "subscriptions", "delete"),
    ("admin:invoices:read", "View Invoices", "Read invoices", "invoices", "read"),
    ("admin:invoices:create", "Create Invoices", "Create invoices", "invoices", "create"),
    ("admin:invoices:update", "Update Invoices", "Update invoices", "invoices", "update"),
    ("admin:invoices:delete", "Delete Invoices", "Delete invoices", "invoices", "delete"),
    ("admin:reports:read", "View Reports", "Read admin reports", "reports", "read"),
    ("admin:reports:export", "Export Reports", "Export admin reports", "reports", "export"),
    ("admin:kiosks:read", "View Kiosks", "Read kiosk fleet", "kiosks", "read"),
    ("admin:kiosks:create", "Create Kiosks", "Create kiosks", "kiosks", "create"),
    ("admin:kiosks:update", "Update Kiosks", "Update kiosks", "kiosks", "update"),
    ("admin:kiosks:delete", "Delete Kiosks", "Delete kiosks", "kiosks", "delete"),
    ("admin:helpdesk:read", "View Helpdesk", "Read helpdesk tickets", "helpdesk", "read"),
    ("admin:helpdesk:create", "Create Helpdesk", "Create helpdesk tickets", "helpdesk", "create"),
    ("admin:helpdesk:update", "Update Helpdesk", "Update helpdesk tickets", "helpdesk", "update"),
    ("admin:helpdesk:delete", "Delete Helpdesk", "Delete helpdesk tickets", "helpdesk", "delete"),
    ("admin:profile:read", "View Profile", "Read admin profile", "profile", "read"),
    ("admin:profile:update", "Update Profile", "Update admin profile", "profile", "update"),
    ("admin:settings:read", "View Settings", "Read platform settings", "settings", "read"),
    ("admin:settings:create", "Create Settings", "Create platform settings", "settings", "create"),
    ("admin:settings:update", "Update Settings", "Update platform settings", "settings", "update"),
    ("admin:settings:delete", "Delete Settings", "Delete platform settings", "settings", "delete"),
    ("admin:impersonation:start", "Start Impersonation", "Start hotel impersonation sessions", "impersonation", "start"),
    ("admin:impersonation:stop", "Stop Impersonation", "Stop hotel impersonation sessions", "impersonation", "stop"),
    ("admin:audit:read", "View Audit Logs", "Read audit logs", "audit", "read"),
]

HOTEL_PERMISSION_SEEDS = [
    ("hotel:*:*", "Hotel Wildcard", "All hotel permissions", "*", "*"),
    ("hotel:dashboard:read", "View Dashboard", "Read hotel dashboard", "dashboard", "read"),
    ("hotel:guests:read", "View Guests", "Read guest registry", "guests", "read"),
    ("hotel:guests:create", "Create Guests", "Create guest entries", "guests", "create"),
    ("hotel:guests:update", "Update Guests", "Update guest entries", "guests", "update"),
    ("hotel:guests:delete", "Delete Guests", "Delete guest entries", "guests", "delete"),
    ("hotel:rooms:read", "View Rooms", "Read room management", "rooms", "read"),
    ("hotel:rooms:create", "Create Rooms", "Create rooms", "rooms", "create"),
    ("hotel:rooms:update", "Update Rooms", "Update rooms", "rooms", "update"),
    ("hotel:rooms:delete", "Delete Rooms", "Delete rooms", "rooms", "delete"),
    ("hotel:incidents:read", "View Incidents", "Read incident records", "incidents", "read"),
    ("hotel:incidents:create", "Create Incidents", "Create incident records", "incidents", "create"),
    ("hotel:incidents:update", "Update Incidents", "Update incident records", "incidents", "update"),
    ("hotel:incidents:delete", "Delete Incidents", "Delete incident records", "incidents", "delete"),
    ("hotel:users:read", "View Users", "Read hotel users", "users", "read"),
    ("hotel:users:create", "Create Users", "Create hotel users", "users", "create"),
    ("hotel:users:update", "Update Users", "Update hotel users", "users", "update"),
    ("hotel:users:delete", "Delete Users", "Delete hotel users", "users", "delete"),
    ("hotel:roles:read", "View Roles", "Read hotel roles", "roles", "read"),
    ("hotel:roles:create", "Create Roles", "Create hotel roles", "roles", "create"),
    ("hotel:roles:update", "Update Roles", "Update hotel roles", "roles", "update"),
    ("hotel:roles:delete", "Delete Roles", "Delete hotel roles", "roles", "delete"),
    ("hotel:kiosks:read", "View Kiosks", "Read hotel kiosks", "kiosks", "read"),
    ("hotel:kiosks:create", "Create Kiosks", "Create hotel kiosks", "kiosks", "create"),
    ("hotel:kiosks:update", "Update Kiosks", "Update hotel kiosks", "kiosks", "update"),
    ("hotel:kiosks:delete", "Delete Kiosks", "Delete hotel kiosks", "kiosks", "delete"),
    ("hotel:billing:read", "View Billing", "Read subscription & billing", "billing", "read"),
    ("hotel:support:read", "View Helpdesk", "Read helpdesk tickets", "support", "read"),
    ("hotel:support:create", "Create Helpdesk", "Create helpdesk tickets", "support", "create"),
    ("hotel:audit:read", "View Audit Logs", "Read hotel audit logs", "audit", "read"),
    ("hotel:reports:read", "View Reports", "Read hotel reports", "reports", "read"),
    ("hotel:reports:export", "Export Reports", "Export hotel reports", "reports", "export"),
    ("hotel:profile:read", "View Profile", "Read hotel profile", "profile", "read"),
    ("hotel:profile:update", "Update Profile", "Update hotel profile", "profile", "update"),
    ("hotel:settings:read", "View Settings", "Read hotel settings", "settings", "read"),
    ("hotel:settings:create", "Create Settings", "Create hotel settings", "settings", "create"),
    ("hotel:settings:update", "Update Settings", "Update hotel settings", "settings", "update"),
    ("hotel:settings:delete", "Delete Settings", "Delete hotel settings", "settings", "delete"),
]


async def ensure_permission(
    session: AsyncSession,
    code: str,
    name: str,
    description: str,
    scope: str,
    resource: str,
    action: str,
) -> Permission:
    existing = await session.scalar(select(Permission).where(Permission.code == code))
    if existing:
        return existing

    permission = Permission(
        code=code,
        name=name,
        description=description,
        scope=scope,
        resource=resource,
        action=action,
    )
    session.add(permission)
    await session.flush()
    return permission


async def ensure_role(
    session: AsyncSession,
    name: str,
    display_name: str,
    description: str,
    role_type: str,
    is_system: bool,
    tenant_id=None,
) -> Role:
    existing = await session.scalar(
        select(Role).where(
            Role.name == name, Role.role_type == role_type, Role.tenant_id == tenant_id
        )
    )
    if existing:
        return existing

    role = Role(
        name=name,
        display_name=display_name,
        description=description,
        role_type=role_type,
        is_system=is_system,
        tenant_id=tenant_id,
    )
    session.add(role)
    await session.flush()
    return role


async def ensure_role_permission(
    session: AsyncSession, role_id, permission_id
) -> None:
    existing = await session.scalar(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    if existing:
        return

    session.add(RolePermission(role_id=role_id, permission_id=permission_id))
    await session.flush()


async def ensure_user_role(session: AsyncSession, user_id, role_id) -> None:
    existing = await session.scalar(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    if existing:
        return
    session.add(UserRole(user_id=user_id, role_id=role_id))
    await session.flush()


async def seed_initial_data(session: AsyncSession) -> None:
    admin_permissions = []
    for code, name, description, resource, action in ADMIN_PERMISSION_SEEDS:
        admin_permissions.append(
            await ensure_permission(session, code, name, description, "admin", resource, action)
        )

    hotel_permissions = []
    for code, name, description, resource, action in HOTEL_PERMISSION_SEEDS:
        hotel_permissions.append(
            await ensure_permission(session, code, name, description, "hotel", resource, action)
        )

    admin_role = await ensure_role(
        session,
        name="SuperAdmin",
        display_name="Super Admin",
        description="Platform super admin",
        role_type="admin",
        is_system=True,
        tenant_id=None,
    )
    hotel_role = await ensure_role(
        session,
        name="HotelManager",
        display_name="Hotel Manager",
        description="Hotel manager role",
        role_type="hotel",
        is_system=True,
        tenant_id=None,
    )

    admin_wildcard = next((perm for perm in admin_permissions if perm.code == "admin:*:*"), None)
    hotel_wildcard = next((perm for perm in hotel_permissions if perm.code == "hotel:*:*"), None)
    if admin_wildcard:
        await ensure_role_permission(session, admin_role.id, admin_wildcard.id)
    if hotel_wildcard:
        await ensure_role_permission(session, hotel_role.id, hotel_wildcard.id)

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == "demo-hotel"))
    if not tenant:
        tenant = Tenant(name="Demo Hotel", slug="demo-hotel")
        session.add(tenant)
        await session.flush()

    admin_user = await session.scalar(select(User).where(User.email == settings.admin_seed_email))
    if not admin_user:
        admin_user = User(
            email=settings.admin_seed_email,
            username="admin",
            password_hash=hash_password(settings.admin_seed_password),
            first_name="Admin",
            last_name="User",
            user_type="platform",
            tenant_id=None,
            is_active=True,
        )
        session.add(admin_user)
        await session.flush()

    hotel_user = await session.scalar(select(User).where(User.email == settings.hotel_seed_email))
    if not hotel_user:
        hotel_user = User(
            email=settings.hotel_seed_email,
            username="manager",
            password_hash=hash_password(settings.hotel_seed_password),
            first_name="Hotel",
            last_name="Manager",
            user_type="hotel",
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(hotel_user)
        await session.flush()

    await ensure_user_role(session, admin_user.id, admin_role.id)
    await ensure_user_role(session, hotel_user.id, hotel_role.id)

    await session.commit()

