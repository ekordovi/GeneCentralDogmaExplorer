import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = GeneDogmaViewModel()
    @State private var selectedTab: Int
    @State private var didApplyDemoConfiguration = false
    private let demoConfiguration: DemoLaunchConfiguration

    init(demoConfiguration: DemoLaunchConfiguration = DemoLaunchConfiguration()) {
        self.demoConfiguration = demoConfiguration
        _selectedTab = State(initialValue: demoConfiguration.initialTab)
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            SearchScreen(viewModel: viewModel, selectedTab: $selectedTab)
                .tabItem { Label("Search", systemImage: "magnifyingglass") }
                .tag(0)

            GeneExploreScreen(viewModel: viewModel)
                .tabItem { Label("Explore", systemImage: "point.3.connected.trianglepath.dotted") }
                .tag(1)

            MutationScreen(viewModel: viewModel)
                .tabItem { Label("Mutation", systemImage: "wand.and.stars") }
                .tag(2)

            StudyQuizScreen(viewModel: viewModel)
                .tabItem { Label("Quiz", systemImage: "questionmark.circle") }
                .tag(3)

            SavedGenesScreen(viewModel: viewModel)
                .tabItem { Label("Saved", systemImage: "bookmark") }
                .tag(4)

            AboutScreen()
                .tabItem { Label("About", systemImage: "info.circle") }
                .tag(5)
        }
        .onAppear {
            guard !didApplyDemoConfiguration else { return }
            didApplyDemoConfiguration = true
            viewModel.applyDemoConfiguration(demoConfiguration)
        }
    }
}

struct SearchScreen: View {
    @ObservedObject var viewModel: GeneDogmaViewModel
    @Binding var selectedTab: Int
    @State private var showSearchFields = false

