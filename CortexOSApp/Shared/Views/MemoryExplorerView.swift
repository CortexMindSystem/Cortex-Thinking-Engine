//
//  MemoryExplorerView.swift
//  CortexOS
//
//  Structured view of the 4 memory layers:
//  identity, projects, research, working.
//  Deep thinking tool for macOS.
//

import SwiftUI

struct MemoryExplorerView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let snapshot = engine.snapshot {
                memoryContent(snapshot)
            } else {
                EmptyStateView(
                    icon: "brain",
                    title: "Memory not loaded",
                    message: "Sync to load your context memory layers.",
                    actionTitle: "Sync",
                    action: { Task { await engine.sync() } }
                )
            }
        }
        .navigationTitle("Memory")
        .refreshable { await engine.sync() }
    }

    @ViewBuilder
    private func memoryContent(_ snapshot: SyncSnapshot) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.xl) {
                // Layer 1: Identity
                MemoryLayer(title: "Identity", icon: "person.fill") {
                    MemoryField(label: "Name", value: snapshot.profile.name)
                    MemoryField(label: "Role", value: snapshot.profile.role)
                    MemoryListField(label: "Goals", items: snapshot.profile.goals)
                    MemoryListField(label: "Interests", items: snapshot.profile.interests)
                    MemoryListField(label: "Projects", items: snapshot.profile.currentProjects)
                    MemoryListField(label: "Ignored", items: snapshot.profile.ignoredTopics)
                }

                // Layer 2: Project
                if let project = snapshot.activeProject {
                    MemoryLayer(title: project.projectName, icon: "folder.fill") {
                        MemoryField(label: "Milestone", value: project.currentMilestone)
                        MemoryListField(label: "Blockers", items: project.activeBlockers)
                        MemoryListField(label: "Decisions", items: project.recentDecisions)
                        MemoryListField(label: "Architecture", items: project.architectureNotes)
                        MemoryListField(label: "Questions", items: project.openQuestions)
                    }
                }

                // Layer 3: Working
                let wm = snapshot.workingMemory
                MemoryLayer(title: "Working Memory", icon: "clock.arrow.circlepath") {
                    MemoryField(label: "Date", value: wm.date)
                    MemoryListField(label: "Priorities", items: wm.todaysPriorities)
                    MemoryListField(label: "Exploring", items: wm.currentlyExploring)
                    MemoryListField(label: "Notes", items: wm.temporaryNotes)
                }

                // Layer 4: Decisions summary
                if !snapshot.recentDecisions.isEmpty {
                    MemoryLayer(title: "Recent Decisions", icon: "checkmark.seal") {
                        ForEach(snapshot.recentDecisions.prefix(5)) { d in
                            VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                                Text(d.decision)
                                    .font(CortexFont.body)
                                    .foregroundStyle(CortexColor.textPrimary)
                                if !d.reason.isEmpty {
                                    Text(d.reason)
                                        .font(CortexFont.caption)
                                        .foregroundStyle(CortexColor.textTertiary)
                                }
                            }
                        }
                    }
                }
            }
            .padding(CortexSpacing.xl)
        }
    }
}

// MARK: - Layer card

private struct MemoryLayer<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.md) {
            Label(title, systemImage: icon)
                .font(CortexFont.headline)
                .foregroundStyle(CortexColor.textPrimary)

            content
        }
        .padding(CortexSpacing.lg)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }
}

// MARK: - Field helpers

private struct MemoryField: View {
    let label: String
    let value: String

    var body: some View {
        if !value.isEmpty {
            HStack {
                Text(label)
                    .font(CortexFont.captionMedium)
                    .foregroundStyle(CortexColor.textTertiary)
                    .frame(width: 80, alignment: .trailing)
                Text(value)
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textPrimary)
            }
        }
    }
}

private struct MemoryListField: View {
    let label: String
    let items: [String]

    var body: some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                Text(label)
                    .font(CortexFont.captionMedium)
                    .foregroundStyle(CortexColor.textTertiary)
                ForEach(items, id: \.self) { item in
                    Text("  • \(item)")
                        .font(CortexFont.body)
                        .foregroundStyle(CortexColor.textSecondary)
                }
            }
        }
    }
}
