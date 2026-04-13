//
//  APIService.swift
//  CortexOS
//
//  Networking layer that talks to the CortexOS Python API server.
//  Uses async/await and Codable for clean Swift concurrency.
//

import Foundation

// MARK: - Errors

enum APIError: LocalizedError {
    case invalidURL
    case httpError(statusCode: Int, body: String)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL."
        case .httpError(let code, let body):
            return "HTTP \(code): \(body)"
        case .decodingError(let err):
            return "Decoding error: \(err.localizedDescription)"
        case .networkError(let err):
            return "Network error: \(err.localizedDescription)"
        }
    }
}

// MARK: - Service

@MainActor
final class APIService: ObservableObject {
    @Published var baseURL: String {
        didSet { UserDefaults.standard.set(baseURL, forKey: "cortex_api_url") }
    }

    var isOffline: Bool {
        baseURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    static let shared = APIService()

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: String? = nil) {
        let saved = UserDefaults.standard.string(forKey: "cortex_api_url")
        self.baseURL = baseURL ?? saved ?? ""

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    // MARK: - Generic request

    private func request<T: Decodable>(
        _ method: String,
        path: String,
        body: (any Encodable)? = nil
    ) async throws -> T {
        if isOffline {
            throw APIError.networkError(NSError(domain: NSURLErrorDomain, code: -1009, userInfo: [NSLocalizedDescriptionKey: "Offline mode: no server URL configured"]))
        }
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body {
            req.httpBody = try encoder.encode(AnyEncodable(body))
        }
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: req)
        } catch {
            throw APIError.networkError(error)
        }
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(statusCode: http.statusCode, body: body)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func requestNoContent(
        _ method: String,
        path: String,
        body: (any Encodable)? = nil
    ) async throws {
        if isOffline {
            throw APIError.networkError(NSError(domain: NSURLErrorDomain, code: -1009, userInfo: [NSLocalizedDescriptionKey: "Offline mode: no server URL configured"]))
        }
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body {
            req.httpBody = try encoder.encode(AnyEncodable(body))
        }
        let (data, response) = try await session.data(for: req)
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(statusCode: http.statusCode, body: body)
        }
    }

    // MARK: - Health

    func health() async throws -> ServerHealth {
        if isOffline {
            return await OfflineStore.shared.serverHealth()
        }
        try await request("GET", path: "/health")
    }

    // MARK: - Knowledge Notes

    func listNotes(includeArchived: Bool = false) async throws -> [KnowledgeNote] {
        if isOffline {
            return await OfflineStore.shared.listNotes(includeArchived: includeArchived)
        }
        try await request("GET", path: "/notes/?include_archived=\(includeArchived)")
    }

    func getNote(id: String) async throws -> KnowledgeNote {
        if isOffline, let note = await OfflineStore.shared.getNote(id: id) {
            return note
        }
        try await request("GET", path: "/notes/\(id)")
    }

    func createNote(_ body: NoteCreateRequest) async throws -> KnowledgeNote {
        if isOffline {
            return await OfflineStore.shared.createNote(body)
        }
        try await request("POST", path: "/notes/", body: body)
    }

    func updateNote(id: String, _ body: NoteUpdateRequest) async throws -> KnowledgeNote {
        if isOffline, let note = await OfflineStore.shared.updateNote(id: id, with: body) {
            return note
        }
        try await request("PATCH", path: "/notes/\(id)", body: body)
    }

    func deleteNote(id: String) async throws {
        if isOffline {
            await OfflineStore.shared.deleteNote(id: id)
            return
        }
        try await requestNoContent("DELETE", path: "/notes/\(id)")
    }

    func searchNotes(query: String) async throws -> [KnowledgeNote] {
        if isOffline {
            return await OfflineStore.shared.searchNotes(query: query)
        }
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return try await request("GET", path: "/notes/search?q=\(encoded)")
    }

    // MARK: - Profile

    func getProfile() async throws -> UserProfile {
        if isOffline {
            return await OfflineStore.shared.getProfile()
        }
        try await request("GET", path: "/profile/")
    }

    func updateProfile(_ body: ProfileUpdate) async throws -> UserProfile {
        if isOffline {
            return await OfflineStore.shared.updateProfile(body)
        }
        try await request("PATCH", path: "/profile/", body: body)
    }

    // MARK: - Sync

    func fetchSnapshot() async throws -> SyncSnapshot {
        if isOffline {
            return await OfflineStore.shared.snapshot()
        }
        try await request("GET", path: "/sync/snapshot")
    }

    // MARK: - Context (mutations)

    func recordDecision(_ body: DecisionCreateRequest) async throws -> SyncDecision {
        if isOffline {
            return await OfflineStore.shared.recordDecision(body)
        }
        try await request("POST", path: "/context/decision", body: body)
    }

    func recordOutcome(_ body: OutcomeCreateRequest) async throws -> SyncDecision {
        try await request("POST", path: "/context/outcome", body: body)
    }

    func storeInsight(_ body: InsightCreateRequest) async throws -> SyncInsight {
        try await request("POST", path: "/context/insight", body: body)
    }

    // MARK: - Feedback

    func sendFeedback(_ body: FeedbackRequest) async throws {
        if isOffline {
            return
        }
        try await requestNoContent("POST", path: "/context/feedback", body: body)
    }

    // MARK: - Summary Ingestion

    func ingestSummary(_ body: SummaryIngestRequest) async throws -> IngestResult {
        if isOffline {
            return await OfflineStore.shared.ingestSummary(body)
        }
        try await request("POST", path: "/ingest/summary", body: body)
    }
}

// MARK: - Helpers

/// Type-erased Encodable wrapper.
private struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void

    init(_ wrapped: any Encodable) {
        _encode = { encoder in
            try wrapped.encode(to: encoder)
        }
    }

    func encode(to encoder: Encoder) throws {
        try _encode(encoder)
    }
}
