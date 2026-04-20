//
//  DecisionHistoryView.swift
//  CortexOS
//
//  Past decisions with reasoning, assumptions, and outcomes.
//  Depth view for macOS research sessions. Record new decisions inline.
//

import SwiftUI

struct DecisionHistoryView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var showNewDecision = false

    var body: some View {
        Group {
            if let decisions = engine.snapshot?.recentDecisions, !decisions.isEmpty {
                List {
                    ForEach(decisions) { decision in
                        DecisionRow(decision: decision)
                    }
                }
                .listStyle(.plain)
            } else {
                EmptyStateView(
                    icon: "checkmark.seal",
                    title: "No decisions yet",
                    message: "Decisions appear here as you record them.",
                    actionTitle: "Sync",
                    action: { Task { await engine.sync() } },
                    isActionLoading: engine.isSyncing
                )
            }
        }
        .navigationTitle("Decisions")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showNewDecision = true } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showNewDecision) {
            RecordDecisionSheet()
                .environmentObject(engine)
        }
        .refreshable { await engine.sync() }
    }
}

// MARK: - Record Decision Sheet

private struct RecordDecisionSheet: View {
    @EnvironmentObject private var engine: CortexEngine
    @Environment(\.dismiss) private var dismiss

    @State private var decision = ""
    @State private var reason = ""
    @State private var project = ""

    private var canSave: Bool {
        !decision.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Decision") {
                    TextField("What did you decide?", text: $decision, axis: .vertical)
                        .lineLimit(1...4)
                        .textFieldStyle(.plain)
                        .cortexInputSurface(minHeight: CortexInput.multiLineMinHeight)
                }
                Section("Why") {
                    TextField("The reasoning", text: $reason, axis: .vertical)
                        .lineLimit(1...3)
                        .textFieldStyle(.plain)
                        .cortexInputSurface(minHeight: 96)
                }
                Section("Project") {
                    if let active = engine.snapshot?.activeProject {
                        Button {
                            project = active.projectName
                        } label: {
                            HStack(spacing: CortexSpacing.xs) {
                                Image(systemName: project == active.projectName ? "checkmark.circle.fill" : "circle")
                                    .foregroundStyle(CortexColor.accent)
                                Text(active.projectName)
                                    .foregroundStyle(CortexColor.textPrimary)
                            }
                        }
                        .buttonStyle(.plain)
                    }
                    TextField("Project name", text: $project)
                        .textFieldStyle(.plain)
                        .cortexInputSurface()
                }
            }
            .navigationTitle("Record Decision")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task { await save() }
                    }
                    .disabled(!canSave)
                }
            }
        }
        #if os(macOS)
        .frame(minWidth: 400, minHeight: 300)
        #endif
    }

    private func save() async {
        let request = DecisionCreateRequest(
            decision: decision.trimmingCharacters(in: .whitespacesAndNewlines),
            reason: reason.trimmingCharacters(in: .whitespacesAndNewlines),
            project: project.trimmingCharacters(in: .whitespacesAndNewlines)
        )
        if await engine.recordDecision(request) {
            dismiss()
        }
    }
}

// MARK: - Row

private struct DecisionRow: View {
    let decision: SyncDecision

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            // Decision text
            Text(decision.decision)
                .font(CortexFont.bodyMedium)
                .foregroundStyle(CortexColor.textPrimary)

            // Reason
            if !decision.reason.isEmpty {
                Text(decision.reason)
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textSecondary)
                    .lineLimit(3)
            }

            // Metadata row
            HStack(spacing: CortexSpacing.lg) {
                if !decision.project.isEmpty {
                    Label(decision.project, systemImage: "folder")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.accent)
                }

                if !decision.createdAt.isEmpty {
                    Label(decision.createdAt.prefix(10).description, systemImage: "calendar")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                }
            }

            // Assumptions
            if !decision.assumptions.isEmpty {
                VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                    Text("Assumptions")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textTertiary)

                    ForEach(decision.assumptions, id: \.self) { assumption in
                        Text("• \(assumption)")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textSecondary)
                    }
                }
            }

            // Outcome
            if !decision.outcome.isEmpty {
                Label {
                    Text(decision.outcome)
                        .lineLimit(2)
                } icon: {
                    Image(systemName: "arrow.turn.down.right")
                }
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.success)
            }

            // Tags
            if !decision.contextTags.isEmpty {
                HStack(spacing: CortexSpacing.xs) {
                    ForEach(decision.contextTags.prefix(4), id: \.self) { tag in
                        ContextTag(text: tag)
                    }
                }
            }
        }
        .padding(.vertical, CortexSpacing.xs)
    }
}
