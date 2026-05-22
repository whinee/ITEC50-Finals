"""
download_css.py: Downloads a hardcoded list of CSS files into a hardcoded output folder.

DISCLAIMER: Generate with Claude.

Skips files that already exist (won't re-download unless you delete them).
"""

import os
import urllib.request
from urllib.parse import urlparse

# ── config ────────────────────────────────────────────────────────────────────

OUTPUT_FOLDER = "./src/static/stylesheets/downloaded"

CSS_FILES = [
    "https://cdn.jsdelivr.net/npm/browserux.css@latest/browserux.css",
]

# ── helpers ───────────────────────────────────────────────────────────────────


def filename_from_url(url: str) -> str:
    """Derives a filename from the last path segment of the URL."""
    return os.path.basename(urlparse(url).path)


def download_file(url: str, dest_path: str) -> None:
    """Downloads a single file from url and saves it to dest_path."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported URL scheme: {parsed.scheme!r}. Only http and https URLs are allowed.",
        )

    print(f"  ↓ Downloading: {url}")
    headers = {"User-Agent": "Mozilla/5.0 download_css.py/1.0"}
    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    with (
        urllib.request.urlopen(req) as response,  # noqa: S310
        open(dest_path, "wb") as out,
    ):
        out.write(response.read())
    print(f"  ✓ Saved to:    {dest_path}")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output folder: {os.path.abspath(OUTPUT_FOLDER)}\n")

    success, skipped, failed = 0, 0, 0

    for url in CSS_FILES:
        filename = filename_from_url(url)
        if not filename.endswith(".css"):
            print(f"  ✗ Skipped (not a .css URL): {url}\n")
            failed += 1
            continue

        dest_path = os.path.join(OUTPUT_FOLDER, filename)

        if os.path.exists(dest_path):
            print(f"  ─ Already exists, skipping: {filename}")
            skipped += 1
            continue

        try:
            download_file(url, dest_path)
            success += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ Failed: {url}\n    Reason: {e}")
            failed += 1

        print()

    print("─" * 50)
    print(f"Done! {success} downloaded, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()
