//
//  SettingsView.swift
//  CortexOS
//
//  Minimal settings. Connection, identity, about.
//  No dashboard metrics. No developer tools exposed.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var serverURL: String = ""
    @State private var connectionFeedback: ConnectionFeedback?
    @State private var isTesting = false
    @State private var isPreparingDemo = false
    @State private var isRetryingQueue = false
    @State private var showQueueSheet = false

    @AppStorage("cortex_system_name") private var systemName: String = "CortexOS"
    @AppStorage("cortex_demo_mode_enabled") private var demoModeEnabled: Bool = true

    var body: some View {
        Form {
            // MARK: - Connection
            Section {
                HStack(spacing: CortexSpacing.sm) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 8, height: 8)
                    Text(statusLabel)
                        .font(CortexFont.body)
                        .foregroundStyle(CortexColor.textPrimary)
                    Spacer()
                }

                DisclosureGroup("Server") {
                    TextField("Endpoint URL", text: $serverURL)
                        #if os(iOS)
                        .keyboardType(.URL)
                        .textInputAutocapitalization(.never)
                        #endif
                        .onChange(of: serverURL) { _, newValue in
                            engine.api.baseURL = newValue
                        }
                        .onAppear {
                            serverURL = engine.api.baseURL
                        }

                    Text("Leave empty to run fully offline on this device.")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)

                    HStack {
                        Button {
                            Task { await testConnection() }
                        } label: {
                            HStack(spacing: CortexSpacing.xs) {
                                Text("Test")
                                if isTesting {
                                    ProgressView()
                                        .controlSize(.small)
                                }
                            }
                        }
                        .disabled(isTesting)

                        Spacer()

                        if let feedback = connectionFeedback {
                            Text(feedback.message)
                                .font(CortexFont.caption)
                                .foregroundStyle(feedback.color)
                        }
                    }
                }

                if engine.pendingSyncActions > 0 {
                    Button {
                        showQueueSheet = true
                    } label: {
                        HStack {
                            Label("Pending offline actions", systemImage: "tray.and.arrow.up")
                                .font(CortexFont.caption)
                                .foregroundStyle(CortexColor.textSecondary)
                            Spacer()
                            Text("\(engine.pendingSyncActions)")
                                .font(CortexFont.captionMedium)
                                .foregroundStyle(CortexColor.accent)
                            Image(systemName: "chevron.right")
                                .font(.caption2)
                                .foregroundStyle(CortexColor.textTertiary)
                        }
                    }
                    .buttonStyle(.plain)
                }
            } header: {
                Text("Connection")
            }

            // MARK: - Identity
            Section {
                TextField("Name", text: $systemName)
            } header: {
                Text("Identity")
            }

            // MARK: - Demo
            Section {
                Toggle("Demo Mode", isOn: $demoModeEnabled)
                    .onChange(of: demoModeEnabled) { _, enabled in
                        Task {
                            isPreparingDemo = true
                            await engine.setDemoMode(enabled: enabled)
                            isPreparingDemo = false
                        }
                    }

                Button {
                    Task {
                        isPreparingDemo = true
                        await engine.populateDemoContent()
                        isPreparingDemo = false
                    }
                } label: {
                    HStack(spacing: CortexSpacing.xs) {
                        Text("Populate Demo Content")
                        if isPreparingDemo {
                            ProgressView()
                                .controlSize(.small)
                        }
                    }
                }
                .disabled(isPreparingDemo)

                Text("Use demo mode to review all screens with realistic preloaded content.")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)
            } header: {
                Text("App Review")
            }

            // MARK: - About
            Section("About") {
                LabeledContent("Version", value: "1.1.0")
                LabeledContent("Built by", value: "Pierre-Henry Soria")

                Link(destination: URL(string: "https://github.com/pH-7")!) {
                    HStack {
                        Text("GitHub")
                        Spacer()
                        Image(systemName: "arrow.up.right")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Link(destination: URL(string: "https://ph7.me")!) {
                    HStack {
                        Text("Website")
                        Spacer()
                        Image(systemName: "arrow.up.right")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Settings")
        .task {
            await engine.checkConnection()
            await engine.refreshPendingSyncActions()
            demoModeEnabled = engine.demoModeEnabled
        }
        .sheet(isPresented: $showQueueSheet) {
            queueSheet
        }
    }

    private func testConnection() async {
        isTesting = true
        connectionFeedback = nil
        defer { isTesting = false }

        await engine.checkConnection()
        if engine.api.isOffline {
            connectionFeedback = .local
        } else {
            connectionFeedback = engine.isConnected ? .success : .failure
        }
    }

    private var statusLabel: String {
        if engine.api.isOffline { return "Local Offline Mode" }
        return engine.isConnected ? "Connected" : "Offline"
    }

    private var statusColor: Color {
        if engine.api.isOffline { return .blue }
        return engine.isConnected ? .green : .red.opacity(0.6)
    }

    private var queueSheet: some View {
        NavigationStack {
            List {
                Section("Pending Counts") {
                    LabeledContent("Notes", value: "\(engine.pendingNotes)")
                    LabeledContent("Decisions", value: "\(engine.pendingDecisions)")
                    LabeledContent("Feedback", value: "\(engine.pendingFeedback)")
                    LabeledContent("Total", value: "\(engine.pendingSyncActions)")
                }

                Section("Queued Items") {
                    if engine.queuedActions.isEmpty {
                        Text("No queued actions.")
                            .font(CortexFont.caption)
                            .foregroundStyle(CortexColor.textTertiary)
                    } else {
                        ForEach(engine.queuedActions) { item in
                            VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                                HStack {
                                    Text(item.kind)
                                        .font(CortexFont.captionMedium)
                                        .foregroundStyle(CortexColor.accent)
                                    Spacer()
                                    Text(item.capturedAt, style: .relative)
                                        .font(CortexFont.caption)
                                        .foregroundStyle(CortexColor.textTertiary)
                                }
                                Text(item.title)
                                    .font(CortexFont.caption)
                                    .foregroundStyle(CortexColor.textPrimary)
                                    .lineLimit(2)
                            }
                            .padding(.vertical, CortexSpacing.xxs)
                        }
                    }
                }
            }
            .navigationTitle("Offline Queue")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { showQueueSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task {
                            isRetryingQueue = true
                            await engine.retryPendingSyncActions()
                            isRetryingQueue = false
                        }
                    } label: {
                        if isRetryingQueue {
                            ProgressView()
                        } else {
                            Text("Retry Sync")
                        }
                    }
                    .disabled(isRetryingQueue)
                }
            }
            .task {
                await engine.refreshPendingSyncActions()
            }
        }
    }
}

// MARK: - Supporting Types

private enum ConnectionFeedback {
    case success, failure, local

    var message: String {
        switch self {
        case .success: "Connected"
        case .failure: "Unable to connect"
        case .local: "Local mode active"
        }
    }

    var color: Color {
        switch self {
        case .success: .green
        case .failure: .red
        case .local: .blue
        }
    }
}

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(CortexEngine())
    }
}
