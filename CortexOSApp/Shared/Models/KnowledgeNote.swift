//
//  KnowledgeNote.swift
//  CortexOS
//
//  The core knowledge note model — mirrors the Python KnowledgeNote dataclass.
//

import Foundation

struct KnowledgeNote: Codable, Identifiable, Hashable {
    let id: String
    var title: String
    var insight: String
    var implication: String
    var action: String
    var sourceURL: String
    var tags: [String]
    var createdAt: String
    var updatedAt: String
    var archived: Bool

    enum CodingKeys: String, CodingKey {
        case id, title, insight, implication, action, tags, archived
        case sourceURL   = "source_url"
        case createdAt   = "created_at"
        case updatedAt   = "updated_at"
    }

    // MARK: - Convenience

    var createdDate: Date? {
        ISO8601DateFormatter().date(from: createdAt)
    }

    var displayTags: String {
        tags.map { "#\($0)" }.joined(separator: " ")
    }

    static let example = KnowledgeNote(
        id: "abc123",
        title: "Context-Aware Retrieval Gains",
        insight: "Contextual embeddings outperform static ones for knowledge retrieval.",
        implication: "CortexOS ranking should use dynamic context windows.",
        action: "Prototype dynamic context embedding pipeline.",
        sourceURL: "https://example.com/paper",
        tags: ["AI", "retrieval"],
        createdAt: ISO8601DateFormatter().string(from: .now),
        updatedAt: "",
        archived: false
    )
}

// MARK: - Create / Update DTOs

struct NoteCreateRequest: Codable {
    var title: String = ""
    var insight: String = ""
    var implication: String = ""
    var action: String = ""
    var sourceURL: String = ""
    var tags: [String] = []

    enum CodingKeys: String, CodingKey {
        case title, insight, implication, action, tags
        case sourceURL = "source_url"
    }
}

struct NoteUpdateRequest: Codable {
    var title: String?
    var insight: String?
    var implication: String?
    var action: String?
    var sourceURL: String?
    var tags: [String]?
    var archived: Bool?

    enum CodingKeys: String, CodingKey {
        case title, insight, implication, action, tags, archived
        case sourceURL = "source_url"
    }
}
