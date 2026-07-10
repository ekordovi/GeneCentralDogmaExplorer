#!/usr/bin/env python3
"""Strict pre-TestFlight checks for public release readiness."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[0]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from verify_ios_config import PBXPROJ, extract_config_value  # noqa: E402
from verify_v1 import verify_api  # noqa: E402


PUBLIC_URLS = {
    "support": "https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html",
    "privacy": "https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html",
}
PLACEHOLDER_MARKERS = (
    "your-api-host.example",
    "example.com",
    "example.org",
    "example.net",
    "<",
    ">",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def release_api_url() -> str:
    project = PBXPROJ.read_text(encoding="utf-8")
    return extract_config_value(project, "Release").rstrip("/")


def verify_public_url(label: str, url: str) -> None:
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        if exc.code != 405:
            raise
        with urllib.request.urlopen(url, timeout=20) as response:
            status = getattr(response, "status", 200)
    require(200 <= status < 300, f"{label} page returned HTTP {status}: {url}")


def verify_production_url(url: str) -> None:
    lower_url = url.lower()
    require(url.startswith("https://"), "Release API URL must use HTTPS.")
    require("localhost" not in lower_url, "Release API URL must not point to localhost.")
    require("127.0.0.1" not in lower_url, "Release API URL must not point to 127.0.0.1.")
    for marker in PLACEHOLDER_MARKERS:
        require(marker not in lower_url, f"Release API URL is still a placeholder: {url}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the app is ready for TestFlight or App Store review.")
    parser.add_argument("--live-lookup", action="store_true", help="Also verify live HBB, BRCA1, and TP53 lookup.")
    parser.add_argument(
        "--skip-public-pages",
        action="store_true",
        help="Skip public GitHub Pages support/privacy URL checks.",
    )
    args = parser.parse_args()

    try:
        api_base_url = release_api_url()
        verify_production_url(api_base_url)

        if not args.skip_public_pages:
            for label, url in PUBLIC_URLS.items():
                verify_public_url(label, url)
            print("ok public support and privacy pages")

        verify_api(api_base_url, args.live_lookup)
        print(f"ok release API checks at {api_base_url}")
        if args.live_lookup:
            print("ok live release lookup for HBB, BRCA1, and TP53")
    except (AssertionError, KeyError, TimeoutError, ValueError, urllib.error.URLError) as exc:
        print(f"release readiness failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
