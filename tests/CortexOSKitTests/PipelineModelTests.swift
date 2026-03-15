//
//  PipelineModelTests.swift
//  CortexOSKitTests
//
//  Tests JSON decoding for Pipeline and Server models.
//

import XCTest
@testable import CortexOSKit

final class PipelineStepResultTests: XCTestCase {

    func testDecodeStep() throws {
        let json = """
        {
            "name": "ingest_feed",
            "status": "success",
            "started_at": "2026-03-15T10:00:00Z",
            "finished_at": "2026-03-15T10:00:05Z",
            "duration_s": 5.12,
            "error": null
        }
        """.data(using: .utf8)!

        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.name, "ingest_feed")
        XCTAssertEqual(step.status, "success")
        XCTAssertEqual(step.durationS, 5.12, accuracy: 0.001)
        XCTAssertNil(step.error)
    }

    func testStepIdentifiable() throws {
        let json = """
        {"name": "score", "status": "running", "started_at": null, "finished_at": null, "duration_s": 0, "error": null}
        """.data(using: .utf8)!

        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.id, "score")
    }

    func testStatusIconSuccess() throws {
        let json = """
        {"name": "s", "status": "success", "started_at": null, "finished_at": null, "duration_s": 0, "error": null}
        """.data(using: .utf8)!
        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.statusIcon, "checkmark.circle.fill")
        XCTAssertEqual(step.statusColor, "green")
    }

    func testStatusIconFailed() throws {
        let json = """
        {"name": "s", "status": "failed", "started_at": null, "finished_at": null, "duration_s": 0, "error": "boom"}
        """.data(using: .utf8)!
        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.statusIcon, "xmark.circle.fill")
        XCTAssertEqual(step.statusColor, "red")
    }

    func testStatusIconRunning() throws {
        let json = """
        {"name": "s", "status": "running", "started_at": null, "finished_at": null, "duration_s": 0, "error": null}
        """.data(using: .utf8)!
        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.statusIcon, "arrow.triangle.2.circlepath")
        XCTAssertEqual(step.statusColor, "blue")
    }

    func testStatusIconSkipped() throws {
        let json = """
        {"name": "s", "status": "skipped", "started_at": null, "finished_at": null, "duration_s": 0, "error": null}
        """.data(using: .utf8)!
        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.statusIcon, "forward.fill")
        XCTAssertEqual(step.statusColor, "gray")
    }

    func testStatusIconUnknown() throws {
        let json = """
        {"name": "s", "status": "pending", "started_at": null, "finished_at": null, "duration_s": 0, "error": null}
        """.data(using: .utf8)!
        let step = try JSONDecoder().decode(PipelineStepResult.self, from: json)
        XCTAssertEqual(step.statusIcon, "circle")
        XCTAssertEqual(step.statusColor, "secondary")
    }
}

final class PipelineResultTests: XCTestCase {

    func testDecodePipeline() throws {
        let json = """
        {
            "name": "CortexOS Pipeline",
            "started_at": "2026-03-15T10:00:00Z",
            "finished_at": "2026-03-15T10:00:10Z",
            "duration_s": 10.5,
            "success": true,
            "steps": [
                {
                    "name": "ingest",
                    "status": "success",
                    "started_at": "2026-03-15T10:00:00Z",
                    "finished_at": "2026-03-15T10:00:05Z",
                    "duration_s": 5.0,
                    "error": null
                }
            ]
        }
        """.data(using: .utf8)!

        let result = try JSONDecoder().decode(PipelineResult.self, from: json)
        XCTAssertEqual(result.name, "CortexOS Pipeline")
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.durationS, 10.5, accuracy: 0.001)
        XCTAssertEqual(result.steps.count, 1)
        XCTAssertEqual(result.steps[0].name, "ingest")
    }
}

final class PipelineRequestTests: XCTestCase {

    func testEncodeRequest() throws {
        let req = PipelineRequest(useLLM: true)
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["use_llm"] as? Bool, true)
    }

    func testDefaultUseLLMIsFalse() {
        let req = PipelineRequest()
        XCTAssertFalse(req.useLLM)
    }
}

