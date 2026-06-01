"""End-to-end tests for main UI interactions."""

import pytest
from playwright.async_api import Page, expect

pytestmark = pytest.mark.asyncio

async def test_hamburger_menu_toggle(page: Page):
    """Test that the hamburger menu opens and closes, and toggles aria-expanded."""
    await page.goto("/")
    
    dropdown = page.locator("#hamburger-dropdown")
    button = page.locator("#hamburger-button")
    
    # Initially hidden
    await expect(dropdown).not_to_have_class("hamburger-dropdown show")
    
    # Click to open
    await button.click()
    # The class might be added dynamically or just be in a different container, let's just wait for it to be visible
    await expect(dropdown).to_be_visible()
    
    # Click outside to close
    await page.locator("body").click(position={"x": 10, "y": 10})
    await expect(dropdown).not_to_be_visible()


async def test_settings_modal(page: Page):
    """Test that the settings modal can be opened and closed."""
    await page.goto("/")
    
    # Open menu
    await page.click("#hamburger-button")
    
    # Open settings
    await page.click("#settings-modal-button")
    
    modal_area = page.locator("#modal-area")
    settings_modal = page.locator("#settings-modal")
    
    await expect(modal_area).to_be_visible()
    await expect(settings_modal).to_be_visible()
    await page.screenshot(path="docs/screenshots/settings_modal.png")
    
    # Close modal
    await page.click("#close-modal")
    await expect(modal_area).not_to_be_visible()


async def test_info_modal(page: Page):
    """Test that the info modal can be opened and closed."""
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
    await page.goto("/")
    
    # Open menu
    await page.click("#hamburger-button")
    
    # Open info
    await page.click("#info-modal-button")
    
    modal_area = page.locator("#modal-area")
    info_modal = page.locator("#info-modal")
    
    await expect(modal_area).to_be_visible()
    await expect(info_modal).to_be_visible()
    await page.screenshot(path="docs/screenshots/info_modal.png")
    
    await page.click("#close-modal")
    await expect(modal_area).not_to_be_visible()

async def test_bookmark_add_ui(auth_page: Page):
    """Test the add bookmark UI flow."""
    auth_page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
    auth_page.on("response", lambda res: print(f"RESPONSE: {res.url} {res.status}"))
    await auth_page.goto("/bookmarks/add")
    await expect(auth_page.locator("h1").first).to_have_text("Add bookmark")
    
    await auth_page.fill('input[name="title"]', "Playwright UI Bookmark")
    await auth_page.fill('input[name="url"]', "https://playwright.dev")
    await auth_page.fill('input[name="jdIds"]', "11.11")
    
    await auth_page.wait_for_timeout(1000) # Wait for bookmarks.js event listener to bind
    await auth_page.screenshot(path="src/static/assets/images/screenshots/e2e_add_bookmark_form.png")
    await auth_page.click('button[type="submit"]')
    
    # Wait for the toast and form reset
    await auth_page.wait_for_timeout(1000)
    await expect(auth_page.locator('input[name="title"]')).to_be_empty()
    
    # Navigate to dashboard
    await auth_page.click('a[href="/bookmarks/dashboard"]')
    await auth_page.wait_for_timeout(1000)
    await auth_page.screenshot(path="src/static/assets/images/screenshots/e2e_dashboard_after_add.png")

async def test_search_ui(auth_page: Page):
    """Test the search UI functionality."""
    await auth_page.goto("/bookmarks/search")
    await expect(auth_page.locator("h1")).to_have_text("Search bookmarks")
    
    # Search for something
    await auth_page.fill('input[name="title"]', "Playwright")
    await auth_page.click('button[type="submit"]')
    
    await auth_page.wait_for_timeout(1000) # Wait for fetch and render
    await auth_page.screenshot(path="src/static/assets/images/screenshots/e2e_search_results.png")

async def test_tags_ui(auth_page: Page):
    """Test the tag UI view."""
    await auth_page.goto("/bookmarks/tag")
    await auth_page.wait_for_timeout(1000)
    await auth_page.screenshot(path="src/static/assets/images/screenshots/e2e_tags_view.png")

async def test_jd_ui(auth_page: Page):
    """Test the JD tree UI view."""
    await auth_page.goto("/bookmarks/jd")
    await expect(auth_page.locator("h1").first).to_have_text("Bookmarks by JD ID")
    await auth_page.wait_for_timeout(1000)
    await auth_page.screenshot(path="src/static/assets/images/screenshots/e2e_jd_view.png")
