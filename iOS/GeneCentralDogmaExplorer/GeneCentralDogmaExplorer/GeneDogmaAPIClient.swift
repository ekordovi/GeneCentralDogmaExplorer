import Foundation
import Combine

enum GeneDogmaAPIError: LocalizedError, Equatable {
    case invalidURL
    case serverMessage(String)
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The API URL is not configured correctly."
        case .serverMessage(let message):
            return message
        case .invalidResponse:
            return "The server returned an unexpected response."
        }
    }
}

struct GeneDogmaAPIClient {
    var baseURL: URL
    var session: URLSession = .shared
    var decoder = JSONDecoder()
    var encoder = JSONEncoder()

    init(baseURL: URL = GeneDogmaAPIClient.configuredBaseURL()) {
        self.baseURL = baseURL
    }

    static func configuredBaseURL(bundle: Bundle = .main) -> URL {
        if let value = bundle.object(forInfoDictionaryKey: "GeneDogmaAPIBaseURL") as? String,
           let url = URL(string: value),
           !value.isEmpty {
            return url
        }
        return URL(string: "http://127.0.0.1:8000")!
    }

    func fetchGene(symbol: String, species: String, transcriptID: String? = nil) async throws -> GeneDogmaResponse {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/gene"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "symbol", value: symbol),
            URLQueryItem(name: "species", value: species),
        ]
        if let transcriptID, !transcriptID.isEmpty {
            components?.queryItems?.append(URLQueryItem(name: "transcript_id", value: transcriptID))
        }
        guard let url = components?.url else { throw GeneDogmaAPIError.invalidURL }
        return try await request(url: url)
    }

    func simulateMutation(codingDNA: String, change: String) async throws -> MutationResult {
        let url = baseURL.appendingPathComponent("api/mutation")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(MutationRequest(codingDna: codingDNA, change: change))
        return try await self.request(request)
    }

    private func request<T: Decodable>(url: URL) async throws -> T {
        try await request(URLRequest(url: url))
    }

    private func request<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw GeneDogmaAPIError.invalidResponse
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            if let apiError = try? decoder.decode(APIErrorResponse.self, from: data) {
                throw GeneDogmaAPIError.serverMessage(apiError.detail)
            }
            throw GeneDogmaAPIError.serverMessage("Request failed with status \(httpResponse.statusCode).")
        }
        return try decoder.decode(T.self, from: data)
    }
}

struct FamousGeneExample: Identifiable, Equatable {
    var id: String { symbol }
    var symbol: String
    var name: String
    var why: String
}

let famousGeneExamples: [FamousGeneExample] = [
    FamousGeneExample(symbol: "HBB", name: "Hemoglobin beta", why: "Classic sickle hemoglobin and beta-globin example."),
    FamousGeneExample(symbol: "BRCA1", name: "DNA repair", why: "Genome repair gene tied to cancer-risk biology."),
    FamousGeneExample(symbol: "TP53", name: "Tumor suppressor", why: "Stress-response gene often called the guardian of the genome."),
    FamousGeneExample(symbol: "CFTR", name: "Ion channel", why: "Membrane channel gene tied to cystic fibrosis."),
    FamousGeneExample(symbol: "INS", name: "Insulin", why: "Familiar hormone gene that controls blood glucose biology."),
    FamousGeneExample(symbol: "APOE", name: "Lipid transport", why: "Lipid-transport gene with memorable common protein variants."),
]

struct DemoLaunchConfiguration: Equatable {
    var initialTab = 0
    var shouldPrimeMutationComparison = false
    var savedGenes: [String] = []

    init(arguments: [String] = ProcessInfo.processInfo.arguments) {
        for argument in arguments {
            if let tabName = argument.value(afterPrefix: "--gene-demo-tab=") ?? argument.value(afterPrefix: "--screenshot-tab="),
               let tab = DemoLaunchConfiguration.tabIndex(for: tabName) {
                initialTab = tab
            }
            if argument == "--gene-demo-compare" || argument == "--screenshot-compare" {
                shouldPrimeMutationComparison = true
            }
            if argument == "--gene-demo-saved" || argument == "--screenshot-saved" {
                savedGenes = ["HBB", "BRCA1", "TP53"]
            }
            if argument == "--gene-demo=screenshots" {
                savedGenes = ["HBB", "BRCA1", "TP53"]
                shouldPrimeMutationComparison = true
            }
        }
    }

