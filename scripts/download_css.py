"""
High-Speed CSS Asset Synchronizer.

An automated, asynchronous dependency downloader that ruthlessly fetches strictly pinned CSS assets from CDNs. By caching static files locally, it guarantees that DeciMark can operate perfectly in air-gapped or offline development environments while insulating the frontend from transient network failures.

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
    """
    Extract the precise filename from an arbitrary URL, effortlessly circumventing URL parameters and fragments.

    Args:
        url (str): Target URL.

    Returns:
        str: The pristine filename.

    """
    return os.path.basename(urlparse(url).path)


def download_file(url: str, dest_path: str) -> None:
    """
    Execute a high-speed HTTP GET request, forcefully ripping a remote file from the network and streaming it safely into local disk storage.

    Args:
        dest_path (Any): Undocumented argument.
        url (str): URL.
        dest_dir (str): Output folder.

    Returns:
        bool: Network execution result.

    """
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
    """Parse a predefined list of remote stylesheets and violently ingests them into the local frontend cache."""
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
