//
//  DecisionResult.swift
//  CortexOS
//
//  Why Engine models — request and structured decision response.
//

import Foundation

// MARK: - Request

struct WhyEvaluateRequest: Codable {
    let title: String
    var content: String = ""
    var sourceType: String = "article"
    var url: String = ""
    var tags: [String] = []

    enum CodingKeys: String, CodingKey {
        case title, content, url, tags
        case sourceType = "source_type"
    }
}

// MARK: - Response

struct DecisionResult: Codable, Identifiable {
    var id: String { evaluatedAt }

    let summary: String
    let whyItMatters: String
    let impactOnActiveProject: String
    let contradictionOrConfirmation: String  // "supports", "contradicts", "unclear"
    let recommendedAction: String
    let ignoreOrWatch: String                // "act_now", "watch", "ignore"
    let confidence: Double
    let tags: [String]
    let evaluatedAt: String

    enum CodingKeys: String, CodingKey {
        case summary, confidence, tags
        case whyItMatters = "why_it_matters"
        case impactOnActiveProject = "impact_on_active_project"
        case contradictionOrConfirmation = "contradiction_or_confirmation"
        case recommendedAction = "recommended_action"
        case ignoreOrWatch = "ignore_or_watch"
        case evaluatedAt = "evaluated_at"
    }
}

// MARK: - Convenience

extension DecisionResult {
    /// Whether this item demands immediate attention.
    var isActionable: Bool { ignoreOrWatch == "act_now" }

    /// Whether this item contradicts a prior assumption.
    var isContradiction: Bool { contradictionOrConfirmation == "contradicts" }
}

// MARK: - Context mutation requests

struct DecisionCreateRequest: Codable {
    let decision: String
    let reason: String
    var project: String = ""
    var assumptions: [String] = []
}

struct OutcomeCreateRequest: Codable {
    let decisionId: String
    let outcome: String
    var impactScore: Double = 0.0

    enum CodingKeys: String, CodingKey {
        case outcome
        case decisionId = "decision_id"
        case impactScore = "impact_score"
    }
}

struct InsightCreateRequest: Codable {
    let title: String
    var summary: String = ""
    var whyItMatters: String = ""
    var architecturalImplication: String = ""
    var nextAction: String = ""
    var confidence: Double = 0.5
    var tags: [String] = []
    var relatedProject: String = ""

    enum CodingKeys: String, CodingKey {
        case title, summary, confidence, tags
        case whyItMatters = "why_it_matters"
        case architecturalImplication = "architectural_implication"
        case nextAction = "next_action"
        case relatedProject = "related_project"
    }
}

// MARK: - Feedback

struct FeedbackRequest: Codable {
    let item: String
    let useful: Bool
}

// MARK: - Summary Ingestion

struct SummaryIngestRequest: Codable {
    let content: String
    var source: String = ""
    var tags: [String] = []
    var createNotes: Bool = true

    enum CodingKeys: String, CodingKey {
        case content, source, tags
        case createNotes = "create_notes"
    }
}

struct IngestResult: Codable {
    let itemsIngested: Int
    let notesCreated: Int

    enum CodingKeys: String, CodingKey {
        case itemsIngested = "items_ingested"
        case notesCreated = "notes_created"
    }
}
