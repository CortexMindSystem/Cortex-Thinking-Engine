//
//  ModelDecodingTests.swift
//  CortexOSKitTests
//
//  Tests JSON decoding for all CortexOS models to ensure
//  API contract compliance and prevent regressions.
//

import XCTest
@testable import CortexOSKit

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

// MARK: - ServerHealth

final class ServerHealthTests: XCTestCase {

    func testDecodeServerHealth() throws {
        let json = """
        {"status": "ok", "timestamp": "2026-03-15T10:00:00Z"}
        """.data(using: .utf8)!

        let health = try JSONDecoder().decode(ServerHealth.self, from: json)
        XCTAssertEqual(health.status, "ok")
        XCTAssertFalse(health.timestamp.isEmpty)
    }
}
