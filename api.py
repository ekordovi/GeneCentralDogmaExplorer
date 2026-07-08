from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gene_dogma import EnsemblError, fetch_gene_central_dogma
from gene_dogma.sequence_utils import simulate_dna_mutation


PROJECT_ROOT = Path(__file__).parent
EXAMPLE_CACHE = PROJECT_ROOT / "data" / "example_gene_cache.json"

GeneFetcher = Callable[[str, str, str | None], dict[str, Any]]

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


def create_app(
    gene_fetcher: GeneFetcher = default_gene_fetcher,
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Gene Central Dogma Explorer API",
        version="1.0.0",
        description="Backend API for the native iOS Gene Central Dogma Explorer app.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or parse_allowed_origins(os.getenv("GENE_DOGMA_ALLOWED_ORIGINS")),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Gene lookup failed: {exc}") from exc

    @app.post("/api/mutation")
    def mutation(request: MutationRequest) -> dict[str, Any]:
        try:
            return simulate_dna_mutation(request.coding_dna, request.change)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
