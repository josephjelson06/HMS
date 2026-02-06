from app.core.permissions import has_permission


def test_exact_match():
    assert has_permission(["hotel:guests:create"], "hotel:guests:create")


def test_wildcard_scope():
    assert has_permission(["hotel:guests:*"], "hotel:guests:create")


def test_wildcard_all():
    assert has_permission(["hotel:*:*"], "hotel:rooms:update")


def test_no_match():
    assert not has_permission(["hotel:guests:read"], "hotel:guests:create")
