import SwiftUI

struct SignalWorkbenchView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let snapshot = engine.snapshot {
                content(snapshot)
            } else {
                EmptyStateView(
                    icon: "list.bullet.rectangle",
                    title: "Signal queues not ready",
                    message: "Sync to build ranked decision and action queues.",
                    actionTitle: "Sync",
                    action: { Task { await engine.sync() } },
                    isActionLoading: engine.isSyncing
                )
            }
        }
        .navigationTitle("Queues")
        .background(CortexColor.bgPrimary)
        .refreshable { await engine.sync() }
    }

    @ViewBuilder
    private func content(_ snapshot: SyncSnapshot) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                metrics(snapshot.signalMatchingCounts)

                queueCard(
                    title: "What Matters Now",
                    icon: "target",
                    items: snapshot.whatMattersNow ?? [],
                    emptyText: "No immediate items right now.",
                    maxVisible: 3
                )

                queueCard(
                    title: "Decision Queue",
                    icon: "checkmark.seal",
                    items: snapshot.decisionQueue ?? [],
                    emptyText: "No decision-ready items yet.",
                    maxVisible: 5
                )

                queueCard(
                    title: "Action-Ready Queue",
                    icon: "bolt.fill",
                    items: snapshot.actionReadyQueue ?? [],
                    emptyText: "No action-ready items yet.",
                    maxVisible: 5
                )

                queueCard(
                    title: "Unresolved Tensions",
                    icon: "exclamationmark.triangle",
                    items: snapshot.unresolvedTensions ?? [],
                    emptyText: "No unresolved tensions detected.",
                    maxVisible: 5
                )

                queueCard(
                    title: "Content Candidates",
                    icon: "doc.text",
                    items: snapshot.contentCandidates ?? [],
                    emptyText: "No safe content candidates right now.",
                    maxVisible: 5
                )

                recurringPatternsCard(snapshot.recurringPatterns ?? [], maxVisible: 5)
            }
            .padding(CortexSpacing.xl)
        }
    }

    @ViewBuilder
    private func metrics(_ counts: SyncSignalMatchingCounts?) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            Text("Signal Matching")
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textTertiary)

            HStack(spacing: CortexSpacing.lg) {
                metric("Total", "\(counts?.signalsTotal ?? 0)")
                metric("Active", "\(counts?.signalsActive ?? 0)")
                metric("Ignored", "\(counts?.ignored ?? 0)")
            }
        }
        .padding(CortexSpacing.lg)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
    }

    @ViewBuilder
    private func queueCard(
        title: String,
        icon: String,
        items: [SyncRankedSignal],
        emptyText: String,
        maxVisible: Int
    ) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.md) {
            Label(title, systemImage: icon)
                .font(CortexFont.headline)
                .foregroundStyle(CortexColor.textPrimary)

            if items.isEmpty {
                Text(emptyText)
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textTertiary)
            } else {
                ForEach(items.prefix(maxVisible)) { item in
                    VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                        Text(item.title)
                            .font(CortexFont.bodyMedium)
                            .foregroundStyle(CortexColor.textPrimary)

                        Text(item.explainability.whyItSurfaced)
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textSecondary)

                        Text("Next: \(item.nextAction)")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.accent)

                        HStack(spacing: CortexSpacing.md) {
                            Text("Rank \(Int(item.rankScore))")
                            Text(item.horizon.capitalized)
                            Text(item.signalType.replacingOccurrences(of: "_", with: " ").capitalized)
                        }
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                    }
                }
            }
        }
        .padding(CortexSpacing.lg)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
    }

    @ViewBuilder
    private func recurringPatternsCard(_ patterns: [SyncRecurringPattern], maxVisible: Int) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.md) {
            Label("Recurring Patterns", systemImage: "waveform.path.ecg")
                .font(CortexFont.headline)
                .foregroundStyle(CortexColor.textPrimary)

            if patterns.isEmpty {
                Text("No recurring patterns detected yet.")
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textTertiary)
            } else {
                ForEach(patterns.prefix(maxVisible)) { pattern in
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                            Text(pattern.topic.replacingOccurrences(of: "_", with: " ").capitalized)
                                .font(CortexFont.bodyMedium)
                                .foregroundStyle(CortexColor.textPrimary)
                            Text("\(pattern.count)x • unresolved \(pattern.unresolvedCount)")
                                .font(CortexFont.caption)
                                .foregroundStyle(CortexColor.textSecondary)
                        }
                        Spacer()
                        Text("\(Int(pattern.avgImportance))")
                            .font(CortexFont.captionMedium)
                            .foregroundStyle(CortexColor.accent)
                    }
                }
            }
        }
        .padding(CortexSpacing.lg)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
    }

    @ViewBuilder
    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
            Text(label)
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.textTertiary)
            Text(value)
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textPrimary)
        }
    }
}
