//
//  DailyFocusView.swift
//  CortexOS
//
//  The only screen that really matters.
//  Open → Understand → Act → Close.
//  Top 3 priorities. Why they matter. One next action. What to ignore.
//

import SwiftUI

struct DailyFocusView: View {
    @EnvironmentObject private var engine: CortexEngine

    /// Priorities the user has swiped away this session (not persisted — resets on next sync)
    @State private var dismissedTitles: Set<String> = []

    var body: some View {
        Group {
            if let brief = engine.snapshot?.priorities {
                focusContent(brief)
            } else {
                VStack(spacing: CortexSpacing.xl) {
                    EmptyStateView(
                        icon: "target",
                        title: "No priorities yet",
                        message: "Your top priorities will appear here after syncing.",
                        actionTitle: "Sync",
                        action: { Task { await engine.sync() } }
                    )

                    if let snapshot = engine.snapshot {
                        quickContextCard(snapshot)
                    }
                }
            }
        }
        .safeAreaInset(edge: .bottom) {
            if !engine.isConnected {
                HStack(spacing: CortexSpacing.sm) {
                    Image(systemName: "arrow.clockwise.circle")
                        .font(.caption2)
                    Text("Offline — will sync when connected")
                        .font(CortexFont.mono)
                }
                .foregroundStyle(CortexColor.textTertiary)
                .padding(.vertical, CortexSpacing.sm)
                .frame(maxWidth: .infinity)
                .background(.ultraThinMaterial)
            }
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Focus")
        .refreshable { await engine.sync() }
    }

    // MARK: - Quick context when empty

    @ViewBuilder
    private func quickContextCard(_ snapshot: SyncSnapshot) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            if let project = snapshot.activeProject {
                HStack(spacing: CortexSpacing.xs) {
                    Image(systemName: "folder.fill")
                        .font(.caption)
                        .foregroundStyle(CortexColor.accent)
                    Text(project.projectName)
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textPrimary)
                }
            }

            if !snapshot.profile.goals.isEmpty {
                VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                    Text("Your goals")
                        .font(CortexFont.mono)
                        .foregroundStyle(CortexColor.textTertiary)
                    ForEach(snapshot.profile.goals.prefix(3), id: \.self) { goal in
                        Text("→ \(goal)")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textSecondary)
                    }
                }
            }
        }
        .padding(CortexSpacing.lg)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
        .padding(.horizontal, CortexSpacing.xl)
    }

    // MARK: - Focus content

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
        let visible = brief.priorities.filter { !dismissedTitles.contains($0.title) }

        VStack(alignment: .leading, spacing: CortexSpacing.lg) {
            // Date — subtle
            Text(brief.date)
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.textTertiary)
                .padding(.bottom, CortexSpacing.xs)

            // #1 Priority — hero card
            if let top = visible.first {
                HeroPriorityCard(priority: top, onFeedback: { useful in
                    Task { await engine.sendFeedback(item: top.title, useful: useful) }
                }, onDismiss: {
                    dismiss(top)
                })
            }

            // Remaining priorities
            ForEach(Array(visible.dropFirst().prefix(2).enumerated()), id: \.element.title) { index, priority in
                FocusPriorityCard(priority: priority, position: index + 2, onFeedback: { useful in
                    Task { await engine.sendFeedback(item: priority.title, useful: useful) }
                }, onDismiss: {
                    dismiss(priority)
                })
            }

            // Dismissed priorities (session only)
            let sessionDismissed = brief.priorities.filter { dismissedTitles.contains($0.title) }
            let allIgnored = brief.ignored + sessionDismissed.map(\.title)

            if !allIgnored.isEmpty {
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Ignored today")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textTertiary)

                    ForEach(allIgnored, id: \.self) { item in
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

            // Emerging signals — macOS only, compact
            #if os(macOS)
            if !brief.emergingSignals.isEmpty {
                FlowTags(items: brief.emergingSignals)
                    .padding(.top, CortexSpacing.xs)
            }
            #endif
        }
        .padding(CortexSpacing.xl)
    }

    private func dismiss(_ priority: SyncPriority) {
        withAnimation(.easeOut(duration: 0.25)) {
            dismissedTitles.insert(priority.title)
        }
        // Send "not useful" feedback — best-effort, never blocks
        Task { await engine.sendFeedback(item: priority.title, useful: false) }
    }
}

