//
//  ServerStatus.swift
//  CortexOS
//
//  Health & status response models.
//

import Foundation

struct ServerHealth: Codable {
    let status: String
    let timestamp: String
}

struct ServerStatus: Codable {
    let version: String
    let dataDir: String
    let notesCount: Int
    let llmProvider: String
    let llmModel: String

    enum CodingKeys: String, CodingKey {
        case version
        case dataDir     = "data_dir"
        case notesCount  = "notes_count"
        case llmProvider = "llm_provider"
        case llmModel    = "llm_model"
    }
}
