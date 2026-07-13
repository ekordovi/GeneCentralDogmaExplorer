#!/usr/bin/env python3
"""Verify the v1 learning loop locally, with optional deployed API checks."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gene_dogma.sequence_utils import simulate_dna_mutation  # noqa: E402


EXAMPLE_CACHE = PROJECT_ROOT / "data" / "example_gene_cache.json"
FAMOUS_SYMBOLS = ("HBB", "BRCA1", "TP53")
API_NAME = "Gene Central Dogma Explorer API"
DATA_SOURCE = "Ensembl REST"


def load_example() -> dict:
    return json.loads(EXAMPLE_CACHE.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_offline_hbb() -> None:
    data = load_example()
    gene = data["gene"]
    sequences = data["sequences"]
    require(gene["display_name"] == "HBB", "Bundled example must open to HBB.")
    require(sequences["coding_dna"], "HBB example must include coding DNA.")
    require(sequences["protein"], "HBB example must include protein sequence.")
    require(data.get("selected_transcript"), "HBB example must include a selected transcript.")

    missense = simulate_dna_mutation(sequences["coding_dna"], "20 A>T")
    nonsense = simulate_dna_mutation(sequences["coding_dna"], "19 G>T")
    frameshift = simulate_dna_mutation(sequences["coding_dna"], "20del")
    require(missense["effect"] == "missense", "HBB 20 A>T should teach missense.")
    require(nonsense["effect"] == "nonsense", "HBB 19 G>T should teach nonsense.")
    require(frameshift["effect"] == "frameshift", "HBB 20del should teach frameshift.")


def request_json(base_url: str, path: str, query: dict[str, str] | None = None) -> object:
    url = base_url.rstrip("/") + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    with urllib.request.urlopen(url, timeout=30) as response:
        status = getattr(response, "status", 200)
        require(200 <= status < 300, f"{url} returned HTTP {status}.")
        return json.loads(response.read().decode("utf-8"))


def verify_api(base_url: str, live_lookup: bool) -> None:
    health = request_json(base_url, "/api/health")
    require(isinstance(health, dict) and health.get("status") == "ok", "Health endpoint must return ok.")
    require(health.get("name") == API_NAME, "Health endpoint must identify the Gene Central Dogma Explorer API.")
    require(bool(health.get("version")), "Health endpoint must include API version.")
    require(health.get("data_source") == DATA_SOURCE, "Health endpoint must identify Ensembl REST data source.")

    info = request_json(base_url, "/api/info")
    require(isinstance(info, dict) and info.get("name") == API_NAME, "Info endpoint must identify the API.")
    require(bool(info.get("educational_disclaimer")), "Info endpoint must include educational disclaimer.")
    require("/api/gene" in set(info.get("endpoints") or []), "Info endpoint must list public API endpoints.")

    example = request_json(base_url, "/api/example")
    require(isinstance(example, dict) and example["gene"]["display_name"] == "HBB", "API example must return HBB.")

    famous = request_json(base_url, "/api/famous-examples")
    symbols = {item["symbol"] for item in famous}
    for symbol in FAMOUS_SYMBOLS:
        require(symbol in symbols, f"Famous examples must include {symbol}.")

    mutation_request = urllib.request.Request(
        base_url.rstrip("/") + "/api/mutation",
        data=json.dumps({"coding_dna": example["sequences"]["coding_dna"], "change": "20 A>T"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(mutation_request, timeout=30) as response:
        mutation = json.loads(response.read().decode("utf-8"))
    require(mutation["effect"] == "missense", "Mutation API should classify HBB 20 A>T as missense.")

    if live_lookup:
        for symbol in FAMOUS_SYMBOLS:
            data = request_json(base_url, "/api/gene", {"symbol": symbol, "species": "homo_sapiens"})
            require(data["gene"]["display_name"].upper() == symbol, f"Live lookup should return {symbol}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Gene Central Dogma Explorer v1 behavior.")
    parser.add_argument("--base-url", help="Optional deployed or local API base URL, such as http://127.0.0.1:8000.")
    parser.add_argument("--live-lookup", action="store_true", help="Also verify live HBB, BRCA1, and TP53 lookup.")
    args = parser.parse_args()

    try:
        verify_offline_hbb()
        print("ok offline HBB + mutation learning loop")
        if args.base_url:
            verify_api(args.base_url, args.live_lookup)
            print(f"ok API checks at {args.base_url.rstrip('/')}")
    except (AssertionError, urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
