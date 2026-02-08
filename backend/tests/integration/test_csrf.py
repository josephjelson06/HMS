"""
Integration tests for CSRF middleware functionality.
Tests Origin/Referer validation, timing-safe comparison, and auto-issued cookies.
"""
import pytest


@pytest.mark.integration
async def test_csrf_endpoint_issues_cookie(client):
    """GET /api/auth/csrf should return success and set a csrf_token cookie."""
    response = await client.get("/api/auth/csrf")
    
    assert response.status_code == 200
    assert response.json() == {"csrf_cookie_issued": True}
    
    # Check that a csrf_token cookie was set
    cookies = response.cookies
    assert "csrf_token" in cookies
    csrf_token = cookies["csrf_token"]
    assert len(csrf_token) > 0


@pytest.mark.integration
async def test_csrf_endpoint_no_new_cookie_when_exists(client):
    """GET /api/auth/csrf when cookie already exists should not set a new cookie."""
    # First request to get a cookie
    response1 = await client.get("/api/auth/csrf")
    csrf_token1 = response1.cookies.get("csrf_token")
    
    # Second request with the existing cookie
    response2 = await client.get("/api/auth/csrf", cookies={"csrf_token": csrf_token1})
    
    assert response2.status_code == 200
    # The response should not set a new cookie (existing one is sufficient)
    # In httpx, if cookie is not being re-set, it won't appear in response.cookies
    # or will have the same value
    csrf_token2 = response2.cookies.get("csrf_token")
    if csrf_token2:
        # If present, it should be the same
        assert csrf_token2 == csrf_token1


@pytest.mark.integration
async def test_refresh_exempt_from_csrf(client):
    """POST /api/auth/refresh should not require CSRF token (exempt path)."""
    response = await client.post("/api/auth/refresh")
    
    # Should not get CSRF error (might get auth error or db error, but not CSRF)
    # CSRF error would be 403 with "CSRF token missing or invalid"
    if response.status_code == 403:
        detail = response.json().get("detail", "")
        assert "CSRF" not in detail
    # Any other error (500, 422, etc.) means it passed CSRF check


@pytest.mark.integration
async def test_post_without_csrf_token_fails(client):
    """POST to non-exempt path without CSRF token should fail with 403."""
    # Using /api/hotel/rooms as a non-exempt endpoint
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"}
    )
    
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "CSRF token missing or invalid" in detail


@pytest.mark.integration
async def test_post_with_mismatched_csrf_token_fails(client):
    """POST with mismatched cookie/header CSRF tokens should fail with 403."""
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"},
        cookies={"csrf_token": "cookie_token_123"},
        headers={"X-CSRF-Token": "different_header_token_456"}
    )
    
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "CSRF token mismatch" in detail


@pytest.mark.integration
async def test_post_with_matching_csrf_token_passes(client):
    """POST with matching cookie/header CSRF tokens should pass CSRF check."""
    # First get a CSRF token
    csrf_response = await client.get("/api/auth/csrf")
    csrf_token = csrf_response.cookies.get("csrf_token")
    
    # Now make a POST request with matching token
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"},
        cookies={"csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    
    # Should pass CSRF check (might fail with other errors like auth, but not CSRF)
    # CSRF errors are 403 with specific messages
    if response.status_code == 403:
        detail = response.json().get("detail", "")
        assert "CSRF" not in detail


@pytest.mark.integration
async def test_post_with_invalid_origin_fails(client):
    """POST with Origin header not in cors_origins should fail with 403."""
    # First get a CSRF token
    csrf_response = await client.get("/api/auth/csrf")
    csrf_token = csrf_response.cookies.get("csrf_token")
    
    # Make POST with evil origin
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"},
        cookies={"csrf_token": csrf_token},
        headers={
            "X-CSRF-Token": csrf_token,
            "Origin": "https://evil.com"
        }
    )
    
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "Origin 'https://evil.com' is not allowed" in detail


@pytest.mark.integration
async def test_post_with_valid_origin_passes(client):
    """POST with Origin header in cors_origins should pass origin check."""
    # First get a CSRF token
    csrf_response = await client.get("/api/auth/csrf")
    csrf_token = csrf_response.cookies.get("csrf_token")
    
    # Make POST with valid origin (localhost:3000 is in default cors_origins)
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"},
        cookies={"csrf_token": csrf_token},
        headers={
            "X-CSRF-Token": csrf_token,
            "Origin": "http://localhost:3000"
        }
    )
    
    # Should pass origin and CSRF check (might fail with auth, but not CSRF/Origin)
    if response.status_code == 403:
        detail = response.json().get("detail", "")
        assert "Origin" not in detail
        assert "CSRF token" not in detail


@pytest.mark.integration
async def test_get_request_not_affected_by_csrf(client):
    """GET requests should not be affected by CSRF checks."""
    # GET to /api/health should work without any CSRF token
    response = await client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
async def test_csrf_error_response_includes_new_cookie(client):
    """When CSRF validation fails, response should include a new csrf_token cookie."""
    # Make a POST without any CSRF token
    response = await client.post(
        "/api/hotel/rooms",
        json={"name": "Test Room"}
    )
    
    assert response.status_code == 403
    # Should have issued a new CSRF cookie in the error response
    assert "csrf_token" in response.cookies
    csrf_token = response.cookies["csrf_token"]
    assert len(csrf_token) > 0
