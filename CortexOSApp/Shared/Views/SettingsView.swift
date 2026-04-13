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

    @AppStorage("cortex_system_name") private var systemName: String = "CortexOS"

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
                        .disabled(isTesting || serverURL.isEmpty)

                        Spacer()

                        if let feedback = connectionFeedback {
                            Text(feedback.message)
                                .font(CortexFont.caption)
                                .foregroundStyle(feedback.color)
                        }
                    }
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
        }
    }

    private func testConnection() async {
        isTesting = true
        connectionFeedback = nil
        defer { isTesting = false }

        await engine.checkConnection()
        connectionFeedback = engine.isConnected ? .success : .failure
    }

    private var statusLabel: String {
        if engine.api.isOffline { return "Local Offline Mode" }
        return engine.isConnected ? "Connected" : "Offline"
    }

    private var statusColor: Color {
        if engine.api.isOffline { return .blue }
        return engine.isConnected ? .green : .red.opacity(0.6)
    }
}

// MARK: - Supporting Types

private enum ConnectionFeedback {
    case success, failure

    var message: String {
        switch self {
        case .success: "Connected"
        case .failure: "Unable to connect"
        }
    }

    var color: Color {
        switch self {
        case .success: .green
        case .failure: .red
        }
    }
}

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(CortexEngine())
    }
}
