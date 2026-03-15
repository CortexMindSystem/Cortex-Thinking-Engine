//
//  FocusBrief.swift
//  CortexOS
//
//  Models for the daily focus brief — the primary CortexOS feature.
//

import Foundation

struct FocusItem: Codable, Identifiable {
    var id: String { "\(rank)-\(title)" }

    let rank: Int
    let title: String
    let whyItMatters: String
    let nextAction: String
    let sourceURL: String
    let relevanceScore: Double
    let tags: [String]

    enum CodingKeys: String, CodingKey {
        case rank, title, tags
        case whyItMatters = "why_it_matters"
        case nextAction = "next_action"
        case sourceURL = "source_url"
        case relevanceScore = "relevance_score"
    }
}

struct DailyBrief: Codable {
    let date: String
    let focusItems: [FocusItem]
    let digestQuality: [String: Double]
    let profileSummary: [String: String]

    enum CodingKeys: String, CodingKey {
        case date
        case focusItems = "focus_items"
        case digestQuality = "digest_quality"
        case profileSummary = "profile_summary"
    }

    init(date: String = "", focusItems: [FocusItem] = [], digestQuality: [String: Double] = [:], profileSummary: [String: String] = [:]) {
        self.date = date
        self.focusItems = focusItems
        self.digestQuality = digestQuality
        self.profileSummary = profileSummary
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        date = try container.decode(String.self, forKey: .date)
        focusItems = try container.decode([FocusItem].self, forKey: .focusItems)

        // profileSummary may come as dict, string, or null from the API
        if let dict = try? container.decode([String: String].self, forKey: .profileSummary) {
            profileSummary = dict
        } else {
            profileSummary = [:]
        }

        // digestQuality comes as mixed types from the API — normalise to [String: Double]
        if let raw = try? container.decode([String: Double].self, forKey: .digestQuality) {
            digestQuality = raw
        } else {
            digestQuality = [:]
        }
    }
}

// MARK: - Request model

struct FocusRequest: Codable {
    var digestPath: String?
    var useLLM: Bool = false

    enum CodingKeys: String, CodingKey {
        case digestPath = "digest_path"
        case useLLM = "use_llm"
    }
}