// MARK: - Hero Priority Card (#1 — visually elevated, calm)

private struct HeroPriorityCard: View {
    let priority: SyncPriority
    let onFeedback: (Bool) -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.md) {
            // Rank indicator — calm, not branded
            Text("#1")
                .font(.system(size: 13, weight: .semibold, design: .rounded))
                .foregroundStyle(CortexColor.accent)

            // Priority title — large, clear
            Text(priority.title)
                .font(.system(size: 20, weight: .bold))
                .foregroundStyle(CortexColor.textPrimary)
                .fixedSize(horizontal: false, vertical: true)

            // Why
            if !priority.whyItMatters.isEmpty {
                Text(priority.whyItMatters)
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textSecondary)
                    .lineLimit(3)
            }

            // Next step
            if !priority.nextStep.isEmpty {
                HStack(spacing: CortexSpacing.sm) {
                    Image(systemName: "arrow.right.circle.fill")
                        .font(.system(size: 14))
                        .foregroundStyle(CortexColor.accent)
                    Text(priority.nextStep)
                        .font(CortexFont.bodyMedium)
                        .foregroundStyle(CortexColor.accent)
                }
                .padding(.top, CortexSpacing.xxs)
            }

            // Feedback — macOS only (research flow)
            #if os(macOS)
            FeedbackRow(onFeedback: onFeedback)
            #endif
        }
        .padding(CortexSpacing.lg)
        .background(
            RoundedRectangle(cornerRadius: CortexRadius.large, style: .continuous)
                .fill(CortexColor.bgSurface)
                .overlay(
                    RoundedRectangle(cornerRadius: CortexRadius.large, style: .continuous)
                        .strokeBorder(CortexColor.accent.opacity(0.12), lineWidth: 1)
                )
        )
        .cortexShadow()
        #if os(iOS)
        .contextMenu {
            Button(role: .destructive) { onDismiss() } label: {
                Label("Ignore today", systemImage: "eye.slash")
            }
        }
        #endif
    }
}

// MARK: - Focus Priority Card (#2+)

private struct FocusPriorityCard: View {
    let priority: SyncPriority
    let position: Int
    let onFeedback: (Bool) -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            HStack(alignment: .top, spacing: CortexSpacing.md) {
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

            // Feedback — macOS only
            #if os(macOS)
            FeedbackRow(onFeedback: onFeedback)
            #endif
        }
        .padding(CortexSpacing.md)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
        #if os(iOS)
        .contextMenu {
            Button(role: .destructive) { onDismiss() } label: {
                Label("Ignore today", systemImage: "eye.slash")
            }
        }
        #endif
    }
}

// MARK: - Shared feedback row (macOS research flow)

private struct FeedbackRow: View {
    let onFeedback: (Bool) -> Void

    @State private var feedbackGiven: Bool? = nil

    var body: some View {
        Group {
            if feedbackGiven == nil {
                HStack(spacing: CortexSpacing.md) {
                    Spacer()
                    Button { submit(true) } label: {
                        Label("Useful", systemImage: "hand.thumbsup")
                            .font(CortexFont.caption)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(CortexColor.textTertiary)

                    Button { submit(false) } label: {
                        Label("Not useful", systemImage: "hand.thumbsdown")
                            .font(CortexFont.caption)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(CortexColor.textTertiary)
                }
            } else {
                HStack {
                    Spacer()
                    Label("Noted", systemImage: "checkmark")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                }
                .transition(.opacity)
            }
        }
        .padding(.top, CortexSpacing.xs)
    }

    private func submit(_ useful: Bool) {
        withAnimation(.easeOut(duration: 0.2)) {
            feedbackGiven = useful
        }
        onFeedback(useful)
    }
}

// MARK: - Flow tags

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
