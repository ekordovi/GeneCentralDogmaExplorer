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
    @Published var mutationResult: MutationResult?
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
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
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
        } catch {
            errorMessage = error.localizedDescription
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
            errorMessage = error.localizedDescription
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
}
