//
//  WidgetData.swift
//  CortexOS
//
//  Shared data bridge between the main app and the widget extension.
//  Lives in /Shared so both targets can compile it.
//
//  The app writes this after every sync.
//  The widget reads it on timeline refresh.
//  Stored in the App Group shared container as a tiny JSON file.
//

import Foundation

// MARK: - Widget Data (what the widget displays)

struct CortexWidgetData: Codable {
    let topPriority: WidgetPriority?
    let priorities: [WidgetPriority]  // up to 3
    let date: String
    let updatedAt: Date

    static let empty = CortexWidgetData(
        topPriority: nil,
        priorities: [],
        date: "",
        updatedAt: .distantPast
    )
}

struct WidgetPriority: Codable, Identifiable {
    var id: String { title }
    let rank: Int
    let title: String
    let whyItMatters: String
    let nextStep: String
}

// MARK: - App Group bridge

enum WidgetDataBridge {
    static let appGroupID = "group.me.ph7.cortexos"

    private static var sharedURL: URL? {
        FileManager.default.containerURL(
            forSecurityApplicationGroupIdentifier: appGroupID
        )?.appendingPathComponent("widget_data.json")
    }

    /// Called by the main app after sync to update widget data.
    static func write(_ data: CortexWidgetData) {
        guard let url = sharedURL else { return }
        guard let encoded = try? JSONEncoder().encode(data) else { return }
        try? encoded.write(to: url, options: .atomic)
    }

    /// Called by the widget extension to read current data.
    static func read() -> CortexWidgetData {
        guard let url = sharedURL,
              let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode(CortexWidgetData.self, from: data)
        else {
            return .empty
        }
        return decoded
    }
}
