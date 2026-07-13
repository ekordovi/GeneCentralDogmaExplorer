from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gene_dogma import EnsemblError, fetch_gene_central_dogma
from gene_dogma.sequence_utils import simulate_dna_mutation


PROJECT_ROOT = Path(__file__).parent
EXAMPLE_CACHE = PROJECT_ROOT / "data" / "example_gene_cache.json"
LOGGER = logging.getLogger("gene_dogma.api")

GeneFetcher = Callable[[str, str, str | None], dict[str, Any]]

API_VERSION = os.getenv("GENE_DOGMA_API_VERSION", "1.0.0")
API_ENVIRONMENT = os.getenv("GENE_DOGMA_API_ENV", "development")
API_NAME = "Gene Central Dogma Explorer API"
DATA_SOURCE = "Ensembl REST"
EDUCATIONAL_DISCLAIMER = "Educational use only. Not medical advice or clinical variant interpretation."
SUPPORT_URL = "https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html"
PRIVACY_URL = "https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html"
PUBLIC_ENDPOINTS = (
    "/api/health",
    "/api/info",
    "/api/example",
    "/api/famous-examples",
    "/api/gene",
    "/api/mutation",
)

GENE_NOT_FOUND_MESSAGE = (
    "We couldn't find that gene symbol for this species. Try checking the spelling "
    "or selecting another species."
)
LIVE_LOOKUP_UNAVAILABLE_MESSAGE = (
    "Live gene lookup is temporarily unavailable. Try the bundled HBB example, or try again soon."
)
GENE_LOOKUP_FAILED_MESSAGE = (
    "We couldn't load that gene right now. Try HBB, BRCA1, TP53, or the bundled HBB example."
)
MUTATION_FORMAT_MESSAGE = "Try a simple coding-DNA edit like 20 A>T, 20del, or 20insA."
MUTATION_MISMATCH_MESSAGE = (
    "That edit does not match the selected coding DNA. Try one of the suggested examples for this gene."
)

FAMOUS_GENE_EXAMPLES: list[dict[str, str]] = [
    {
        "symbol": "HBB",
        "name": "Hemoglobin beta",
        "why": "Classic DNA-to-protein consequence example for sickle hemoglobin and beta-globin biology.",
    },
    {
        "symbol": "BRCA1",
        "name": "DNA repair",
        "why": "Shows how genome repair genes connect sequence changes to cancer-risk biology.",
    },
    {
        "symbol": "TP53",
        "name": "Tumor suppressor",
        "why": "A famous stress-response gene often called the guardian of the genome.",
    },
    {
        "symbol": "CFTR",
        "name": "Ion channel",
        "why": "Connects coding sequence, membrane-protein function, and cystic fibrosis.",
    },
    {
        "symbol": "INS",
        "name": "Insulin",
        "why": "A beginner-friendly hormone gene with a familiar protein product.",
    },
    {
        "symbol": "APOE",
        "name": "Lipid transport",
        "why": "Common protein variants connect lipid biology with Alzheimer disease risk.",
    },
]


class MutationRequest(BaseModel):
    coding_dna: str = Field(..., min_length=1)
    change: str = Field(..., min_length=1, examples=["20 A>T", "20del", "20insA"])


def load_example() -> dict[str, Any]:
    return json.loads(EXAMPLE_CACHE.read_text())


def default_gene_fetcher(symbol: str, species: str, transcript_id: str | None) -> dict[str, Any]:
    return fetch_gene_central_dogma(
        symbol=symbol,
        species=species,
        preferred_transcript_id=transcript_id,
    )


def parse_allowed_origins(raw_origins: str | None) -> list[str]:
    if not raw_origins:
        return ["*"]
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


def friendly_mutation_error(exc: ValueError) -> str:
    message = str(exc)
    if "Reference base mismatch" in message:
        return MUTATION_MISMATCH_MESSAGE
    if "Position must be" in message:
        return message
    return MUTATION_FORMAT_MESSAGE


def service_metadata() -> dict[str, Any]:
    return {
        "name": API_NAME,
        "version": API_VERSION,
        "environment": API_ENVIRONMENT,
        "data_source": DATA_SOURCE,
        "educational_disclaimer": EDUCATIONAL_DISCLAIMER,
        "support_url": SUPPORT_URL,
        "privacy_url": PRIVACY_URL,
        "privacy_safe_logging": True,
        "endpoints": list(PUBLIC_ENDPOINTS),
    }


def request_log_category(status_code: int) -> str:
    if status_code < 400:
        return "ok"
    if status_code < 500:
        return "client_error"
    return "server_error"


def create_app(
    gene_fetcher: GeneFetcher = default_gene_fetcher,
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(
        title=API_NAME,
        version=API_VERSION,
        description="Backend API for the native iOS Gene Central Dogma Explorer app.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or parse_allowed_origins(os.getenv("GENE_DOGMA_ALLOWED_ORIGINS")),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def privacy_safe_request_log(request: Request, call_next):
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            LOGGER.info(
                "api_request method=%s path=%s status=%s category=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                status_code,
                request_log_category(status_code),
                duration_ms,
            )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        metadata = service_metadata()
        return {
            "status": "ok",
            "name": metadata["name"],
            "version": metadata["version"],
            "environment": metadata["environment"],
            "data_source": metadata["data_source"],
        }

    @app.get("/api/info")
    def info() -> dict[str, Any]:
        return service_metadata()

    @app.get("/api/example")
    def example() -> dict[str, Any]:
        return load_example()

    @app.get("/api/famous-examples")
    def famous_examples() -> list[dict[str, str]]:
        return FAMOUS_GENE_EXAMPLES

    @app.get("/api/gene")
    def gene(
        symbol: str = Query(..., min_length=1, max_length=40),
        species: str = Query("homo_sapiens", min_length=1, max_length=80),
        transcript_id: str | None = Query(None, min_length=1, max_length=80),
    ) -> dict[str, Any]:
        try:
            return gene_fetcher(symbol.strip(), species.strip(), transcript_id.strip() if transcript_id else None)
        except EnsemblError as exc:
            raise HTTPException(status_code=502, detail=LIVE_LOOKUP_UNAVAILABLE_MESSAGE) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=GENE_NOT_FOUND_MESSAGE) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=GENE_LOOKUP_FAILED_MESSAGE) from exc

    @app.post("/api/mutation")
    def mutation(request: MutationRequest) -> dict[str, Any]:
        try:
            return simulate_dna_mutation(request.coding_dna, request.change)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=friendly_mutation_error(exc)) from exc

    return app


app = create_app()
