import SwiftUI

struct WatchRootView: View {
    @EnvironmentObject private var model: WatchDecisionModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        TabView {
            NavigationStack {
                ScrollView {
                    VStack(alignment: .leading, spacing: 10) {
                        statusRow

                        if let priority = model.topPriority {
                            Text(priority.title)
                                .font(.headline)
                                .lineLimit(2)
                                .multilineTextAlignment(.leading)

                            Text(priority.action)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)

                            NavigationLink {
                                WatchFeedbackView(priority: priority)
                            } label: {
                                Label("Feedback", systemImage: "hand.thumbsup")
                            }
                            .buttonStyle(.borderedProminent)
                        } else {
                            Text("No priority yet")
                                .font(.headline)
                            Text("Sync to pull your latest action.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Button {
                                Task { await model.sync() }
                            } label: {
                                Label(model.isSyncing ? "Syncing..." : "Sync", systemImage: "arrow.clockwise")
                            }
                            .disabled(model.isSyncing)
                            .buttonStyle(.borderedProminent)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 8)
                }
                .navigationTitle("Next")
            }
            .tag(0)

            NavigationStack {
                WatchFeedbackView(priority: model.topPriority)
            }
            .tag(1)

            NavigationStack {
                WatchCaptureView()
            }
            .tag(2)
        }
        .tabViewStyle(.page)
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
}

private struct WatchFeedbackView: View {
    @EnvironmentObject private var model: WatchDecisionModel
    let priority: SyncTodayPriority?

    var body: some View {
        List {
            if let priority {
                Section {
                    Text(priority.title)
                        .font(.caption)
                        .lineLimit(2)
                        .foregroundStyle(.secondary)
                }

                Section("Useful?") {
                    Button("Useful") {
                        Task { await model.sendQuickFeedback(for: priority, useful: true, acted: nil) }
                    }
                    Button("Not useful") {
                        Task { await model.sendQuickFeedback(for: priority, useful: false, acted: nil) }
                    }
                }

                Section("Done?") {
                    Button("Done") {
                        Task { await model.sendQuickFeedback(for: priority, useful: true, acted: true) }
                    }
                    Button("Not done") {
                        Task { await model.sendQuickFeedback(for: priority, useful: true, acted: false) }
                    }
                }
            } else {
                Text("No priority to rate yet.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Feedback")
    }
}

private struct WatchCaptureView: View {
    @EnvironmentObject private var model: WatchDecisionModel

    var body: some View {
        List {
            Section {
                TextField("Dictate or type a note", text: $model.captureText, axis: .vertical)
                    .lineLimit(2...4)
                    .textFieldStyle(.plain)
                    .padding(8)
                    .background(CortexColor.bgSecondary)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                Button {
                    Task { await model.captureByVoice() }
                } label: {
                    Label("Save note", systemImage: "mic.fill")
                }
                .disabled(model.captureText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            } footer: {
                Text(model.isOffline ? "Offline: captured items queue automatically." : "Captured items sync automatically.")
                    .font(.caption2)
            }
        }
        .navigationTitle("Capture")
    }
}
