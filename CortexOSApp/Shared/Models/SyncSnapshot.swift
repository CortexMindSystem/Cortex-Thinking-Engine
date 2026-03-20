//
//  SyncSnapshot.swift
//  CortexOS
//
//  Single-call sync model — everything a client needs in one pull.
//  Backend is source of truth. Clients decode this on launch.
//

import Foundation

// MARK: - Snapshot

struct SyncSnapshot: Codable {
    let profile: SyncProfile
    let activeProject: ProjectContext?
    let priorities: PriorityBrief?
    let recentDecisions: [SyncDecision]
    let insights: [SyncInsight]
    let signals: [SyncSignal]
    let workingMemory: SyncWorkingMemory
    let syncedAt: String

    enum CodingKeys: String, CodingKey {
        case profile, priorities, insights, signals
        case activeProject = "active_project"
        case recentDecisions = "recent_decisions"
        case workingMemory = "working_memory"
        case syncedAt = "synced_at"
    }
}

// MARK: - Profile (subset for sync)

struct SyncProfile: Codable {
    let name: String
    let role: String
    let goals: [String]
    let interests: [String]
    let currentProjects: [String]
    let ignoredTopics: [String]

    enum CodingKeys: String, CodingKey {
        case name, role, goals, interests
        case currentProjects = "current_projects"
        case ignoredTopics = "ignored_topics"
    }
}

// MARK: - Project

struct ProjectContext: Codable {
    let projectName: String
    let currentMilestone: String
    let activeBlockers: [String]
    let recentDecisions: [String]
    let architectureNotes: [String]
    let openQuestions: [String]

    enum CodingKeys: String, CodingKey {
        case projectName = "project_name"
        case currentMilestone = "current_milestone"
        case activeBlockers = "active_blockers"
        case recentDecisions = "recent_decisions"
        case architectureNotes = "architecture_notes"
        case openQuestions = "open_questions"
    }
}

// MARK: - Priority Brief

struct SyncPriority: Codable, Identifiable {
    var id: String { title }
    let rank: Int
    let title: String
    let whyItMatters: String
    let nextStep: String
    let source: String
    let relevanceScore: Double
    let tags: [String]

    enum CodingKeys: String, CodingKey {
        case rank, title, source, tags
        case whyItMatters = "why_it_matters"
        case nextStep = "next_step"
        case relevanceScore = "relevance_score"
    }
}

struct PriorityBrief: Codable {
    let date: String
    let priorities: [SyncPriority]
    let ignored: [String]
    let emergingSignals: [String]
    let changesSinceYesterday: [String]

    enum CodingKeys: String, CodingKey {
        case date, priorities, ignored
        case emergingSignals = "emerging_signals"
        case changesSinceYesterday = "changes_since_yesterday"
    }
}

// MARK: - Decision

struct SyncDecision: Codable, Identifiable {
    let id: String
    let decision: String
    let reason: String
    let project: String
    let assumptions: [String]
    let contextTags: [String]
    let createdAt: String
    let outcome: String
    let impactScore: Double

    enum CodingKeys: String, CodingKey {
        case id, decision, reason, project, assumptions, outcome
        case contextTags = "context_tags"
        case createdAt = "created_at"
        case impactScore = "impact_score"
    }
}

// MARK: - Insight

struct SyncInsight: Codable, Identifiable {
    let id: String
    let title: String
    let summary: String
    let whyItMatters: String
    let architecturalImplication: String
    let nextAction: String
    let confidence: Double
    let tags: [String]
    let relatedProject: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, title, summary, confidence, tags
        case whyItMatters = "why_it_matters"
        case architecturalImplication = "architectural_implication"
        case nextAction = "next_action"
        case relatedProject = "related_project"
        case createdAt = "created_at"
    }
}

// MARK: - Signal

struct SyncSignal: Codable, Identifiable {
    let id: String
    let topic: String
    let frequency: Int
    let strength: Double
    let status: String  // emerging, confirmed, fading, archived
    let firstSeen: String
    let lastSeen: String
    let sourceTitles: [String]

    enum CodingKeys: String, CodingKey {
        case id, topic, frequency, strength, status
        case firstSeen = "first_seen"
        case lastSeen = "last_seen"
        case sourceTitles = "source_titles"
    }
}

// MARK: - Working Memory

struct SyncWorkingMemory: Codable {
    let date: String
    let todaysPriorities: [String]
    let currentlyExploring: [String]
    let temporaryNotes: [String]

    enum CodingKeys: String, CodingKey {
        case date
        case todaysPriorities = "todays_priorities"
        case currentlyExploring = "currently_exploring"
        case temporaryNotes = "temporary_notes"
    }
}
