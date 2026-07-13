#!/usr/bin/env python3
"""Verify iOS API URL configuration is safe for Debug and Release builds."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PBXPROJ = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer.xcodeproj" / "project.pbxproj"
INFO_PLIST = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "Info.plist"
CONTENT_VIEW = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "ContentView.swift"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_config_value(project: str, config_name: str) -> str:
    for line in project.splitlines():
        if f"/* {config_name} */" not in line or f"name = {config_name};" not in line:
            continue
        match = re.search(r'GENE_DOGMA_API_BASE_URL = "([^"]+)";', line)
        if match:
            return match.group(1)
    raise AssertionError(f"{config_name} GENE_DOGMA_API_BASE_URL is missing.")


def main() -> int:
    project = PBXPROJ.read_text(encoding="utf-8")
    plist = INFO_PLIST.read_text(encoding="utf-8")
    content = CONTENT_VIEW.read_text(encoding="utf-8")

    require("$(GENE_DOGMA_API_BASE_URL)" in plist, "Info.plist must read GeneDogmaAPIBaseURL from build settings.")

    debug_url = extract_config_value(project, "Debug")
    release_url = extract_config_value(project, "Release")

    require(debug_url == "http://127.0.0.1:8000", "Debug API URL should point to local simulator backend.")
    require(release_url.startswith("https://"), "Release API URL must be HTTPS.")
    require("127.0.0.1" not in release_url and "localhost" not in release_url, "Release API URL must not point to localhost.")
    require("DisclosureGroup(\"Show sequence preview\")" in content, "Dogma sequence previews must be opt-in.")
    require('DisclosureGroup("Show \\(title) letters")' in content, "Key sequence letters must be opt-in.")
    require("sequenceSummaryText" in content, "iOS app must summarize sequences before revealing letters.")

    print("ok iOS API URL build settings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