    var shouldApply: Bool {
        shouldPrimeMutationComparison || !savedGenes.isEmpty
    }

    static func tabIndex(for value: String) -> Int? {
        switch value.lowercased() {
        case "search", "start", "hbb":
            return 0
        case "explore", "dogma":
            return 1
        case "mutation", "compare":
            return 2
        case "quiz", "study":
            return 3
        case "saved":
            return 4
        case "about", "privacy":
            return 5
        default:
            return nil
        }
    }
}

private extension String {
    func value(afterPrefix prefix: String) -> String? {
        hasPrefix(prefix) ? String(dropFirst(prefix.count)) : nil
    }
}

enum LocalExampleStore {
    static func loadHBBExample(bundle: Bundle = .main) throws -> GeneDogmaResponse {
        guard let url = bundle.url(forResource: "example_gene_cache", withExtension: "json") else {
            throw GeneDogmaAPIError.serverMessage("Bundled HBB example is missing.")
        }
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(GeneDogmaResponse.self, from: data)
    }
}

@MainActor
final class GeneDogmaViewModel: ObservableObject {
    @Published var symbol = "HBB"
    @Published var species = "homo_sapiens"
    @Published var response: GeneDogmaResponse?
    @Published var mutationText = "20 A>T"
    @Published var comparisonMutationA = "20 A>T"
    @Published var comparisonMutationB = "19 G>T"
    @Published var mutationResult: MutationResult?
    @Published var comparisonResultA: MutationResult?
    @Published var comparisonResultB: MutationResult?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var savedGenes: [String] = []
    @Published var selectedQuizAnswer = ""
    @Published var quizFeedback: String?

    private let savedGenesKey = "saved_gene_symbols"
    private let userDefaults: UserDefaults
    private var client: GeneDogmaAPIClient

    init(client: GeneDogmaAPIClient = GeneDogmaAPIClient(), userDefaults: UserDefaults = .standard) {
        self.client = client
        self.userDefaults = userDefaults
        self.savedGenes = userDefaults.stringArray(forKey: savedGenesKey) ?? []
        loadBundledExample()
    }

    func loadBundledExample() {
        do {
            response = try LocalExampleStore.loadHBBExample()
            symbol = response?.gene.displayName ?? "HBB"
            applyMutationExamples()
            errorMessage = nil
        } catch {
            errorMessage = friendlyErrorMessage(error)
        }
    }