    var body: some View {
        NavigationStack {
            Form {
                if let response = viewModel.response {
                    Section {
                        GeneSummaryCard(response: response)
                        BeginnerTakeaway(response: response)
                        CompactDogmaPath()
                    } header: {
                        Text(response.gene.displayName.uppercased() == "HBB" ? "Start with HBB" : "Current gene story")
                    } footer: {
                        Text(
                            response.gene.displayName.uppercased() == "HBB"
                                ? "The bundled HBB example works offline and shows how a DNA change can alter beta-globin."
                                : "Use Explore to follow this gene from DNA to RNA to protein."
                        )
                    }
                }

                Section {
                    Button {
                        viewModel.loadBundledExample()
                        selectedTab = 1
                    } label: {
                        Label("Explore HBB", systemImage: "doc.text.magnifyingglass")
                    }

                    Button {
                        Task {
                            await viewModel.loadFamousExample(
                                FamousGeneExample(
                                    symbol: "BRCA1",
                                    name: "DNA repair",
                                    why: "Genome repair gene tied to cancer-risk biology."
                                )
                            )
                            selectedTab = 1
                        }
                    } label: {
                        Label("Try BRCA1", systemImage: "wrench.and.screwdriver")
                    }
                    .disabled(viewModel.isLoading)

                    Button {
                        Task {
                            await viewModel.loadFamousExample(
                                FamousGeneExample(
                                    symbol: "TP53",
                                    name: "Tumor suppressor",
                                    why: "Stress-response gene often called the guardian of the genome."
                                )
                            )
                            selectedTab = 1
                        }
                    } label: {
                        Label("Try TP53", systemImage: "shield")
                    }
                    .disabled(viewModel.isLoading)

                    Button {
                        showSearchFields = true
                    } label: {
                        Label("Search any gene", systemImage: "magnifyingglass")
                    }

                    Button {
                        selectedTab = 2
                    } label: {
                        Label("Simulate a mutation", systemImage: "wand.and.stars")
                    }
                } header: {
                    Text("Choose a path")
                } footer: {
                    Text("You can understand the app from these examples before typing a symbol.")
                }

                if showSearchFields {
                    Section {
                        TextField("Gene symbol", text: $viewModel.symbol)
                            .textInputAutocapitalization(.characters)
                            .autocorrectionDisabled()
                        TextField("Species", text: $viewModel.species)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                        Button {
                            Task { await viewModel.lookupGene() }
                        } label: {
                            Label("Look Up Gene", systemImage: "magnifyingglass")
                        }
                        .disabled(viewModel.isLoading)
                    } header: {
                        Text("Search any gene")
                    } footer: {
                        Text("Try HBB, BRCA1, TP53, CFTR, INS, or APOE. Live lookups use the Gene Central Dogma API and Ensembl.")
                    }
                }

                Section("More examples") {
                    DisclosureGroup("Famous genes") {
                        ForEach(famousGeneExamples) { example in
                            Button {
                                Task {
                                    await viewModel.loadFamousExample(example)
                                    selectedTab = 1
                                }
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("\(example.symbol) - \(example.name)")
                                        .font(.headline)
                                    Text(example.why)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }

                if viewModel.isLoading {
                    ProgressView("Loading gene data")
                }

                if let error = viewModel.errorMessage {
                    ErrorNotice(message: error)
                }

                if let response = viewModel.response {
                    Section("Session") {
                        Button {
                            viewModel.saveCurrentGene()
                        } label: {
                            Label("Save Gene", systemImage: "bookmark")
                        }
                        ShareLink(item: storyReport(response: response)) {
                            Label("Share Report", systemImage: "square.and.arrow.up")
                        }
                    }
                }
            }
            .navigationTitle("Gene Explorer")
        }
    }
}

struct CompactDogmaPath: View {
    var body: some View {
        HStack(spacing: 8) {
            DogmaPill(label: "DNA", color: .blue)
            Image(systemName: "arrow.right")
                .foregroundStyle(.secondary)
            DogmaPill(label: "RNA", color: .teal)
            Image(systemName: "arrow.right")
                .foregroundStyle(.secondary)
            DogmaPill(label: "Protein", color: .pink)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("DNA to RNA to protein")
        .padding(.vertical, 4)
    }
}

struct DogmaPill: View {
    var label: String
    var color: Color

    var body: some View {
        Text(label)
            .font(.caption.weight(.bold))
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(color.gradient)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

struct GeneExploreScreen: View {
    @ObservedObject var viewModel: GeneDogmaViewModel
    @AppStorage("gene_explore_learning_mode") private var learningMode = "Beginner"

    private var isAdvancedMode: Bool {
        learningMode == "Advanced"
    }

    var body: some View {
        NavigationStack {
            List {
                if let response = viewModel.response {
                    Section {
                        Picker("Learning mode", selection: $learningMode) {
                            Text("Beginner").tag("Beginner")
                            Text("Advanced").tag("Advanced")
                        }
                        .pickerStyle(.segmented)
                        Text(isAdvancedMode ? "Advanced mode shows isoforms, expression, structure links, and sequence previews." : "Beginner mode keeps the main story visible first.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Section("Start here") {
                        GeneSummaryCard(response: response)
                        BeginnerTakeaway(response: response)
                    }
                    Section("Central dogma") {
                        DogmaStep(title: "Genomic DNA", detail: "The gene locus before RNA processing.", sequence: response.sequences.genomicDna)
                        DogmaStep(title: "Exons / introns", detail: "Exons remain in the transcript; introns are removed during splicing.", sequence: "")
                        DogmaStep(title: "Spliced mRNA", detail: "A processed RNA-style copy of the transcript.", sequence: response.sequences.transcriptCdna.replacingOccurrences(of: "T", with: "U"))
                        DogmaStep(title: "Coding sequence", detail: "The part read in three-letter codons.", sequence: response.sequences.codingDna)
                        DogmaStep(title: "Amino acid chain", detail: "The translated protein sequence.", sequence: response.sequences.protein)
                    }
                    Section("Teaching context") {
                        Text(diseaseNote(response))
                    }
                    Section("Story report") {
                        Text(storyReport(response: response))
                            .font(.body)
                            .textSelection(.enabled)
                        ShareLink(item: storyReport(response: response)) {
                            Label("Share Report", systemImage: "square.and.arrow.up")
                        }
                    }
                    if isAdvancedMode {
                        Section("Isoforms") {
                            ForEach(response.transcripts) { transcript in
                                TranscriptRow(transcript: transcript)
                            }
                        }
                        Section("Expression context") {
                            Text(expressionNote(response))
                        }
                        Section("Structure mode") {
                            if let proteinID = response.selectedTranslation?.id, !proteinID.isEmpty {
                                Link("Open AlphaFold entry", destination: URL(string: "https://alphafold.ebi.ac.uk/entry/\(proteinID)")!)
                                Link("Search PDB", destination: URL(string: "https://www.rcsb.org/search?request=%7B%22query%22:%7B%22type%22:%22terminal%22,%22service%22:%22full_text%22,%22parameters%22:%7B%22value%22:%22\(proteinID)%22%7D%7D,%22return_type%22:%22entry%22%7D")!)
                            } else {
                                Text("No protein ID returned for structure lookup.")
                            }
                        }
                        Section("Key sequences") {
                            SequencePreview(title: "Coding DNA", sequence: response.sequences.codingDna)
                            SequencePreview(title: "Protein", sequence: response.sequences.protein)
                        }
                    } else {
                        Section("Advanced details") {
                            Text("Switch to Advanced mode to inspect isoforms, expression notes, structure links, and sequence previews.")
                                .foregroundStyle(.secondary)
                        }
                    }
                } else {
                    ContentUnavailableView("No gene loaded", systemImage: "dna", description: Text("Load the HBB demo or search for a gene."))
                }
            }
            .navigationTitle("Explore")
        }
    }
}

struct MutationScreen: View {
    @ObservedObject var viewModel: GeneDogmaViewModel

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Example: 20 A>T", text: $viewModel.mutationText)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                    Button {
                        Task { await viewModel.simulateMutation() }
                    } label: {
                        Label("Simulate Mutation", systemImage: "play.fill")
                    }
                    .disabled(viewModel.isLoading)
                } header: {
                    Text("Coding DNA change")
                } footer: {
                    Text("Supported examples: 20 A>T, 20del, 20insA. This is a simple coding-DNA practice tool, not HGVS parsing, splice prediction, ClinVar interpretation, or medical variant classification.")
                }

                if let result = viewModel.mutationResult {
                    Section("Result") {
                        LabeledContent("Effect", value: result.effect.capitalized)
                        LabeledContent("Original codon", value: result.originalCodon)
                        LabeledContent("Mutated codon", value: result.mutatedCodon)
                        LabeledContent("Original amino acid", value: result.originalAminoAcid)
                        LabeledContent("Changed amino acid", value: result.mutatedAminoAcid)
                        Text(mutationEffectExplanation(result.effect))
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                }

                Section {
                    TextField("Mutation A", text: $viewModel.comparisonMutationA)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                    TextField("Mutation B", text: $viewModel.comparisonMutationB)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                    Button {
                        Task { await viewModel.compareMutations() }
                    } label: {
                        Label("Compare Mutations", systemImage: "arrow.left.arrow.right")
                    }
                    .disabled(viewModel.isLoading)
                } header: {
                    Text("Compare two mutations")
                } footer: {
                    Text("Compare a missense-style edit with a nonsense or frameshift-style edit to see why the effect label changes.")
                }

                if let first = viewModel.comparisonResultA, let second = viewModel.comparisonResultB {
                    Section("Comparison") {
                        MutationComparisonCard(label: "Mutation A", result: first)
                        MutationComparisonCard(label: "Mutation B", result: second)
                        Text(first.effect == second.effect ? "Both edits are classified as \(first.effect)." : "Mutation A is \(first.effect); Mutation B is \(second.effect).")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                }

                if let error = viewModel.errorMessage {
                    ErrorNotice(message: error)
                }
            }
            .navigationTitle("Mutation")
        }
    }
}

struct ErrorNotice: View {
    var message: String

    var body: some View {
        Section {
            Label {
                Text(message)
                    .foregroundStyle(.primary)
            } icon: {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
            }
        }
    }
}

struct MutationComparisonCard: View {
    var label: String
    var result: MutationResult

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.headline)
            LabeledContent("Input", value: result.input)
            LabeledContent("Effect", value: result.effect.capitalized)
            LabeledContent("Codon", value: "\(result.originalCodon) -> \(result.mutatedCodon)")
            LabeledContent("Amino acid", value: "\(result.originalAminoAcid) -> \(result.mutatedAminoAcid)")
            Text(mutationEffectExplanation(result.effect))
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct SavedGenesScreen: View {
    @ObservedObject var viewModel: GeneDogmaViewModel

    var body: some View {
        NavigationStack {
            List {
                if viewModel.savedGenes.isEmpty {
                    ContentUnavailableView("No saved genes", systemImage: "bookmark", description: Text("Save a gene from the Search tab."))
                } else {
                    Section("Study pack") {
                        Text("Share a Markdown review sheet for your saved genes.")
                            .foregroundStyle(.secondary)
                        ShareLink(item: savedGeneStudyPack(savedGenes: viewModel.savedGenes)) {
                            Label("Share Study Pack", systemImage: "square.and.arrow.up")
                        }
                    }
                    ForEach(viewModel.savedGenes, id: \.self) { gene in
                        Button {
                            viewModel.loadSavedGene(gene)
                            Task { await viewModel.lookupGene() }
                        } label: {
                            Label(gene, systemImage: "bookmark")
                        }
                    }
                }
            }
            .navigationTitle("Saved Genes")
        }
    }
}

struct StudyQuizScreen: View {
    @ObservedObject var viewModel: GeneDogmaViewModel

    var body: some View {
        NavigationStack {
            Form {
                if let response = viewModel.response {
                    let questions = quizQuestions(response: response)
                    Section("Study this gene") {
                        Text("Quiz questions update around the loaded gene, so famous examples and saved genes become repeatable practice.")
                            .foregroundStyle(.secondary)
                    }
                    Section("Teacher guide") {
                        Text("A ready two-minute classroom flow for HBB or any loaded gene.")
                            .foregroundStyle(.secondary)
                        ForEach(teacherLessonSteps(response: response)) { step in
                            TeacherLessonStepCard(step: step)
                        }
                        Text("Exit ticket: In one sentence, explain why not every DNA change has the same protein effect.")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    Section("Two-minute mutation lesson") {
                        Text("Compare a missense change, a nonsense stop, and a frameshift before you quiz yourself.")
                            .foregroundStyle(.secondary)
                        let lessonExamples = mutationLessonExamples(codingDNA: response.sequences.codingDna)
                        if lessonExamples.isEmpty {
                            Text("No coding DNA returned, so the mutation lesson is unavailable for this transcript.")
                                .foregroundStyle(.secondary)
                        } else {
                            ForEach(lessonExamples) { example in
                                MutationLessonCard(example: example)
                            }
                        }
                    }
                    ForEach(questions) { question in
                        Section(question.prompt) {
                            ForEach(question.choices, id: \.self) { choice in
                                Button(choice) {
                                    viewModel.quizFeedback = choice == question.answer ? "Correct. \(question.explanation)" : "Not quite. Correct answer: \(question.answer). \(question.explanation)"
                                }
                            }
                        }
                    }
                    if let feedback = viewModel.quizFeedback {
                        Section("Feedback") {
                            Text(feedback)
                        }
                    }
                } else {
                    ContentUnavailableView("No gene loaded", systemImage: "questionmark.circle", description: Text("Load a gene before starting study mode."))
                }
            }
            .navigationTitle("Quiz")
        }
    }
}

struct TeacherLessonStepCard: View {
    var step: TeacherLessonStep

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(step.timing)
                .font(.caption.weight(.bold))
                .foregroundStyle(.blue)
            Text(step.title)
                .font(.headline)
            Text(step.prompt)
                .font(.callout)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct MutationLessonCard: View {
    var example: MutationLessonExample

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(example.title)
                    .font(.headline)
                Spacer()
                Text(example.change)
                    .font(.system(.caption, design: .monospaced).bold())
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(.thinMaterial)
                    .clipShape(Capsule())
            }
            Text(example.explanation)
                .font(.callout)
                .foregroundStyle(.secondary)
            LabeledContent("Effect", value: example.effect)
            LabeledContent("Codon", value: example.codonChange)
            LabeledContent("Amino acid", value: example.aminoAcidChange)
        }
        .padding(.vertical, 4)
    }
}

struct AboutScreen: View {
    var body: some View {
        NavigationStack {
            List {
                Section("Educational use") {
                    Text("Gene Central Dogma Explorer is for education and portfolio demonstration. It is not medical advice, diagnosis, or treatment guidance.")
                }
                Section("Privacy") {
                    Text("The app does not use accounts, ads, payments, or analytics in v1. Live lookups send the gene symbol, species, and optional transcript ID to the app backend, which queries Ensembl.")
                }
                Section("App Store category") {
                    LabeledContent("Category", value: "Education")
                    LabeledContent("Bundle ID", value: "com.evankordovi.GeneCentralDogmaExplorer")
                }
                Section("Roadmap") {
                    Text("Future versions may add curated protein features, ClinVar-style variant lookup, expression atlas data, and cross-species comparison. Version 1 focuses on gene lookup, central-dogma sequence views, simple coding-DNA mutation practice, saved genes, and study questions.")
                }
            }
            .navigationTitle("About")
        }
    }
}

struct GeneSummaryCard: View {
    var response: GeneDogmaResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(response.gene.displayName)
                .font(.title2.bold())
            Text(whyGeneMatters(response))
                .font(.body)
            Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 8) {
                GridRow {
                    Text("Aliases").foregroundStyle(.secondary)
                    Text(response.gene.aliases?.prefix(4).joined(separator: ", ") ?? "None returned")
                }
                GridRow {
                    Text("Species").foregroundStyle(.secondary)
                    Text(response.gene.species ?? response.query.species)
                }
                GridRow {
                    Text("Type").foregroundStyle(.secondary)
                    Text(response.gene.biotype)
                }
                GridRow {
                    Text("Location").foregroundStyle(.secondary)
                    Text(response.gene.locus)
                }
                GridRow {
                    Text("Strand").foregroundStyle(.secondary)
                    Text(response.gene.strandLabel)
                }
                GridRow {
                    Text("Protein").foregroundStyle(.secondary)
                    Text("\(response.sequences.protein.count) amino acids")
                }
            }
            .font(.subheadline)
            Text("Function: \(knownFunction(response))")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct BeginnerTakeaway: View {
    var response: GeneDogmaResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(response.gene.displayName) is found at \(response.gene.locus) on the \(response.gene.strandLabel) strand.")
            Text("The selected transcript is \(response.selectedTranscript?.displayName ?? response.selectedTranscript?.id ?? "not available").")
            if !response.sequences.codingDna.isEmpty, !response.sequences.protein.isEmpty {
                Text("Its coding sequence has \(response.sequences.codingDna.count) DNA letters and translates into \(response.sequences.protein.count) amino acids.")
            }
        }
    }
}

struct DogmaStep: View {
    var title: String
    var detail: String
    var sequence: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.headline)
            Text(detail)
                .foregroundStyle(.secondary)
            if !sequence.isEmpty {
                Text(sequenceSummaryText(sequence))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                DisclosureGroup("Show sequence preview") {
                    Text(sequencePreviewText(sequence, limit: 240))
                        .font(.system(.caption, design: .monospaced))
                        .textSelection(.enabled)
                }
            }
        }
    }
}

