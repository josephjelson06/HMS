from datetime import datetime, timezone
from uuid import uuid4

from app.modules.auth.service import AuthService


class _DummySession:
    def __init__(self):
        self.id = uuid4()
        self.tenant_id = uuid4()
        self.actor_user_id = uuid4()
        self.acting_as_user_id = uuid4()
        self.started_at = datetime.now(timezone.utc)


class _DummyTenant:
    def __init__(self, name: str):
        self.name = name


def test_build_impersonation_context_includes_canonical_and_legacy_keys():
    session = _DummySession()
    tenant = _DummyTenant("Demo Hotel")

    payload = AuthService._build_impersonation_context(session, tenant)

    assert payload["active"] is True
    assert payload["tenant_id"] == str(session.tenant_id)
    assert payload["tenant_name"] == "Demo Hotel"
    assert payload["session_id"] == str(session.id)

    # Canonical keys
    assert payload["actor_user_id"] == str(session.actor_user_id)
    assert payload["acting_as_user_id"] == str(session.acting_as_user_id)

    # Backward-compatible aliases
    assert payload["admin_user_id"] == str(session.actor_user_id)
    assert payload["target_user_id"] == str(session.acting_as_user_id)
