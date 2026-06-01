"""End-to-end tests for the authentication and login flow."""

import re

import pytest
from playwright.async_api import Page, expect

pytestmark = pytest.mark.asyncio

async def test_successful_login(page: Page):
    """Test that a valid user can log in and is redirected to the dashboard."""
    import json
    import os
    
    # Load first credential from seed
    creds_path = os.path.join(os.path.dirname(__file__), "..", "..", "seed_credentials.json")
    with open(creds_path) as f:
        creds = json.load(f)
    user = creds[0]
    
    await page.goto("/login")
    
    await page.fill('input[name="identifier"]', user["username"])
    await page.fill('input[name="password"]', user["password"])
    await page.fill('input[name="captcha_answer"]', "1234")
    await page.click('input[type="submit"]')
    
    # Wait for navigation and verify we're on the dashboard
    await page.wait_for_url("**/bookmarks*")
    await expect(page).to_have_url(re.compile(r".*/bookmarks.*"))
    
    # Verify authentication cookie exists
    cookies = await page.context.cookies()
    print("COOKIES:", cookies)
    assert any(c["name"] == "session" for c in cookies), "Session cookie should be set after login" # pyright: ignore[reportTypedDictNotRequiredAccess]

async def test_invalid_login(page: Page):
    """Test that an invalid login displays an error toast/message and remains on login page."""
    await page.goto("/login")
    
    await page.fill('input[name="identifier"]', "invalid_user")
    await page.fill('input[name="password"]', "wrongpassword")
    await page.fill('input[name="captcha_answer"]', "1234")
    await page.click('input[type="submit"]')
    
    # Wait for the toast container or error element
    toast_element = page.locator("#toast")
    await expect(toast_element).to_be_visible(timeout=5000)
    
    # URL should remain /login
    await expect(page).to_have_url(re.compile(r".*/login"))

async def test_logout_flow(auth_page: Page):
    """Test that logging out removes the cookie and redirects to /login."""
    await auth_page.goto("/bookmarks")
    
    # Click hamburger menu
    await auth_page.click("#hamburger-button")
    
    # Click logout link
    await auth_page.click('a[href="/auth/logout"]')
    
    # Should be redirected to landing page or login
    await auth_page.wait_for_url("**/login*")
    
    # Verify cookie is gone
    cookies = await auth_page.context.cookies()
    assert not any(c["name"] == "session" for c in cookies), "Session cookie should be removed after logout" # pyright: ignore[reportTypedDictNotRequiredAccess]

async def test_protected_route_redirect(page: Page):
    """Test that an unauthenticated user cannot access the dashboard."""
    await page.goto("/bookmarks")
    
    # Wait for redirect to login or 401/403 page
    await page.wait_for_url("**/login")
    await expect(page).to_have_url(re.compile(r".*/login"))
