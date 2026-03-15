//
//  PipelineStatus.swift
//  CortexOS
//
//  Models for pipeline execution status.
//

import Foundation

struct PipelineStepResult: Codable, Identifiable {
    var id: String { name }

    let name: String
    let status: String
    let startedAt: String?
    let finishedAt: String?
    let durationS: Double
    let error: String?

    enum CodingKeys: String, CodingKey {
        case name, status, error
        case startedAt  = "started_at"
        case finishedAt = "finished_at"
        case durationS  = "duration_s"
    }

    var statusIcon: String {
        switch status {
        case "success": return "checkmark.circle.fill"
        case "running": return "arrow.triangle.2.circlepath"
        case "failed":  return "xmark.circle.fill"
        case "skipped": return "forward.fill"
        default:        return "circle"
        }
    }

    var statusColor: String {
        switch status {
        case "success": return "green"
        case "running": return "blue"
        case "failed":  return "red"
        case "skipped": return "gray"
        default:        return "secondary"
        }
    }
}

struct PipelineResult: Codable {
    let name: String
    let startedAt: String
    let finishedAt: String
    let durationS: Double
    let success: Bool
    let steps: [PipelineStepResult]

    enum CodingKeys: String, CodingKey {
        case name, success, steps
        case startedAt  = "started_at"
        case finishedAt = "finished_at"
        case durationS  = "duration_s"
    }
}

struct PipelineRequest: Codable {
    var useLLM: Bool = false

    enum CodingKeys: String, CodingKey {
        case useLLM = "use_llm"
    }
}
