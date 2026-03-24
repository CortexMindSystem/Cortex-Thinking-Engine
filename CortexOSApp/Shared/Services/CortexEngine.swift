//
//  CortexEngine.swift
//  CortexOS
//
//  Client-side engine that wraps APIService with observable state
//  for SwiftUI bindings.
//

import Foundation

@MainActor
final class CortexEngine: ObservableObject {

    // MARK: - Published State

    @Published var notes: [KnowledgeNote] = []
    @Published var posts: [SocialPost] = []
    @Published var pipelineResult: PipelineResult?
    @Published var serverStatus: ServerStatus?
    @Published var dailyBrief: DailyBrief?
    @Published var profile: UserProfile = .empty
    @Published var digestScore: DigestScore?
    @Published var snapshot: SyncSnapshot?
    @Published var isConnected = false
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Dependencies

    let api: APIService

    init(api: APIService = .shared) {
        self.api = api
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

    func fetchStatus() async {
        do {
            serverStatus = try await api.status()
            isConnected = true
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
            errorMessage = error.localizedDescription
            return false
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

    // MARK: - Posts

    func generatePosts(limit: Int = 3, platform: String = "general", useLLM: Bool = false) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let request = PostGenerateRequest(limit: limit, platform: platform, useLLM: useLLM)
            posts = try await api.generatePosts(request)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Pipeline

    func runPipeline(useLLM: Bool = false) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let request = PipelineRequest(useLLM: useLLM)
            pipelineResult = try await api.runPipeline(request)
            errorMessage = nil
            // Refresh notes after pipeline
            await fetchNotes()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Focus (primary feature)

    func fetchTodayBrief() async {
        do {
            dailyBrief = try await api.getTodayBrief()
            errorMessage = nil
        } catch {
            // 404 is expected when no brief exists yet
            dailyBrief = nil
        }
    }

    func generateFocusBrief(useLLM: Bool = false) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let request = FocusRequest(useLLM: useLLM)
            dailyBrief = try await api.generateBrief(request)
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

    // MARK: - Digest Evaluation

    func evaluateDigest() async {
        isLoading = true
        defer { isLoading = false }
        do {
            digestScore = try await api.evaluateDigest()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Sync (single-call pull)

    func sync() async {
        do {
            snapshot = try await api.fetchSnapshot()
            isConnected = true
            errorMessage = nil
        } catch {
            isConnected = false
            errorMessage = error.localizedDescription
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