struct FeatureRow: View {
    var title: String
    var value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.headline)
            Text(value)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

struct TranscriptRow: View {
    var transcript: Transcript

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(transcript.displayName ?? transcript.id)
                .font(.headline)
            Text(transcript.id)
                .font(.caption)
                .foregroundStyle(.secondary)
                .textSelection(.enabled)
            HStack {
                Text(transcript.biotype ?? "unknown")
                Spacer()
                Text(transcript.isCanonical == 1 ? "canonical" : "noncanonical")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
            Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 4) {
                GridRow {
                    Text("Exons")
                    Text(transcript.exonCount == 0 ? "NA" : "\(transcript.exonCount)")
                }
                GridRow {
                    Text("Transcript")
                    Text(transcript.length.map { "\($0) bases" } ?? "NA")
                }
                GridRow {
                    Text("CDS")
                    Text(transcript.cdsLengthEstimate.map { "\($0) bases est." } ?? "NA")
                }
                GridRow {
                    Text("Protein")
                    Text(transcript.translation?.length.map { "\($0) aa" } ?? "noncoding")
                }
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
    }
}

struct SequencePreview: View {
    var title: String
    var sequence: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.headline)
            Text(sequenceSummaryText(sequence))
                .font(.caption)
                .foregroundStyle(.secondary)
            DisclosureGroup("Show \(title) letters") {
                Text(sequencePreviewText(sequence, limit: 480))
                    .font(.system(.caption, design: .monospaced))
                    .textSelection(.enabled)
            }
        }
    }
}

