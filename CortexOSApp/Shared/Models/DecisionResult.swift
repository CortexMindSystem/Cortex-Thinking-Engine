//
//  DecisionResult.swift
//  CortexOS
//
//  Context mutation DTOs — decisions, outcomes, insights, feedback, ingestion.
//

import Foundation

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
    var acted: Bool? = nil
}

struct SignalFeedbackRequest: Codable {
    let signalID: String
    let actionType: String
    var note: String = ""

    enum CodingKeys: String, CodingKey {
        case note
        case signalID = "signal_id"
        case actionType = "action_type"
    }
}

struct SignalOverrideRequest: Codable {
    let signalID: String
    let overrideType: String
    var note: String = ""
    var expiresAt: String = ""

    enum CodingKeys: String, CodingKey {
        case note
        case signalID = "signal_id"
        case overrideType = "override_type"
        case expiresAt = "expires_at"
    }
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
