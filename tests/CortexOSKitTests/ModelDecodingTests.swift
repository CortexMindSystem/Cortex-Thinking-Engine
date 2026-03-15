//
//  ModelDecodingTests.swift
//  CortexOSKitTests
//
//  Tests JSON decoding for all CortexOS models to ensure
//  API contract compliance and prevent regressions.
//

import XCTest
@testable import CortexOSKit

final class FocusItemTests: XCTestCase {

    func testDecodeFocusItem() throws {
        let json = """
        {
            "rank": 1,
            "title": "Build context engine",
            "why_it_matters": "Core product",
            "next_action": "Write scoring module",
            "source_url": "https://example.com",
            "relevance_score": 0.92,
            "tags": ["ai", "product"]
        }
        """.data(using: .utf8)!

        let item = try JSONDecoder().decode(FocusItem.self, from: json)
        XCTAssertEqual(item.rank, 1)
        XCTAssertEqual(item.title, "Build context engine")
        XCTAssertEqual(item.whyItMatters, "Core product")
        XCTAssertEqual(item.nextAction, "Write scoring module")
        XCTAssertEqual(item.sourceURL, "https://example.com")
        XCTAssertEqual(item.relevanceScore, 0.92, accuracy: 0.001)
        XCTAssertEqual(item.tags, ["ai", "product"])
    }

    func testFocusItemIdentifiable() throws {
        let json = """
        {
            "rank": 2,
            "title": "Test item",
            "why_it_matters": "Testing",
            "next_action": "Verify",
            "source_url": "",
            "relevance_score": 0.5,
            "tags": []
        }
        """.data(using: .utf8)!

        let item = try JSONDecoder().decode(FocusItem.self, from: json)
        XCTAssertEqual(item.id, "2-Test item")
    }
}

final class DailyBriefTests: XCTestCase {

    func testDecodeFullBrief() throws {
        let json = """
        {
            "date": "2026-03-15",
            "focus_items": [
                {
                    "rank": 1,
                    "title": "Focus item",
                    "why_it_matters": "Important",
                    "next_action": "Do it",
                    "source_url": "",
                    "relevance_score": 0.8,
                    "tags": ["ai"]
                }
            ],
            "digest_quality": {"ai_article_ratio": 0.75, "high_signal_ratio": 0.5},
            "profile_summary": {"name": "Builder", "goals_count": "3"}
        }
        """.data(using: .utf8)!

        let brief = try JSONDecoder().decode(DailyBrief.self, from: json)
        XCTAssertEqual(brief.date, "2026-03-15")
        XCTAssertEqual(brief.focusItems.count, 1)
        XCTAssertEqual(brief.focusItems[0].title, "Focus item")
        XCTAssertEqual(brief.digestQuality["ai_article_ratio"], 0.75)
        XCTAssertEqual(brief.profileSummary["name"], "Builder")
    }

    func testDecodeNullOptionals() throws {
        let json = """
        {
            "date": "2026-03-15",
            "focus_items": [],
            "digest_quality": null,
            "profile_summary": null
        }
        """.data(using: .utf8)!

        let brief = try JSONDecoder().decode(DailyBrief.self, from: json)
        XCTAssertEqual(brief.date, "2026-03-15")
        XCTAssertTrue(brief.focusItems.isEmpty)
        XCTAssertTrue(brief.digestQuality.isEmpty)
        XCTAssertTrue(brief.profileSummary.isEmpty)
    }

    func testDecodeMissingOptionals() throws {
        let json = """
        {
            "date": "2026-03-15",
            "focus_items": []
        }
        """.data(using: .utf8)!

        let brief = try JSONDecoder().decode(DailyBrief.self, from: json)
        XCTAssertTrue(brief.digestQuality.isEmpty)
        XCTAssertTrue(brief.profileSummary.isEmpty)
    }

    func testMemberwiseInit() {
        let brief = DailyBrief(date: "2026-01-01")
        XCTAssertEqual(brief.date, "2026-01-01")
        XCTAssertTrue(brief.focusItems.isEmpty)
    }
}

final class UserProfileTests: XCTestCase {

    func testDecodeProfile() throws {
        let json = """
        {
            "name": "Pierre",
            "goals": ["Ship CortexOS"],
            "interests": ["AI", "Swift"],
            "current_projects": ["CortexOS"],
            "constraints": ["Solo founder"],
            "ignored_topics": ["crypto"]
        }
        """.data(using: .utf8)!

        let profile = try JSONDecoder().decode(UserProfile.self, from: json)
        XCTAssertEqual(profile.name, "Pierre")
        XCTAssertEqual(profile.goals, ["Ship CortexOS"])
        XCTAssertEqual(profile.interests, ["AI", "Swift"])
        XCTAssertEqual(profile.currentProjects, ["CortexOS"])
        XCTAssertEqual(profile.constraints, ["Solo founder"])
        XCTAssertEqual(profile.ignoredTopics, ["crypto"])
    }

    func testEmptyProfile() {
        let profile = UserProfile.empty
        XCTAssertEqual(profile.name, "")
        XCTAssertTrue(profile.goals.isEmpty)
        XCTAssertTrue(profile.interests.isEmpty)
    }