func cleanDisplaySequence(_ sequence: String) -> String {
    sequence.uppercased().filter { $0.isLetter || $0 == "*" }
}

func sequenceSummaryText(_ sequence: String) -> String {
    let cleaned = cleanDisplaySequence(sequence)
    guard !cleaned.isEmpty else { return "No sequence returned." }
    let unit = cleaned.allSatisfy { "ACGTUN".contains($0) } ? "letters" : "amino acids"
    let start = String(cleaned.prefix(10))
    let end = String(cleaned.suffix(10))
    return "\(cleaned.count) \(unit) · starts \(start) · ends \(end)"
}

func sequencePreviewText(_ sequence: String, limit: Int) -> String {
    let cleaned = cleanDisplaySequence(sequence)
    guard !cleaned.isEmpty else { return "No sequence returned." }
    guard cleaned.count > limit else { return cleaned }
    let shown = String(cleaned.prefix(limit))
    return "\(shown)\n...\n\(cleaned.count - limit) more symbols hidden"
}

func whyGeneMatters(_ response: GeneDogmaResponse) -> String {
    let name = response.gene.displayName
    if name.uppercased() == "HBB" {
        return "HBB encodes beta-globin, one of the core protein chains in adult hemoglobin. It is the classic sickle-cell central-dogma example."
    }
    if name.uppercased() == "BRCA1" {
        return "BRCA1 helps repair damaged DNA, so it is a strong example of how genome maintenance genes affect cancer-risk biology."
    }
    if name.uppercased() == "TP53" {
        return "TP53 helps cells respond to DNA damage and stress, which makes it one of the most famous tumor-suppressor genes."
    }
    if name.uppercased() == "CFTR" {
        return "CFTR encodes an ion channel, connecting coding sequence to membrane-protein function and cystic fibrosis biology."
    }
    if name.uppercased() == "INS" {
        return "INS encodes the insulin precursor, a beginner-friendly route from gene sequence to a familiar hormone."
    }
    if name.uppercased() == "APOE" {
        return "APOE helps transport lipids, and common protein variants are tied to Alzheimer disease and cardiovascular risk."
    }
    if response.gene.biotype == "protein_coding" {
        return "\(name) matters because its coding DNA can be translated into a protein that may affect cell behavior."
    }
    return "\(name) is a \(response.gene.biotype); its role may come from RNA function, regulation, or transcript processing."
}

