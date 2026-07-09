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
    private var client: GeneDogmaAPIClient

    init(client: GeneDogmaAPIClient = GeneDogmaAPIClient()) {
        self.client = client
        self.savedGenes = UserDefaults.standard.stringArray(forKey: savedGenesKey) ?? []
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
            mutationResult = try await client.simulateMutation(codingDNA: codingDNA, change: mutationText)
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
            async let first = client.simulateMutation(codingDNA: codingDNA, change: comparisonMutationA)
            async let second = client.simulateMutation(codingDNA: codingDNA, change: comparisonMutationB)
            comparisonResultA = try await first
            comparisonResultB = try await second
        } catch {
            errorMessage = friendlyErrorMessage(error, context: "mutation")
        }
    }

    func saveCurrentGene() {
        guard let gene = response?.gene.displayName, !gene.isEmpty else { return }
        if !savedGenes.contains(gene) {
            savedGenes.insert(gene, at: 0)
            UserDefaults.standard.set(savedGenes, forKey: savedGenesKey)
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

    private func applyMutationExamples() {
        guard let codingDNA = response?.sequences.codingDna, !codingDNA.isEmpty else { return }
        let substitution = exampleSubstitutionChange(codingDNA)
        let nonsense = exampleNonsenseChange(codingDNA)
        let deletion = exampleDeletionChange(codingDNA)
        mutationText = substitution
        comparisonMutationA = substitution
        comparisonMutationB = nonsense.isEmpty ? deletion : nonsense
    }
}

func friendlyErrorMessage(_ error: Error, context: String = "lookup") -> String {
    let message = error.localizedDescription
    if context == "mutation" {
        if message.contains("Reference base mismatch") {
            return "That edit does not match the selected coding DNA. Try one of the suggested examples for this gene."
        }
        if message.contains("Position must be") {
            return message
        }
        return "Try a simple coding-DNA edit like 20 A>T, 20del, or 20insA."
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
