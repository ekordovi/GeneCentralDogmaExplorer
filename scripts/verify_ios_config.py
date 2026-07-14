#!/usr/bin/env python3
"""Verify iOS API URL configuration is safe for Debug and Release builds."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PBXPROJ = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer.xcodeproj" / "project.pbxproj"
INFO_PLIST = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "Info.plist"
CONTENT_VIEW = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "ContentView.swift"
API_CLIENT = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "GeneDogmaAPIClient.swift"


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
    api_client = API_CLIENT.read_text(encoding="utf-8")

    require("$(GENE_DOGMA_API_BASE_URL)" in plist, "Info.plist must read GeneDogmaAPIBaseURL from build settings.")

    debug_url = extract_config_value(project, "Debug")
    release_url = extract_config_value(project, "Release")

    require(debug_url == "http://127.0.0.1:8000", "Debug API URL should point to local simulator backend.")
    require(release_url.startswith("https://"), "Release API URL must be HTTPS.")
    require("127.0.0.1" not in release_url and "localhost" not in release_url, "Release API URL must not point to localhost.")
    require("DisclosureGroup(\"Show sequence preview\")" in content, "Dogma sequence previews must be opt-in.")
    require('DisclosureGroup("Show \\(title) letters")' in content, "Key sequence letters must be opt-in.")
    require("sequenceSummaryText" in content, "iOS app must summarize sequences before revealing letters.")
    require('@AppStorage("gene_explore_learning_mode")' in content, "iOS Explore must persist Beginner/Advanced mode.")
    require('Picker("Learning mode"' in content, "iOS Explore must expose a Beginner/Advanced mode picker.")
    require("Switch to Advanced mode to inspect isoforms" in content, "iOS Beginner mode must hide advanced gene details.")
    require("savedGeneStudyPack(savedGenes:" in content, "iOS saved genes must include a shareable study pack.")
    require("Share Study Pack" in content, "iOS saved genes must expose the study-pack share action.")
    require("Version and data source" in content, "iOS About must show version and data-source context.")
    require("https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html" in content, "iOS About must link to public support page.")
    require("https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html" in content, "iOS About must link to public privacy page.")
    require("userDefaults.stringArray(forKey: savedGenesKey)" in api_client, "iOS saved genes must load from local storage.")
    require("userDefaults.set(savedGenes, forKey: savedGenesKey)" in api_client, "iOS saved genes must persist to local storage.")

    print("ok iOS API URL build settings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