func knownFunction(_ response: GeneDogmaResponse) -> String {
    switch response.gene.displayName.uppercased() {
    case "HBB": return "Encodes beta-globin, a core chain of adult hemoglobin."
    case "BRCA1": return "Supports DNA damage repair, especially homologous recombination."
    case "TP53": return "Encodes p53, a transcription factor that controls stress responses."
    case "CFTR": return "Encodes a chloride/bicarbonate channel in epithelial tissues."
    case "INS": return "Encodes preproinsulin, which is processed into insulin."
    case "APOE": return "Encodes apolipoprotein E, a lipid-transport protein."
    default:
        return response.gene.description.isEmpty ? "No function summary returned yet." : response.gene.description
    }
}

func diseaseNote(_ response: GeneDogmaResponse) -> String {
    switch response.gene.displayName.uppercased() {
    case "HBB": return "Teaching examples include HbS, HbC, and beta-thalassemia variants. Use Mutation mode for simple codon-level practice."
    case "BRCA1": return "Some pathogenic variants are associated with hereditary breast and ovarian cancer risk. This app does not classify variants or provide medical guidance."
    case "TP53": return "Somatic variants are common across cancers; inherited variants can cause Li-Fraumeni syndrome. This app keeps the focus on educational sequence flow."
    case "CFTR": return "Pathogenic variants can cause cystic fibrosis and related CFTR disorders. Mutation mode is only a simplified coding-DNA exercise."
    case "INS": return "Some variants are linked to monogenic diabetes and insulin-processing disorders. This app does not interpret patient variants."
    case "APOE": return "Common APOE alleles are associated with Alzheimer disease and cardiovascular-risk differences. This app is educational, not diagnostic."
    default: return "Use Mutation mode for simple codon and amino-acid consequences. This app does not perform clinical variant interpretation."
    }
}

