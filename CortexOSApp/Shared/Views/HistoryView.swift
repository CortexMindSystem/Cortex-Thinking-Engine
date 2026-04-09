//
//  HistoryView.swift
//  CortexOS
//
//  Lightweight history — decisions, notes, insights.
//  Simple segmented view. Tap for detail. No overload.
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var segment: HistorySegment = .decisions

    var body: some View {
        VStack(spacing: 0) {
            Picker("", selection: $segment) {
                Text("Decisions").tag(HistorySegment.decisions)
                Text("Notes").tag(HistorySegment.notes)
                Text("Insights").tag(HistorySegment.insights)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, CortexSpacing.xl)
            .padding(.vertical, CortexSpacing.md)

            switch segment {
            case .decisions:
                decisionsSection
            case .notes:
                notesSection
            case .insights:
                insightsSection
            }
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("History")
        .refreshable { await engine.sync() }
        .task {
            if engine.notes.isEmpty {
                await engine.fetchNotes()
            }
        }
    }

    // MARK: - Decisions

    @ViewBuilder
    private var decisionsSection: some View {
        if let decisions = engine.snapshot?.recentDecisions, !decisions.isEmpty {
            List {
                ForEach(decisions) { d in
                    NavigationLink {
                        DecisionDetailView(decision: d)
                    } label: {
                        HistoryDecisionRow(decision: d)
                    }
                }
            }
            .listStyle(.plain)
        } else {
            EmptyStateView(
                icon: "checkmark.seal",
                title: "No decisions yet",
                message: "Decisions appear here as you record them.",
                actionTitle: nil,
                action: nil
            )
        }
    }

    // MARK: - Notes

    @ViewBuilder
    private var notesSection: some View {
        if !engine.notes.isEmpty {
            List {
                ForEach(engine.notes) { note in
                    NavigationLink {
                        NoteDetailView(note: note)
                    } label: {
                        HistoryNoteRow(note: note)
                    }
                }
            }
            .listStyle(.plain)
        } else {
            EmptyStateView(
                icon: "doc.text",
                title: "No notes yet",
                message: "Notes appear here as you capture thoughts.",
                actionTitle: nil,
                action: nil
            )
        }
    }

    // MARK: - Insights

    @ViewBuilder
    private var insightsSection: some View {
        if let insights = engine.snapshot?.insights, !insights.isEmpty {
            ScrollView {
                LazyVStack(spacing: CortexSpacing.md) {
                    ForEach(insights) { insight in
                        NavigationLink {
                            InsightDetailView(insight: insight)
                        } label: {
                            HistoryInsightRow(insight: insight)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(CortexSpacing.xl)
            }
        } else {
            EmptyStateView(
                icon: "lightbulb",
                title: "No insights yet",
                message: "Insights appear as you add notes and sync.",
                actionTitle: nil,
                action: nil
            )
        }
    }
}

// MARK: - Segments

private enum HistorySegment: String, CaseIterable {
    case decisions, notes, insights
}

// MARK: - Row views

private struct HistoryDecisionRow: View {
    let decision: SyncDecision

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
            Text(decision.decision)
                .font(CortexFont.bodyMedium)
                .foregroundStyle(CortexColor.textPrimary)
                .lineLimit(2)

            HStack(spacing: CortexSpacing.md) {
                if !decision.project.isEmpty {
                    Text(decision.project)
                        .font(CortexFont.mono)
                        .foregroundStyle(CortexColor.accent)
                }
                if !decision.createdAt.isEmpty {
                    Text(decision.createdAt.prefix(10))
                        .font(CortexFont.mono)
                        .foregroundStyle(CortexColor.textTertiary)
                }
            }
        }
        .padding(.vertical, CortexSpacing.xxs)
    }
}

private struct HistoryNoteRow: View {
    let note: KnowledgeNote

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
            Text(note.title)
                .font(CortexFont.bodyMedium)
                .foregroundStyle(CortexColor.textPrimary)
                .lineLimit(2)

            HStack(spacing: CortexSpacing.md) {
                if !note.tags.isEmpty {
                    Text(note.tags.prefix(2).map { "#\($0)" }.joined(separator: " "))
                        .font(CortexFont.mono)
                        .foregroundStyle(CortexColor.accent)
                }
                Text(note.createdAt.prefix(10))
                    .font(CortexFont.mono)
                    .foregroundStyle(CortexColor.textTertiary)
            }
        }
        .padding(.vertical, CortexSpacing.xxs)
    }
}

