import uuid


class TenantContextMissingError(RuntimeError):
    pass


class BaseService:
    def __init__(self, tenant_id: uuid.UUID | None = None) -> None:
        self.tenant_id = tenant_id

    def ensure_tenant_context(self) -> uuid.UUID:
        if not self.tenant_id:
            raise TenantContextMissingError("Tenant context missing")
        return self.tenant_id