    func lookupGene() async {
        let trimmedSymbol = symbol.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedSpecies = species.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedSymbol.isEmpty, !trimmedSpecies.isEmpty else {
            errorMessage = "Enter a gene symbol and species."
            return
        }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            response = try await client.fetchGene(symbol: trimmedSymbol, species: trimmedSpecies)
            mutationResult = nil
            comparisonResultA = nil
            comparisonResultB = nil
            applyMutationExamples()
        } catch {
            errorMessage = friendlyErrorMessage(error)
        }
    }

    func simulateMutation() async {
        guard let codingDNA = response?.sequences.codingDna, !codingDNA.isEmpty else {
            errorMessage = "This gene does not have coding DNA available for mutation simulation."
            return
        }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            mutationResult = try simulateLocalMutation(codingDNA: codingDNA, change: mutationText)
        } catch {
            errorMessage = friendlyErrorMessage(error, context: "mutation")
        }
    }

    func compareMutations() async {
        guard let codingDNA = response?.sequences.codingDna, !codingDNA.isEmpty else {
            errorMessage = "This gene does not have coding DNA available for mutation comparison."
            return
        }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            comparisonResultA = try simulateLocalMutation(codingDNA: codingDNA, change: comparisonMutationA)
            comparisonResultB = try simulateLocalMutation(codingDNA: codingDNA, change: comparisonMutationB)
        } catch {
            errorMessage = friendlyErrorMessage(error, context: "mutation")
        }
    }

    func saveCurrentGene() {
        guard let gene = response?.gene.displayName, !gene.isEmpty else { return }
        if !savedGenes.contains(gene) {
            savedGenes.insert(gene, at: 0)
            persistSavedGenes()
        }
    }

    func loadSavedGene(_ gene: String) {
        symbol = gene
    }

    func loadFamousExample(_ example: FamousGeneExample) async {
        symbol = example.symbol
        species = "homo_sapiens"
        if example.symbol == "HBB" {
            loadBundledExample()
        } else {
            await lookupGene()
        }
    }

    func applyDemoConfiguration(_ configuration: DemoLaunchConfiguration) {
        guard configuration.shouldApply else { return }
        if !configuration.savedGenes.isEmpty {
            savedGenes = configuration.savedGenes
            persistSavedGenes()
        }
        if configuration.shouldPrimeMutationComparison {
            loadBundledExample()
            guard let codingDNA = response?.sequences.codingDna, !codingDNA.isEmpty else { return }
            applyMutationExamples()
            mutationResult = try? simulateLocalMutation(codingDNA: codingDNA, change: mutationText)
            comparisonResultA = try? simulateLocalMutation(codingDNA: codingDNA, change: comparisonMutationA)
            comparisonResultB = try? simulateLocalMutation(codingDNA: codingDNA, change: comparisonMutationB)
        }
    }

    private func applyMutationExamples() {
        guard let codingDNA = response?.sequences.codingDna, !codingDNA.isEmpty else { return }
        let substitution = exampleMissenseChange(codingDNA)
        let nonsense = exampleNonsenseChange(codingDNA)
        let deletion = exampleDeletionChange(codingDNA)
        mutationText = substitution
        comparisonMutationA = substitution
        comparisonMutationB = nonsense.isEmpty ? deletion : nonsense
    }

    private func persistSavedGenes() {
        userDefaults.set(savedGenes, forKey: savedGenesKey)
    }
}

func friendlyErrorMessage(_ error: Error, context: String = "lookup") -> String {
    let message = error.localizedDescription
    if context == "mutation" {
        if message.contains("does not match") || message.contains("Try a simple coding-DNA edit") {
            return message
        }
        if message.contains("Reference base mismatch") {
            return "That edit does not match the selected coding DNA. Try one of the suggested examples for this gene."
        }
        if message.contains("Position must be") {
            return message
        }
        return "Try a simple coding-DNA edit like 20 A>T, 20del, or 20insA."
    }
    if message.hasPrefix("We couldn't") || message.hasPrefix("Live gene lookup") || message.hasPrefix("We could not") {
        return message
    }
    if message.localizedCaseInsensitiveContains("not found") || message.localizedCaseInsensitiveContains("lookup") {
        return "We could not find that gene symbol for this species. Try checking the spelling or selecting another species."
    }
    if message.localizedCaseInsensitiveContains("offline") || message.localizedCaseInsensitiveContains("network") {
        return "Live lookup is not reachable right now. The bundled HBB demo still works offline."
    }
    return "We could not load that gene right now. Try HBB, BRCA1, TP53, or the offline HBB demo."
}

func mutationEffectExplanation(_ effect: String) -> String {
    switch effect.lowercased() {
    case "silent":
        return "The DNA changed, but the codon still points to the same amino acid."
    case "missense":
        return "One amino acid changed. This can matter if that spot is important for the protein."
    case "nonsense":
        return "The edit creates a stop signal, so translation may stop early."
    case "frameshift":
        return "The reading frame shifts, so many downstream codons can change."
    default:
        return "The coding sequence changed."
    }
}

func exampleSubstitutionChange(_ codingDNA: String, preferredPosition: Int = 20) -> String {
    let cleaned = cleanDNA(codingDNA)
    guard !cleaned.isEmpty else { return "" }
    let position = min(max(1, preferredPosition), cleaned.count)
    let reference = characterAt(cleaned, oneBasedPosition: position)
    return "\(position) \(reference)>\(alternateBase(reference))"
}

