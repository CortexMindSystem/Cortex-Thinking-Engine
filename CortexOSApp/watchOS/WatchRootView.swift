import SwiftUI

struct WatchRootView: View {
    @EnvironmentObject private var model: WatchDecisionModel

    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Circle()
                            .fill(model.isOffline ? Color.orange : Color.green)
                            .frame(width: 8, height: 8)
                        Text(model.isOffline ? "Offline" : "Connected")
                            .font(.caption2)
                        Spacer()
                        if model.pendingCount > 0 {
                            Text("Queue \(model.pendingCount)")
                                .font(.caption2)
                                .foregroundStyle(.blue)
                        }
                    }
                    Text(model.status)
                        .font(.caption2)
                        .foregroundStyle(.secondary)

                    Button {
                        Task { await model.sync() }
                    } label: {
                        Label(model.isSyncing ? "Syncing..." : "Sync", systemImage: "arrow.clockwise")
                    }
                    .disabled(model.isSyncing)
                }

                Section("Top 3 Priorities") {
                    if let today = model.snapshot?.today, !today.priorities.isEmpty {
                        ForEach(today.priorities.prefix(3)) { priority in
                            NavigationLink {
                                WatchPriorityDetailView(priority: priority)
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("\(priority.rank). \(priority.title)")
                                        .font(.headline)
                                        .lineLimit(2)
                                    Text(priority.action)
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(2)
                                }
                            }
                        }
                    } else {
                        Text("No priorities yet.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Section("Voice Capture") {
                    TextField("Speak or dictate a thought", text: $model.captureText, axis: .vertical)
                        .lineLimit(2...4)
                    Button {
                        Task { await model.captureByVoice() }
                    } label: {
                        Label("Capture", systemImage: "mic.fill")
                    }
                    .disabled(model.captureText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
            .navigationTitle("CortexOS")
        }
    }
}

private struct WatchPriorityDetailView: View {
    @EnvironmentObject private var model: WatchDecisionModel
    let priority: SyncTodayPriority

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                Text(priority.title)
                    .font(.headline)
                Text("Why")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(priority.why)
                    .font(.caption)

                Text("Action")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(priority.action)
                    .font(.caption)

                HStack(spacing: 8) {
                    Button("Done") {
                        Task {
                            await model.sendQuickFeedback(for: priority, useful: true, acted: true)
                            await model.sync()
                        }
                    }
                    .buttonStyle(.borderedProminent)

                    Button("Later") {
                        Task {
                            await model.sendQuickFeedback(for: priority, useful: false, acted: false)
                        }
                    }
                    .buttonStyle(.bordered)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 8)
        }
        .navigationTitle("Priority \(priority.rank)")
    }
}

