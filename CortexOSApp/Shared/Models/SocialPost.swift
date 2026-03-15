//
//  SocialPost.swift
//  CortexOS
//
//  Model for AI-generated social media posts.
//

import Foundation

struct SocialPost: Codable, Identifiable {
    var id: String { noteID + platform }

    let text: String
    let platform: String
    let noteID: String

    enum CodingKeys: String, CodingKey {
        case text, platform
        case noteID = "note_id"
    }

    var platformIcon: String {
        switch platform {
        case "twitter":  return "bird"
        case "linkedin": return "briefcase.fill"
        case "bluesky":  return "cloud.fill"
        default:         return "text.bubble.fill"
        }
    }

    static let example = SocialPost(
        text: "💡 Context-Aware Retrieval Gains\n\nContextual embeddings outperform static ones.\n\n→ Prototype dynamic context pipeline\n\n#CortexOS #AI",
        platform: "twitter",
        noteID: "abc123"
    )
}

struct PostGenerateRequest: Codable {
    var limit: Int = 3
    var platform: String = "general"
    var useLLM: Bool = false

    enum CodingKeys: String, CodingKey {
        case limit, platform
        case useLLM = "use_llm"
    }
}
