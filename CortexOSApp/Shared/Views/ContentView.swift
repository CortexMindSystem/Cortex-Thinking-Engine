//
//  ContentView.swift
//  CortexOS
//
//  Root navigation — radically simple.
//  iOS: Focus is the hero. Capture + Insights secondary.
//  macOS: 4 sidebar items. That's it.
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

    // MARK: - iOS (3 tabs — Focus first, always)

    #if os(iOS)
    private var iOSRoot: some View {
        TabView {
            NavigationStack { DailyFocusView() }
                .tabItem { Label("Focus", systemImage: "sparkles") }

            NavigationStack { QuickCaptureView() }
                .tabItem { Label("Capture", systemImage: "plus.circle") }

            NavigationStack { InsightFeedView() }
                .tabItem { Label("Insights", systemImage: "lightbulb") }
        }
        .tint(CortexColor.accent)
        .environmentObject(engine)
        .task { await engine.sync() }
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
