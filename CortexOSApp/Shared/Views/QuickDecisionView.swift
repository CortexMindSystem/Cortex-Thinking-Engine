//
//  QuickDecisionView.swift
//  CortexOS
//
//  Record a decision fast. What, why, which project.
//  Builds compounding intelligence — CortexOS learns your patterns.
//

import SwiftUI

struct QuickDecisionView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var decision = ""
    @State private var reason = ""
    @State private var project = ""
    @State private var assumptions: [String] = []
    @State private var newAssumption = ""
    @State private var showAssumptions = false
    @State private var saved = false
    @State private var isSaving = false

    private var canSave: Bool {
        !decision.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                // Hero prompt
                Text("What did you decide?")
                    .font(CortexFont.largeTitle)
                    .foregroundStyle(CortexColor.textPrimary)
                    .padding(.top, CortexSpacing.lg)

                // Decision — the what
                TextField("e.g. Use SQLite instead of Postgres", text: $decision, axis: .vertical)
                    .font(CortexFont.body)
                    .lineLimit(1...4)
                    .textFieldStyle(.plain)
                    .padding(CortexSpacing.md)
                    .background(CortexColor.bgSurface)
                    .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
                    .cortexShadow()
                    #if os(iOS)
                    .textInputAutocapitalization(.sentences)
                    #endif

                // Reason — the why
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Why?")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textTertiary)

                    TextField("The reasoning behind this decision", text: $reason, axis: .vertical)
                        .font(CortexFont.body)
                        .lineLimit(1...4)
                        .textFieldStyle(.plain)
                        .padding(CortexSpacing.md)
                        .background(CortexColor.bgSurface)
                        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
                        .cortexShadow()
                        #if os(iOS)
                        .textInputAutocapitalization(.sentences)
                        #endif
                }

                // Project — optional context
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Project")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textTertiary)

                    if let active = engine.snapshot?.activeProject {
                        // Quick-select the active project
                        Button {
                            project = active.projectName
                        } label: {
                            HStack(spacing: CortexSpacing.xs) {
                                Image(systemName: project == active.projectName ? "checkmark.circle.fill" : "circle")
                                    .foregroundStyle(CortexColor.accent)
                                Text(active.projectName)
                                    .font(CortexFont.body)
                                    .foregroundStyle(CortexColor.textPrimary)
                            }
                        }
                        .buttonStyle(.plain)
                    }

                    TextField("Or type a project name", text: $project)
                        .font(CortexFont.body)
                        .textFieldStyle(.plain)
                        .padding(CortexSpacing.md)
                        .background(CortexColor.bgSurface)
                        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
                        .cortexShadow()
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        #endif
                }

                // Assumptions — collapsible
                DisclosureGroup("Assumptions", isExpanded: $showAssumptions) {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        ForEach(assumptions, id: \.self) { assumption in
                            HStack {
                                Text("• \(assumption)")
                                    .font(CortexFont.caption)
                                    .foregroundStyle(CortexColor.textSecondary)
                                Spacer()
                                Button {
                                    assumptions.removeAll { $0 == assumption }
                                } label: {
                                    Image(systemName: "xmark.circle.fill")
                                        .font(.caption)
                                        .foregroundStyle(CortexColor.textTertiary)
                                }
                                .buttonStyle(.plain)
                            }
                        }

                        HStack(spacing: CortexSpacing.sm) {
                            TextField("Add an assumption", text: $newAssumption)
                                .font(CortexFont.caption)
                                .textFieldStyle(.plain)
                                .onSubmit { addAssumption() }

                            Button {
                                addAssumption()
                            } label: {
                                Image(systemName: "plus.circle.fill")
                                    .foregroundStyle(CortexColor.accent)
                            }
                            .buttonStyle(.plain)
                            .disabled(newAssumption.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                        .padding(CortexSpacing.sm)
                        .background(CortexColor.bgSurface)
                        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.small, style: .continuous))
                    }
                    .padding(.top, CortexSpacing.xs)
                }
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textTertiary)

                // Save
                Button {
                    Task { await save() }
                } label: {
                    HStack {
                        Spacer()
                        if isSaving {
                            ProgressView()
                                .controlSize(.small)
                                .tint(.white)
                        } else {
                            Label("Record Decision", systemImage: "checkmark.seal.fill")
                                .font(CortexFont.bodyMedium)
                        }
                        Spacer()
                    }
                    .padding(.vertical, CortexSpacing.md)
                }
                .buttonStyle(.borderedProminent)
                .tint(CortexColor.accent)
                .disabled(!canSave || isSaving)

                // Saved confirmation
                if saved {
                    HStack {
                        Spacer()
                        Label("Decision recorded — CortexOS will remember this.", systemImage: "brain")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.success)
                        Spacer()
                    }
                    .transition(.opacity)
                }

                // Recent decisions — quick reference
                if let decisions = engine.snapshot?.recentDecisions, !decisions.isEmpty {
                    recentDecisionsSection(decisions)
                }
            }
            .padding(.horizontal, CortexSpacing.xl)
            .padding(.bottom, CortexSpacing.xxl)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Decide")
        .refreshable { await engine.sync() }
    }

    // MARK: - Recent decisions

    @ViewBuilder
    private func recentDecisionsSection(_ decisions: [SyncDecision]) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            Text("Recent decisions")
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textTertiary)
                .padding(.top, CortexSpacing.lg)

            ForEach(decisions.prefix(3)) { d in
                VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                    Text(d.decision)
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textPrimary)
                        .lineLimit(1)

                    HStack(spacing: CortexSpacing.sm) {
                        if !d.project.isEmpty {
                            Text(d.project)
                                .font(CortexFont.mono)
                                .foregroundStyle(CortexColor.accent)
                        }
                        if !d.createdAt.isEmpty {
                            Text(d.createdAt.prefix(10))
                                .font(CortexFont.mono)
                                .foregroundStyle(CortexColor.textTertiary)
                        }
                    }
                }
                .padding(CortexSpacing.sm)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(CortexColor.bgSurface)
                .clipShape(RoundedRectangle(cornerRadius: CortexRadius.small, style: .continuous))
            }
        }
    }

    // MARK: - Actions

    private func addAssumption() {
        let trimmed = newAssumption.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        assumptions.append(trimmed)
        newAssumption = ""
    }

    private func save() async {
        let trimmedDecision = decision.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedDecision.isEmpty else { return }

        isSaving = true
        defer { isSaving = false }

        let request = DecisionCreateRequest(
            decision: trimmedDecision,
            reason: reason.trimmingCharacters(in: .whitespacesAndNewlines),
            project: project.trimmingCharacters(in: .whitespacesAndNewlines),
            assumptions: assumptions
        )

        let success = await engine.recordDecision(request)
        guard success else { return }

        withAnimation {
            saved = true
            decision = ""
            reason = ""
            assumptions = []
            newAssumption = ""
        }

        try? await Task.sleep(for: .seconds(3))
        withAnimation { saved = false }
    }
}
