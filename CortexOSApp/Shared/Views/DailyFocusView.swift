//
//  DailyFocusView.swift
//  CortexOS
//
//  The most important screen. Shows today's top priorities,
//  why they matter, and the next action. No scrolling if ≤ 3.
//  Feels like "today matters".
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

    // MARK: - Sync-powered focus (priority brief)

    @ViewBuilder
    private func focusContent(_ brief: PriorityBrief) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.xl) {
                // Date header
                Text(brief.date)
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)

                // Priorities — the core
                if !brief.priorities.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                        Text("Priorities")
                            .font(CortexFont.headline)
                            .foregroundStyle(CortexColor.textPrimary)

                        PriorityList(priorities: brief.priorities)
                    }
                }

                // Emerging signals
                if !brief.emergingSignals.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                        Text("Emerging Signals")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textSecondary)

                        FlowTags(items: brief.emergingSignals)
                    }
                }

                // Changes since yesterday
                if !brief.changesSinceYesterday.isEmpty {
                    VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                        Text("Changed Since Yesterday")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.textSecondary)

                        ForEach(brief.changesSinceYesterday, id: \.self) { change in
                            Label(change, systemImage: "arrow.triangle.2.circlepath")
                                .font(CortexFont.caption)
                                .foregroundStyle(CortexColor.textSecondary)
                        }
                    }
                }
            }
            .padding(CortexSpacing.xl)
        }
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

// MARK: - Legacy row (for /focus/today data)

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
        // Simple horizontal scroll for now — wrapping layout is complex
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: CortexSpacing.xs) {
                ForEach(items, id: \.self) { item in
                    ContextTag(text: item)
                }
            }
        }
    }
}
