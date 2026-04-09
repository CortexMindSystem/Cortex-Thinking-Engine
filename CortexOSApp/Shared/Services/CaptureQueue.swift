//
//  CaptureQueue.swift
//  CortexOS
//
//  Offline-first capture queue. Notes are saved locally first,
//  then flushed to the server when connectivity returns.
//
//  "Capture must always work." — offline or not.
//

import Foundation

actor CaptureQueue {
    static let shared = CaptureQueue()

    // MARK: - Types

    struct QueuedNote: Codable, Identifiable {
        let id: UUID
        let title: String
        let sourceURL: String
        let capturedAt: Date
    }

    struct QueuedDecision: Codable, Identifiable {
        let id: UUID
        let decision: String
        let reason: String
        let project: String
        let assumptions: [String]
        let capturedAt: Date
    }

    // MARK: - State

    private var notes: [QueuedNote] = []
    private var decisions: [QueuedDecision] = []

    private let notesURL: URL
    private let decisionsURL: URL

    private init() {
        let support = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0].appendingPathComponent("CortexOS", isDirectory: true)

        try? FileManager.default.createDirectory(
            at: support,
            withIntermediateDirectories: true
        )

        notesURL = support.appendingPathComponent("capture_queue_notes.json")
        decisionsURL = support.appendingPathComponent("capture_queue_decisions.json")

        // Load persisted queues
        if let data = try? Data(contentsOf: notesURL),
           let saved = try? JSONDecoder().decode([QueuedNote].self, from: data) {
            notes = saved
        }

        if let data = try? Data(contentsOf: decisionsURL),
           let saved = try? JSONDecoder().decode([QueuedDecision].self, from: data) {
            decisions = saved
        }
    }

    // MARK: - Enqueue

    func enqueueNote(title: String, sourceURL: String = "") {
        let item = QueuedNote(
            id: UUID(),
            title: title,
            sourceURL: sourceURL,
            capturedAt: Date()
        )
        notes.append(item)
        persistNotes()
    }

    func enqueueDecision(
        decision: String,
        reason: String = "",
        project: String = "",
        assumptions: [String] = []
    ) {
        let item = QueuedDecision(
            id: UUID(),
            decision: decision,
            reason: reason,
            project: project,
            assumptions: assumptions,
            capturedAt: Date()
        )
        decisions.append(item)
        persistDecisions()
    }

    // MARK: - Flush (send to server)

    @MainActor
    func flushNotes(using api: APIService) async -> Int {
        let queued = await getQueuedNotes()
        guard !queued.isEmpty else { return 0 }

        var remaining: [QueuedNote] = []
        var flushed = 0

        for item in queued {
            let request = NoteCreateRequest(
                title: item.title,
                insight: "",
                sourceURL: item.sourceURL,
                tags: []
            )

            do {
                _ = try await api.createNote(request)
                flushed += 1
            } catch {
                remaining.append(item)
            }
        }

        await setQueuedNotes(remaining)
        return flushed
    }

    @MainActor
    func flushDecisions(using api: APIService) async -> Int {
        let queued = await getQueuedDecisions()
        guard !queued.isEmpty else { return 0 }

        var remaining: [QueuedDecision] = []
        var flushed = 0

        for item in queued {
            let request = DecisionCreateRequest(
                decision: item.decision,
                reason: item.reason,
                project: item.project,
                assumptions: item.assumptions
            )

            do {
                _ = try await api.recordDecision(request)
                flushed += 1
            } catch {
                remaining.append(item)
            }
        }

        await setQueuedDecisions(remaining)
        return flushed
    }

    // MARK: - Counts

    var pendingNoteCount: Int { notes.count }
    var pendingDecisionCount: Int { decisions.count }
    var totalPending: Int { notes.count + decisions.count }

    // MARK: - Actor-isolated helpers

    private func getQueuedNotes() -> [QueuedNote] { notes }
    private func getQueuedDecisions() -> [QueuedDecision] { decisions }

    private func setQueuedNotes(_ value: [QueuedNote]) {
        notes = value
        persistNotes()
    }

    private func setQueuedDecisions(_ value: [QueuedDecision]) {
        decisions = value
        persistDecisions()
    }

    // MARK: - Persistence

    private func persistNotes() {
        guard let data = try? JSONEncoder().encode(notes) else { return }
        try? data.write(to: notesURL, options: .atomic)
    }

    private func persistDecisions() {
        guard let data = try? JSONEncoder().encode(decisions) else { return }
        try? data.write(to: decisionsURL, options: .atomic)
    }
}
