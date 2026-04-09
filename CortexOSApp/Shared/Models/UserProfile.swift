//
//  UserProfile.swift
//  CortexOS
//
//  User profile model for CortexOS context memory.
//

import Foundation

struct UserProfile: Codable {
    var name: String
    var role: String
    var goals: [String]
    var interests: [String]
    var currentProjects: [String]
    var constraints: [String]
    var ignoredTopics: [String]

    enum CodingKeys: String, CodingKey {
        case name, role, goals, interests, constraints
        case currentProjects = "current_projects"
        case ignoredTopics = "ignored_topics"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        name = try container.decode(String.self, forKey: .name)
        role = try container.decodeIfPresent(String.self, forKey: .role) ?? ""
        goals = try container.decode([String].self, forKey: .goals)
        interests = try container.decode([String].self, forKey: .interests)
        currentProjects = try container.decode([String].self, forKey: .currentProjects)
        constraints = try container.decode([String].self, forKey: .constraints)
        ignoredTopics = try container.decode([String].self, forKey: .ignoredTopics)
    }

    init(name: String = "", role: String = "", goals: [String] = [], interests: [String] = [], currentProjects: [String] = [], constraints: [String] = [], ignoredTopics: [String] = []) {
        self.name = name
        self.role = role
        self.goals = goals
        self.interests = interests
        self.currentProjects = currentProjects
        self.constraints = constraints
        self.ignoredTopics = ignoredTopics
    }

    static let empty = UserProfile()
}

struct ProfileUpdate: Codable {
    var name: String?
    var role: String?
    var goals: [String]?
    var interests: [String]?
    var currentProjects: [String]?
    var constraints: [String]?
    var ignoredTopics: [String]?

    enum CodingKeys: String, CodingKey {
        case name, role, goals, interests, constraints
        case currentProjects = "current_projects"
        case ignoredTopics = "ignored_topics"
    }
}
