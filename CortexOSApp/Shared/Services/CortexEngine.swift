//
//  CortexEngine.swift
//  CortexOS
//
//  Client-side engine that wraps APIService with observable state
//  for SwiftUI bindings.
//

import Foundation
#if canImport(WidgetKit)
import WidgetKit
#endif

@MainActor
final class CortexEngine: ObservableObject {

    // MARK: - Published State

    @Published var notes: [KnowledgeNote] = []
    @Published var profile: UserProfile = .empty
    @Published var snapshot: SyncSnapshot?
    @Published var isConnected = false
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Dependencies

    let api: APIService

    init(api: APIService = .shared) {
        self.api = api

        // Always load cached snapshot for instant launch
        Task { [weak self] in
            if let cached = await SnapshotCache.shared.load() {
                self?.snapshot = cached
            }
        }
    }

    // MARK: - Connection

    func checkConnection() async {
        do {
            _ = try await api.health()
            isConnected = true
            errorMessage = nil
        } catch {
            isConnected = false
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Notes

    func fetchNotes() async {
        isLoading = true
        defer { isLoading = false }
        do {
            notes = try await api.listNotes()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createNote(_ request: NoteCreateRequest) async -> Bool {
        do {
            let note = try await api.createNote(request)
            notes.insert(note, at: 0)
            errorMessage = nil
            return true
        } catch {
            // Queue for offline sync — capture always works
            await CaptureQueue.shared.enqueueNote(
                title: request.title,
                sourceURL: request.sourceURL
            )
            errorMessage = nil
            return true
        }
    }

    func deleteNote(_ id: String) async -> Bool {
        do {
            try await api.deleteNote(id: id)
            notes.removeAll { $0.id == id }
            errorMessage = nil
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func searchNotes(query: String) async {
        guard !query.isEmpty else {
            await fetchNotes()
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            notes = try await api.searchNotes(query: query)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Profile

    func fetchProfile() async {
        do {
            profile = try await api.getProfile()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func saveProfile(_ update: ProfileUpdate) async -> Bool {
        do {
            profile = try await api.updateProfile(update)
            errorMessage = nil
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    // MARK: - Sync (single-call pull + offline-first)

    func sync() async {
        if api.isOffline {
            isConnected = false
            // Always load from cache in offline mode
            if snapshot == nil {
                snapshot = await SnapshotCache.shared.load()
            }
            errorMessage = "Offline mode: no server URL configured."
            return
        }
        do {
            snapshot = try await api.fetchSnapshot()
            isConnected = true
            errorMessage = nil

            // Cache for instant launch next time
            if let snapshot { await SnapshotCache.shared.save(snapshot) }

            // Update Lock Screen / Home Screen widget
            updateWidgetData()

            // Flush any queued offline captures
            let flushedNotes = await CaptureQueue.shared.flushNotes(using: api)
            let flushedDecisions = await CaptureQueue.shared.flushDecisions(using: api)
            if flushedNotes + flushedDecisions > 0 {
                // Re-sync to pick up server-side changes
                snapshot = try? await api.fetchSnapshot()
                updateWidgetData()
            }
        } catch {
            isConnected = false
            // Fall back to cached snapshot — app still works offline
            if snapshot == nil {
                snapshot = await SnapshotCache.shared.load()
            }
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Widget Data

    private func updateWidgetData() {
        guard let brief = snapshot?.priorities else { return }

        let widgetPriorities = brief.priorities.prefix(3).map { p in
            WidgetPriority(
                rank: p.rank,
                title: p.title,
                whyItMatters: p.whyItMatters,
                nextStep: p.nextStep
            )
        }

        let data = CortexWidgetData(
            topPriority: widgetPriorities.first,
            priorities: Array(widgetPriorities),
            date: brief.date,
            updatedAt: Date()
        )

        WidgetDataBridge.write(data)

        // Tell WidgetKit to refresh
        #if canImport(WidgetKit)
        WidgetCenter.shared.reloadTimelines(ofKind: "CortexFocusWidget")
        #endif
    }

    // MARK: - Decisions

    func recordDecision(_ request: DecisionCreateRequest) async -> Bool {
        do {
            _ = try await api.recordDecision(request)
            // Merge into local snapshot if available
            if snapshot != nil {
                await sync()
            }
            errorMessage = nil
            return true
        } catch {
            // Queue for offline sync — decisions always save
            await CaptureQueue.shared.enqueueDecision(
                decision: request.decision,
                reason: request.reason,
                project: request.project,
                assumptions: request.assumptions
            )
            errorMessage = nil
            return true
        }
    }

    // MARK: - Feedback (was this useful?)

    func sendFeedback(item: String, useful: Bool) async {
        do {
            try await api.sendFeedback(FeedbackRequest(item: item, useful: useful))
        } catch {
            // Silent — feedback is best-effort, never block UX
        }
    }

    // MARK: - Summary Ingestion

    @Published var lastIngestResult: IngestResult?

    func ingestSummary(content: String, source: String = "", tags: [String] = []) async -> Bool {
        isLoading = true
        defer { isLoading = false }
        do {
            let request = SummaryIngestRequest(content: content, source: source, tags: tags)
            lastIngestResult = try await api.ingestSummary(request)
            errorMessage = nil
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }
}