final class ServerStatusTests: XCTestCase {

    func testDecodeServerStatus() throws {
        let json = """
        {
            "version": "0.1.0",
            "data_dir": "/home/user/.cortexos",
            "notes_count": 42,
            "llm_provider": "openai",
            "llm_model": "gpt-4o"
        }
        """.data(using: .utf8)!

        let status = try JSONDecoder().decode(ServerStatus.self, from: json)
        XCTAssertEqual(status.version, "0.1.0")
        XCTAssertEqual(status.notesCount, 42)
        XCTAssertEqual(status.llmProvider, "openai")
        XCTAssertEqual(status.llmModel, "gpt-4o")
    }

    func testDecodeServerHealth() throws {
        let json = """
        {"status": "ok", "timestamp": "2026-03-15T10:00:00Z"}
        """.data(using: .utf8)!

        let health = try JSONDecoder().decode(ServerHealth.self, from: json)
        XCTAssertEqual(health.status, "ok")
        XCTAssertFalse(health.timestamp.isEmpty)
    }
}

final class SocialPostTests: XCTestCase {

    func testDecodePost() throws {
        let json = """
        {
            "text": "Great insight about AI",
            "platform": "twitter",
            "note_id": "abc123"
        }
        """.data(using: .utf8)!

        let post = try JSONDecoder().decode(SocialPost.self, from: json)
        XCTAssertEqual(post.text, "Great insight about AI")
        XCTAssertEqual(post.platform, "twitter")
        XCTAssertEqual(post.noteID, "abc123")
    }

    func testPostIdentifiable() {
        let post = SocialPost.example
        XCTAssertEqual(post.id, "abc123twitter")
    }

    func testPlatformIcons() {
        XCTAssertEqual(SocialPost(text: "", platform: "twitter", noteID: "").platformIcon, "bird")
        XCTAssertEqual(SocialPost(text: "", platform: "linkedin", noteID: "").platformIcon, "briefcase.fill")
        XCTAssertEqual(SocialPost(text: "", platform: "bluesky", noteID: "").platformIcon, "cloud.fill")
        XCTAssertEqual(SocialPost(text: "", platform: "mastodon", noteID: "").platformIcon, "text.bubble.fill")
    }

    func testPostRoundtrip() throws {
        let original = SocialPost.example
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(SocialPost.self, from: data)
        XCTAssertEqual(decoded.text, original.text)
        XCTAssertEqual(decoded.platform, original.platform)
        XCTAssertEqual(decoded.noteID, original.noteID)
    }
}

final class PostGenerateRequestTests: XCTestCase {

    func testEncodeRequest() throws {
        let req = PostGenerateRequest(limit: 5, platform: "twitter", useLLM: true)
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["limit"] as? Int, 5)
        XCTAssertEqual(dict?["platform"] as? String, "twitter")
        XCTAssertEqual(dict?["use_llm"] as? Bool, true)
    }

    func testDefaults() {
        let req = PostGenerateRequest()
        XCTAssertEqual(req.limit, 3)
        XCTAssertEqual(req.platform, "general")
        XCTAssertFalse(req.useLLM)
    }
}

final class FocusRequestTests: XCTestCase {

    func testEncodeRequest() throws {
        let req = FocusRequest(digestPath: "/path/to/digest.md", useLLM: false)
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["digest_path"] as? String, "/path/to/digest.md")
        XCTAssertEqual(dict?["use_llm"] as? Bool, false)
    }

    func testDefaults() {
        let req = FocusRequest()
        XCTAssertNil(req.digestPath)
        XCTAssertFalse(req.useLLM)
    }
}

final class DigestEvalRequestTests: XCTestCase {

    func testEncodeRequest() throws {
        let req = DigestEvalRequest(path: "/digest.md", context: ["ai", "ml"])
        let data = try JSONEncoder().encode(req)
        let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        XCTAssertEqual(dict?["path"] as? String, "/digest.md")
    }
}
