import os

import pytest


@pytest.mark.system
def test_auth_negative_regressions_smoke_gate():
    """
    Phase 4.5: Auth-negative regression automation (black-box).

    This reuses the API smoke runner as a repeatable, 0-fail gate that includes:
    - CSRF missing/mismatch rejection + positive path
    - tenant boundary enforcement (hotel cannot hit /admin/*)
    - must_reset_password lifecycle (reset -> forced change-password)
    - refresh token reuse detection revokes family (hotel)
    - impersonation lifecycle + revocation isolation (admin vs impersonation family)

    Requirements:
    - Backend running and reachable at SMOKE_BASE_URL (expects /api prefix).
    - Seed data enabled (admin@demo.com / manager@demo.com) OR SMOKE_* creds set.
    """

    base_url = os.getenv("SMOKE_BASE_URL")
    if not base_url:
        pytest.skip("SMOKE_BASE_URL not set (requires running backend)")

    base_url = base_url.rstrip("/")
    if not base_url.endswith("/api"):
        base_url = f"{base_url}/api"

    origin = os.getenv("SMOKE_ORIGIN", "http://localhost:3000").rstrip("/")

    admin_email = os.getenv("SMOKE_ADMIN_EMAIL", "admin@demo.com")
    admin_password = os.getenv("SMOKE_ADMIN_PASSWORD", "Admin123!")
    hotel_email = os.getenv("SMOKE_HOTEL_EMAIL", "manager@demo.com")
    hotel_password = os.getenv("SMOKE_HOTEL_PASSWORD", "Manager123!")

    # Import lazily so collection doesn't require httpx if tests are skipped.
    from scripts.smoke_api import Credentials, SmokeError, run

    try:
        run(
            base_url=base_url,
            origin=origin,
            admin=Credentials(email=admin_email, password=admin_password),
            hotel=Credentials(email=hotel_email, password=hotel_password),
        )
    except SmokeError as exc:
        pytest.fail(str(exc))