func expressionNote(_ response: GeneDogmaResponse) -> String {
    switch response.gene.displayName.uppercased() {
    case "HBB": return "Most associated with erythroid blood-lineage cells that make hemoglobin."
    case "BRCA1": return "Broadly expressed, especially important in dividing cells that need accurate DNA repair."
    case "TP53": return "Broadly expressed and activated during cellular stress."
    case "CFTR": return "Important in airway, pancreatic, intestinal, sweat gland, and reproductive epithelial tissues."
    case "INS": return "Highly specialized expression in pancreatic beta cells."
    case "APOE": return "Relevant in liver, brain glia, macrophages, and lipid-handling tissues."
    default: return "No tissue-expression summary is bundled for this gene yet."
    }
}

struct StudyQuestion: Identifiable {
    var id: String { prompt }
    var prompt: String
    var choices: [String]
    var answer: String
    var explanation: String
}

struct TeacherLessonStep: Identifiable, Equatable {
    var id: String { "\(timing)-\(title)" }
    var timing: String
    var title: String
    var prompt: String
}

struct MutationLessonExample: Identifiable, Equatable {
    var id: String { "\(title)-\(change)" }
    var title: String
    var change: String
    var effect: String
    var codonChange: String
    var aminoAcidChange: String
    var explanation: String
}

