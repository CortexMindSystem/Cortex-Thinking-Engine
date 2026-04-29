import SwiftUI

struct WatchRootView: View {
    @EnvironmentObject private var model: WatchDecisionModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 10) {
                    statusRow

                    if let priority = model.topPriority {
                        priorityCard(priority)
                        feedbackCard(priority)
                    } else {
                        emptyStateCard
                    }

                    captureCard
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 8)
            }
            .navigationTitle("Next")
        }
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active else { return }
            Task { await model.sync() }
        }
    }

    private var statusRow: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(model.isOffline ? CortexColor.warning : CortexColor.success)
                .frame(width: 6, height: 6)
            Text(model.updatedStatus)
                .font(.caption2)
                .foregroundStyle(CortexColor.textSecondary)
            Spacer()
            if model.pendingCount > 0 {
                Text("Q\(model.pendingCount)")
                    .font(.caption2)
                    .foregroundStyle(CortexColor.accent)
            }
        }
    }

    @ViewBuilder
    private func priorityCard(_ priority: SyncTodayPriority) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Top Priority")
                .font(.caption2)
                .foregroundStyle(.secondary)

            Text(priority.title)
                .font(.headline)
                .lineLimit(2)
                .multilineTextAlignment(.leading)

            if !priority.action.isEmpty {
                Label(priority.action, systemImage: "arrow.right.circle.fill")
                    .font(.caption)
                    .foregroundStyle(CortexColor.accent)
                    .lineLimit(2)
            }
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func feedbackCard(_ priority: SyncTodayPriority) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Feedback")
                .font(.caption2)
                .foregroundStyle(.secondary)

            HStack(spacing: 6) {
                feedbackButton("Useful", icon: "hand.thumbsup.fill") {
                    Task { await model.sendQuickFeedback(for: priority, useful: true, acted: nil) }
                }
                feedbackButton("Not useful", icon: "hand.thumbsdown.fill") {
                    Task { await model.sendQuickFeedback(for: priority, useful: false, acted: nil) }
                }
            }

            HStack(spacing: 6) {
                feedbackButton("Done", icon: "checkmark.circle.fill") {
                    Task { await model.sendQuickFeedback(for: priority, useful: true, acted: true) }
                }
                feedbackButton("Not done", icon: "xmark.circle.fill") {
                    Task { await model.sendQuickFeedback(for: priority, useful: true, acted: false) }
                }
            }
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func feedbackButton(_ title: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Label(title, systemImage: icon)
                .font(.caption2)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.bordered)
    }

    private var captureCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Capture")
                .font(.caption2)
                .foregroundStyle(.secondary)

            TextField("Dictate or type a note", text: $model.captureText, axis: .vertical)
                .lineLimit(2...4)
                .textFieldStyle(.plain)
                .padding(8)
                .background(CortexColor.bgSecondary)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))

            Button {
                Task { await model.captureByVoice() }
            } label: {
                Label("Save capture", systemImage: "mic.fill")
                    .frame(maxWidth: .infinity)
            }
            .disabled(model.captureText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .buttonStyle(.borderedProminent)

            Text(model.isOffline ? "Offline: capture queues automatically." : "Capture syncs automatically.")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var emptyStateCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("No priority yet")
                .font(.headline)
            Text("Sync to pull your latest next action.")
                .font(.caption2)
                .foregroundStyle(.secondary)
            Button {
                Task { await model.sync() }
            } label: {
                Label(model.isSyncing ? "Syncing..." : "Sync", systemImage: "arrow.clockwise")
                    .frame(maxWidth: .infinity)
            }
            .disabled(model.isSyncing)
            .buttonStyle(.borderedProminent)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CortexColor.bgSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}
