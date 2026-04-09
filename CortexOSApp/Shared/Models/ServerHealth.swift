//
//  ServerHealth.swift
//  CortexOS
//
//  Health response model.
//

import Foundation

struct ServerHealth: Codable {
    let status: String
    let timestamp: String
}
