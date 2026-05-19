"""
download_fontawesome.py: Download FontAwesome CSS and Webfonts.

DISCLAIMER: Generated with Claude.

1. Hits the GitHub API to find the latest non-prerelease Font Awesome release.
2. Downloads the `*-web.zip` asset from that release.
3. Extracts it to a temp folder.
4. Copies css/all.css  → src/static/stylesheets/downloaded/fontawesome.css
5. Copies webfonts/*   → src/static/assets/fonts/
6. Rewrites `url("../webfonts/` → `url("/static/assets/fonts/` in the CSS.
"""

import io
import json
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile

# ── config ────────────────────────────────────────────────────────────────────

GITHUB_API_RELEASES = "https://api.github.com/repos/FortAwesome/Font-Awesome/releases"

CSS_DEST = "src/static/stylesheets/downloaded/fontawesome.css"
FONTS_DEST = "src/static/assets/fonts"

# The path FastAPI serves fonts from (used to rewrite @font-face src URLs)
FONTS_SERVE_PATH = "/static/assets/fonts"

# ── helpers ───────────────────────────────────────────────────────────────────


def get_json(url: str) -> object:
    """GETs a URL and parses the response as JSON."""
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "User-Agent": "download_fontawesome.py/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


def download_bytes(url: str, label: str = "") -> bytes:
    """Downloads a URL and returns raw bytes, with a basic progress label."""
    print(f"  ↓ Downloading {label or url} ...")
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={"User-Agent": "download_fontawesome.py/1.0"},
    )
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        data = resp.read()
    print(f"  ✓ {len(data) / 1_048_576:.2f} MB received")
    return data


def find_latest_release(releases: list) -> dict:
    """Returns the first release that is not a prerelease and not a draft."""
    for release in releases:
        if not release.get("prerelease") and not release.get("draft"):
            return release
    raise RuntimeError("No stable (non-prerelease) release found.")


def find_web_zip_asset(assets: list) -> dict:
    """Finds the *-web.zip asset in a release's asset list."""
    for asset in assets:
        name = asset["name"]
        if name.endswith("-web.zip") or (
            name.startswith("fontawesome") and name.endswith(".zip") and "web" in name
        ):
            return asset
    raise RuntimeError(
        "Could not find a *-web.zip asset in this release.\n"
        f"Available assets: {[a['name'] for a in assets]}",
    )


def rewrite_font_urls(css: str, serve_path: str) -> str:
    """Replaces all occurrences of `url("../webfonts/` with `url("{serve_path}/` in a CSS string. Handles both single and double quotes."""
    # match url("../webfonts/  or  url('../webfonts/
    pattern = re.compile(r"""url\((['"]?)\.\.\/webfonts\/""")
    replacement = rf"url(\g<1>{serve_path}/"
    rewritten, count = re.subn(pattern, replacement, css)
    print(f"  ✓ Rewrote {count} font URL(s) → {serve_path}/...")
    return rewritten


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    # ── 1. find latest stable release ────────────────────────────────────────
    print("── Step 1: Fetching release list from GitHub API...")
    releases = get_json(GITHUB_API_RELEASES)
    release = find_latest_release(releases)  # type: ignore
    tag = release["tag_name"]
    print(f"  ✓ Latest stable release: {tag}")

    # ── 2. find & download the web zip ───────────────────────────────────────
    print("\n── Step 2: Finding *-web.zip asset...")
    asset = find_web_zip_asset(release["assets"])
    zip_name = asset["name"]
    zip_url = asset["browser_download_url"]
    print(f"  ✓ Found asset: {zip_name}")

    zip_bytes = download_bytes(zip_url, label=zip_name)

    # ── 3. extract to a temp folder ──────────────────────────────────────────
    print("\n── Step 3: Extracting zip...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(tmp_dir)
        print("  ✓ Extracted to temp dir")

        # the zip typically contains a single top-level folder, e.g. fontawesome-free-7.x.x-web/
        entries = os.listdir(tmp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
            extracted_root = os.path.join(tmp_dir, entries[0])
        else:
            extracted_root = tmp_dir
        print(f"  ✓ Root folder: {os.path.basename(extracted_root)}")

        src_css_path = os.path.join(extracted_root, "css", "all.css")
        src_fonts_dir = os.path.join(extracted_root, "webfonts")

        if not os.path.isfile(src_css_path):
            raise FileNotFoundError(
                f"Expected css/all.css inside zip, not found at: {src_css_path}",
            )
        if not os.path.isdir(src_fonts_dir):
            raise FileNotFoundError(
                f"Expected webfonts/ dir inside zip, not found at: {src_fonts_dir}",
            )

        # ── 4. copy & rewrite CSS ────────────────────────────────────────────
        print("\n── Step 4: Processing CSS...")
        os.makedirs(os.path.dirname(CSS_DEST), exist_ok=True)

        with open(src_css_path, encoding="utf-8") as f:
            css = f.read()

        css = rewrite_font_urls(css, FONTS_SERVE_PATH)

        with open(CSS_DEST, "w", encoding="utf-8") as f:
            f.write(css)
        print(f"  ✓ CSS saved to: {CSS_DEST}")

        # ── 5. copy webfonts ─────────────────────────────────────────────────
        print("\n── Step 5: Copying webfonts...")
        os.makedirs(FONTS_DEST, exist_ok=True)

        font_files = os.listdir(src_fonts_dir)
        for fname in font_files:
            src = os.path.join(src_fonts_dir, fname)
            dest = os.path.join(FONTS_DEST, fname)
            shutil.copy2(src, dest)
            print(f"  ✓ {fname}")

        print(f"\n  → {len(font_files)} font file(s) copied to: {FONTS_DEST}")

    # tmp_dir (and everything in it) is automatically deleted here

    print("\n── All done! ✓")
    print(f"   CSS   → {CSS_DEST}")
    print(f"   Fonts → {FONTS_DEST}")


if __name__ == "__main__":
    main()
