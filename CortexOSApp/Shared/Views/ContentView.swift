//
//  ContentView.swift
//  CortexOS
//
//  Root navigation — radically simple.
//  iOS: Focus is the hero. Decide + Capture secondary.
//  macOS: 5 sidebar items. That's it.
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

    // MARK: - iOS (3 tabs — Focus / Decide / Capture)

    #if os(iOS)
    @State private var showSettings = false

    private var iOSRoot: some View {
        TabView {
            NavigationStack {
                DailyFocusView()
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button { showSettings = true } label: {
                                Image(systemName: "gearshape")
                                    .foregroundStyle(CortexColor.textTertiary)
                            }
                        }
                    }
            }
            .tabItem { Label("Focus", systemImage: "sparkles") }

            NavigationStack { QuickDecisionView() }
                .tabItem { Label("Decide", systemImage: "checkmark.seal") }

            NavigationStack { QuickCaptureView() }
                .tabItem { Label("Capture", systemImage: "plus.circle") }
        }
        .tint(CortexColor.accent)
        .environmentObject(engine)
        .task { await engine.sync() }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView()
                    .environmentObject(engine)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") { showSettings = false }
                        }
                    }
            }
        }
    }
    #endif

    // MARK: - macOS (4 sidebar items — clarity, not chrome)

    #if os(macOS)
    @State private var selection: MacSection? = .focus

    private var macOSRoot: some View {
        NavigationSplitView {
            List(selection: $selection) {
                Label("Focus", systemImage: "sparkles")
                    .tag(MacSection.focus)
                Label("Insights", systemImage: "lightbulb")
                    .tag(MacSection.insights)
                Label("Ingest", systemImage: "square.and.arrow.down")
                    .tag(MacSection.ingest)
                Label("Memory", systemImage: "brain")
                    .tag(MacSection.memory)
                Label("Decisions", systemImage: "checkmark.seal")
                    .tag(MacSection.decisions)
            }
            .navigationTitle("CortexOS")
            .listStyle(.sidebar)
        } detail: {
            switch selection {
            case .focus:       DailyFocusView()
            case .insights:    InsightFeedView()
            case .ingest:      SummaryIngestView()
            case .memory:      MemoryExplorerView()
            case .decisions:   DecisionHistoryView()
            case nil:          DailyFocusView()
            }
        }
        .environmentObject(engine)
        .frame(minWidth: 800, minHeight: 500)
        .task { await engine.sync() }
    }

    enum MacSection: Hashable {
        case focus, insights, ingest, memory, decisions
    }
    #endif
}

#Preview {
    ContentView()
}
