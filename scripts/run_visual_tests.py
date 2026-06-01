"""Automated visual regression testing script."""

import asyncio
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.async_api import async_playwright

# Ensure the root directory is on the path so we can import 'src'
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import tex_escape

# Dynamically calculate a healthy concurrency limit based on CPU threads.
# We multiply by 2 because screenshots are mostly I/O bound (network/IPC).
# Max cap at 24 to prevent memory exhaustion on massive core-count machines.
concurrency_limit = min(24, max(4, (multiprocessing.cpu_count() or 4) * 2))
sem = asyncio.Semaphore(concurrency_limit)


PORT = 4173
BASE_URL = f"http://127.0.0.1:{PORT}"
TEX_MAIN_PAPER_DIR = Path("paper/").absolute()
SCREENSHOTS_OUTPUT_DIR = Path("src/static/assets/images/screenshots/").absolute()

# Added auth requirement flag to prevent protected redirects during testing
PAGES = [
    ("landing", "/", False),
    ("login", "/login", False),
    ("register", "/register", False),
    ("2fa", "/login/2fa", False),
    ("docs", "/docs", False),
    ("dashboard", "/bookmarks", True),
    ("add", "/bookmarks/add", True),
    ("edit", "/bookmarks/edit?id=1", True),
    ("jd", "/bookmarks/jd", True),
    ("tag", "/bookmarks/tag", True),
    ("search", "/bookmarks/search?q=test", True),
    ("404", "/http_code/404", False),
    ("500", "/http_code/500", False),
]

VIEWPORTS = [
    {"width": 1920, "height": 1080, "label": "default"},
    {"width": 1680, "height": 1050, "label": "1680x1050"},
    {"width": 1280, "height": 800, "label": "1280x800"},
    {"width": 1024, "height": 768, "label": "1024x768"},
    {"width": 980, "height": 600, "label": "980x600"},
    {"width": 736, "height": 414, "label": "736x414"},
    {"width": 320, "height": 640, "label": "320x640"},
]


