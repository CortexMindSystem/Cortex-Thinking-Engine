//
//  DecisionHistoryView.swift
//  CortexOS
//
//  Past decisions with reasoning, assumptions, and outcomes.
//  Depth view — designed for macOS research sessions.
//

import SwiftUI

struct DecisionHistoryView: View {
    @EnvironmentObject private var engine: CortexEngine

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
                    title: "No decisions recorded",
                    message: "Decisions are logged when you record them through the API or pipeline.",
                    actionTitle: "Refresh",
                    action: { Task { await engine.sync() } }
                )
            }
        }
        .navigationTitle("Decisions")
        .refreshable { await engine.sync() }
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

                if decision.impactScore > 0 {
                    Label(String(format: "%.1f", decision.impactScore), systemImage: "gauge")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.confidence(decision.impactScore))
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
