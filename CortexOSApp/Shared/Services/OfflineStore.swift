import Foundation

actor OfflineStore {
    static let shared = OfflineStore()

    private let notesURL: URL
    private let profileURL: URL
    private let decisionsURL: URL
    private let insightsURL: URL

    private var notes: [KnowledgeNote] = []
    private var profile: UserProfile = .empty
    private var decisions: [SyncDecision] = []
    private var insights: [SyncInsight] = []

    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let iso = ISO8601DateFormatter()

    private init() {
        let support = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0].appendingPathComponent("CortexOS", isDirectory: true)

        try? FileManager.default.createDirectory(
            at: support,
            withIntermediateDirectories: true
        )

        notesURL = support.appendingPathComponent("offline_notes.json")
        profileURL = support.appendingPathComponent("offline_profile.json")
        decisionsURL = support.appendingPathComponent("offline_decisions.json")
        insightsURL = support.appendingPathComponent("offline_insights.json")

        if let data = try? Data(contentsOf: notesURL),
           let value = try? decoder.decode([KnowledgeNote].self, from: data) {
            notes = value
        }

        if let data = try? Data(contentsOf: profileURL),
           let value = try? decoder.decode(UserProfile.self, from: data) {
            profile = value
        }

        if let data = try? Data(contentsOf: decisionsURL),
           let value = try? decoder.decode([SyncDecision].self, from: data) {
            decisions = value
        }

        if let data = try? Data(contentsOf: insightsURL),
           let value = try? decoder.decode([SyncInsight].self, from: data) {
            insights = value
        }
    }

    func serverHealth() -> ServerHealth {
        ServerHealth(status: "local", timestamp: iso.string(from: Date()))
    }

    func listNotes(includeArchived: Bool = false) -> [KnowledgeNote] {
        orderedNotes().filter { includeArchived || !$0.archived }
    }

    func getNote(id: String) -> KnowledgeNote? {
        notes.first(where: { $0.id == id })
    }

    func createNote(_ body: NoteCreateRequest) -> KnowledgeNote {
        let now = iso.string(from: Date())
        let note = KnowledgeNote(
            id: UUID().uuidString,
            title: body.title,
            insight: body.insight,
            implication: body.implication,
            action: body.action,
            sourceURL: body.sourceURL,
            tags: body.tags,
            createdAt: now,
            updatedAt: now,
            archived: false
        )
        notes.insert(note, at: 0)
        persistNotes()
        return note
    }

    func updateNote(id: String, with body: NoteUpdateRequest) -> KnowledgeNote? {
        guard let idx = notes.firstIndex(where: { $0.id == id }) else { return nil }
        notes[idx].title = body.title ?? notes[idx].title
        notes[idx].insight = body.insight ?? notes[idx].insight
        notes[idx].implication = body.implication ?? notes[idx].implication
        notes[idx].action = body.action ?? notes[idx].action
        notes[idx].sourceURL = body.sourceURL ?? notes[idx].sourceURL
        notes[idx].tags = body.tags ?? notes[idx].tags
        notes[idx].archived = body.archived ?? notes[idx].archived
        notes[idx].updatedAt = iso.string(from: Date())
        persistNotes()
        return notes[idx]
    }

    func deleteNote(id: String) {
        notes.removeAll { $0.id == id }
        persistNotes()
    }

    func searchNotes(query: String) -> [KnowledgeNote] {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !q.isEmpty else { return listNotes() }
        return orderedNotes().filter {
            ($0.title + " " + $0.insight + " " + $0.implication + " " + $0.action + " " + $0.tags.joined(separator: " "))
                .lowercased()
                .contains(q)
        }
    }

    func getProfile() -> UserProfile {
        profile
    }

    func updateProfile(_ update: ProfileUpdate) -> UserProfile {
        profile = UserProfile(
            name: update.name ?? profile.name,
            role: update.role ?? profile.role,
            goals: update.goals ?? profile.goals,
            interests: update.interests ?? profile.interests,
            currentProjects: update.currentProjects ?? profile.currentProjects,
            constraints: update.constraints ?? profile.constraints,
            ignoredTopics: update.ignoredTopics ?? profile.ignoredTopics
        )
        persistProfile()
        return profile
    }

    func recordDecision(_ request: DecisionCreateRequest) -> SyncDecision {
        let now = iso.string(from: Date())
        let decision = SyncDecision(
            id: UUID().uuidString,
            decision: request.decision,
            reason: request.reason,
            project: request.project,
            assumptions: request.assumptions,
            contextTags: request.project.isEmpty ? [] : [request.project],
            createdAt: now,
            outcome: "",
            impactScore: 0.0
        )
        decisions.insert(decision, at: 0)
        persistDecisions()
        return decision
    }

    func recordOutcome(_ request: OutcomeCreateRequest) -> SyncDecision? {
        guard let idx = decisions.firstIndex(where: { $0.id == request.decisionId }) else {
            return nil
        }

        let existing = decisions[idx]
        let updated = SyncDecision(
            id: existing.id,
            decision: existing.decision,
            reason: existing.reason,
            project: existing.project,
            assumptions: existing.assumptions,
            contextTags: existing.contextTags,
            createdAt: existing.createdAt,
            outcome: request.outcome,
            impactScore: request.impactScore
        )

        decisions[idx] = updated
        persistDecisions()
        return updated
    }

    func storeInsight(_ request: InsightCreateRequest) -> SyncInsight {
        let insight = SyncInsight(
            id: UUID().uuidString,
            title: request.title,
            summary: request.summary,
            whyItMatters: request.whyItMatters,
            architecturalImplication: request.architecturalImplication,
            nextAction: request.nextAction,
            confidence: request.confidence,
            tags: request.tags,
            relatedProject: request.relatedProject,
            createdAt: iso.string(from: Date())
        )
        insights.insert(insight, at: 0)
        persistInsights()
        return insight
    }

    func ingestSummary(_ request: SummaryIngestRequest) -> IngestResult {
        let trimmed = request.content.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return IngestResult(itemsIngested: 0, notesCreated: 0)
        }

        let lines = trimmed
            .split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        let title = lines.first.map(String.init) ?? "Captured summary"
        let summary = lines.dropFirst().joined(separator: " ")

        if request.createNotes {
            _ = createNote(
                NoteCreateRequest(
                    title: title,
                    insight: summary,
                    implication: "",
                    action: "",
                    sourceURL: request.source,
                    tags: request.tags
                )
            )
        }

        let insight = SyncInsight(
            id: UUID().uuidString,
            title: title,
            summary: summary,
            whyItMatters: "Captured locally for later synthesis.",
            architecturalImplication: "",
            nextAction: "Review and connect this with current priorities.",
            confidence: 0.65,
            tags: request.tags,
            relatedProject: profile.currentProjects.first ?? "",
            createdAt: iso.string(from: Date())
        )
        insights.insert(insight, at: 0)
        persistInsights()

        return IngestResult(itemsIngested: 1, notesCreated: request.createNotes ? 1 : 0)
    }

    func snapshot() -> SyncSnapshot {
        let now = Date()
        let nowISO = iso.string(from: now)
        let dateString = Self.dateOnly(now)

        let priorities: [SyncPriority] = buildPriorities(from: orderedNotes(), decisions: decisions)

        let brief = priorities.isEmpty ? nil : PriorityBrief(
            date: dateString,
            priorities: priorities,
            ignored: [],
            emergingSignals: [],
            changesSinceYesterday: []
        )

        let activeProjectName = profile.currentProjects.first ?? ""
        let activeProject: ProjectContext? = activeProjectName.isEmpty ? nil : ProjectContext(
            projectName: activeProjectName,
            currentMilestone: "",
            activeBlockers: [],
            recentDecisions: decisions.prefix(3).map { $0.decision },
            architectureNotes: [],
            openQuestions: []
        )

        let signals = buildSignals(from: notes, insights: insights)

        return SyncSnapshot(
            profile: SyncProfile(
                name: profile.name,
                role: profile.role,
                goals: profile.goals,
                interests: profile.interests,
                currentProjects: profile.currentProjects,
                ignoredTopics: profile.ignoredTopics
            ),
            activeProject: activeProject,
            priorities: brief,
            recentDecisions: Array(decisions.prefix(50)),
            insights: Array(insights.prefix(50)),
            signals: signals,
            workingMemory: SyncWorkingMemory(
                date: dateString,
                todaysPriorities: priorities.map { $0.title },
                currentlyExploring: signals.map { $0.topic },
                temporaryNotes: Array(orderedNotes().prefix(5).map { $0.title })
            ),
            syncedAt: nowISO
        )
    }

    private static func dateOnly(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private func orderedNotes() -> [KnowledgeNote] {
        notes.sorted { lhs, rhs in
            (iso.date(from: lhs.updatedAt) ?? .distantPast) > (iso.date(from: rhs.updatedAt) ?? .distantPast)
        }
    }

    private func buildPriorities(from notes: [KnowledgeNote], decisions: [SyncDecision]) -> [SyncPriority] {
        var items: [SyncPriority] = []

        for (idx, note) in notes.prefix(3).enumerated() {
            items.append(
                SyncPriority(
                    rank: idx + 1,
                    title: note.title,
                    whyItMatters: note.implication.isEmpty ? "Captured in your local knowledge base." : note.implication,
                    nextStep: note.action.isEmpty ? "Review and decide the next concrete step." : note.action,
                    source: note.sourceURL.isEmpty ? "local" : note.sourceURL,
                    relevanceScore: max(0.5, 1.0 - (Double(idx) * 0.15)),
                    tags: note.tags
                )
            )
        }

        if items.isEmpty, let latestDecision = decisions.first {
            items.append(
                SyncPriority(
                    rank: 1,
                    title: latestDecision.decision,
                    whyItMatters: latestDecision.reason.isEmpty ? "Latest local decision." : latestDecision.reason,
                    nextStep: "Track the outcome and refine assumptions.",
                    source: "local",
                    relevanceScore: 0.8,
                    tags: latestDecision.contextTags
                )
            )
        }

        if items.isEmpty {
            items.append(
                SyncPriority(
                    rank: 1,
                    title: "Define today's most important decision",
                    whyItMatters: "A clear first decision anchors the rest of the day.",
                    nextStep: "Capture one note or decision to initialize your local focus.",
                    source: "local",
                    relevanceScore: 0.7,
                    tags: ["focus"]
                )
            )
        }

        return items.enumerated().map { idx, item in
            SyncPriority(
                rank: idx + 1,
                title: item.title,
                whyItMatters: item.whyItMatters,
                nextStep: item.nextStep,
                source: item.source,
                relevanceScore: item.relevanceScore,
                tags: item.tags
            )
        }
    }

    private func buildSignals(from notes: [KnowledgeNote], insights: [SyncInsight]) -> [SyncSignal] {
        var frequency: [String: Int] = [:]

        for note in notes {
            for tag in note.tags where !tag.isEmpty {
                frequency[tag, default: 0] += 1
            }
        }

        for insight in insights {
            for tag in insight.tags where !tag.isEmpty {
                frequency[tag, default: 0] += 1
            }
        }

        let now = iso.string(from: Date())
        return frequency
            .sorted { $0.value > $1.value }
            .prefix(8)
            .enumerated()
            .map { idx, pair in
                SyncSignal(
                    id: "local-signal-\(idx)-\(pair.key)",
                    topic: pair.key,
                    frequency: pair.value,
                    strength: min(1.0, Double(pair.value) / 5.0),
                    status: pair.value >= 3 ? "confirmed" : "emerging",
                    firstSeen: now,
                    lastSeen: now,
                    sourceTitles: []
                )
            }
    }

    private func persistNotes() {
        guard let data = try? encoder.encode(notes) else { return }
        try? data.write(to: notesURL, options: .atomic)
    }

    private func persistProfile() {
        guard let data = try? encoder.encode(profile) else { return }
        try? data.write(to: profileURL, options: .atomic)
    }

    private func persistDecisions() {
        guard let data = try? encoder.encode(decisions) else { return }
        try? data.write(to: decisionsURL, options: .atomic)
    }

    private func persistInsights() {
        guard let data = try? encoder.encode(insights) else { return }
        try? data.write(to: insightsURL, options: .atomic)
    }
}
