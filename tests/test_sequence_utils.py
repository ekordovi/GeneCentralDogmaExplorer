import unittest

from gene_dogma.sequence_utils import gc_content, reverse_complement, simulate_dna_mutation, to_mrna, translate_dna


class SequenceUtilsTests(unittest.TestCase):
    def test_to_mrna_replaces_thymine(self):
        self.assertEqual(to_mrna("ATGC"), "AUGC")

    def test_gc_content(self):
        self.assertEqual(gc_content("GGCCAA"), 66.67)

    def test_reverse_complement(self):
        self.assertEqual(reverse_complement("ATGC"), "GCAT")

    def test_translate_dna(self):
        self.assertEqual(translate_dna("ATGGAGTAA"), "ME*")

    def test_simulate_substitution_labels_missense(self):
        result = simulate_dna_mutation("ATGGAGTAA", "5 A>T")
        self.assertEqual(result["original_codon"], "GAG")
        self.assertEqual(result["mutated_codon"], "GTG")
        self.assertEqual(result["original_amino_acid"], "E")
        self.assertEqual(result["mutated_amino_acid"], "V")
        self.assertEqual(result["effect"], "missense")

    def test_simulate_deletion_labels_frameshift(self):
        result = simulate_dna_mutation("ATGGAGTAA", "5del")
        self.assertEqual(result["effect"], "frameshift")

    def test_simulate_rejects_reference_mismatch(self):
        with self.assertRaises(ValueError):
            simulate_dna_mutation("ATGGAGTAA", "5 C>T")


if __name__ == "__main__":
    unittest.main()
