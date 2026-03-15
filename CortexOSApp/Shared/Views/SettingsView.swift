//
//  SettingsView.swift
//  CortexOS
//
//  Configure server URL, LLM preferences, and app settings.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var serverURL: String = ""
    @State private var testResult: String?
    @State private var isTesting = false

    var body: some View {
        Form {
            Section("Server Connection") {
                TextField("API Server URL", text: $serverURL)
                    #if os(iOS)
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    #endif
                    .onAppear { serverURL = engine.api.baseURL }

                HStack {
                    Button("Save & Test") {
                        engine.api.baseURL = serverURL
                        Task { await testConnection() }
                    }
                    .disabled(isTesting)

                    if isTesting {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Spacer()

                    if let result = testResult {
                        Text(result)
                            .font(.caption)
                            .foregroundStyle(result.contains("✓") ? .green : .red)
                    }
                }
            }

            Section("System Info") {
                if let status = engine.serverStatus {
                    LabeledContent("Version", value: status.version)
                    LabeledContent("Data Directory", value: status.dataDir)
                    LabeledContent("LLM Provider", value: status.llmProvider)
                    LabeledContent("LLM Model", value: status.llmModel)
                    LabeledContent("Total Notes", value: "\(status.notesCount)")
                } else {
                    Text("Connect to server to view system info")
                        .foregroundStyle(.secondary)
                }
            }

            Section("About") {
                LabeledContent("App", value: "CortexOS")
                LabeledContent("Version", value: "0.1.0")
                LabeledContent("Author", value: "Pierre-Henry Soria")

                Link("GitHub", destination: URL(string: "https://github.com/pH-7")!)
                Link("Website", destination: URL(string: "https://ph7.me")!)
            }
        }
        .navigationTitle("Settings")
        .task {
            await engine.fetchStatus()
        }
    }

    private func testConnection() async {
        isTesting = true
        defer { isTesting = false }

        await engine.checkConnection()
        if engine.isConnected {
            await engine.fetchStatus()
            testResult = "✓ Connected"
        } else {
            testResult = "✗ \(engine.errorMessage ?? "Failed")"
        }
    }
}

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(CortexEngine())
    }
}