func teacherLessonSteps(response: GeneDogmaResponse) -> [TeacherLessonStep] {
    let name = response.gene.displayName
    return [
        TeacherLessonStep(
            timing: "0-30 sec",
            title: "Hook",
            prompt: "Ask: how can one DNA letter in \(name) change a protein enough for biology to notice?"
        ),
        TeacherLessonStep(
            timing: "30-90 sec",
            title: "Trace the path",
            prompt: "Open the dogma path: DNA is stored, RNA is copied and processed, codons are read, protein is built."
        ),
        TeacherLessonStep(
            timing: "90-120 sec",
            title: "Compare edits",
            prompt: "Run missense versus nonsense. Have students explain why one swaps an amino acid while the other creates a stop."
        ),
    ]
}

func mutationLessonExamples(codingDNA: String) -> [MutationLessonExample] {
    let examples = [
        (
            title: "Missense",
            change: exampleMissenseChange(codingDNA),
            effect: "missense",
            explanation: "A DNA edit changes one codon so the protein gets a different amino acid."
        ),
        (
            title: "Nonsense",
            change: exampleNonsenseChange(codingDNA),
            effect: "nonsense",
            explanation: "A DNA edit creates an early stop signal, which can shorten the protein."
        ),
        (
            title: "Frameshift",
            change: exampleDeletionChange(codingDNA),
            effect: "frameshift",
            explanation: "A one-base deletion shifts the reading frame, changing downstream codons."
        ),
    ]
    return examples.compactMap { example in
        mutationLessonExample(
            codingDNA: codingDNA,
            title: example.title,
            change: example.change,
            effect: example.effect,
            explanation: example.explanation
        )
    }
}

