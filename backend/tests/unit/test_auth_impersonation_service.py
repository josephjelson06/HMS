from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.modules.auth.service as auth_service_module
from app.modules.auth.service import AuthResult, AuthService


class _FakeSession:
    def __init__(self, tenants_by_id: dict):
        self._tenants_by_id = tenants_by_id
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def get(self, _model, key):
        return self._tenants_by_id.get(key)

    async def commit(self):
        self.committed = True


def _make_request():
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={"user-agent": "pytest"})


@pytest.mark.asyncio
async def test_start_impersonation_links_family_to_actor_parent(monkeypatch):
    admin_id = uuid4()
    target_id = uuid4()
    tenant_id = uuid4()
    parent_family_id = uuid4()
    impersonation_family_id = uuid4()

    admin_user = SimpleNamespace(
        id=admin_id,
        is_active=True,
        user_type="platform",
        tenant_id=tenant_id,
        email="admin@demo.com",
        first_name="Admin",
        last_name="User",
        must_reset_password=False,
    )
    target_user = SimpleNamespace(
        id=target_id,
        is_active=True,
        user_type="hotel",
        tenant_id=tenant_id,
        email="manager@demo.com",
        first_name="Hotel",
        last_name="Manager",
        must_reset_password=False,
    )
    tenant = SimpleNamespace(id=tenant_id, name="Demo Hotel", slug="demo-hotel")
    imp_session = SimpleNamespace(
        id=uuid4(),
        actor_user_id=admin_id,
        acting_as_user_id=target_id,
        tenant_id=tenant_id,
        started_at=datetime.now(timezone.utc),
        refresh_token_family_id=None,
    )

    class _UserRepo:
        async def get_by_id(self, user_id):
            if str(user_id) == str(admin_id):
                return admin_user
            if str(user_id) == str(target_id):
                return target_user
            return None

    class _PermRepo:
        async def get_role_names_for_user(self, _user_id):
            return ["hotel:manager"]

        async def get_permissions_for_user(self, _user_id):
            return ["hotel:dashboard:read"]

    class _TokenRepo:
        async def get_by_hash(self, _token_hash):
            return SimpleNamespace(user_id=admin_id, family_id=parent_family_id)

    class _ImpersonationRepo:
        async def get_active_for_actor(self, _actor_user_id):
            return None

        async def create(self, **_kwargs):
            return imp_session

        async def set_refresh_token_family_id(self, session, refresh_token_family_id):
            session.refresh_token_family_id = refresh_token_family_id

    captured = {}

    async def fake_issue_new_refresh_token_family(session, **kwargs):
        captured["parent_family_id"] = kwargs.get("parent_family_id")
        return SimpleNamespace(raw_token="impersonation-refresh-token", family_id=impersonation_family_id)

    async def fake_issue_auth_result(self, **kwargs):
        captured["impersonation_payload"] = kwargs.get("impersonation")
        return AuthResult(
            response=None,
            access_token="access-token",
            refresh_token=kwargs["refresh_token_override"],
            csrf_token="csrf-token",
        )

    monkeypatch.setattr(auth_service_module, "issue_new_refresh_token_family", fake_issue_new_refresh_token_family)
    monkeypatch.setattr(AuthService, "_issue_auth_result", fake_issue_auth_result)

    service = AuthService(_FakeSession({tenant_id: tenant}), _make_request())
    service.user_repo = _UserRepo()
    service.perm_repo = _PermRepo()
    service.token_repo = _TokenRepo()
    service.impersonation_repo = _ImpersonationRepo()

    result = await service.start_impersonation(
        admin_user_id=admin_id,
        tenant_id=tenant_id,
        target_user_id=target_id,
        reason="support",
        actor_refresh_token="actor-refresh-token",
    )

    assert captured["parent_family_id"] == parent_family_id
    assert imp_session.refresh_token_family_id == impersonation_family_id
    assert captured["impersonation_payload"]["actor_user_id"] == str(admin_id)
    assert captured["impersonation_payload"]["acting_as_user_id"] == str(target_id)
    assert result.refresh_token == "impersonation-refresh-token"


