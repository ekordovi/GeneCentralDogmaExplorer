import unittest

from gene_dogma.visualization import dogma_visual_html, sequence_ribbon


class VisualizationTests(unittest.TestCase):
    def test_sequence_ribbon_contains_base_blocks(self):
        html = sequence_ribbon("ATGC", "dna")
        self.assertIn("sequence-ribbon", html)
        self.assertIn(">A<", html)
        self.assertIn(">T<", html)

    def test_dogma_visual_contains_gene_and_steps(self):
        data = {
            "gene": {
                "display_name": "TEST",
                "seq_region_name": "1",
                "start": 10,
                "end": 30,
                "strand": 1,
                "biotype": "protein_coding",
                "assembly_name": "ASM",
            },
            "selected_transcript": {"id": "TX1"},
            "selected_translation": {"id": "P1"},
            "sequences": {
                "genomic_dna": "ATGC",
                "transcript_cdna": "ATGC",
                "coding_mrna": "AUGC",
                "protein": "MA",
            },
        }
        html = dogma_visual_html(data)
        self.assertIn("TEST", html)
        self.assertIn("Genomic DNA", html)
        self.assertIn("Protein product", html)


if __name__ == "__main__":
    unittest.main()
