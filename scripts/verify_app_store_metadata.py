#!/usr/bin/env python3
"""Check App Store metadata files for basic length and required-link rules."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "app_store" / "metadata" / "en-US"
SUPPORT_URL = "https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html"
PRIVACY_URL = "https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html"

LIMITS = {
    "name.txt": 30,
    "subtitle.txt": 30,
    "promotional_text.txt": 170,
    "keywords.txt": 100,
    "description.txt": 4000,
    "release_notes.txt": 4000,
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for filename, limit in LIMITS.items():
        value = read(METADATA / filename)
        require(value, f"{filename} is empty.")
        require(len(value) <= limit, f"{filename} is {len(value)} characters; limit is {limit}.")

    support = read(METADATA / "support_url.txt")
    privacy = read(METADATA / "privacy_url.txt")
    require(support == SUPPORT_URL, "support_url.txt does not match the public support URL.")
    require(privacy == PRIVACY_URL, "privacy_url.txt does not match the public privacy URL.")

    description = read(METADATA / "description.txt").lower()
    forbidden = ["diagnose", "diagnosis", "treatment guidance", "clinical variant interpretation"]
    require("not medical advice" in description, "description.txt must include the medical disclaimer.")
    require("education only" in description, "description.txt must clearly frame the app as educational.")
    for phrase in forbidden:
        if phrase in {"diagnosis", "treatment guidance", "clinical variant interpretation"}:
            continue
        require(phrase not in description, f"description.txt should not imply medical use: {phrase}")

    print("ok App Store metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
