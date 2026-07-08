import Foundation

struct GeneDogmaResponse: Codable, Equatable {
    var query: GeneQuery
    var gene: GeneIdentity
    var transcripts: [Transcript]
    var selectedTranscript: Transcript?
    var selectedTranslation: Translation?
    var sequences: GeneSequences
    var summaries: [String: SequenceSummary]
    var source: GeneSource

    enum CodingKeys: String, CodingKey {
        case query
        case gene
        case transcripts
        case selectedTranscript = "selected_transcript"
        case selectedTranslation = "selected_translation"
        case sequences
        case summaries
        case source
    }
}

struct GeneQuery: Codable, Equatable {
    var symbol: String
    var species: String
}

struct GeneIdentity: Codable, Equatable, Identifiable {
    var id: String
    var displayName: String
    var description: String
    var aliases: [String]?
    var biotype: String
    var assemblyName: String
    var seqRegionName: String
    var start: Int?
    var end: Int?
    var strand: Int?
    var species: String?
    var source: String
    var objectType: String

    enum CodingKeys: String, CodingKey {
        case id
        case displayName = "display_name"
        case description
        case aliases
        case biotype
        case assemblyName = "assembly_name"
        case seqRegionName = "seq_region_name"
        case start
        case end
        case strand
        case species
        case source
        case objectType = "object_type"
    }

    var locus: String {
        guard let start, let end else { return "chr\(seqRegionName)" }
        return "chr\(seqRegionName):\(start.formatted())-\(end.formatted())"
    }

    var strandLabel: String {
        switch strand {
        case 1: return "+ sense"
        case -1: return "- antisense"
        default: return "unknown"
        }
    }
}

struct Transcript: Codable, Equatable, Identifiable {
    var id: String
    var displayName: String?
    var biotype: String?
    var isCanonical: Int?
    var length: Int?
    var translation: Translation?
    var exons: [Exon]?

    enum CodingKeys: String, CodingKey {
        case id
        case displayName = "display_name"
        case biotype
        case isCanonical = "is_canonical"
        case length
        case translation = "Translation"
        case exons = "Exon"
    }

    var isProteinCoding: Bool {
        translation?.id.isEmpty == false
    }

    var exonCount: Int {
        exons?.count ?? 0
    }

    var cdsLengthEstimate: Int? {
        guard let proteinLength = translation?.length else { return nil }
        return proteinLength * 3
    }
}

struct Translation: Codable, Equatable {
    var id: String
    var length: Int?
}

struct Exon: Codable, Equatable, Identifiable {
    var stableID: String?
    var start: Int?
    var end: Int?
    var strand: Int?

    enum CodingKeys: String, CodingKey {
        case stableID = "id"
        case start
        case end
        case strand
    }

    var id: String {
        stableID ?? "\(start ?? 0)-\(end ?? 0)"
    }
}

struct GeneSequences: Codable, Equatable {
    var genomicDna: String
    var preMrnaProxy: String
    var transcriptCdna: String
    var codingDna: String
    var codingMrna: String
    var protein: String

    enum CodingKeys: String, CodingKey {
        case genomicDna = "genomic_dna"
        case preMrnaProxy = "pre_mrna_proxy"
        case transcriptCdna = "transcript_cdna"
        case codingDna = "coding_dna"
        case codingMrna = "coding_mrna"
        case protein
    }
}

struct SequenceSummary: Codable, Equatable {
    var length: Int
    var gcPercent: Double?
    var startsWith: String
    var endsWith: String
    var composition: [String: Int]?

    enum CodingKeys: String, CodingKey {
        case length
        case gcPercent = "gc_percent"
        case startsWith = "starts_with"
        case endsWith = "ends_with"
        case composition
    }
}

struct GeneSource: Codable, Equatable {
    var database: String
    var lookupEndpoint: String?
    var sequenceEndpoint: String?

    enum CodingKeys: String, CodingKey {
        case database
        case lookupEndpoint = "lookup_endpoint"
        case sequenceEndpoint = "sequence_endpoint"
    }
}

struct MutationRequest: Codable, Equatable {
    var codingDna: String
    var change: String

    enum CodingKeys: String, CodingKey {
        case codingDna = "coding_dna"
        case change
    }
}

struct MutationResult: Codable, Equatable {
    var input: String
    var mutationType: String
    var position: Int
    var codonNumber: Int
    var originalBase: String
    var originalCodon: String
    var mutatedCodon: String
    var originalAminoAcid: String
    var mutatedAminoAcid: String
    var effect: String
    var mutatedDna: String

    enum CodingKeys: String, CodingKey {
        case input
        case mutationType = "mutation_type"
        case position
        case codonNumber = "codon_number"
        case originalBase = "original_base"
        case originalCodon = "original_codon"
        case mutatedCodon = "mutated_codon"
        case originalAminoAcid = "original_amino_acid"
        case mutatedAminoAcid = "mutated_amino_acid"
        case effect
        case mutatedDna = "mutated_dna"
    }
}

struct APIErrorResponse: Codable {
    var detail: String
}