func exampleMissenseChange(_ codingDNA: String) -> String {
    let cleaned = cleanDNA(codingDNA)
    let preferred = exampleSubstitutionChange(cleaned)
    if mutationEffectForSubstitution(cleaned, change: preferred) == "missense" {
        return preferred
    }
    guard !cleaned.isEmpty else { return "" }
    for position in 1...cleaned.count {
        let reference = characterAt(cleaned, oneBasedPosition: position)
        for alternate in ["A", "C", "G", "T"] where alternate != reference {
            let change = "\(position) \(reference)>\(alternate)"
            if mutationEffectForSubstitution(cleaned, change: change) == "missense" {
                return change
            }
        }
    }
    return exampleSubstitutionChange(codingDNA)
}

func exampleDeletionChange(_ codingDNA: String, preferredPosition: Int = 20) -> String {
    let cleaned = cleanDNA(codingDNA)
    guard !cleaned.isEmpty else { return "" }
    let position = min(max(1, preferredPosition), cleaned.count)
    return "\(position)del"
}

func exampleNonsenseChange(_ codingDNA: String) -> String {
    let cleaned = cleanDNA(codingDNA)
    guard cleaned.count >= 3 else { return "" }
    let stops: Set<String> = ["TAA", "TAG", "TGA"]
    var index = cleaned.startIndex
    var codonStart = 0
    while cleaned.distance(from: index, to: cleaned.endIndex) >= 3 {
        let end = cleaned.index(index, offsetBy: 3)
        let codon = String(cleaned[index..<end])
        if !stops.contains(codon) {
            let bases = Array(codon)
            for offset in bases.indices {
                for alternate in ["A", "C", "G", "T"] {
                    let reference = String(bases[offset])
                    guard alternate != reference else { continue }
                    var mutated = bases
                    mutated[offset] = Character(alternate)
                    if stops.contains(String(mutated)) {
                        return "\(codonStart + offset + 1) \(reference)>\(alternate)"
                    }
                }
            }
        }
        index = end
        codonStart += 3
    }
    return ""
}

func cleanDNA(_ sequence: String) -> String {
    sequence.uppercased().filter { "ACGTU".contains($0) }.replacingOccurrences(of: "U", with: "T")
}

func characterAt(_ sequence: String, oneBasedPosition: Int) -> String {
    let index = sequence.index(sequence.startIndex, offsetBy: oneBasedPosition - 1)
    return String(sequence[index])
}

func alternateBase(_ base: String) -> String {
    for candidate in ["T", "G", "C", "A"] where candidate != base {
        return candidate
    }
    return "A"
}

enum LocalMutationKind: Equatable {
    case substitution(alternate: String)
    case deletion
    case insertion(alternate: String)
}

struct ParsedMutationChange: Equatable {
    var position: Int
    var kind: LocalMutationKind
}

func parseSimpleMutationChange(_ change: String, codingDNA: String) -> ParsedMutationChange? {
    let requested = change.trimmingCharacters(in: .whitespacesAndNewlines).uppercased().replacingOccurrences(of: " ", with: "")
    if requested.isEmpty {
        return nil
    }

    if let delRange = requested.range(of: "DEL") {
        let positionText = requested[..<delRange.lowerBound]
        guard let position = Int(positionText), position >= 1, position <= codingDNA.count else { return nil }
        let reference = String(requested[delRange.upperBound...])
        if !reference.isEmpty, characterAt(codingDNA, oneBasedPosition: position) != reference {
            return nil
        }
        return ParsedMutationChange(position: position, kind: .deletion)
    }

    if let insRange = requested.range(of: "INS") {
        let positionText = requested[..<insRange.lowerBound]
        let alternate = String(requested[insRange.upperBound...])
        guard let position = Int(positionText),
              position >= 1,
              position <= codingDNA.count,
              !alternate.isEmpty,
              alternate.allSatisfy({ "ACGT".contains($0) }) else { return nil }
        return ParsedMutationChange(position: position, kind: .insertion(alternate: alternate))
    }

    let baseChange = requested.split(separator: ">")
    guard baseChange.count == 2,
          let referencePart = baseChange.first,
          let alternatePart = baseChange.last,
          let position = Int(referencePart.dropLast()),
          let reference = referencePart.last,
          position >= 1,
          position <= codingDNA.count,
          alternatePart.count == 1,
          alternatePart.allSatisfy({ "ACGT".contains($0) }) else { return nil }
    guard characterAt(codingDNA, oneBasedPosition: position) == String(reference) else { return nil }
    return ParsedMutationChange(position: position, kind: .substitution(alternate: String(alternatePart)))
}