    func testProfileRoundtrip() throws {
        let profile = UserProfile(
            name: "Test",
            goals: ["g1"],
            interests: ["i1"],
            currentProjects: ["p1"],
            constraints: [],
            ignoredTopics: []
        )
        let data = try JSONEncoder().encode(profile)
        let decoded = try JSONDecoder().decode(UserProfile.self, from: data)
        XCTAssertEqual(decoded.name, profile.name)
        XCTAssertEqual(decoded.goals, profile.goals)
        XCTAssertEqual(decoded.currentProjects, profile.currentProjects)
    }
}

final class ProfileUpdateTests: XCTestCase {

    func testEncodePartialUpdate() throws {
        let update = ProfileUpdate(name: "Pierre", goals: ["Ship v1"])
        let data = try JSONEncoder().encode(update)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertNotNil(dict?["name"])
        XCTAssertNotNil(dict?["goals"])
    }
}

final class DigestScoreTests: XCTestCase {

    func testDecodeDigestScore() throws {
        let json = """
        {
            "total_articles": 10,
            "ai_article_ratio": 0.6,
            "high_signal_ratio": 0.4,
            "signal_to_noise_ratio": 1.5,
            "context_keyword_coverage": 0.3,
            "project_fit_score": 0.7,
            "top_articles": [
                {"title": "LLM breakthroughs", "score": 0.95}
            ]
        }
        """.data(using: .utf8)!

        let score = try JSONDecoder().decode(DigestScore.self, from: json)
        XCTAssertEqual(score.totalArticles, 10)
        XCTAssertEqual(score.aiArticleRatio, 0.6, accuracy: 0.001)
        XCTAssertEqual(score.highSignalRatio, 0.4, accuracy: 0.001)
        XCTAssertEqual(score.signalToNoiseRatio, 1.5, accuracy: 0.001)
        XCTAssertEqual(score.projectFitScore, 0.7, accuracy: 0.001)
        XCTAssertEqual(score.topArticles.count, 1)
        XCTAssertEqual(score.topArticles[0].title, "LLM breakthroughs")
        XCTAssertEqual(score.topArticles[0].score, 0.95, accuracy: 0.001)
    }

    func testArticleScoreItemIdentifiable() throws {
        let json = """
        {"title": "Test article", "score": 0.5}
        """.data(using: .utf8)!

        let item = try JSONDecoder().decode(ArticleScoreItem.self, from: json)
        XCTAssertEqual(item.id, "Test article")
    }
}

final class KnowledgeNoteTests: XCTestCase {

    func testDecodeNote() throws {
        let json = """
        {
            "id": "abc123",
            "title": "Context-Aware Retrieval",
            "insight": "Dynamic embeddings work better.",
            "implication": "Use in CortexOS.",
            "action": "Prototype it.",
            "source_url": "https://example.com",
            "tags": ["AI", "retrieval"],
            "created_at": "2026-03-15T10:00:00Z",
            "updated_at": "",
            "archived": false
        }
        """.data(using: .utf8)!

        let note = try JSONDecoder().decode(KnowledgeNote.self, from: json)
        XCTAssertEqual(note.id, "abc123")
        XCTAssertEqual(note.title, "Context-Aware Retrieval")
        XCTAssertEqual(note.tags, ["AI", "retrieval"])
        XCTAssertFalse(note.archived)
        XCTAssertEqual(note.sourceURL, "https://example.com")
    }

    func testNoteIdentifiable() throws {
        let note = KnowledgeNote.example
        XCTAssertEqual(note.id, "abc123")
    }

    func testNoteHashable() {
        let note1 = KnowledgeNote.example
        let note2 = KnowledgeNote.example
        // Both have same id, both hash equal
        XCTAssertEqual(note1, note2)
    }

    func testDisplayTags() {
        let note = KnowledgeNote.example
        XCTAssertTrue(note.displayTags.contains("#AI"))
        XCTAssertTrue(note.displayTags.contains("#retrieval"))
    }

    func testCreatedDate() {
        let note = KnowledgeNote.example
        // createdAt is set via ISO8601DateFormatter so createdDate should parse
        XCTAssertNotNil(note.createdDate)
    }

    func testNoteRoundtrip() throws {
        let original = KnowledgeNote.example
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(KnowledgeNote.self, from: data)
        XCTAssertEqual(decoded.id, original.id)
        XCTAssertEqual(decoded.title, original.title)
        XCTAssertEqual(decoded.tags, original.tags)
    }
}

final class NoteRequestTests: XCTestCase {

    func testCreateRequestEncode() throws {
        let req = NoteCreateRequest(title: "Test", insight: "Insight", tags: ["ai"])
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["title"] as? String, "Test")
        XCTAssertEqual(dict?["insight"] as? String, "Insight")
    }

    func testUpdateRequestEncode() throws {
        let req = NoteUpdateRequest(title: "Updated", archived: true)
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["title"] as? String, "Updated")
        XCTAssertEqual(dict?["archived"] as? Bool, true)
    }
}
