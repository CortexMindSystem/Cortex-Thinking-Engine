//
//  DashboardView.swift
//  CortexOS
//
//  Main dashboard showing system status, note count, and quick actions.
//

import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                headerSection
                connectionCard
                statsGrid
                quickActions
                recentNotes
            }
            .padding()
        }
        .navigationTitle("CortexOS")
        .task {
            await engine.checkConnection()
            await engine.fetchStatus()
            await engine.fetchNotes()
        }
        .refreshable {
            await engine.fetchStatus()
            await engine.fetchNotes()
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 4) {
            Text("CortexOS")
                .font(.largeTitle.bold())
            Text("Your operating system for thinking")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
    }

    // MARK: - Connection Status

    private var connectionCard: some View {
        HStack {
            Image(systemName: engine.isConnected ? "wifi" : "wifi.slash")
                .foregroundStyle(engine.isConnected ? .green : .red)
                .font(.title2)

            VStack(alignment: .leading, spacing: 2) {
                Text(engine.isConnected ? "Connected" : "Disconnected")
                    .font(.headline)
                if let status = engine.serverStatus {
                    Text("v\(status.version) · \(status.llmProvider)/\(status.llmModel)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            Button {
                Task { await engine.checkConnection() }
            } label: {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.bordered)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Stats

    private var statsGrid: some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible()),
        ], spacing: 12) {
            StatCard(
                title: "Notes",
                value: "\(engine.notes.count)",
                icon: "doc.text.fill",
                color: .blue
            )
            StatCard(
                title: "Posts",
                value: "\(engine.posts.count)",
                icon: "text.bubble.fill",
                color: .purple
            )
            StatCard(
                title: "Pipeline",
                value: engine.pipelineResult?.success == true ? "✓" : "—",
                icon: "arrow.triangle.branch",
                color: .orange
            )
        }
    }

    // MARK: - Quick Actions

    private var quickActions: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)

            HStack(spacing: 12) {
                ActionButton(title: "Run Pipeline", icon: "play.fill", color: .green) {
                    Task { await engine.runPipeline() }
                }
                ActionButton(title: "Generate Posts", icon: "text.bubble", color: .purple) {
                    Task { await engine.generatePosts() }
                }
            }
        }
    }

    // MARK: - Recent Notes

    private var recentNotes: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Notes")
                    .font(.headline)
                Spacer()
                NavigationLink("See All") {
                    KnowledgeListView()
                }
                .font(.subheadline)
            }

            if engine.notes.isEmpty {
                Text("No knowledge notes yet. Run the pipeline to get started.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 24)
            } else {
                ForEach(engine.notes.prefix(5)) { note in
                    NoteRowView(note: note)
                }
            }
        }
    }
}

// MARK: - Sub-Components

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(color)
            Text(value)
                .font(.title.bold())
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: icon)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
        .tint(color)
    }
}

struct NoteRowView: View {
    let note: KnowledgeNote

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(note.title)
                .font(.subheadline.bold())
                .lineLimit(1)
            Text(note.insight)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            if !note.tags.isEmpty {
                Text(note.displayTags)
                    .font(.caption2)
                    .foregroundStyle(.blue)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    NavigationStack {
        DashboardView()
            .environmentObject(CortexEngine())
    }
}
