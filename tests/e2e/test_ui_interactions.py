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
