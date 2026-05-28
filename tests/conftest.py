"""Global pytest configuration and fixtures."""

import os
import subprocess
import time

import httpx
import pytest
import pytest_asyncio
from playwright.async_api import Browser, BrowserContext, async_playwright

PORT = 4173
BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="session", autouse=True)
def test_server():
    """Spins up a FastAPI test server bound to a specific port."""
    # Ensure test environment variables are set if necessary.
    os.environ["TESTING"] = "true"
    
    server_process = subprocess.Popen(  # noqa: S603
        ["hypercorn", "main:app", "--bind", f"0.0.0.0:{PORT}", "--workers", "1"],  # noqa: S607
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    # Wait for the server to be responsive
    start_time = time.time()
    server_ready = False
    while time.time() - start_time < 15:
        try:
            response = httpx.get(BASE_URL)
            if response.status_code == 200:
                server_ready = True
                break
        except httpx.RequestError:
            time.sleep(0.5)

    if not server_ready:
        server_process.kill()
        raise RuntimeError(f"Server did not start within 15 seconds on port {PORT}")

    yield BASE_URL

    server_process.kill()
    server_process.wait()


@pytest_asyncio.fixture(scope="function")
async def browser():
    """Provide a Playwright browser instance."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest_asyncio.fixture(scope="function")
async def context(browser: Browser):
    """Provide a fresh browser context for each test."""
    context = await browser.new_context(base_url=BASE_URL)
    yield context
    await context.close()


@pytest_asyncio.fixture(scope="function")
async def page(context: BrowserContext):
    """Provide a fresh page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest_asyncio.fixture(scope="function")
async def auth_context(browser: Browser):
    """Provide a browser context that is already logged in using a valid seed credential."""
    import json
    
    context = await browser.new_context(base_url=BASE_URL)
    page = await context.new_page()
    
    # Load first credential from seed
    creds_path = os.path.join(os.path.dirname(__file__), "..", "seed_credentials.json")
    with open(creds_path) as f:
        creds = json.load(f)
    user = creds[0]
    
    await page.goto("/login")
    await page.fill('input[name="identifier"]', user["username"])
    await page.fill('input[name="password"]', user["password"])
    await page.click('input[type="submit"]')
    
    # Wait for successful login redirect
    await page.wait_for_url("**/bookmarks*")
    
    yield context
    
    await context.close()


@pytest_asyncio.fixture(scope="function")
async def auth_page(auth_context: BrowserContext):
    """Provide a page from an authenticated context."""
    page = await auth_context.new_page()
    yield page
    await page.close()
