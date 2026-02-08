#!/usr/bin/env python3
"""
API smoke runner (Phase 3A)

Runs a minimal, repeatable set of black-box checks against a live HMS backend.
Exits non-zero on any failure.

Usage:
  python backend/scripts/smoke_api.py --base-url http://127.0.0.1:8000/api

Environment overrides:
  SMOKE_BASE_URL, SMOKE_ORIGIN,
  SMOKE_ADMIN_EMAIL, SMOKE_ADMIN_PASSWORD,
  SMOKE_HOTEL_EMAIL, SMOKE_HOTEL_PASSWORD
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
DEFAULT_ORIGIN = os.getenv("SMOKE_ORIGIN", "http://localhost:3000").rstrip("/")

DEFAULT_ADMIN_EMAIL = os.getenv("SMOKE_ADMIN_EMAIL", "admin@demo.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD", "Admin123!")
DEFAULT_HOTEL_EMAIL = os.getenv("SMOKE_HOTEL_EMAIL", "manager@demo.com")
DEFAULT_HOTEL_PASSWORD = os.getenv("SMOKE_HOTEL_PASSWORD", "Manager123!")


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str


def _now_ms() -> int:
    return int(time.time() * 1000)


def _title(msg: str) -> str:
    return f"[smoke] {msg}"


def _fail(msg: str) -> None:
    raise SmokeError(msg)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        _fail(msg)


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception as exc:  # pragma: no cover
        _fail(f"Expected JSON response but failed to parse: {exc}")
    if not isinstance(data, dict):
        _fail(f"Expected JSON object, got: {type(data).__name__}")
    return data


def _origin_headers(origin: str) -> dict[str, str]:
    # For browser-equivalent behavior. Keep Origin stable so CSRF origin checks pass.
    return {"Origin": origin}


def _ensure_csrf_cookie(client: httpx.Client, origin: str) -> str:
    r = client.get("/auth/csrf", headers=_origin_headers(origin))
    _require(r.status_code == 200, f"GET /auth/csrf expected 200, got {r.status_code}: {r.text}")

    csrf_cookie = client.cookies.get("csrf_token")
    _require(bool(csrf_cookie), "csrf_token cookie was not set after GET /auth/csrf")
    return str(csrf_cookie)


def _csrf_headers(client: httpx.Client, origin: str) -> dict[str, str]:
    csrf_cookie = client.cookies.get("csrf_token")
    if not csrf_cookie:
        csrf_cookie = _ensure_csrf_cookie(client, origin)
    return {"X-CSRF-Token": str(csrf_cookie), "Origin": origin}


def _login(client: httpx.Client, origin: str, creds: Credentials) -> dict[str, Any]:
    # Ensure CSRF cookie exists; login endpoint is exempt from double-submit but still uses origin checks.
    _ensure_csrf_cookie(client, origin)
    r = client.post(
        "/auth/login",
        headers=_origin_headers(origin),
        json={"email": creds.email, "password": creds.password},
    )
    _require(r.status_code == 200, f"POST /auth/login expected 200, got {r.status_code}: {r.text}")
    _require(bool(client.cookies.get("access_token")), "access_token cookie missing after login")
    _require(bool(client.cookies.get("refresh_token")), "refresh_token cookie missing after login")
    _require(bool(client.cookies.get("csrf_token")), "csrf_token cookie missing after login")
    return _json(r)


def _me(client: httpx.Client, origin: str) -> dict[str, Any]:
    r = client.get("/auth/me", headers=_origin_headers(origin))
    _require(r.status_code == 200, f"GET /auth/me expected 200, got {r.status_code}: {r.text}")
    return _json(r)


def _refresh(client: httpx.Client, origin: str) -> dict[str, Any]:
    # /auth/refresh is exempt from double-submit; still keep Origin for consistency.
    r = client.post("/auth/refresh", headers=_origin_headers(origin))
    _require(r.status_code == 200, f"POST /auth/refresh expected 200, got {r.status_code}: {r.text}")
    _require(bool(client.cookies.get("refresh_token")), "refresh_token cookie missing after refresh")
    return _json(r)


def _expect_refresh_fails_with_token(
    *, base_url: str, origin: str, refresh_token: str, expect_detail_contains: str | None = None
) -> None:
    with httpx.Client(base_url=base_url, timeout=20, follow_redirects=False) as c:
        c.cookies.set("refresh_token", refresh_token)
        r = c.post("/auth/refresh", headers=_origin_headers(origin))
        _require(r.status_code >= 400, f"Expected refresh to fail, got {r.status_code}")
        if expect_detail_contains:
            detail = ""
            try:
                detail = str(r.json().get("detail", ""))
            except Exception:
                detail = r.text
            _require(
                expect_detail_contains.lower() in detail.lower(),
                f"Expected refresh failure detail to contain '{expect_detail_contains}', got: {detail}",
            )


def _list_hotels(client: httpx.Client, origin: str) -> dict[str, Any]:
    r = client.get("/admin/hotels/", headers=_origin_headers(origin))
    _require(r.status_code == 200, f"GET /admin/hotels expected 200, got {r.status_code}: {r.text}")
    return _json(r)


def _find_demo_hotel_tenant_id(hotels_payload: dict[str, Any]) -> str:
    items = hotels_payload.get("items") or []
    _require(isinstance(items, list) and items, "admin hotels list returned no items")
    for item in items:
        if isinstance(item, dict) and item.get("slug") == "demo-hotel" and item.get("id"):
            return str(item["id"])
    # Fallback: just pick first item id.
    first = items[0]
    _require(isinstance(first, dict) and first.get("id"), "admin hotels list items missing id")
    return str(first["id"])


def _start_impersonation(client: httpx.Client, origin: str, tenant_id: str) -> dict[str, Any]:
    r = client.post(
        "/auth/impersonation/start",
        headers=_csrf_headers(client, origin),
        json={"tenant_id": tenant_id, "reason": "smoke"},
    )
    _require(
        r.status_code == 200,
        f"POST /auth/impersonation/start expected 200, got {r.status_code}: {r.text}",
    )
    _require(bool(client.cookies.get("refresh_token")), "refresh_token cookie missing after impersonation start")
    return _json(r)


def _stop_impersonation(client: httpx.Client, origin: str) -> dict[str, Any]:
    r = client.post("/auth/impersonation/stop", headers=_csrf_headers(client, origin))
    _require(
        r.status_code == 200,
        f"POST /auth/impersonation/stop expected 200, got {r.status_code}: {r.text}",
    )
    return _json(r)


def _admin_reset_password(client: httpx.Client, origin: str, user_id: str) -> str:
    r = client.post(
        "/auth/password/reset",
        headers=_csrf_headers(client, origin),
        json={"user_id": user_id},
    )
    _require(
        r.status_code == 200,
        f"POST /auth/password/reset expected 200, got {r.status_code}: {r.text}",
    )
    body = _json(r)
    temp_password = body.get("temporary_password")
    _require(bool(temp_password), "password/reset response missing temporary_password")
    return str(temp_password)


def _hotel_change_password(client: httpx.Client, origin: str, current_password: str, new_password: str) -> None:
    r = client.post(
        "/auth/password/change",
        headers=_csrf_headers(client, origin),
        json={"current_password": current_password, "new_password": new_password},
    )
    _require(
        r.status_code == 200,
        f"POST /auth/password/change expected 200, got {r.status_code}: {r.text}",
    )


def _hotel_create_room(client: httpx.Client, origin: str) -> dict[str, Any]:
    room_number = f"SMOKE-{_now_ms()}-{uuid.uuid4().hex[:6]}"
    payload = {"number": room_number, "room_type": "standard"}
    r = client.post("/hotel/rooms/", headers=_csrf_headers(client, origin), json=payload)
    _require(
        r.status_code == 201,
        f"POST /hotel/rooms expected 201, got {r.status_code}: {r.text}",
    )
    body = _json(r)
    _require(str(body.get("number")) == room_number, "created room response did not echo number")
    return body


def _hotel_list_rooms(client: httpx.Client, origin: str) -> dict[str, Any]:
    r = client.get("/hotel/rooms/", headers=_origin_headers(origin))
    _require(
        r.status_code == 200,
        f"GET /hotel/rooms expected 200, got {r.status_code}: {r.text}",
    )
    return _json(r)


def _hotel_list_audit(client: httpx.Client, origin: str) -> dict[str, Any]:
    r = client.get("/hotel/audit/", headers=_origin_headers(origin))
    _require(
        r.status_code == 200,
        f"GET /hotel/audit expected 200, got {r.status_code}: {r.text}",
    )
    return _json(r)


def _expect_admin_forbidden(client: httpx.Client, origin: str) -> None:
    r = client.get("/admin/hotels/", headers=_origin_headers(origin))
    _require(r.status_code == 403, f"Expected hotel user to be forbidden from admin endpoints, got {r.status_code}")


def _logout_requires_csrf(client: httpx.Client, origin: str) -> None:
    # Negative: logout without CSRF header should be rejected.
    r = client.post("/auth/logout", headers=_origin_headers(origin))
    _require(r.status_code == 403, f"Expected POST /auth/logout without CSRF header to return 403, got {r.status_code}")

    # Positive: logout with CSRF header should succeed.
    r2 = client.post("/auth/logout", headers=_csrf_headers(client, origin))
    _require(r2.status_code == 200, f"Expected POST /auth/logout with CSRF header to return 200, got {r2.status_code}")


def run(base_url: str, origin: str, admin: Credentials, hotel: Credentials) -> None:
    print(_title(f"base_url={base_url} origin={origin}"))

    # --- Health ---
    with httpx.Client(base_url=base_url, timeout=10, follow_redirects=False) as c:
        r = c.get("/health")
        _require(r.status_code == 200, f"GET /health expected 200, got {r.status_code}: {r.text}")

    # --- Admin: login + impersonation lifecycle ---
    hotel_manager_user_id: str | None = None
    hotel_temp_password: str | None = None

    with httpx.Client(base_url=base_url, timeout=20, follow_redirects=False) as admin_client:
        print(_title("admin login"))
        _login(admin_client, origin, admin)
        me1 = _me(admin_client, origin)
        _require(me1.get("user", {}).get("user_type") in {"platform", "admin"}, "admin user_type not platform/admin")

        print(_title("admin list hotels"))
        hotels_payload = _list_hotels(admin_client, origin)
        demo_tenant_id = _find_demo_hotel_tenant_id(hotels_payload)

        print(_title("impersonation start"))
        start_payload = _start_impersonation(admin_client, origin, demo_tenant_id)
        hotel_manager_user_id = str((start_payload.get("user") or {}).get("id") or "") or None
        _require(bool(hotel_manager_user_id), "impersonation start response missing user.id")
        me2 = _me(admin_client, origin)
        imp = me2.get("impersonation")
        _require(isinstance(imp, dict) and imp.get("active") is True, "impersonation not active after start")
        impersonation_refresh_token = str(admin_client.cookies.get("refresh_token"))

        print(_title("impersonation refresh rotate preserves context"))
        _refresh(admin_client, origin)
        me3 = _me(admin_client, origin)
        imp2 = me3.get("impersonation")
        _require(isinstance(imp2, dict) and imp2.get("active") is True, "impersonation context lost after refresh")

        print(_title("impersonation stop"))
        _stop_impersonation(admin_client, origin)
        me4 = _me(admin_client, origin)
        _require(me4.get("impersonation") is None, "impersonation still present after stop")
        admin_refresh_token_after_stop = str(admin_client.cookies.get("refresh_token"))

        print(_title("old impersonation refresh token is rejected"))
        _expect_refresh_fails_with_token(
            base_url=base_url,
            origin=origin,
            refresh_token=impersonation_refresh_token,
        )

        print(_title("admin refresh still works after impersonation end"))
        # Platform users use the legacy (non-family) refresh token path; this should still succeed.
        with httpx.Client(base_url=base_url, timeout=20, follow_redirects=False) as tmp:
            tmp.cookies.set("refresh_token", admin_refresh_token_after_stop)
            r = tmp.post("/auth/refresh", headers=_origin_headers(origin))
            _require(r.status_code == 200, f"Expected admin refresh to work after stop, got {r.status_code}: {r.text}")

        print(_title("admin resets demo hotel manager password (forces must_reset_password)"))
        hotel_temp_password = _admin_reset_password(admin_client, origin, str(hotel_manager_user_id))
        _require(bool(hotel_temp_password), "failed to obtain temporary password for hotel manager")

        print(_title("csrf enforcement on logout"))
        _logout_requires_csrf(admin_client, origin)

    _require(bool(hotel_manager_user_id), "hotel manager user id missing (internal error)")
    _require(bool(hotel_temp_password), "hotel temp password missing (internal error)")

    # --- Hotel: must-reset flow + tenant boundary + CRUD sanity + audit read ---
    stable_hotel_password = os.getenv("SMOKE_HOTEL_NEW_PASSWORD", "SmokeStrongPass123!")
    with httpx.Client(base_url=base_url, timeout=20, follow_redirects=False) as hotel_client:
        print(_title("hotel login with temporary password"))
        _login(hotel_client, origin, Credentials(email=hotel.email, password=str(hotel_temp_password)))
        me_h1 = _me(hotel_client, origin)
        _require(me_h1.get("user", {}).get("user_type") == "hotel", "hotel user_type not hotel")
        _require(bool(me_h1.get("user", {}).get("tenant_id")), "hotel tenant_id missing from /auth/me")
        _require(me_h1.get("must_reset_password") is True, "expected must_reset_password=true after admin reset")

        print(_title("hotel changes password to clear must-reset"))
        _hotel_change_password(hotel_client, origin, current_password=str(hotel_temp_password), new_password=stable_hotel_password)
        me_h2 = _me(hotel_client, origin)
        _require(me_h2.get("must_reset_password") in {False, None}, "must_reset_password still true after change-password")

        print(_title("tenant boundary: hotel cannot access /admin/*"))
        _expect_admin_forbidden(hotel_client, origin)

        print(_title("hotel CRUD sanity: create room"))
        created_room = _hotel_create_room(hotel_client, origin)

        print(_title("hotel CRUD sanity: list rooms contains created"))
        rooms_payload = _hotel_list_rooms(hotel_client, origin)
        items = rooms_payload.get("items") or []
        _require(
            any(isinstance(it, dict) and str(it.get("id")) == str(created_room.get("id")) for it in items),
            "created room not found in list",
        )

        print(_title("audit read sanity"))
        _hotel_list_audit(hotel_client, origin)

        print(_title("csrf enforcement on logout"))
        _logout_requires_csrf(hotel_client, origin)

    # --- Refresh reuse detection (family tokens) ---
    print(_title("refresh reuse detection revokes family (hotel)"))
    with httpx.Client(base_url=base_url, timeout=20, follow_redirects=False) as reuse_client:
        _login(reuse_client, origin, Credentials(email=hotel.email, password=stable_hotel_password))
        token1 = str(reuse_client.cookies.get("refresh_token"))
        _require(bool(token1), "missing hotel refresh token before rotation")
        _refresh(reuse_client, origin)
        token2 = str(reuse_client.cookies.get("refresh_token"))
        _require(bool(token2) and token2 != token1, "refresh rotation did not change token")

        # Trigger reuse detection with old token. This should revoke the whole family.
        _expect_refresh_fails_with_token(
            base_url=base_url,
            origin=origin,
            refresh_token=token1,
            expect_detail_contains="reuse detected",
        )

        # The "current" token should also be invalid now (family revoked).
        _expect_refresh_fails_with_token(
            base_url=base_url,
            origin=origin,
            refresh_token=token2,
        )

    print(_title("OK"))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="HMS API smoke runner")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend API base url (default: %(default)s)")
    parser.add_argument("--origin", default=DEFAULT_ORIGIN, help="Origin header to send (default: %(default)s)")
    parser.add_argument("--admin-email", default=DEFAULT_ADMIN_EMAIL)
    parser.add_argument("--admin-password", default=DEFAULT_ADMIN_PASSWORD)
    parser.add_argument("--hotel-email", default=DEFAULT_HOTEL_EMAIL)
    parser.add_argument("--hotel-password", default=DEFAULT_HOTEL_PASSWORD)
    args = parser.parse_args(argv)

    try:
        run(
            base_url=str(args.base_url).rstrip("/"),
            origin=str(args.origin).rstrip("/"),
            admin=Credentials(email=args.admin_email, password=args.admin_password),
            hotel=Credentials(email=args.hotel_email, password=args.hotel_password),
        )
    except SmokeError as exc:
        print(_title(f"FAILED: {exc}"), file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(_title(f"FAILED (http): {exc}"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
