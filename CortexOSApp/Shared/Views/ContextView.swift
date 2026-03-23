//
//  ContextView.swift
//  CortexOS
//
//  Shows current project, goals, active themes, and signals.
//  Quick orientation — "here's where I am".
//

import SwiftUI

struct ContextView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let snapshot = engine.snapshot {
                contextContent(snapshot)
            } else {
                EmptyStateView(
                    icon: "brain.head.profile",
                    title: "No context loaded",
                    message: "Connect to the server to load your profile and projects.",
                    actionTitle: "Sync",
                    action: { Task { await engine.sync() } }
                )
            }
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Context")
        .refreshable { await engine.sync() }
    }

    @ViewBuilder
    private func contextContent(_ snapshot: SyncSnapshot) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.xl) {
                // Goals
                if !snapshot.profile.goals.isEmpty {
                    ContextSection(title: "Goals", icon: "target") {
                        ForEach(snapshot.profile.goals, id: \.self) { goal in
                            Label(goal, systemImage: "circle.fill")
                                .font(CortexFont.body)
                                .foregroundStyle(CortexColor.textPrimary)
                                .labelStyle(SmallDotLabel())
                        }
                    }
                }

                // Active project
                if let project = snapshot.activeProject {
                    ContextSection(title: project.projectName, icon: "folder.fill") {
                        if !project.currentMilestone.isEmpty {
                            InfoRow(label: "Milestone", value: project.currentMilestone)
                        }
                        if !project.activeBlockers.isEmpty {
                            ForEach(project.activeBlockers, id: \.self) { blocker in
                                Label(blocker, systemImage: "exclamationmark.triangle")
                                    .font(CortexFont.caption)
                                    .foregroundStyle(CortexColor.warning)
                            }
                        }
                        if !project.openQuestions.isEmpty {
                            ForEach(project.openQuestions, id: \.self) { q in
                                Label(q, systemImage: "questionmark.circle")
                                    .font(CortexFont.caption)
                                    .foregroundStyle(CortexColor.textSecondary)
                            }
                        }
                    }
                }

                // Interests
                if !snapshot.profile.interests.isEmpty {
                    ContextSection(title: "Interests", icon: "heart") {
                        FlowTags(items: snapshot.profile.interests)
                    }
                }

                // Signals
                if !snapshot.signals.isEmpty {
                    ContextSection(title: "Active Signals", icon: "antenna.radiowaves.left.and.right") {
                        ForEach(snapshot.signals.prefix(5)) { signal in
                            HStack {
                                Text(signal.topic)
                                    .font(CortexFont.body)
                                    .foregroundStyle(CortexColor.textPrimary)
                                Spacer()
                                Text(signal.status)
                                    .font(CortexFont.mono)
                                    .foregroundStyle(signal.status == "confirmed"
                                        ? CortexColor.success : CortexColor.neutral)
                                Text("×\(signal.frequency)")
                                    .font(CortexFont.mono)
                                    .foregroundStyle(CortexColor.textTertiary)
                            }
                        }
                    }
                }

                // Working memory
                let wm = snapshot.workingMemory
                if !wm.currentlyExploring.isEmpty {
                    ContextSection(title: "Exploring", icon: "magnifyingglass") {
                        FlowTags(items: wm.currentlyExploring)
                    }
                }
            }
            .padding(CortexSpacing.xl)
        }
    }
}

// MARK: - Helpers

private struct ContextSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
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

private struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textSecondary)
            Spacer()
            Text(value)
                .font(CortexFont.body)
                .foregroundStyle(CortexColor.textPrimary)
        }
    }
}

private struct SmallDotLabel: LabelStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: CortexSpacing.sm) {
            configuration.icon
                .font(.system(size: 5))
                .foregroundStyle(CortexColor.accent)
            configuration.title
        }
    }
}
