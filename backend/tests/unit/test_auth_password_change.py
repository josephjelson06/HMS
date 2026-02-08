from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.modules.auth.service as auth_service_module
from app.modules.auth.service import AuthResult, AuthService


class _FakeSession:
    def __init__(self, tenants_by_id: dict):
        self._tenants_by_id = tenants_by_id
        self.committed = False

    async def get(self, _model, key):
        return self._tenants_by_id.get(key)

    async def commit(self):
        self.committed = True


def _make_request():
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={"user-agent": "pytest"})


@pytest.mark.asyncio
async def test_change_password_revokes_sessions_and_issues_new_family_session(monkeypatch):
    user_id = uuid4()
    tenant_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=True,
        user_type="hotel",
        tenant_id=tenant_id,
        email="manager@demo.com",
        first_name="Hotel",
        last_name="Manager",
        password_hash="old-hash",
        must_reset_password=True,
    )

    class _UserRepo:
        async def get_by_id(self, lookup_id):
            if str(lookup_id) == str(user_id):
                return user
            return None

    class _PermRepo:
        async def get_role_names_for_user(self, _user_id):
            return ["hotel:manager"]

        async def get_permissions_for_user(self, _user_id):
            return ["hotel:dashboard:read"]

    monkeypatch.setattr(auth_service_module, "verify_password_constant_time", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(auth_service_module, "validate_password_strength", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth_service_module, "hash_password", lambda *_args, **_kwargs: "new-hash")

    captured = {"revoked": False, "issued_family": False, "refresh_token_override": None}

    async def fake_revoke_all_refresh_token_families(_session, *, user_id, reason):
        assert str(user_id) == str(user.id)
        assert reason == "password_changed"
        captured["revoked"] = True
        return 1

    async def fake_issue_new_refresh_token_family(_session, **kwargs):
        assert str(kwargs["tenant_id"]) == str(tenant_id)
        assert str(kwargs["user_id"]) == str(user_id)
        captured["issued_family"] = True
        return SimpleNamespace(raw_token="new-family-refresh-token", family_id=uuid4())

    async def fake_issue_auth_result(self, **kwargs):
        captured["refresh_token_override"] = kwargs.get("refresh_token_override")
        return AuthResult(
            response=None,
            access_token="new-access-token",
            refresh_token=kwargs.get("refresh_token_override") or "legacy-refresh-token",
            csrf_token="new-csrf-token",
        )

    monkeypatch.setattr(auth_service_module, "revoke_all_refresh_token_families", fake_revoke_all_refresh_token_families)
    monkeypatch.setattr(auth_service_module, "issue_new_refresh_token_family", fake_issue_new_refresh_token_family)
    monkeypatch.setattr(AuthService, "_issue_auth_result", fake_issue_auth_result)

    tenant_obj = SimpleNamespace(id=tenant_id, name="Demo Hotel", slug="demo-hotel")
    service = AuthService(_FakeSession({tenant_id: tenant_obj}), _make_request())
    service.user_repo = _UserRepo()
    service.perm_repo = _PermRepo()

    result = await service.change_password(
        user_id=user_id,
        current_password="OldPassword123!",
        new_password="NewPassword123!",
    )

    assert captured["revoked"] is True
    assert captured["issued_family"] is True
    assert captured["refresh_token_override"] == "new-family-refresh-token"
    assert user.password_hash == "new-hash"
    assert user.must_reset_password is False
    assert service.session.committed is True
    assert result.access_token == "new-access-token"
    assert result.refresh_token == "new-family-refresh-token"


@pytest.mark.asyncio
async def test_change_password_platform_user_uses_legacy_refresh_token_path(monkeypatch):
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=True,
        user_type="platform",
        tenant_id=None,
        email="admin@demo.com",
        first_name="Admin",
        last_name="User",
        password_hash="old-hash",
        must_reset_password=False,
    )

    class _UserRepo:
        async def get_by_id(self, lookup_id):
            if str(lookup_id) == str(user_id):
                return user
            return None

    class _PermRepo:
        async def get_role_names_for_user(self, _user_id):
            return ["platform:admin"]

        async def get_permissions_for_user(self, _user_id):
            return ["admin:dashboard:read"]

    monkeypatch.setattr(auth_service_module, "verify_password_constant_time", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(auth_service_module, "validate_password_strength", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth_service_module, "hash_password", lambda *_args, **_kwargs: "new-hash")

    async def fake_revoke_all_refresh_token_families(_session, *, user_id, reason):
        assert str(user_id) == str(user.id)
        assert reason == "password_changed"
        return 0

    issue_family_called = {"called": False}

    async def fake_issue_new_refresh_token_family(_session, **_kwargs):
        issue_family_called["called"] = True
        return SimpleNamespace(raw_token="should-not-happen", family_id=uuid4())

    captured = {"refresh_token_override": object()}

    async def fake_issue_auth_result(self, **kwargs):
        captured["refresh_token_override"] = kwargs.get("refresh_token_override")
        return AuthResult(
            response=None,
            access_token="new-access-token",
            refresh_token="legacy-refresh-token",
            csrf_token="new-csrf-token",
        )

    monkeypatch.setattr(auth_service_module, "revoke_all_refresh_token_families", fake_revoke_all_refresh_token_families)
    monkeypatch.setattr(auth_service_module, "issue_new_refresh_token_family", fake_issue_new_refresh_token_family)
    monkeypatch.setattr(AuthService, "_issue_auth_result", fake_issue_auth_result)

    service = AuthService(_FakeSession({}), _make_request())
    service.user_repo = _UserRepo()
    service.perm_repo = _PermRepo()

    result = await service.change_password(
        user_id=user_id,
        current_password="OldPassword123!",
        new_password="NewPassword123!",
    )

    assert issue_family_called["called"] is False
    assert captured["refresh_token_override"] is None
    assert service.session.committed is True
    assert result.refresh_token == "legacy-refresh-token"