func mutationLessonExample(codingDNA: String, title: String, change: String, effect: String, explanation: String) -> MutationLessonExample? {
    guard !change.isEmpty else { return nil }
    let cleaned = cleanDNA(codingDNA)
    guard let parsed = parseSimpleMutationChange(change, codingDNA: cleaned) else { return nil }
    let originalCodonStart = ((parsed.position - 1) / 3) * 3
    guard originalCodonStart + 3 <= cleaned.count else { return nil }
    let originalCodon = substring(cleaned, zeroBasedStart: originalCodonStart, length: 3)
    let mutatedDNA: String

    switch parsed.kind {
    case .substitution(let alternate):
        mutatedDNA = replacingCharacter(cleaned, oneBasedPosition: parsed.position, with: alternate)
    case .deletion:
        mutatedDNA = deletingCharacter(cleaned, oneBasedPosition: parsed.position)
    case .insertion(let alternate):
        mutatedDNA = insertingString(cleaned, afterOneBasedPosition: parsed.position, insertion: alternate)
    }

    let mutatedCodon = originalCodonStart + 3 <= mutatedDNA.count ? substring(mutatedDNA, zeroBasedStart: originalCodonStart, length: 3) : "NA"
    return MutationLessonExample(
        title: title,
        change: change,
        effect: effect,
        codonChange: "\(originalCodon) -> \(mutatedCodon)",
        aminoAcidChange: "\(translateCodon(originalCodon)) -> \(translateCodon(mutatedCodon))",
        explanation: explanation
    )
}

func quizQuestions(response: GeneDogmaResponse) -> [StudyQuestion] {
    let transcriptName = response.selectedTranscript?.displayName ?? response.selectedTranscript?.id ?? "No transcript returned"
    return [
        StudyQuestion(
            prompt: "What transcript is this app following for \(response.gene.displayName)?",
            choices: [transcriptName, response.gene.id, response.gene.seqRegionName],
            answer: transcriptName,
            explanation: "The transcript is the RNA version selected for the DNA -> RNA -> protein walk-through."
        ),
        StudyQuestion(
            prompt: "Which sequence is read three letters at a time to build a protein?",
            choices: ["Coding DNA / mRNA", "Chromosome location", "Gene alias list"],
            answer: "Coding DNA / mRNA",
            explanation: "Three-letter codons map to amino acids."
        ),
        StudyQuestion(
            prompt: "How long is the selected protein for \(response.gene.displayName)?",
            choices: ["\(response.sequences.protein.count) amino acids", "\(response.sequences.codingDna.count) chromosomes", "\(response.transcripts.count) species"],
            answer: "\(response.sequences.protein.count) amino acids",
            explanation: "Protein sequences are counted in amino-acid letters."
        ),
        StudyQuestion(
            prompt: "What does a nonsense mutation usually create?",
            choices: ["A premature stop signal", "A longer chromosome", "A new species"],
            answer: "A premature stop signal",
            explanation: "A nonsense change turns an amino-acid codon into a stop codon."
        ),
    ]
}

func storyReport(response: GeneDogmaResponse) -> String {
    """
    Gene Central Dogma Report: \(response.gene.displayName)

    Beginner explanation:
    \(whyGeneMatters(response))

    Advanced summary:
    \(response.gene.displayName) is a \(response.gene.biotype) gene at \(response.gene.locus).

    In central dogma terms, the app follows this path: genomic DNA, transcript RNA, coding sequence, then protein when one is available.

    Known biology:
    \(knownFunction(response))

    Teaching context:
    \(diseaseNote(response))

    Selected transcript: \(response.selectedTranscript?.id ?? "not available")
    Protein product: \(response.selectedTranslation?.id ?? "not available")
    Coding DNA length: \(response.sequences.codingDna.count) bases
    Protein length: \(response.sequences.protein.count) amino acids

    This report is educational and is not medical advice.
    """
}

func savedGeneStudyPack(savedGenes: [String]) -> String {
    var lines = [
        "# Gene Central Dogma Explorer study pack",
        "",
        "Use this as a lightweight review sheet for saved genes. It is educational only and is not medical advice.",
        "",
        "## Saved genes",
    ]
    if savedGenes.isEmpty {
        lines.append("- No saved genes yet.")
    } else {
        for (index, gene) in savedGenes.enumerated() {
            lines.append("\(index + 1). \(gene)")
        }
    }
    lines.append(contentsOf: [
        "",
        "## Review prompts",
        "- Pick one saved gene and trace DNA -> RNA -> protein in one sentence.",
        "- Compare a missense and nonsense mutation. What changes at the codon and amino-acid levels?",
        "- Explain why this app is a teaching tool rather than clinical variant interpretation.",
    ])
    return lines.joined(separator: "\n")
}
