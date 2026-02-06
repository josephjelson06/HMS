import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TenantAwareRepository:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID | None = None) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def require_tenant(self) -> uuid.UUID:
        if not self.tenant_id:
            raise ValueError("Tenant context missing")
        return self.tenant_id

    def apply_tenant_filter(self, stmt, model):
        if self.tenant_id and hasattr(model, "tenant_id"):
            return stmt.where(model.tenant_id == self.tenant_id)
        return stmt
