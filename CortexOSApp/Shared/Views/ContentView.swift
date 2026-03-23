//
//  ContentView.swift
//  CortexOS
//
//  Root navigation — iOS: 4 focused tabs, macOS: sidebar + detail.
//  Pulls sync snapshot on launch.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var engine = CortexEngine()

    var body: some View {
        #if os(iOS)
        iOSRoot
        #else
        macOSRoot
        #endif
    }

    // MARK: - iOS (4 tabs — daily decisions)

    #if os(iOS)
    private var iOSRoot: some View {
        TabView {
            NavigationStack { DailyFocusView() }
                .tabItem { Label("Focus", systemImage: "sparkles") }

            NavigationStack { InsightFeedView() }
                .tabItem { Label("Insights", systemImage: "lightbulb") }

            NavigationStack { QuickCaptureView() }
                .tabItem { Label("Capture", systemImage: "plus.circle") }

            NavigationStack { ContextView() }
                .tabItem { Label("Context", systemImage: "brain.head.profile") }
        }
        .tint(CortexColor.accent)
        .environmentObject(engine)
        .task { await engine.sync() }
    }
    #endif

    // MARK: - macOS (sidebar — deep thinking)

    #if os(macOS)
    @State private var selection: MacSection? = .focus

    private var macOSRoot: some View {
        NavigationSplitView {
            List(selection: $selection) {
                Section("Intelligence") {
                    Label("Focus", systemImage: "sparkles")
                        .tag(MacSection.focus)
                    Label("Insights", systemImage: "lightbulb")
                        .tag(MacSection.insights)
                    Label("Signals", systemImage: "antenna.radiowaves.left.and.right")
                        .tag(MacSection.signals)
                }

                Section("Depth") {
                    Label("Decisions", systemImage: "checkmark.seal")
                        .tag(MacSection.decisions)
                    Label("Memory", systemImage: "brain")
                        .tag(MacSection.memory)
                    Label("Knowledge", systemImage: "doc.text")
                        .tag(MacSection.knowledge)
                }

                Section("System") {
                    Label("Pipeline", systemImage: "arrow.triangle.branch")
                        .tag(MacSection.pipeline)
                    Label("Profile", systemImage: "person.crop.circle")
                        .tag(MacSection.profile)
                    Label("Settings", systemImage: "gear")
                        .tag(MacSection.settings)
                }
            }
            .navigationTitle("CortexOS")
            .listStyle(.sidebar)
        } detail: {
            Group {
                switch selection {
                case .focus:       DailyFocusView()
                case .insights:    InsightFeedView()
                case .signals:     SignalsView()
                case .decisions:   DecisionHistoryView()
                case .memory:      MemoryExplorerView()
                case .knowledge:   KnowledgeListView()
                case .pipeline:    PipelineView()
                case .profile:     ProfileView()
                case .settings:    SettingsView()
                case nil:          DailyFocusView()
                }
            }
        }
        .environmentObject(engine)
        .frame(minWidth: 800, minHeight: 500)
        .task { await engine.sync() }
    }

    enum MacSection: Hashable {
        case focus, insights, signals, decisions, memory, knowledge, pipeline, profile, settings
    }
    #endif
}

#Preview {
    ContentView()
}
