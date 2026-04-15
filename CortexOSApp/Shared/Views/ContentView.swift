//
//  ContentView.swift
//  CortexOS
//
//  Root navigation — calm, focused, minimal.
//  iOS: Focus / Capture. Open → Understand → Capture → Close.
//  macOS: Focus / Notes / Insights / Decisions / Memory. Quiet workbench.
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

    // MARK: - iOS (Focus / Capture)

    #if os(iOS)
    @State private var showSettings = false
    @State private var showReview = false

    private var iOSRoot: some View {
        TabView {
            NavigationStack {
                DailyFocusView()
                    .toolbar {
                        ToolbarItem(placement: .topBarLeading) {
                            Button { showReview = true } label: {
                                Image(systemName: "clock")
                                    .foregroundStyle(CortexColor.textTertiary)
                            }
                        }
                        ToolbarItem(placement: .topBarTrailing) {
                            Button { showSettings = true } label: {
                                Image(systemName: "gearshape")
                                    .foregroundStyle(CortexColor.textTertiary)
                            }
                        }
                    }
            }
            .tabItem { Label("Focus", systemImage: "target") }

            NavigationStack { QuickCaptureView() }
                .tabItem { Label("Capture", systemImage: "square.and.pencil") }
        }
        .tint(CortexColor.accent)
        .environmentObject(engine)
        .task {
            await engine.sync()
        }
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
        .sheet(isPresented: $showReview) {
            NavigationStack {
                HistoryView()
                    .environmentObject(engine)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") { showReview = false }
                        }
                    }
            }
        }
    }
    #endif

    // MARK: - macOS (Focus / Notes / Insights / Decisions / Memory)

    #if os(macOS)
    @State private var selection: MacSection? = .focus

    private var macOSRoot: some View {
        NavigationSplitView {
            List(selection: $selection) {
                Label("Focus", systemImage: "target")
                    .tag(MacSection.focus)
                Label("Notes", systemImage: "doc.text")
                    .tag(MacSection.notes)
                Label("Insights", systemImage: "lightbulb")
                    .tag(MacSection.insights)
                Label("Decisions", systemImage: "checkmark.seal")
                    .tag(MacSection.decisions)
                Label("Memory", systemImage: "brain.head.profile")
                    .tag(MacSection.memory)
            }
            .navigationTitle("CortexOS")
            .listStyle(.sidebar)
        } detail: {
            NavigationStack {
                switch selection {
                case .focus:       DailyFocusView()
                case .notes:       KnowledgeListView()
                case .insights:    InsightFeedView()
                case .decisions:   DecisionHistoryView()
                case .memory:      MemoryExplorerView()
                case nil:          DailyFocusView()
                }
            }
        }
        .environmentObject(engine)
        .frame(minWidth: 800, minHeight: 500)
        .task {
            await engine.sync()
        }
    }

    enum MacSection: Hashable {
        case focus, notes, insights, decisions, memory
    }
    #endif
}

#Preview {
    ContentView()
}
