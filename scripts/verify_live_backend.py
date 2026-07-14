#!/usr/bin/env python3
"""Verify a deployed backend is ready for TestFlight live lookup."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_NAME = "Gene Central Dogma Explorer API"
DATA_SOURCE = "Ensembl REST"
REQUIRED_LIVE_SYMBOLS = ("HBB", "BRCA1", "TP53")
PLACEHOLDER_MARKERS = (
    "your-api-host.example",
    "example.com",
    "example.org",
    "example.net",
    "<",
    ">",
)
FRIENDLY_NOT_FOUND = "We couldn't find that gene symbol for this species"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def normalize_base_url(raw_url: str) -> str:
    return raw_url.strip().rstrip("/")


def validate_base_url(base_url: str, allow_local: bool = False) -> None:
    lower_url = base_url.lower()
    if allow_local and (lower_url.startswith("http://127.0.0.1") or lower_url.startswith("http://localhost")):
        return
    require(base_url.startswith("https://"), "Production backend URL must use HTTPS.")
    require("localhost" not in lower_url, "Production backend URL must not use localhost.")
    require("127.0.0.1" not in lower_url, "Production backend URL must not use 127.0.0.1.")
    for marker in PLACEHOLDER_MARKERS:
        require(marker not in lower_url, f"Backend URL is still a placeholder: {base_url}")


def endpoint_url(base_url: str, path: str, query: dict[str, str] | None = None) -> str:
    url = normalize_base_url(base_url) + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    return url


def request_json(base_url: str, path: str, query: dict[str, str] | None = None) -> Any:
    url = endpoint_url(base_url, path, query)
    with urllib.request.urlopen(url, timeout=35) as response:
        status = getattr(response, "status", 200)
        require(200 <= status < 300, f"{url} returned HTTP {status}.")
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url: str, path: str, payload: dict[str, Any]) -> Any:
    request = urllib.request.Request(
        endpoint_url(base_url, path),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        status = getattr(response, "status", 200)
        require(200 <= status < 300, f"{request.full_url} returned HTTP {status}.")
        return json.loads(response.read().decode("utf-8"))


def request_error_detail(base_url: str, path: str, query: dict[str, str]) -> tuple[int, str]:
    try:
        request_json(base_url, path, query)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return exc.code, body
        return exc.code, str(payload.get("detail", ""))
    raise AssertionError("Invalid lookup unexpectedly succeeded.")


def verify_metadata(base_url: str) -> None:
    health = request_json(base_url, "/api/health")
    require(isinstance(health, dict), "Health endpoint must return a JSON object.")
    require(health.get("status") == "ok", "Health endpoint must return status ok.")
    require(health.get("name") == API_NAME, "Health endpoint must identify the API.")
    require(bool(health.get("version")), "Health endpoint must include an API version.")
    require(health.get("data_source") == DATA_SOURCE, "Health endpoint must identify Ensembl REST.")

    info = request_json(base_url, "/api/info")
    require(isinstance(info, dict), "Info endpoint must return a JSON object.")
    require(info.get("name") == API_NAME, "Info endpoint must identify the API.")
    require(info.get("privacy_safe_logging") is True, "Info endpoint must advertise privacy-safe logging.")
    require("not medical advice" in str(info.get("educational_disclaimer", "")).lower(), "Info endpoint must include the educational disclaimer.")
    endpoints = set(info.get("endpoints") or [])
    for endpoint in ("/api/health", "/api/info", "/api/example", "/api/famous-examples", "/api/gene", "/api/mutation"):
        require(endpoint in endpoints, f"Info endpoint must list {endpoint}.")


def verify_famous_examples(base_url: str) -> None:
    famous = request_json(base_url, "/api/famous-examples")
    require(isinstance(famous, list), "Famous examples endpoint must return a list.")
    symbols = {str(item.get("symbol", "")).upper() for item in famous if isinstance(item, dict)}
    for symbol in REQUIRED_LIVE_SYMBOLS:
        require(symbol in symbols, f"Famous examples must include {symbol}.")


def verify_live_gene_lookup(base_url: str) -> None:
    for symbol in REQUIRED_LIVE_SYMBOLS:
        data = request_json(base_url, "/api/gene", {"symbol": symbol, "species": "homo_sapiens"})
        require(isinstance(data, dict), f"{symbol} lookup must return a JSON object.")
        gene = data.get("gene") or {}
        sequences = data.get("sequences") or {}
        require(str(gene.get("display_name", "")).upper() == symbol, f"Live lookup should return {symbol}.")
        require(data.get("selected_transcript"), f"{symbol} lookup must include a selected transcript.")
        if symbol == "HBB":
            require(bool(sequences.get("coding_dna")), "Live HBB lookup must include coding DNA.")
            require(bool(sequences.get("protein")), "Live HBB lookup must include a protein sequence.")


def verify_mutation_comparison(base_url: str) -> None:
    example = request_json(base_url, "/api/example")
    coding_dna = ((example.get("sequences") or {}).get("coding_dna") or "").strip()
    require(bool(coding_dna), "Bundled API example must include HBB coding DNA for mutation checks.")

    missense = post_json(base_url, "/api/mutation", {"coding_dna": coding_dna, "change": "20 A>T"})
    nonsense = post_json(base_url, "/api/mutation", {"coding_dna": coding_dna, "change": "19 G>T"})
    require(missense.get("effect") == "missense", "Mutation API must classify HBB 20 A>T as missense.")
    require(nonsense.get("effect") == "nonsense", "Mutation API must classify HBB 19 G>T as nonsense.")
    require(missense.get("effect") != nonsense.get("effect"), "Mutation comparison must show two different effects.")


def verify_friendly_failure(base_url: str) -> None:
    status, detail = request_error_detail(
        base_url,
        "/api/gene",
        {"symbol": "NOTAREALGENEZZZ", "species": "homo_sapiens"},
    )
    require(status == 404, f"Unknown gene should return HTTP 404, got {status}.")
    require(FRIENDLY_NOT_FOUND in detail, "Unknown gene should return learner-friendly not-found copy.")


def verify_backend(base_url: str, *, require_live_lookup: bool = True, allow_local: bool = False) -> None:
    base_url = normalize_base_url(base_url)
    validate_base_url(base_url, allow_local=allow_local)
    verify_metadata(base_url)
    verify_famous_examples(base_url)
    verify_mutation_comparison(base_url)
    verify_friendly_failure(base_url)
    if require_live_lookup:
        verify_live_gene_lookup(base_url)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify deployed Gene Central Dogma Explorer backend readiness.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("GENE_DOGMA_API_BASE_URL", ""),
        help="Deployed backend base URL. Defaults to GENE_DOGMA_API_BASE_URL.",
    )
    parser.add_argument(
        "--skip-live-lookup",
        action="store_true",
        help="Skip live /api/gene checks for HBB, BRCA1, and TP53.",
    )
    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Allow http://127.0.0.1 or http://localhost for local backend testing.",
    )
    args = parser.parse_args()

    try:
        require(bool(args.base_url.strip()), "Set --base-url or GENE_DOGMA_API_BASE_URL.")
        verify_backend(
            args.base_url,
            require_live_lookup=not args.skip_live_lookup,
            allow_local=args.allow_local,
        )
    except (AssertionError, KeyError, TimeoutError, ValueError, urllib.error.URLError) as exc:
        print(f"live backend verification failed: {exc}", file=sys.stderr)
        return 1

    base_url = normalize_base_url(args.base_url)
    print(f"ok live backend contract at {base_url}")
    if not args.skip_live_lookup:
        print("ok live lookup for HBB, BRCA1, and TP53")
    print("ok mutation comparison and friendly failure behavior")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