@pytest.mark.asyncio
async def test_stop_impersonation_revokes_linked_family(monkeypatch):
    admin_id = uuid4()
    target_id = uuid4()
    tenant_id = uuid4()
    session_id = uuid4()
    impersonation_family_id = uuid4()
    new_admin_family_id = uuid4()

    imp_session = SimpleNamespace(
        id=session_id,
        actor_user_id=admin_id,
        acting_as_user_id=target_id,
        tenant_id=tenant_id,
        refresh_token_family_id=impersonation_family_id,
        started_at=datetime.now(timezone.utc),
        ended_at=None,
    )
    admin_user = SimpleNamespace(
        id=admin_id,
        is_active=True,
        user_type="platform",
        tenant_id=tenant_id,
        email="admin@demo.com",
        first_name="Admin",
        last_name="User",
        must_reset_password=False,
    )

    class _UserRepo:
        async def get_by_id(self, user_id):
            if str(user_id) == str(admin_id):
                return admin_user
            return None

    class _PermRepo:
        async def get_role_names_for_user(self, _user_id):
            return ["platform:admin"]

        async def get_permissions_for_user(self, _user_id):
            return ["admin:dashboard:read"]

    class _ImpersonationRepo:
        async def get_active_by_id(self, session_uuid):
            if str(session_uuid) == str(session_id):
                return imp_session
            return None

        async def end(self, session):
            session.ended_at = datetime.now(timezone.utc)

    revoke_calls = {"by_family_id": 0, "by_token": 0}

    async def fake_revoke_refresh_token_family(_session, *, family_id, reason):
        assert family_id == impersonation_family_id
        assert reason == "impersonation_ended"
        revoke_calls["by_family_id"] += 1
        return 1

    async def fake_revoke_family_by_refresh_token(*_args, **_kwargs):
        revoke_calls["by_token"] += 1
        return None, 0

    async def fake_issue_new_refresh_token_family(_session, **_kwargs):
        return SimpleNamespace(raw_token="new-admin-refresh-token", family_id=new_admin_family_id)

    async def fake_issue_auth_result(self, **kwargs):
        return AuthResult(
            response=None,
            access_token="admin-access-token",
            refresh_token=kwargs["refresh_token_override"],
            csrf_token="csrf-token",
        )

    monkeypatch.setattr(auth_service_module, "revoke_refresh_token_family", fake_revoke_refresh_token_family)
    monkeypatch.setattr(auth_service_module, "revoke_family_by_refresh_token", fake_revoke_family_by_refresh_token)
    monkeypatch.setattr(auth_service_module, "issue_new_refresh_token_family", fake_issue_new_refresh_token_family)
    monkeypatch.setattr(AuthService, "_issue_auth_result", fake_issue_auth_result)

    service = AuthService(_FakeSession({}), _make_request())
    service.user_repo = _UserRepo()
    service.perm_repo = _PermRepo()
    service.impersonation_repo = _ImpersonationRepo()

    result = await service.stop_impersonation(
        acting_user_id=target_id,
        impersonation={
            "active": True,
            "session_id": str(session_id),
            "actor_user_id": str(admin_id),
            "acting_as_user_id": str(target_id),
        },
        current_refresh_token="current-refresh-token",
    )

    assert revoke_calls["by_family_id"] == 1
    assert revoke_calls["by_token"] == 0
    assert result.refresh_token == "new-admin-refresh-token"


@pytest.mark.asyncio
async def test_refresh_uses_family_linked_impersonation_lookup(monkeypatch):
    user_id = uuid4()
    tenant_id = uuid4()
    family_id = uuid4()
    actor_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=True,
        user_type="hotel",
        tenant_id=tenant_id,
        email="manager@demo.com",
        first_name="Hotel",
        last_name="Manager",
        must_reset_password=False,
    )
    imp_session = SimpleNamespace(
        id=uuid4(),
        actor_user_id=actor_id,
        acting_as_user_id=user_id,
        tenant_id=tenant_id,
        started_at=datetime.now(timezone.utc),
    )
    tenant = SimpleNamespace(id=tenant_id, name="Demo Hotel", slug="demo-hotel")
    stored_token = SimpleNamespace(
        user_id=user_id,
        family_id=family_id,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    class _TokenRepo:
        async def get_by_hash(self, _token_hash):
            return stored_token

    class _UserRepo:
        async def get_by_id(self, _user_id):
            return user

    class _PermRepo:
        async def get_role_names_for_user(self, _user_id):
            return ["hotel:manager"]

        async def get_permissions_for_user(self, _user_id):
            return ["hotel:dashboard:read"]

    class _ImpersonationRepo:
        async def find_active_impersonation_for_refresh_family(self, lookup_family_id):
            assert lookup_family_id == family_id
            return imp_session

    captured = {}

    async def fake_rotate_refresh_token(_session, **_kwargs):
        return SimpleNamespace(
            raw_token="rotated-refresh-token",
            family_id=family_id,
            token_id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def fake_issue_auth_result(self, **kwargs):
        captured["impersonation"] = kwargs.get("impersonation")
        return AuthResult(
            response=None,
            access_token="access-token",
            refresh_token=kwargs["refresh_token_override"],
            csrf_token="csrf-token",
        )

    monkeypatch.setattr(auth_service_module, "rotate_refresh_token", fake_rotate_refresh_token)
    monkeypatch.setattr(AuthService, "_issue_auth_result", fake_issue_auth_result)

    service = AuthService(_FakeSession({tenant_id: tenant}), _make_request())
    service.token_repo = _TokenRepo()
    service.user_repo = _UserRepo()
    service.perm_repo = _PermRepo()
    service.impersonation_repo = _ImpersonationRepo()

    result = await service.refresh("incoming-refresh-token")

    assert result.refresh_token == "rotated-refresh-token"
    assert captured["impersonation"]["actor_user_id"] == str(actor_id)
    assert captured["impersonation"]["acting_as_user_id"] == str(user_id)
