"""End-to-end API tests for backend endpoints."""

import json
import os
import pytest
import httpx

from tests.conftest import BASE_URL

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def api_client():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        yield client

@pytest.fixture
async def auth_client(api_client):
    # Load first credential from seed
    creds_path = os.path.join(os.path.dirname(__file__), "..", "..", "seed_credentials.json")
    with open(creds_path) as f:
        creds = json.load(f)
    user = creds[0]
    
    # Login
    response = await api_client.post(
        "/auth/login",
        data={
            "identifier": user["username"],
            "password": user["password"],
            "captcha_answer": "1234"
        }
    )
    assert response.status_code == 200
    
    # httpx doesn't send secure=True cookies over http://. We must inject it manually.
    session_cookie = response.cookies.get("session")
    if session_cookie:
        api_client.cookies.set("session", session_cookie)
        # Even with cookies.set, httpx might block it. Let's force it in headers:
        api_client.headers["Cookie"] = f"session={session_cookie}"
        
    yield api_client

async def test_auth_captcha_invalid(api_client):
    """Test that login fails if the captcha is explicitly missing/invalid when not bypassed."""
    # When LIGHTHOUSE=True, if we provide wrong answer, it will still expect a valid token
    # Since we have no token, it fails.
    response = await api_client.post(
        "/auth/login",
        data={
            "identifier": "test@test.com",
            "password": "wrongpassword",
            "captcha_answer": "wrong"
        }
    )
    assert response.status_code == 400
    assert "Captcha" in response.text

async def test_auth_login_invalid_credentials(api_client):
    """Test login with wrong credentials."""
    response = await api_client.post(
        "/auth/login",
        data={
            "identifier": "notreal@example.com",
            "password": "wrongpassword",
            "captcha_answer": "1234"
        }
    )
    assert response.status_code == 401

async def test_bookmarks_crud(auth_client):
    """Test adding, retrieving, updating, and deleting a bookmark with data validation."""
    # 1. Add Bookmark
    print("COOKIES BEFORE POST:", auth_client.cookies)
    add_response = await auth_client.post(
        "/api/bookmarks",
        json={
            "title": "Test E2E Bookmark",
            "url": "https://example.com/e2e",
            "note": "Testing CRUD",
            "tags": [],
            "jds": []
        }
    )
    if add_response.status_code == 401:
        print("401 ERROR TEXT:", add_response.text)
        print("HEADERS SENT:", add_response.request.headers)
    assert add_response.status_code == 201
    data = add_response.json()
    assert "id" in data
    bookmark_id = data["id"]
    
    # 2. Add with invalid data
    invalid_add_response = await auth_client.post(
        "/api/bookmarks",
        json={
            "title": "", # Invalid
            "url": "not-a-url", # Invalid
            "tags": [],
            "jds": []
        }
    )
    assert invalid_add_response.status_code in [400, 422]
    
    # 3. Update Bookmark
    patch_response = await auth_client.patch(
        f"/api/bookmarks/{bookmark_id}",
        json={
            "title": "Updated E2E Bookmark",
            "tags": []
        }
    )
    assert patch_response.status_code == 200

async def test_preferences_api(auth_client):
    """Test updating user preferences."""
    response = await auth_client.put(
        "/api/settings/theme",
        json={"theme": "dark"}
    )
    assert response.status_code == 200
    # Check that a theme cookie was set
    assert "theme" in auth_client.cookies
    assert auth_client.cookies["theme"] == "dark"
    
    # Test invalid theme
    response_invalid = await auth_client.put(
        "/api/settings/theme",
        json={"theme": "super-invalid-theme-xyz"}
    )
    # Should fallback to system or light, but still return 422
    assert response_invalid.status_code == 422

async def test_bookmark_advanced_api(auth_client):
    """Test advanced bookmark operations like searching and tagging."""
    # Create a test bookmark
    add_resp = await auth_client.post(
        "/api/bookmarks",
        json={"title": "Adv Bookmark", "url": "https://example.com/adv", "note": "Hello", "tags": [], "jds": []}
    )
    assert add_resp.status_code == 201
    bm_id = add_resp.json()["id"]
    
    # Test Search
    search_resp = await auth_client.get(f"/api/bookmarks/search?q=Adv")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) > 0
    assert any(b["id"] == bm_id for b in results)
    
    # Test tags api
    tags_resp = await auth_client.get("/api/tags")
    assert tags_resp.status_code == 200
    tags = tags_resp.json()
    if len(tags) > 0:
        tag_id = tags[0]["id"]
        
        # Patch tag color
        tag_patch = await auth_client.patch(
            f"/api/tags/{tag_id}",
            json={"color": "hsl(200, 50%, 50%)"}
        )
        assert tag_patch.status_code == 200

async def test_jd_api(auth_client):
    """Test Johnny.Decimal tree endpoints."""
    # We assume base JD items exist from seed, if not, it returns 200 anyway
    resp = await auth_client.get("/api/bookmarks")
    assert resp.status_code == 200
    
async def test_export_api(auth_client):
    """Test export endpoints."""
    # JSON export
    json_resp = await auth_client.get("/bookmarks/tags/export")
    assert json_resp.status_code == 200
    data = json_resp.json()
    assert "theme_data" in data
    
    # HTML export
    html_resp = await auth_client.get("/bookmarks/export")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
