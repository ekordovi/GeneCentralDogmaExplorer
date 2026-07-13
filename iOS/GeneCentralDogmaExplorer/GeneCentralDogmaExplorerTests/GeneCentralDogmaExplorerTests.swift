import XCTest
@testable import GeneCentralDogmaExplorer

final class GeneCentralDogmaExplorerTests: XCTestCase {
    func testBundledHBBDecodes() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        XCTAssertEqual(response.gene.displayName, "HBB")
        XCTAssertEqual(response.query.species, "homo_sapiens")
        XCTAssertFalse(response.sequences.codingDna.isEmpty)
        XCTAssertFalse(response.sequences.protein.isEmpty)
    }

    func testMutationResultDecodes() throws {
        let json = """
        {
          "input": "5 A>T",
          "mutation_type": "substitution",
          "position": 5,
          "codon_number": 2,
          "original_base": "A",
          "original_codon": "GAG",
          "mutated_codon": "GTG",
          "original_amino_acid": "E",
          "mutated_amino_acid": "V",
          "effect": "missense",
          "mutated_dna": "ATGGTGTAA"
        }
        """.data(using: .utf8)!
        let result = try JSONDecoder().decode(MutationResult.self, from: json)
        XCTAssertEqual(result.effect, "missense")
        XCTAssertEqual(result.originalCodon, "GAG")
        XCTAssertEqual(result.mutatedCodon, "GTG")
    }

    func testBundledHBBMutationExamplesAreTeachable() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        XCTAssertEqual(exampleSubstitutionChange(response.sequences.codingDna), "20 A>T")
        XCTAssertEqual(exampleMissenseChange(response.sequences.codingDna), "20 A>T")
        XCTAssertEqual(exampleNonsenseChange(response.sequences.codingDna), "19 G>T")
        XCTAssertEqual(exampleDeletionChange(response.sequences.codingDna), "20del")
        XCTAssertEqual(mutationEffectExplanation("missense"), "One amino acid changed. This can matter if that spot is important for the protein.")
        XCTAssertEqual(mutationEffectExplanation("nonsense"), "The edit creates a stop signal, so translation may stop early.")
    }

    func testBundledHBBMutationLessonExamplesAreTeachable() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        let examples = mutationLessonExamples(codingDNA: response.sequences.codingDna)
        XCTAssertEqual(examples.map(\.title), ["Missense", "Nonsense", "Frameshift"])
        XCTAssertEqual(examples.map(\.change), ["20 A>T", "19 G>T", "20del"])
        XCTAssertEqual(examples.map(\.effect), ["missense", "nonsense", "frameshift"])
        XCTAssertEqual(examples[0].codonChange, "GAG -> GTG")
        XCTAssertEqual(examples[0].aminoAcidChange, "E -> V")
        XCTAssertEqual(examples[1].codonChange, "GAG -> TAG")
        XCTAssertEqual(examples[1].aminoAcidChange, "E -> *")
    }
}
