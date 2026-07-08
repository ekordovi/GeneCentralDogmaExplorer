"""Ensembl REST client for gene -> RNA -> protein central-dogma lookup."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .sequence_utils import summarize_sequence, to_mrna


ENSEMBL_REST = "https://rest.ensembl.org"


class EnsemblError(RuntimeError):
    """Raised when Ensembl lookup or sequence retrieval fails."""


@dataclass(frozen=True)
class EnsemblClient:
    """Tiny JSON client for the Ensembl REST API."""

    base_url: str = ENSEMBL_REST
    timeout: int = 20

    def _request(self, path: str, params: dict[str, Any] | None, accept: str) -> str:
        query = f"?{urlencode(params or {})}" if params else ""
        request = Request(
            f"{self.base_url}{path}{query}",
            headers={"Content-Type": accept, "Accept": accept},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8").strip()
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            raise EnsemblError(f"Ensembl request failed: {exc.code} {body}") from exc
        except URLError as exc:
            raise EnsemblError(f"Could not reach Ensembl REST: {exc.reason}") from exc
        except TimeoutError as exc:
            raise EnsemblError("Ensembl request timed out.") from exc

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return json.loads(self._request(path, params, "application/json"))

    def get_text(self, path: str, params: dict[str, Any] | None = None) -> str:
        return self._request(path, params, "text/plain")

    def lookup_symbol(self, species: str, symbol: str, expand: bool = True) -> dict[str, Any]:
        params = {"expand": 1 if expand else 0}
        return self.get_json(f"/lookup/symbol/{species}/{symbol}", params=params)

    def sequence(self, stable_id: str, sequence_type: str) -> str:
        return self.get_text(f"/sequence/id/{stable_id}", params={"type": sequence_type})


def _transcript_rank(transcript: dict[str, Any]) -> tuple[int, int, int]:
    is_canonical = 0 if transcript.get("is_canonical") else 1
    has_translation = 0 if transcript.get("Translation") else 1
    length = -(int(transcript.get("length") or 0))
    return (is_canonical, has_translation, length)


def choose_transcript(gene: dict[str, Any], preferred_transcript_id: str | None = None) -> dict[str, Any] | None:
    transcripts = gene.get("Transcript") or []
    if not transcripts:
        return None
    if preferred_transcript_id:
        for transcript in transcripts:
            if transcript.get("id") == preferred_transcript_id:
                return transcript
    return sorted(transcripts, key=_transcript_rank)[0]


def _safe_sequence(client: EnsemblClient, stable_id: str | None, sequence_type: str) -> str:
    if not stable_id:
        return ""
    try:
        return client.sequence(stable_id, sequence_type)
    except EnsemblError:
        return ""


def fetch_gene_central_dogma(
    symbol: str,
    species: str = "homo_sapiens",
    preferred_transcript_id: str | None = None,
    client: EnsemblClient | None = None,
) -> dict[str, Any]:
    """Fetch gene, transcript, cDNA/CDS, and protein information from Ensembl."""

    client = client or EnsemblClient()
    gene = client.lookup_symbol(species, symbol, expand=True)
    transcript = choose_transcript(gene, preferred_transcript_id)
    translation = (transcript or {}).get("Translation") or {}

    gene_id = gene.get("id", "")
    transcript_id = (transcript or {}).get("id", "")
    protein_id = translation.get("id", "")

    genomic_dna = _safe_sequence(client, gene_id, "genomic")
    cdna = _safe_sequence(client, transcript_id, "cdna")
    cds = _safe_sequence(client, transcript_id, "cds")
    protein = _safe_sequence(client, protein_id, "protein")

    return {
        "query": {"symbol": symbol, "species": species},
        "gene": {
            "id": gene_id,
            "display_name": gene.get("display_name", symbol),
            "description": gene.get("description", ""),
            "aliases": gene.get("synonyms") or gene.get("aliases") or [],
            "biotype": gene.get("biotype", ""),
            "assembly_name": gene.get("assembly_name", ""),
            "seq_region_name": gene.get("seq_region_name", ""),
            "start": gene.get("start"),
            "end": gene.get("end"),
            "strand": gene.get("strand"),
            "species": species,
            "source": gene.get("source", "Ensembl"),
            "object_type": gene.get("object_type", "Gene"),
        },
        "transcripts": gene.get("Transcript") or [],
        "selected_transcript": transcript or {},
        "selected_translation": translation,
        "sequences": {
            "genomic_dna": genomic_dna,
            "pre_mrna_proxy": to_mrna(genomic_dna),
            "transcript_cdna": cdna,
            "coding_dna": cds,
            "coding_mrna": to_mrna(cds),
            "protein": protein,
        },
        "summaries": {
            "genomic_dna": summarize_sequence(genomic_dna, "dna"),
            "transcript_cdna": summarize_sequence(cdna, "dna"),
            "coding_dna": summarize_sequence(cds, "dna"),
            "protein": summarize_sequence(protein, "protein"),
        },
        "source": {
            "database": "Ensembl REST",
            "lookup_endpoint": "/lookup/symbol/:species/:symbol?expand=1",
            "sequence_endpoint": "/sequence/id/:id?type=...",
        },
    }
