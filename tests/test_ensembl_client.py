import unittest

from gene_dogma.ensembl_client import choose_transcript, fetch_gene_central_dogma


class FakeClient:
    def lookup_symbol(self, species, symbol, expand=True):
        return {
            "id": "GENE1",
            "display_name": symbol,
            "description": "Example gene",
            "biotype": "protein_coding",
            "assembly_name": "TESTASM",
            "seq_region_name": "1",
            "start": 1,
            "end": 99,
            "strand": 1,
            "source": "Fake",
            "object_type": "Gene",
            "Transcript": [
                {
                    "id": "TX_NONCANON",
                    "display_name": "example-002",
                    "biotype": "protein_coding",
                    "is_canonical": 0,
                    "length": 120,
                    "Translation": {"id": "PROT2", "length": 3},
                },
                {
                    "id": "TX_CANON",
                    "display_name": "example-001",
                    "biotype": "protein_coding",
                    "is_canonical": 1,
                    "length": 90,
                    "Translation": {"id": "PROT1", "length": 3},
                },
            ],
        }

    def sequence(self, stable_id, sequence_type):
        sequences = {
            ("GENE1", "genomic"): "ATGGAGTAA",
            ("TX_CANON", "cdna"): "ATGGAGTAA",
            ("TX_CANON", "cds"): "ATGGAGTAA",
            ("PROT1", "protein"): "ME",
            ("TX_NONCANON", "cdna"): "ATGAAATAG",
            ("TX_NONCANON", "cds"): "ATGAAATAG",
            ("PROT2", "protein"): "MK",
        }
        return sequences[(stable_id, sequence_type)]


class EnsemblClientTests(unittest.TestCase):
    def test_choose_transcript_prefers_canonical(self):
        gene = FakeClient().lookup_symbol("fake_species", "FAKE")
        self.assertEqual(choose_transcript(gene)["id"], "TX_CANON")

    def test_choose_transcript_prefers_longest_when_other_ranks_match(self):
        gene = {
            "Transcript": [
                {"id": "TX_SHORT", "is_canonical": 0, "length": 900, "Translation": {"id": "P1"}},
                {"id": "TX_LONG", "is_canonical": 0, "length": 1000, "Translation": {"id": "P2"}},
            ]
        }
        self.assertEqual(choose_transcript(gene)["id"], "TX_LONG")

    def test_choose_transcript_honors_preferred_id(self):
        gene = FakeClient().lookup_symbol("fake_species", "FAKE")
        self.assertEqual(choose_transcript(gene, "TX_NONCANON")["id"], "TX_NONCANON")

    def test_fetch_gene_central_dogma(self):
        result = fetch_gene_central_dogma("FAKE", "fake_species", client=FakeClient())
        self.assertEqual(result["gene"]["id"], "GENE1")
        self.assertEqual(result["selected_transcript"]["id"], "TX_CANON")
        self.assertEqual(result["sequences"]["coding_mrna"], "AUGGAGUAA")
        self.assertEqual(result["sequences"]["protein"], "ME")
        self.assertEqual(result["summaries"]["coding_dna"]["length"], 9)


if __name__ == "__main__":
    unittest.main()
