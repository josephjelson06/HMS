from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.seed import seed_initial_data
from app.middleware.auth import JwtPayloadMiddleware
from app.middleware.csrf import CsrfMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.modules.tenant.middleware import TenantContextMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.admin.dashboard.router import router as admin_dashboard_router
from app.modules.admin.hotels.router import router as admin_hotels_router
from app.modules.admin.users.router import router as admin_users_router
from app.modules.admin.roles.router import router as admin_roles_router
from app.modules.admin.audit.router import router as admin_audit_router
from app.modules.admin.plans.router import router as admin_plans_router
from app.modules.admin.subscriptions.router import router as admin_subscriptions_router
from app.modules.admin.invoices.router import router as admin_invoices_router
from app.modules.admin.reports.router import router as admin_reports_router
from app.modules.admin.kiosks.router import router as admin_kiosks_router
from app.modules.admin.helpdesk.router import router as admin_helpdesk_router
from app.modules.admin.profile.router import router as admin_profile_router
from app.modules.admin.settings.router import router as admin_settings_router
from app.modules.hotel.guests.router import router as hotel_guests_router
from app.modules.hotel.dashboard.router import router as hotel_dashboard_router
from app.modules.hotel.rooms.router import router as hotel_rooms_router
from app.modules.hotel.incidents.router import router as hotel_incidents_router
from app.modules.hotel.users.router import router as hotel_users_router
from app.modules.hotel.roles.router import router as hotel_roles_router
from app.modules.hotel.kiosk_settings.router import router as hotel_kiosk_settings_router
from app.modules.hotel.billing.router import router as hotel_billing_router
from app.modules.hotel.helpdesk.router import router as hotel_helpdesk_router
from app.modules.hotel.audit.router import router as hotel_audit_router
from app.modules.hotel.reports.router import router as hotel_reports_router
from app.modules.hotel.profile.router import router as hotel_profile_router
from app.modules.hotel.settings.router import router as hotel_settings_router
from app.workers.report_exports import start_report_export_worker, stop_report_export_worker


def create_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # Startup: validate configuration first
        settings.validate_startup_guards()

        # Seed data (existing behavior)
        if settings.seed_data:
            async with AsyncSessionLocal() as session:
                await seed_initial_data(session)

        # Start background workers (existing behavior)
        start_report_export_worker()

        yield

        # Shutdown: stop background workers (existing behavior)
        await stop_report_export_worker()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # Must be added before other middlewares so it also wraps early returns.
    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(JwtPayloadMiddleware)
    app.add_middleware(CsrfMiddleware)

    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(admin_dashboard_router, prefix="/api/admin/dashboard", tags=["admin-dashboard"])
    app.include_router(admin_hotels_router, prefix="/api/admin/hotels", tags=["admin-hotels"])
    app.include_router(admin_users_router, prefix="/api/admin/users", tags=["admin-users"])
    app.include_router(admin_roles_router, prefix="/api/admin/roles", tags=["admin-roles"])
    app.include_router(admin_audit_router, prefix="/api/admin/audit", tags=["admin-audit"])
    app.include_router(admin_plans_router, prefix="/api/admin/plans", tags=["admin-plans"])
    app.include_router(admin_subscriptions_router, prefix="/api/admin/subscriptions", tags=["admin-subscriptions"])
    app.include_router(admin_invoices_router, prefix="/api/admin/invoices", tags=["admin-invoices"])
    app.include_router(admin_reports_router, prefix="/api/admin/reports", tags=["admin-reports"])
    app.include_router(admin_kiosks_router, prefix="/api/admin/kiosks", tags=["admin-kiosks"])
    app.include_router(admin_helpdesk_router, prefix="/api/admin/helpdesk", tags=["admin-helpdesk"])
    app.include_router(admin_profile_router, prefix="/api/admin/profile", tags=["admin-profile"])
    app.include_router(admin_settings_router, prefix="/api/admin/settings", tags=["admin-settings"])
    app.include_router(hotel_dashboard_router, prefix="/api/hotel/dashboard", tags=["hotel-dashboard"])
    app.include_router(hotel_guests_router, prefix="/api/hotel/guests", tags=["hotel-guests"])
    app.include_router(hotel_rooms_router, prefix="/api/hotel/rooms", tags=["hotel-rooms"])
    app.include_router(hotel_incidents_router, prefix="/api/hotel/incidents", tags=["hotel-incidents"])
    app.include_router(hotel_users_router, prefix="/api/hotel/users", tags=["hotel-users"])
    app.include_router(hotel_roles_router, prefix="/api/hotel/roles", tags=["hotel-roles"])
    app.include_router(hotel_kiosk_settings_router, prefix="/api/hotel/kiosks", tags=["hotel-kiosks"])
    app.include_router(hotel_billing_router, prefix="/api/hotel/billing", tags=["hotel-billing"])
    app.include_router(hotel_helpdesk_router, prefix="/api/hotel/helpdesk", tags=["hotel-helpdesk"])
    app.include_router(hotel_audit_router, prefix="/api/hotel/audit", tags=["hotel-audit"])
    app.include_router(hotel_reports_router, prefix="/api/hotel/reports", tags=["hotel-reports"])
    app.include_router(hotel_profile_router, prefix="/api/hotel/profile", tags=["hotel-profile"])
    app.include_router(hotel_settings_router, prefix="/api/hotel/settings", tags=["hotel-settings"])

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
