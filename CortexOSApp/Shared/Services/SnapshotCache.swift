//
//  SnapshotCache.swift
//  CortexOS
//
//  Local-first persistence for the sync snapshot.
//  App opens instantly with last-known data.
//  Sync updates the cache silently in the background.
//
//  Design: JSON file in Application Support. No database needed —
//  the snapshot is a single document that replaces itself on each sync.
//

import Foundation

actor SnapshotCache {
    static let shared = SnapshotCache()

    private let fileURL: URL

    private init() {
        let support = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0].appendingPathComponent("CortexOS", isDirectory: true)

        try? FileManager.default.createDirectory(
            at: support,
            withIntermediateDirectories: true
        )

        fileURL = support.appendingPathComponent("snapshot.json")
    }

    // MARK: - Read

    func load() -> SyncSnapshot? {
        guard let data = try? Data(contentsOf: fileURL) else { return nil }
        return try? JSONDecoder().decode(SyncSnapshot.self, from: data)
    }

    // MARK: - Write

    func save(_ snapshot: SyncSnapshot) {
        guard let data = try? JSONEncoder().encode(snapshot) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }

    // MARK: - Clear (for logout or reset)

    func clear() {
        try? FileManager.default.removeItem(at: fileURL)
    }
}
