#!/usr/bin/env python3
"""Verify local product-readiness promises from the v1 business plan."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
API = ROOT / "api.py"
README = ROOT / "README.md"
SUPPORT_HTML = ROOT / "docs" / "support.html"
PRIVACY_HTML = ROOT / "docs" / "privacy.html"
SUPPORT_MD = ROOT / "docs" / "support.md"
PRIVACY_MD = ROOT / "docs" / "privacy_policy.md"
APP_STORE_READINESS = ROOT / "docs" / "app_store_readiness.md"
APP_STORE_METADATA = ROOT / "docs" / "app_store_metadata.md"
BUSINESS_PLAN = ROOT / "docs" / "business_plan.md"
DEMO_SCRIPT = ROOT / "docs" / "demo_script.md"
SCREENSHOTS = ROOT / "app_store" / "screenshots.md"
REVIEW_NOTES = ROOT / "app_store" / "review_notes.txt"
PRIVACY_ANSWERS = ROOT / "app_store" / "privacy_answers.md"
EXAMPLE_CACHE = ROOT / "data" / "example_gene_cache.json"
IOS_CONTENT = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "ContentView.swift"
IOS_API_CLIENT = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "GeneDogmaAPIClient.swift"
IOS_PRIVACY = ROOT / "iOS" / "GeneCentralDogmaExplorer" / "GeneCentralDogmaExplorer" / "PrivacyInfo.xcprivacy"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_all(text: str, phrases: list[str], label: str) -> None:
    for phrase in phrases:
        require(phrase in text, f"{label} is missing: {phrase}")


def require_any(text: str, phrases: list[str], label: str) -> None:
    require(any(phrase in text for phrase in phrases), f"{label} is missing one of: {', '.join(phrases)}")


def verify_first_30_seconds(app: str, example: dict) -> None:
    require(example["gene"]["display_name"] == "HBB", "Bundled offline example must be HBB.")
    require(example["sequences"]["coding_dna"], "Bundled HBB example must include coding DNA.")
    require(example["sequences"]["protein"], "Bundled HBB example must include protein sequence.")
    require_all(
        app,
        [
            "Start with a real gene story",
            "Explore HBB",
            "Try BRCA1",
            "Try TP53",
            "Search any gene",
            "Simulate mutation",
            "Tap a gene card to inspect it",
            "Approximate chromosome position",
            "Exon model visual",
            "Tap a central dogma step",
        ],
        "Streamlit first-screen loop",
    )
    require_all(
        app,
        [
            "render_web_trust_strip",
            "Education only",
            "Trusted data",
            "Offline start",
            "Privacy first",
            "No accounts, payments, ads, or analytics",
        ],
        "Streamlit first-screen trust strip",
    )


def verify_learning_loop(app: str, ios: str, ios_api_client: str) -> None:
    require_all(
        app,
        [
            "Compare two mutations",
            "Two-minute mutation lesson",
            "Teacher guide",
            "Exit ticket",
            "Beginner mode",
            "Advanced mode",
            "Show readable",
            "Show more",
        ],
        "Streamlit learning loop",
    )
    require_all(
        ios,
        [
            "DisclosureGroup(\"Show sequence preview\")",
            "DisclosureGroup(\"Show \\(title) letters\")",
            "ShareLink",
            "Gene Central Dogma Report",
            "@AppStorage(\"gene_explore_learning_mode\")",
            "Picker(\"Learning mode\"",
            "Switch to Advanced mode to inspect isoforms",
            "savedGeneStudyPack(savedGenes:",
            "Share Study Pack",
            "Version and data source",
            "Support page",
            "Privacy policy",
        ],
        "iOS mobile learning loop",
    )
    require_all(
        ios_api_client,
        [
            "userDefaults.stringArray(forKey: savedGenesKey)",
            "userDefaults.set(savedGenes, forKey: savedGenesKey)",
            "persistSavedGenes()",
        ],
        "iOS saved-gene persistence",
    )
    require_all(
        app,
        [
            "saved_gene_study_pack",
            "Download Study Pack",
            "Review prompts",
            "saved_gene_study_pack.md",
        ],
        "Streamlit study-pack export",
    )


def verify_trust_and_scope(texts: dict[str, str]) -> None:
    trust_bundle = "\n".join(texts.values()).lower()
    require_all(
        trust_bundle,
        [
            "education only",
            "not medical advice",
            "clinical variant interpretation",
            "ensembl rest",
            "no accounts",
            "no gene-search terms",
            "mutation payloads",
            "privacy_safe_logging",
        ],
        "trust/privacy/source package",
    )
    require_any(
        trust_bundle,
        ["does not parse hgvs", "does not parse hgvs notation"],
        "mutation scope",
    )
    require_any(
        trust_bundle,
        ["does not query clinvar", "query clinvar"],
        "mutation scope",
    )
    require("diagnose disease" not in trust_bundle, "Product copy must not claim disease diagnosis.")
    require("treat disease" not in trust_bundle, "Product copy must not claim treatment use.")
    require("use for medical decisions" not in trust_bundle, "Product copy must not imply medical decision support.")
    require("make medical decisions" not in trust_bundle, "Product copy must not imply medical decision support.")


def verify_demo_script(demo_script: str) -> None:
    require_all(
        demo_script,
        [
            "Two-Minute Walkthrough",
            "built-in HBB example",
            "central dogma path",
            "compare two edits",
            "missense",
            "nonsense",
            "teacher guide",
            "downloadable study pack",
            "Ensembl REST attribution",
            "not clinical variant interpretation",
            "python scripts/verify_product_readiness.py",
        ],
        "demo script",
    )


def verify_business_plan(business_plan: str) -> None:
    require_all(
        business_plan,
        [
            "Business Plan",
            "Positioning",
            "First 30 Seconds",
            "Version 1 Scope",
            "Trust Package",
            "Distribution Plan",
            "Backend Cost Plan",
            "Success Criteria",
            "Current Blocking Items Before App Store",
            "Apple Developer Program enrollment",
            "Production FastAPI backend URL over HTTPS",
            "Live release verification for HBB, BRCA1, and TP53",
            "serious biology/software",
        ],
        "business plan",
    )


def verify_app_store_artifacts(texts: dict[str, str], ios_privacy: str) -> None:
    require_all(
        "\n".join(texts.values()),
        [
            "Gene Central Dogma Explorer",
            "Support URL",
            "Privacy URL",
            "Start with HBB",
            "Compare Mutations",
            "Study and Save",
            "HBB offline demo",
            "live lookup",
            "teacher guide",
        ],
        "App Store artifact package",
    )
    require("NSPrivacyCollectedDataTypes" in ios_privacy, "Privacy manifest must declare collected data types.")
    require("<array/>" in ios_privacy, "Privacy manifest should declare no collected data for v1.")


def verify_api_contract(api: str) -> None:
    require_all(
        api,
        [
            "/api/health",
            "/api/info",
            "/api/example",
            "/api/famous-examples",
            "/api/gene",
            "/api/mutation",
            "EDUCATIONAL_DISCLAIMER",
            "SUPPORT_URL",
            "PRIVACY_URL",
            "privacy_safe_logging",
            "GENE_DOGMA_ALLOWED_ORIGINS",
        ],
        "API public contract",
    )


def main() -> int:
    try:
        app = read(APP)
        api = read(API)
        ios = read(IOS_CONTENT)
        ios_api_client = read(IOS_API_CLIENT)
        ios_privacy = read(IOS_PRIVACY)
        example = json.loads(read(EXAMPLE_CACHE))
        docs = {
            "README": read(README),
            "support.html": read(SUPPORT_HTML),
            "privacy.html": read(PRIVACY_HTML),
            "support.md": read(SUPPORT_MD),
            "privacy_policy.md": read(PRIVACY_MD),
            "app_store_readiness.md": read(APP_STORE_READINESS),
            "app_store_metadata.md": read(APP_STORE_METADATA),
            "business_plan.md": read(BUSINESS_PLAN),
            "demo_script.md": read(DEMO_SCRIPT),
            "screenshots.md": read(SCREENSHOTS),
            "review_notes.txt": read(REVIEW_NOTES),
            "privacy_answers.md": read(PRIVACY_ANSWERS),
        }

        verify_first_30_seconds(app, example)
        verify_learning_loop(app, ios, ios_api_client)
        verify_trust_and_scope({**docs, "api.py": api})
        verify_business_plan(docs["business_plan.md"])
        verify_demo_script(docs["demo_script.md"])
        verify_app_store_artifacts(docs, ios_privacy)
        verify_api_contract(api)
        print("ok local product readiness")
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"product readiness failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
