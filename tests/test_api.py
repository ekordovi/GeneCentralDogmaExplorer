import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from api import (
    GENE_LOOKUP_FAILED_MESSAGE,
    GENE_NOT_FOUND_MESSAGE,
    LIVE_LOOKUP_UNAVAILABLE_MESSAGE,
    MUTATION_MISMATCH_MESSAGE,
    create_app,
    parse_allowed_origins,
)
from gene_dogma import EnsemblError


def fake_gene(symbol: str, species: str, transcript_id: str | None = None) -> dict:
    protein = "" if symbol == "NCRNA" else "ME"
    translation = {} if symbol == "NCRNA" else {"id": "PROT1", "length": 2}
    return {
        "query": {"symbol": symbol, "species": species},
        "gene": {
            "id": "GENE1",
            "display_name": symbol,
            "description": "Fake gene",
            "aliases": ["FAKE_ALIAS"],
            "biotype": "lncRNA" if symbol == "NCRNA" else "protein_coding",
            "assembly_name": "TESTASM",
            "seq_region_name": "1",
            "start": 1,
            "end": 9,
            "strand": 1,
            "species": species,
            "source": "Fake",
            "object_type": "Gene",
        },
        "transcripts": [
            {
                "id": transcript_id or "TX1",
                "display_name": "fake-001",
                "biotype": "lncRNA" if symbol == "NCRNA" else "protein_coding",
                "is_canonical": 1,
                "length": 9,
                "Translation": translation,
            }
        ],
        "selected_transcript": {"id": transcript_id or "TX1", "display_name": "fake-001"},
        "selected_translation": translation,
        "sequences": {
            "genomic_dna": "ATGGAGTAA",
            "pre_mrna_proxy": "AUGGAGUAA",
            "transcript_cdna": "ATGGAGTAA",
            "coding_dna": "" if symbol == "NCRNA" else "ATGGAGTAA",
            "coding_mrna": "" if symbol == "NCRNA" else "AUGGAGUAA",
            "protein": protein,
        },
        "summaries": {},
        "source": {"database": "Fake"},
    }


def failing_gene(symbol: str, species: str, transcript_id: str | None = None) -> dict:
    raise EnsemblError("Fake Ensembl outage")


def missing_gene(symbol: str, species: str, transcript_id: str | None = None) -> dict:
    raise LookupError("Internal lookup text with database details")


def broken_gene(symbol: str, species: str, transcript_id: str | None = None) -> dict:
    raise RuntimeError("Secret stack detail")


def test_example_returns_hbb_fixture():
    client = TestClient(create_app(fake_gene))
    response = client.get("/api/example")
    assert response.status_code == 200
    assert response.json()["gene"]["display_name"] == "HBB"


def test_famous_examples_include_study_genes():
    client = TestClient(create_app(fake_gene))
    response = client.get("/api/famous-examples")
    assert response.status_code == 200
    symbols = {item["symbol"] for item in response.json()}
    assert {"HBB", "BRCA1", "TP53", "CFTR", "INS", "APOE"}.issubset(symbols)


def test_gene_lookup_returns_current_json_shape():
    client = TestClient(create_app(fake_gene))
    response = client.get("/api/gene", params={"symbol": "FAKE", "species": "fake_species", "transcript_id": "TX2"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["gene"]["display_name"] == "FAKE"
    assert payload["gene"]["aliases"] == ["FAKE_ALIAS"]
    assert payload["selected_transcript"]["id"] == "TX2"
    assert payload["sequences"]["protein"] == "ME"


def test_gene_lookup_reports_ensembl_failure():
    client = TestClient(create_app(failing_gene))
    response = client.get("/api/gene", params={"symbol": "FAKE"})
    assert response.status_code == 502
    assert response.json()["detail"] == LIVE_LOOKUP_UNAVAILABLE_MESSAGE
    assert "Fake Ensembl outage" not in response.text


def test_gene_lookup_reports_missing_symbol_without_raw_details():
    client = TestClient(create_app(missing_gene))
    response = client.get("/api/gene", params={"symbol": "NOPE"})
    assert response.status_code == 404
    assert response.json()["detail"] == GENE_NOT_FOUND_MESSAGE
    assert "database details" not in response.text


def test_gene_lookup_reports_generic_failure_without_raw_exception():
    client = TestClient(create_app(broken_gene))
    response = client.get("/api/gene", params={"symbol": "FAKE"})
    assert response.status_code == 500
    assert response.json()["detail"] == GENE_LOOKUP_FAILED_MESSAGE
    assert "Secret stack detail" not in response.text


def test_non_coding_gene_can_return_without_protein():
    client = TestClient(create_app(fake_gene))
    response = client.get("/api/gene", params={"symbol": "NCRNA"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["gene"]["biotype"] == "lncRNA"
    assert payload["sequences"]["protein"] == ""


def test_mutation_success():
    client = TestClient(create_app(fake_gene))
    response = client.post("/api/mutation", json={"coding_dna": "ATGGAGTAA", "change": "5 A>T"})
    assert response.status_code == 200
    assert response.json()["effect"] == "missense"


def test_mutation_validation_error():
    client = TestClient(create_app(fake_gene))
    response = client.post("/api/mutation", json={"coding_dna": "ATGGAGTAA", "change": "5 C>T"})
    assert response.status_code == 400
    assert response.json()["detail"] == MUTATION_MISMATCH_MESSAGE
    assert "Reference base mismatch" not in response.text


def test_parse_allowed_origins_defaults_to_dev_wildcard():
    assert parse_allowed_origins(None) == ["*"]
    assert parse_allowed_origins("  ") == ["*"]


def test_parse_allowed_origins_accepts_comma_separated_domains():
    assert parse_allowed_origins("https://gene.example, https://app.example") == [
        "https://gene.example",
        "https://app.example",
    ]