def run_lighthouse(url: str, file_label: str) -> dict:
    """Run Lighthouse CLI against the URL and returns the parsed JSON scores."""
    print(f"Running Lighthouse for {url}...")
    tmp = tempfile.NamedTemporaryFile(
        prefix=f"lighthouse_{file_label}_",
        suffix=".json",
        delete=False,
    )
    output_path = tmp.name
    tmp.close()

    cmd = [
        "npx",
        "lighthouse",
        url,
        "--output=json",
        f"--output-path={output_path}",
        "--chrome-flags=--headless --no-sandbox --disable-gpu --disable-dev-shm-usage",
        "--preset=desktop",
        "--no-enable-error-reporting",
    ]

    subprocess.run(  # noqa: S603
        cmd,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        with open(output_path) as f:
            lhr = json.load(f)

        return {
            "performance": round(
                (lhr["categories"]["performance"]["score"] or 0) * 100,
            ),
            "accessibility": round(
                (lhr["categories"]["accessibility"]["score"] or 0) * 100,
            ),
            "bestPractices": round(
                (lhr["categories"]["best-practices"]["score"] or 0) * 100,
            ),
            "seo": round((lhr["categories"]["seo"]["score"] or 0) * 100),
            "metrics": {
                "FCP": lhr["audits"]["first-contentful-paint"].get(
                    "displayValue",
                    "N/A",
                ),
                "LCP": lhr["audits"]["largest-contentful-paint"].get(
                    "displayValue",
                    "N/A",
                ),
                "SpeedIndex": lhr["audits"]["speed-index"].get("displayValue", "N/A"),
                "TTI": lhr["audits"]["interactive"].get("displayValue", "N/A"),
                "TBT": lhr["audits"]["total-blocking-time"].get("displayValue", "N/A"),
                "CLS": lhr["audits"]["cumulative-layout-shift"].get(
                    "displayValue",
                    "N/A",
                ),
            },
        }
    except Exception as e:  # noqa: BLE001
        print(f"Lighthouse failed for {url}: {e}")
        return {
            "performance": 0,
            "accessibility": 0,
            "bestPractices": 0,
            "seo": 0,
            "metrics": {
                "FCP": "N/A",
                "LCP": "N/A",
                "SpeedIndex": "N/A",
                "TTI": "N/A",
                "TBT": "N/A",
                "CLS": "N/A",
            },
        }
    finally:
        try:
            os.remove(output_path)
        except Exception as e:  # noqa: BLE001
            print(f"Lighthouse failed for {url}: {e}")


async def capture_viewport(context, url, theme, vp, output_dir, label):
    """Capture a single viewport using its own page instance concurrently."""
    async with sem:
        page = await context.new_page()
        page.set_default_timeout(90000)
        await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        filename = f"{label}-{theme}-{vp['width']}x{vp['height']}.png"
        if vp["label"] == "default":
            filename = f"{label}-{theme}.png"

        output_path = os.path.join(output_dir, filename)
        await page.screenshot(path=output_path)
        print(f"✔ Screenshot saved: {filename}")
        await page.close()

        return vp, filename, output_path


def make_theme_route_handler(theme_val):
    """Mock the backend API so it returns the requested theme without hitting the DB."""

    async def route_handler(route):
        if route.request.method == "GET":
            await route.fulfill(status=200, json={"theme": theme_val})
        else:
            await route.continue_()

    return route_handler


async def process_pages(
    contexts,
    pages_subset,
    pages_tex_content,
    lighthouse_tex_content,
):
    """Process a subset of pages using the provided contexts."""
    for label, path, _requires_auth in pages_subset:
        page_start_time = time.time()
        url = f"{BASE_URL}{path}"
        escaped_path = f"\\texttt{{{tex_escape(path)}}}"
        path_section = f"\\section{{{escaped_path}}}\n\n"
        path_subsection = f"\\subsection{{{escaped_path}}}\n\n"
        pages_tex_content += path_section
        lighthouse_tex_content += path_subsection

        screenshot_tasks = []
        for theme in ["light", "dark"]:
            ctx = contexts[theme]
            screenshot_tasks.extend(
                [
                    capture_viewport(ctx, url, theme, vp, SCREENSHOTS_OUTPUT_DIR, label)
                    for vp in VIEWPORTS
                ],
            )

        # Run screenshots and Lighthouse concurrently
        lighthouse_task = asyncio.to_thread(run_lighthouse, url, label)
        results, metrics = await asyncio.gather(
            asyncio.gather(*screenshot_tasks),
            lighthouse_task,
        )

        # Write LaTeX based on screenshot results (grouping by theme to maintain order)
        for theme in ["light", "dark"]:
            theme_results = [r for r in results if r[1].startswith(f"{label}-{theme}")]
            for vp, _filename, output_path in theme_results:
                pages_tex_content += f"\\begin{{figure}}[H]\n    \\centering\n    \\includegraphics[width=\\linewidth, height=0.8\\paperheight, keepaspectratio]{{{Path(output_path).relative_to(TEX_MAIN_PAPER_DIR, walk_up=True)}}}\n    \\caption{{{escaped_path} ({theme}) {vp['width']}x{vp['height']}px}}\n    \\label{{fig:{label}-{theme}-{vp['width']}x{vp['height']}}}\n\\end{{figure}}\n"

        lighthouse_tex_content += f"\\begin{{table}}[H]\n\\centering\n\\caption{{Lighthouse Scores for {escaped_path}}}\n\\begin{{tabular}}{{|l|c|}}\n\\hline\nCategory & Score \\\\ \\hline\nPerformance & {metrics['performance']} \\\\ \\hline\nAccessibility & {metrics['accessibility']} \\\\ \\hline\nBest Practices & {metrics['bestPractices']} \\\\ \\hline\nSEO & {metrics['seo']} \\\\ \\hline\n\\end{{tabular}}\n\\end{{table}}\n\n\\begin{{table}}[H]\n\\centering\n\\caption{{Lighthouse Metrics for {escaped_path}}}\n\\begin{{tabular}}{{|l|c|}}\n\\hline\nMetric & Value \\\\ \\hline\nFCP & {metrics['metrics']['FCP']} \\\\ \\hline\nLCP & {metrics['metrics']['LCP']} \\\\ \\hline\nSpeedIndex & {metrics['metrics']['SpeedIndex']} \\\\ \\hline\nTTI & {metrics['metrics']['TTI']} \\\\ \\hline\nTBT & {metrics['metrics']['TBT']} \\\\ \\hline\nCLS & {metrics['metrics']['CLS']} \\\\ \\hline\n\\end{{tabular}}\n\\end{{table}}\n"

        page_elapsed = time.time() - page_start_time
        print(f"⏱️ Tested page '{label}' in {page_elapsed:.2f} seconds.")

    return pages_tex_content, lighthouse_tex_content


async def run_tests():  # noqa: C901
    """Missing docstring."""
    os.environ["TEST__LIGHTHOUSE"] = "true"
    os.environ["AUTH__OTP"] = "true"

    port = os.environ.get("EXTERNAL_DB_PORT", "5432")
    user = os.environ.get("PG__USER", "postgres")
    pwd = os.environ.get("PG__PASSWORD", "postgres")
    db = os.environ.get("PG__DBNAME", "decimark")

    os.environ["PG_SYNC_URL"] = (
        f"postgresql+psycopg://{user}:{pwd}@localhost:{port}/{db}"
    )
    os.environ["PG_ASYNC_URL"] = (
        f"postgresql+psycopg://{user}:{pwd}@localhost:{port}/{db}"
    )
    os.environ["REDIS_URL"] = (
        f"redis://localhost:{os.environ.get('EXTERNAL_REDIS_PORT', '6379')}/0"
    )
    os.environ["TEST__SMTP"] = "true"
    # Using 4 workers to ensure Hypercorn doesn't choke under Playwright concurrency
    server_process = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "hypercorn",
            "main:app",
            "--bind",
            f"0.0.0.0:{PORT}",
            "--workers",
            "4",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    start_time = time.time()
    server_ready = False
    while time.time() - start_time < 30:
        """Fix missing docstring."""
        try:
            resp = httpx.get(BASE_URL, follow_redirects=True)
            if resp.status_code == 200:
                server_ready = True
                break
            print(f"Server not ready, status code: {resp.status_code}, {resp.text}")
            time.sleep(0.5)
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            time.sleep(0.5)

    if not server_ready:
        server_process.kill()
        raise RuntimeError("Server did not start")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            contexts = {}
            for theme in ["light", "dark"]:
                ctx = await browser.new_context(base_url=BASE_URL)
                await ctx.add_cookies(
                    [{"name": "theme", "value": theme, "url": BASE_URL}],
                )
                await ctx.route(
                    "**/api/settings/theme*",
                    make_theme_route_handler(theme),
                )
                contexts[theme] = ctx

            os.makedirs(SCREENSHOTS_OUTPUT_DIR, exist_ok=True)
            pages_tex_content = ""
            lighthouse_tex_content = ""

            total_test_start = time.time()

            print(
                f"Executing with hardware-optimized concurrency: {concurrency_limit} viewports max.",
            )

            # 1. Unauthenticated Pages
            unauth_pages = [p for p in PAGES if not p[2]]
            pages_tex_content, lighthouse_tex_content = await process_pages(
                contexts,
                unauth_pages,
                pages_tex_content,
                lighthouse_tex_content,
            )

            # 2. Login both contexts
            with open("seed_credentials.json") as f:
                user = json.load(f)[0]

            for theme in ["light", "dark"]:
                ctx = contexts[theme]
                page = await ctx.new_page()
                page.set_default_timeout(90000)
                await page.goto("/login")
                await page.fill('input[name="identifier"]', user["username"])
                await page.fill('input[name="password"]', user["password"])
                await page.fill('input[name="captcha_answer"]', "1234")
                await page.click('input[type="submit"]')
                await page.wait_for_selector(
                    'input[name="otp"]',
                    state="visible",
                    timeout=30000,
                )
                await page.fill('input[name="otp"]', "000000")
                await page.click('input[type="submit"]')
                await page.wait_for_url("**/bookmarks*")
                await page.close()
            print("Logged in successfully in both contexts.")

            # 3. Authenticated Pages
            auth_pages = [p for p in PAGES if p[2]]
            pages_tex_content, lighthouse_tex_content = await process_pages(
                contexts,
                auth_pages,
                pages_tex_content,
                lighthouse_tex_content,
            )

            # Write outputs
            with open(TEX_MAIN_PAPER_DIR / Path("pages.tex"), "w") as f:
                f.write(pages_tex_content)
            print("LaTeX file created: pages.tex")

            with open(TEX_MAIN_PAPER_DIR / Path("lighthouse_reports.tex"), "w") as f:
                f.write(lighthouse_tex_content)
            print("LaTeX file created: lighthouse_reports.tex")

            total_test_elapsed = time.time() - total_test_start
            print(f"🎉 All tests fully completed in {total_test_elapsed:.2f} seconds!")

    finally:
        server_process.kill()
        server_process.wait()


if __name__ == "__main__":
    asyncio.run(run_tests())
