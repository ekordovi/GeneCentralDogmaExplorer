#!/usr/bin/env python3
"""Check GitHub workflows enforce the release/product verification gates."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_HEALTH_WORKFLOW = ROOT / ".github" / "workflows" / "api-health.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    api_health = API_HEALTH_WORKFLOW.read_text(encoding="utf-8")
    ci = CI_WORKFLOW.read_text(encoding="utf-8")

    require("GENE_DOGMA_API_BASE_URL" in api_health, "API health workflow must support base URL configuration.")
    require("GENE_DOGMA_API_HEALTH_URL" in api_health, "API health workflow must keep health URL compatibility.")
    require("python scripts/verify_v1.py --base-url" in api_health, "API health workflow must run the API contract verifier.")
    require("curl " not in api_health, "API health workflow should not fall back to curl-only checks.")

    require("python scripts/verify_workflows.py" in ci, "CI must run workflow verification.")
    require("python scripts/verify_product_readiness.py" in ci, "CI must run local product readiness verification.")
    print("ok workflow verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