func mutationEffectForSubstitution(_ codingDNA: String, change: String) -> String? {
    guard let parsed = parseSimpleMutationChange(change, codingDNA: codingDNA),
          case .substitution(let alternate) = parsed.kind else { return nil }
    let originalCodonStart = ((parsed.position - 1) / 3) * 3
    guard originalCodonStart + 3 <= codingDNA.count else { return nil }
    let originalCodon = substring(codingDNA, zeroBasedStart: originalCodonStart, length: 3)
    let mutatedDNA = replacingCharacter(codingDNA, oneBasedPosition: parsed.position, with: alternate)
    let mutatedCodon = substring(mutatedDNA, zeroBasedStart: originalCodonStart, length: 3)
    let originalAA = translateCodon(originalCodon)
    let mutatedAA = translateCodon(mutatedCodon)
    if mutatedAA == "*" {
        return "nonsense"
    }
    return originalAA == mutatedAA ? "silent" : "missense"
}

enum LocalMutationError: LocalizedError {
    case noCodingDNA
    case emptyChange
    case invalidFormat
    case invalidPosition(max: Int)
    case referenceMismatch(position: Int, expected: String)

    var errorDescription: String? {
        switch self {
        case .noCodingDNA:
            return "No coding DNA sequence is available for mutation simulation."
        case .emptyChange:
            return "Enter a mutation such as 20 A>T, 20del, or 20insA."
        case .invalidFormat:
            return "Use a simple format like 20 A>T, 20del, or 20insA."
        case .invalidPosition(let max):
            return "Position must be between 1 and \(max.formatted())."
        case .referenceMismatch(let position, let expected):
            return "Reference base mismatch at \(position): expected \(expected)."
        }
    }
}

func simulateLocalMutation(codingDNA: String, change: String) throws -> MutationResult {
    let cleaned = cleanDNA(codingDNA)
    let requested = change.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !cleaned.isEmpty else { throw LocalMutationError.noCodingDNA }
    guard !requested.isEmpty else { throw LocalMutationError.emptyChange }
    guard let parsed = parseSimpleMutationChange(requested, codingDNA: cleaned) else {
        if let position = leadingInteger(in: requested), position < 1 || position > cleaned.count {
            throw LocalMutationError.invalidPosition(max: cleaned.count)
        }
        if let mismatch = substitutionReferenceMismatch(requested, codingDNA: cleaned) {
            throw LocalMutationError.referenceMismatch(position: mismatch.position, expected: mismatch.expected)
        }
        throw LocalMutationError.invalidFormat
    }

    let zeroIndex = parsed.position - 1
    let actualBase = characterAt(cleaned, oneBasedPosition: parsed.position)
    let mutationType: String
    let mutatedDNA: String

    switch parsed.kind {
    case .substitution(let alternate):
        mutationType = "substitution"
        mutatedDNA = replacingCharacter(cleaned, oneBasedPosition: parsed.position, with: alternate)
    case .deletion:
        mutationType = "deletion"
        mutatedDNA = deletingCharacter(cleaned, oneBasedPosition: parsed.position)
    case .insertion(let alternate):
        mutationType = "insertion"
        mutatedDNA = insertingString(cleaned, afterOneBasedPosition: parsed.position, insertion: alternate)
    }

    let codonIndex = zeroIndex / 3
    let codonStart = codonIndex * 3
    let originalCodon = substring(cleaned, zeroBasedStart: codonStart, length: 3, fallback: "")
    let mutatedCodon = substring(mutatedDNA, zeroBasedStart: codonStart, length: 3, fallback: "")
    let originalAA = originalCodon.count == 3 ? translateCodon(originalCodon) : ""
    let mutatedAA = mutatedCodon.count == 3 ? translateCodon(mutatedCodon) : ""
    let effect: String
    if mutatedDNA.count % 3 != cleaned.count % 3 {
        effect = "frameshift"
    } else if mutatedAA == "*" {
        effect = "nonsense"
    } else if originalAA == mutatedAA {
        effect = "silent"
    } else {
        effect = "missense"
    }

    return MutationResult(
        input: change,
        mutationType: mutationType,
        position: parsed.position,
        codonNumber: codonIndex + 1,
        originalBase: actualBase,
        originalCodon: originalCodon,
        mutatedCodon: mutatedCodon,
        originalAminoAcid: originalAA,
        mutatedAminoAcid: mutatedAA,
        effect: effect,
        mutatedDna: mutatedDNA
    )
}

