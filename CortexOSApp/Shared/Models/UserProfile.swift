//
//  UserProfile.swift
//  CortexOS
//
//  User profile model for CortexOS context memory.
//

import Foundation

struct UserProfile: Codable {
    var name: String
    var goals: [String]
    var interests: [String]
    var currentProjects: [String]
    var constraints: [String]
    var ignoredTopics: [String]

    enum CodingKeys: String, CodingKey {
        case name, goals, interests, constraints
        case currentProjects = "current_projects"
        case ignoredTopics = "ignored_topics"
    }

    static let empty = UserProfile(
        name: "",
        goals: [],
        interests: [],
        currentProjects: [],
        constraints: [],
        ignoredTopics: []
    )
}

struct ProfileUpdate: Codable {
    var name: String?
    var goals: [String]?
    var interests: [String]?
    var currentProjects: [String]?
    var constraints: [String]?
    var ignoredTopics: [String]?

    enum CodingKeys: String, CodingKey {
        case name, goals, interests, constraints
        case currentProjects = "current_projects"
        case ignoredTopics = "ignored_topics"
    }
}
