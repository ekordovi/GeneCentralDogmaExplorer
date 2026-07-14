import XCTest
@testable import GeneCentralDogmaExplorer

final class GeneCentralDogmaExplorerTests: XCTestCase {
    func temporaryDefaults(named name: String = #function) -> UserDefaults {
        let suiteName = "GeneCentralDogmaExplorerTests.\(name).\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suiteName)!
        defaults.removePersistentDomain(forName: suiteName)
        return defaults
    }

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

    func testTeacherLessonStepsAreClassroomReady() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        let steps = teacherLessonSteps(response: response)

        XCTAssertEqual(steps.map(\.title), ["Hook", "Trace the path", "Compare edits"])
        XCTAssertTrue(steps[0].prompt.contains("HBB"))
        XCTAssertTrue(steps[1].prompt.contains("DNA is stored"))
        XCTAssertTrue(steps[2].prompt.contains("missense versus nonsense"))
    }

    func testStoryReportIsShareableAndEducational() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        let report = storyReport(response: response)

        XCTAssertTrue(report.contains("Gene Central Dogma Report: HBB"))
        XCTAssertTrue(report.contains("Selected transcript"))
        XCTAssertTrue(report.contains("This report is educational and is not medical advice."))
    }

    func testSavedGeneStudyPackIsShareableAndEducational() throws {
        let studyPack = savedGeneStudyPack(savedGenes: ["HBB", "BRCA1", "TP53"])

        XCTAssertTrue(studyPack.contains("Gene Central Dogma Explorer study pack"))
        XCTAssertTrue(studyPack.contains("1. HBB"))
        XCTAssertTrue(studyPack.contains("2. BRCA1"))
        XCTAssertTrue(studyPack.contains("DNA -> RNA -> protein"))
        XCTAssertTrue(studyPack.contains("missense and nonsense"))
        XCTAssertTrue(studyPack.contains("educational only and is not medical advice"))
    }

    func testSequenceDisplaySummariesKeepRawLettersOptIn() throws {
        let summary = sequenceSummaryText("ATGGAGTAA")
        let preview = sequencePreviewText("ATGGAGTAA", limit: 6)

        XCTAssertEqual(summary, "9 letters · starts ATGGAGTAA · ends ATGGAGTAA")
        XCTAssertEqual(preview, "ATGGAG\n...\n3 more symbols hidden")
        XCTAssertEqual(sequencePreviewText("", limit: 6), "No sequence returned.")
    }

    func testLocalMutationSimulationMatchesTeachingExamples() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        let missense = try simulateLocalMutation(codingDNA: response.sequences.codingDna, change: "20 A>T")
        let nonsense = try simulateLocalMutation(codingDNA: response.sequences.codingDna, change: "19 G>T")
        let frameshift = try simulateLocalMutation(codingDNA: response.sequences.codingDna, change: "20del")
        let insertion = try simulateLocalMutation(codingDNA: response.sequences.codingDna, change: "20insA")

        XCTAssertEqual(missense.effect, "missense")
        XCTAssertEqual(missense.originalCodon, "GAG")
        XCTAssertEqual(missense.mutatedCodon, "GTG")
        XCTAssertEqual(missense.originalAminoAcid, "E")
        XCTAssertEqual(missense.mutatedAminoAcid, "V")
        XCTAssertEqual(nonsense.effect, "nonsense")
        XCTAssertEqual(nonsense.mutatedCodon, "TAG")
        XCTAssertEqual(frameshift.effect, "frameshift")
        XCTAssertEqual(insertion.effect, "frameshift")
    }

    func testLocalMutationSimulationRejectsReferenceMismatch() throws {
        let response = try LocalExampleStore.loadHBBExample(bundle: Bundle(for: GeneDogmaViewModel.self))
        XCTAssertThrowsError(try simulateLocalMutation(codingDNA: response.sequences.codingDna, change: "20 C>T"))
    }

    func testDemoLaunchConfigurationParsesScreenshotTabs() throws {
        XCTAssertEqual(DemoLaunchConfiguration(arguments: ["app", "--gene-demo-tab=explore"]).initialTab, 1)
        XCTAssertEqual(DemoLaunchConfiguration(arguments: ["app", "--screenshot-tab=mutation"]).initialTab, 2)
        XCTAssertEqual(DemoLaunchConfiguration(arguments: ["app", "--gene-demo-tab=study"]).initialTab, 3)
        XCTAssertEqual(DemoLaunchConfiguration(arguments: ["app", "--gene-demo-tab=saved"]).initialTab, 4)
        XCTAssertEqual(DemoLaunchConfiguration(arguments: ["app", "--gene-demo-tab=about"]).initialTab, 5)
    }

    @MainActor
    func testDemoConfigurationPrimesScreenshotState() throws {
        let viewModel = GeneDogmaViewModel(userDefaults: temporaryDefaults())
        viewModel.applyDemoConfiguration(
            DemoLaunchConfiguration(arguments: ["app", "--gene-demo=screenshots", "--gene-demo-tab=mutation"])
        )

        XCTAssertEqual(viewModel.savedGenes, ["HBB", "BRCA1", "TP53"])
        XCTAssertEqual(viewModel.mutationResult?.effect, "missense")
        XCTAssertEqual(viewModel.comparisonResultA?.effect, "missense")
        XCTAssertEqual(viewModel.comparisonResultB?.effect, "nonsense")
    }

    @MainActor
    func testSavedGenesPersistAcrossViewModelInstances() throws {
        let defaults = temporaryDefaults()
        let firstViewModel = GeneDogmaViewModel(userDefaults: defaults)

        firstViewModel.saveCurrentGene()

        let secondViewModel = GeneDogmaViewModel(userDefaults: defaults)
        XCTAssertEqual(secondViewModel.savedGenes, ["HBB"])
    }

    @MainActor
    func testDemoSavedGenesPersistForScreenshotPreparation() throws {
        let defaults = temporaryDefaults()
        let firstViewModel = GeneDogmaViewModel(userDefaults: defaults)

        firstViewModel.applyDemoConfiguration(DemoLaunchConfiguration(arguments: ["app", "--gene-demo-saved"]))

        let secondViewModel = GeneDogmaViewModel(userDefaults: defaults)
        XCTAssertEqual(secondViewModel.savedGenes, ["HBB", "BRCA1", "TP53"])
    }
}
