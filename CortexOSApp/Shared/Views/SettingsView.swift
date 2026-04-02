//
//  SettingsView.swift
//  CortexOS
//
//  System settings and connection configuration.
//

import SwiftUI

// MARK: - Settings View

struct SettingsView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var serverURL: String = ""
    @State private var connectionFeedback: ConnectionFeedback?
    @State private var isTesting = false

    // Identity (persisted via UserDefaults)
    @AppStorage("cortex_system_name") private var systemName: String = "CortexOS"
    @AppStorage("cortex_mode") private var mode: String = "Focused Thinking"

    var body: some View {
        Form {
            // MARK: - CortexOS System
            Section {
                SystemStatusRow(isConnected: engine.isConnected)
            } header: {
                Text("CortexOS System")
            } footer: {
                if !engine.isConnected {
                    Text("Connect to enable CortexOS")
                        .foregroundStyle(.secondary)
                }
            }

            // MARK: - Connection
            Section("Connection") {
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

                HStack {
                    Button {
                        Task { await testConnection() }
                    } label: {
                        HStack(spacing: 8) {
                            Text("Test Connection")
                            if isTesting {
                                ProgressView()
                                    .controlSize(.small)
                            }
                        }
                    }
                    .disabled(isTesting || serverURL.isEmpty)

                    Spacer()

                    if let feedback = connectionFeedback {
                        ConnectionFeedbackLabel(feedback: feedback)
                    }
                }
            }

            // MARK: - Identity
            Section {
                TextField("System Name", text: $systemName)
                TextField("Mode", text: $mode)
            } header: {
                Text("Identity")
            } footer: {
                Text("Personalize how CortexOS identifies itself")
                    .foregroundStyle(.tertiary)
            }

            // MARK: - About CortexOS
            Section("About CortexOS") {
                LabeledContent("App", value: "CortexOS")
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
            await engine.fetchStatus()
        }
    }

    private func testConnection() async {
        isTesting = true
        connectionFeedback = nil
        defer { isTesting = false }

        await engine.checkConnection()
        if engine.isConnected {
            await engine.fetchStatus()
            connectionFeedback = .success
        } else {
            connectionFeedback = .failure
        }
    }
}

// MARK: - Supporting Types

private enum ConnectionFeedback {
    case success
    case failure

    var message: String {
        switch self {
        case .success: "Connected successfully"
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

// MARK: - Reusable Components

private struct SystemStatusRow: View {
    let isConnected: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(isConnected ? Color.green : Color.red.opacity(0.6))
                .frame(width: 10, height: 10)
                .shadow(color: isConnected ? .green.opacity(0.5) : .clear, radius: 4)

            Text(isConnected ? "Connected" : "Not connected")
                .font(.body)

            Spacer()
        }
        .padding(.vertical, 4)
    }
}

private struct ConnectionFeedbackLabel: View {
    let feedback: ConnectionFeedback

    var body: some View {
        Text(feedback.message)
            .font(.caption)
            .foregroundStyle(feedback.color)
            .transition(.opacity)
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(CortexEngine())
    }
}