func substring(_ sequence: String, zeroBasedStart: Int, length: Int, fallback: String = "NA") -> String {
    guard zeroBasedStart >= 0, length > 0, zeroBasedStart + length <= sequence.count else { return fallback }
    let start = sequence.index(sequence.startIndex, offsetBy: zeroBasedStart)
    let end = sequence.index(start, offsetBy: length)
    return String(sequence[start..<end])
}

func replacingCharacter(_ sequence: String, oneBasedPosition: Int, with replacement: String) -> String {
    var characters = Array(sequence)
    guard oneBasedPosition >= 1, oneBasedPosition <= characters.count, let first = replacement.first else { return sequence }
    characters[oneBasedPosition - 1] = first
    return String(characters)
}

func deletingCharacter(_ sequence: String, oneBasedPosition: Int) -> String {
    var characters = Array(sequence)
    guard oneBasedPosition >= 1, oneBasedPosition <= characters.count else { return sequence }
    characters.remove(at: oneBasedPosition - 1)
    return String(characters)
}

func insertingString(_ sequence: String, afterOneBasedPosition position: Int, insertion: String) -> String {
    var characters = Array(sequence)
    guard position >= 1, position <= characters.count else { return sequence }
    characters.insert(contentsOf: Array(insertion), at: position)
    return String(characters)
}

func leadingInteger(in value: String) -> Int? {
    let digits = value.trimmingCharacters(in: .whitespacesAndNewlines).prefix { $0.isNumber }
    return digits.isEmpty ? nil : Int(digits)
}

func substitutionReferenceMismatch(_ change: String, codingDNA: String) -> (position: Int, expected: String)? {
    let requested = change.trimmingCharacters(in: .whitespacesAndNewlines).uppercased().replacingOccurrences(of: " ", with: "")
    let baseChange = requested.split(separator: ">")
    guard baseChange.count == 2,
          let referencePart = baseChange.first,
          let position = Int(referencePart.dropLast()),
          let reference = referencePart.last,
          position >= 1,
          position <= codingDNA.count else { return nil }
    let expected = characterAt(codingDNA, oneBasedPosition: position)
    return expected == String(reference) ? nil : (position, expected)
}

func translateCodon(_ codon: String) -> String {
    switch codon {
    case "TTT", "TTC": return "F"
    case "TTA", "TTG", "CTT", "CTC", "CTA", "CTG": return "L"
    case "ATT", "ATC", "ATA": return "I"
    case "ATG": return "M"
    case "GTT", "GTC", "GTA", "GTG": return "V"
    case "TCT", "TCC", "TCA", "TCG", "AGT", "AGC": return "S"
    case "CCT", "CCC", "CCA", "CCG": return "P"
    case "ACT", "ACC", "ACA", "ACG": return "T"
    case "GCT", "GCC", "GCA", "GCG": return "A"
    case "TAT", "TAC": return "Y"
    case "TAA", "TAG", "TGA": return "*"
    case "CAT", "CAC": return "H"
    case "CAA", "CAG": return "Q"
    case "AAT", "AAC": return "N"
    case "AAA", "AAG": return "K"
    case "GAT", "GAC": return "D"
    case "GAA", "GAG": return "E"
    case "TGT", "TGC": return "C"
    case "TGG": return "W"
    case "CGT", "CGC", "CGA", "CGG", "AGA", "AGG": return "R"
    case "GGT", "GGC", "GGA", "GGG": return "G"
    default: return "NA"
    }
}
