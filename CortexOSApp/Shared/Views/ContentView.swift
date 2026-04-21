//
//  ContentView.swift
//  CortexOS
//
//  Root navigation — calm, focused, minimal.
//  iOS: Focus / Capture. Open → Understand → Capture → Close.
//  macOS: Focus / Notes / Insights / Decisions / Memory / Weekly Review.
//  Quiet workbench.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var engine = CortexEngine()
    @AppStorage("simplixio_onboarding_completed") private var onboardingCompleted = false
    @State private var showOnboarding = false

    var body: some View {
        Group {
            #if os(iOS)
            iOSRoot
            #else
            macOSRoot
            #endif
        }
        .sheet(isPresented: $showOnboarding) {
            SimpliXioOnboardingView(
                showOnboarding: $showOnboarding,
                onboardingCompleted: $onboardingCompleted
            )
            .environmentObject(engine)
        }
        .task {
            if !onboardingCompleted {
                showOnboarding = true
            }
        }
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

    // MARK: - macOS (Focus / Notes / Insights / Decisions / Memory / Weekly Review)

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
                Label("Weekly Review", systemImage: "calendar.badge.clock")
                    .tag(MacSection.weeklyReview)
                Label("Decision Replay", systemImage: "arrow.triangle.branch")
                    .tag(MacSection.decisionReplay)
                Label("Settings", systemImage: "gearshape")
                    .tag(MacSection.settings)
            }
            .navigationTitle("SimpliXio")
            .listStyle(.sidebar)
        } detail: {
            NavigationStack {
                switch selection {
                case .focus:       DailyFocusView()
                case .notes:       KnowledgeListView()
                case .insights:    InsightFeedView()
                case .decisions:   DecisionHistoryView()
                case .memory:      MemoryExplorerView()
                case .weeklyReview: WeeklyReviewView()
                case .decisionReplay: DecisionReplayView()
                case .settings:    SettingsView()
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
        case focus, notes, insights, decisions, memory, weeklyReview, decisionReplay, settings
    }
    #endif
}

#Preview {
    ContentView()
}

private struct SimpliXioOnboardingView: View {
    @EnvironmentObject private var engine: CortexEngine
    @Binding var showOnboarding: Bool
    @Binding var onboardingCompleted: Bool
    @State private var isPreparingDemo = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                    VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                        Text("SimpliXio")
                            .font(CortexFont.largeTitle)
                            .foregroundStyle(CortexColor.textPrimary)

                        Text("Decide what matters.")
                            .font(CortexFont.title)
                            .foregroundStyle(CortexColor.textSecondary)
                    }

                    VStack(alignment: .leading, spacing: CortexSpacing.md) {
                        onboardingRow(
                            icon: "target",
                            title: "See 3 priorities",
                            message: "Get immediate clarity on what deserves attention now."
                        )
                        onboardingRow(
                            icon: "lightbulb",
                            title: "Understand why",
                            message: "Every priority includes reasoning and one next action."
                        )
                        onboardingRow(
                            icon: "square.and.pencil",
                            title: "Capture fast",
                            message: "Save thoughts and decisions instantly, even when offline."
                        )
                    }

                    Text("You can stay fully offline, or connect a server later in Settings.")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                }
                .padding(CortexSpacing.xl)
            }
            .background(CortexColor.bgPrimary)
            .navigationTitle("Welcome")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Skip") { finish() }
                }
            }
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: CortexSpacing.sm) {
                    Button {
                        Task {
                            isPreparingDemo = true
                            await engine.populateDemoContent()
                            isPreparingDemo = false
                            finish()
                        }
                    } label: {
                        HStack {
                            Spacer()
                            if isPreparingDemo {
                                ProgressView()
                                    .controlSize(.small)
                            } else {
                                Text("Start with Demo Data")
                                    .font(CortexFont.bodyMedium)
                            }
                            Spacer()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(CortexColor.accent)
                    .disabled(isPreparingDemo)

                    Button("Continue") {
                        finish()
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal, CortexSpacing.xl)
                .padding(.vertical, CortexSpacing.sm)
                .background(.ultraThinMaterial)
            }
        }
    }

    private func onboardingRow(icon: String, title: String, message: String) -> some View {
        HStack(alignment: .top, spacing: CortexSpacing.md) {
            Image(systemName: icon)
                .font(.headline)
                .foregroundStyle(CortexColor.accent)
                .frame(width: 24, alignment: .center)

            VStack(alignment: .leading, spacing: CortexSpacing.xxs) {
                Text(title)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)
                Text(message)
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textSecondary)
            }
        }
    }

    private func finish() {
        onboardingCompleted = true
        showOnboarding = false
    }
}
