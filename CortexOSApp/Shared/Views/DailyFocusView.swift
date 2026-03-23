//
//  DailyFocusView.swift
//  CortexOS
//
//  The only screen that really matters.
//  Open → Understand → Act → Close.
//  No scrolling if ≤ 3 priorities. No clutter. Pre-computed clarity.
//

import SwiftUI

struct DailyFocusView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let brief = engine.snapshot?.priorities {
                focusContent(brief)
            } else if let legacy = engine.dailyBrief {
                legacyContent(legacy)
            } else {
                EmptyStateView(
                    icon: "sparkles",
                    title: "No focus brief yet",
                    message: "Run the pipeline to generate today's priorities.",
                    actionTitle: "Generate",
                    action: { Task { await engine.generateFocusBrief() } }
                )
            }
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Focus")
        .refreshable { await engine.sync() }
    }

    // MARK: - Sync-powered focus

    @ViewBuilder
    private func focusContent(_ brief: PriorityBrief) -> some View {
        let needsScroll = brief.priorities.count > 3

        Group {
            if needsScroll {
                ScrollView { focusBody(brief) }
            } else {
                focusBody(brief)
            }
        }
    }

    @ViewBuilder
    private func focusBody(_ brief: PriorityBrief) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.lg) {
            // Date — subtle
            Text(brief.date)
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.textTertiary)
                .padding(.bottom, CortexSpacing.xs)

            // Priorities — no header, just show them
            ForEach(Array(brief.priorities.prefix(5).enumerated()), id: \.element.title) { index, priority in
                FocusPriorityCard(priority: priority, position: index + 1) { useful in
                    Task { await engine.sendFeedback(item: priority.title, useful: useful) }
                }
            }

            // Ignored today — first-class citizen
            if !brief.ignored.isEmpty {
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Ignored today")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textTertiary)

                    ForEach(brief.ignored, id: \.self) { item in
                        HStack(spacing: CortexSpacing.xs) {
                            Image(systemName: "minus.circle")
                                .font(.caption2)
                                .foregroundStyle(CortexColor.textTertiary)
                            Text(item)
                                .font(CortexFont.caption)
                                .foregroundStyle(CortexColor.textTertiary)
                        }
                    }
                }
                .padding(.top, CortexSpacing.sm)
            }

            // Emerging signals — compact pills, only if present
            if !brief.emergingSignals.isEmpty {
                FlowTags(items: brief.emergingSignals)
                    .padding(.top, CortexSpacing.xs)
            }
        }
        .padding(CortexSpacing.xl)
    }

    // MARK: - Legacy focus (DailyBrief from /focus/today)

    @ViewBuilder
    private func legacyContent(_ brief: DailyBrief) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.xl) {
                Text(brief.date)
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)

                ForEach(brief.focusItems) { item in
                    LegacyFocusRow(item: item)
                }
            }
            .padding(CortexSpacing.xl)
        }
    }
}

// MARK: - Focus Priority Card (with feedback)

private struct FocusPriorityCard: View {
    let priority: SyncPriority
    let position: Int
    let onFeedback: (Bool) -> Void

    @State private var feedbackGiven: Bool? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            HStack(alignment: .top, spacing: CortexSpacing.md) {
                // Rank badge
                Text("\(position)")
                    .font(CortexFont.captionMedium)
                    .foregroundStyle(.white)
                    .frame(width: 24, height: 24)
                    .background(CortexColor.rank(position))
                    .clipShape(Circle())

                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text(priority.title)
                        .font(CortexFont.bodyMedium)
                        .foregroundStyle(CortexColor.textPrimary)

                    if !priority.whyItMatters.isEmpty {
                        Text(priority.whyItMatters)
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textSecondary)
                            .lineLimit(2)
                    }

                    if !priority.nextStep.isEmpty {
                        Label {
                            Text(priority.nextStep)
                                .lineLimit(1)
                        } icon: {
                            Image(systemName: "arrow.right.circle.fill")
                        }
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.accent)
                    }
                }

                Spacer(minLength: 0)
            }

            // Feedback — was this useful?
            if feedbackGiven == nil {
                HStack(spacing: CortexSpacing.md) {
                    Spacer()
                    Button { submitFeedback(true) } label: {
                        Label("Yes", systemImage: "hand.thumbsup")
                            .font(CortexFont.caption)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(CortexColor.textTertiary)

                    Button { submitFeedback(false) } label: {
                        Label("No", systemImage: "hand.thumbsdown")
                            .font(CortexFont.caption)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(CortexColor.textTertiary)
                }
            } else {
                HStack {
                    Spacer()
                    Label(
                        feedbackGiven == true ? "Noted" : "Got it",
                        systemImage: "checkmark"
                    )
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)
                }
                .transition(.opacity)
            }
        }
        .padding(CortexSpacing.md)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }

    private func submitFeedback(_ useful: Bool) {
        withAnimation(.easeOut(duration: 0.2)) {
            feedbackGiven = useful
        }
        onFeedback(useful)
    }
}

// MARK: - Legacy row

private struct LegacyFocusRow: View {
    let item: FocusItem

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            HStack {
                Text("#\(item.rank)")
                    .font(CortexFont.captionMedium)
                    .foregroundStyle(.white)
                    .frame(width: 24, height: 24)
                    .background(CortexColor.rank(item.rank))
                    .clipShape(Circle())

                Text(item.title)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)

                Spacer()
            }

            if !item.whyItMatters.isEmpty {
                Text(item.whyItMatters)
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textSecondary)
            }

            if !item.nextAction.isEmpty {
                Label(item.nextAction, systemImage: "arrow.right.circle.fill")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.accent)
            }
        }
        .padding(CortexSpacing.md)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }
}

// MARK: - Flow tags (wrapping horizontal pills)

struct FlowTags: View {
    let items: [String]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: CortexSpacing.xs) {
                ForEach(items, id: \.self) { item in
                    ContextTag(text: item)
                }
            }
        }
    }
}