private struct HistoryInsightRow: View {
    let insight: SyncInsight

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xs) {
            Text(insight.title)
                .font(CortexFont.bodyMedium)
                .foregroundStyle(CortexColor.textPrimary)
                .lineLimit(2)

            if !insight.summary.isEmpty {
                Text(insight.summary)
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textSecondary)
                    .lineLimit(2)
            }

            if !insight.createdAt.isEmpty {
                Text(insight.createdAt.prefix(10))
                    .font(CortexFont.mono)
                    .foregroundStyle(CortexColor.textTertiary)
            }
        }
        .padding(CortexSpacing.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }
}

// MARK: - Decision Detail

struct DecisionDetailView: View {
    let decision: SyncDecision

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                Text(decision.decision)
                    .font(CortexFont.title)
                    .foregroundStyle(CortexColor.textPrimary)

                if !decision.reason.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        Text("Why")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textTertiary)
                        Text(decision.reason)
                            .font(CortexFont.body)
                            .foregroundStyle(CortexColor.textSecondary)
                    }
                }

                if !decision.assumptions.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        Text("Assumptions")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textTertiary)
                        ForEach(decision.assumptions, id: \.self) { a in
                            Text("  \(a)")
                                .font(CortexFont.body)
                                .foregroundStyle(CortexColor.textSecondary)
                        }
                    }
                }

                if !decision.outcome.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        Text("Outcome")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textTertiary)
                        Text(decision.outcome)
                            .font(CortexFont.body)
                            .foregroundStyle(CortexColor.success)
                    }
                }

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

                if !decision.contextTags.isEmpty {
                    HStack(spacing: CortexSpacing.xs) {
                        ForEach(decision.contextTags, id: \.self) { tag in
                            ContextTag(text: tag)
                        }
                    }
                }
            }
            .padding(CortexSpacing.xl)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Decision")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}

// MARK: - Insight Detail

struct InsightDetailView: View {
    let insight: SyncInsight

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                Text(insight.title)
                    .font(CortexFont.title)
                    .foregroundStyle(CortexColor.textPrimary)

                if !insight.summary.isEmpty {
                    Text(insight.summary)
                        .font(CortexFont.body)
                        .foregroundStyle(CortexColor.textSecondary)
                }

                if !insight.whyItMatters.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        Text("Why it matters")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textTertiary)
                        Text(insight.whyItMatters)
                            .font(CortexFont.body)
                            .foregroundStyle(CortexColor.textPrimary)
                    }
                }

                if !insight.architecturalImplication.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                        Text("Implication")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textTertiary)
                        Text(insight.architecturalImplication)
                            .font(CortexFont.body)
                            .foregroundStyle(CortexColor.textSecondary)
                    }
                }

                if !insight.nextAction.isEmpty {
                    HStack(spacing: CortexSpacing.sm) {
                        Image(systemName: "arrow.right.circle.fill")
                            .foregroundStyle(CortexColor.accent)
                        Text(insight.nextAction)
                            .font(CortexFont.bodyMedium)
                            .foregroundStyle(CortexColor.accent)
                    }
                }

                if !insight.tags.isEmpty {
                    HStack(spacing: CortexSpacing.xs) {
                        ForEach(insight.tags, id: \.self) { tag in
                            ContextTag(text: tag)
                        }
                    }
                }

                HStack(spacing: CortexSpacing.lg) {
                    if !insight.relatedProject.isEmpty {
                        Label(insight.relatedProject, systemImage: "folder")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.accent)
                    }
                    if !insight.createdAt.isEmpty {
                        Label(insight.createdAt.prefix(10).description, systemImage: "calendar")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textTertiary)
                    }
                }
            }
            .padding(CortexSpacing.xl)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Insight")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}
