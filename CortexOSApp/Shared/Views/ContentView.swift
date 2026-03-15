//
//  ContentView.swift
//  CortexOS
//
//  Root navigation structure shared by iOS and macOS.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var engine = CortexEngine()

    var body: some View {
        #if os(iOS)
        TabView {
            NavigationStack {
                FocusView()
            }
            .tabItem {
                Label("Focus", systemImage: "sparkles")
            }

            NavigationStack {
                DashboardView()
            }
            .tabItem {
                Label("Dashboard", systemImage: "brain.head.profile")
            }

            NavigationStack {
                DigestView()
            }
            .tabItem {
                Label("Digest", systemImage: "chart.bar.xaxis")
            }

            NavigationStack {
                KnowledgeListView()
            }
            .tabItem {
                Label("Knowledge", systemImage: "doc.text.fill")
            }

            NavigationStack {
                PipelineView()
            }
            .tabItem {
                Label("Pipeline", systemImage: "arrow.triangle.branch")
            }

            NavigationStack {
                PostsView()
            }
            .tabItem {
                Label("Posts", systemImage: "text.bubble.fill")
            }

            NavigationStack {
                ProfileView()
            }
            .tabItem {
                Label("Profile", systemImage: "person.crop.circle")
            }

            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Settings", systemImage: "gear")
            }
        }
        .environmentObject(engine)
        #else
        NavigationSplitView {
            List {
                NavigationLink {
                    FocusView()
                } label: {
                    Label("Focus", systemImage: "sparkles")
                }

                NavigationLink {
                    DashboardView()
                } label: {
                    Label("Dashboard", systemImage: "brain.head.profile")
                }

                NavigationLink {
                    DigestView()
                } label: {
                    Label("Digest", systemImage: "chart.bar.xaxis")
                }

                NavigationLink {
                    KnowledgeListView()
                } label: {
                    Label("Knowledge", systemImage: "doc.text.fill")
                }

                NavigationLink {
                    PipelineView()
                } label: {
                    Label("Pipeline", systemImage: "arrow.triangle.branch")
                }

                NavigationLink {
                    PostsView()
                } label: {
                    Label("Posts", systemImage: "text.bubble.fill")
                }

                Spacer()

                NavigationLink {
                    ProfileView()
                } label: {
                    Label("Profile", systemImage: "person.crop.circle")
                }

                NavigationLink {
                    SettingsView()
                } label: {
                    Label("Settings", systemImage: "gear")
                }
            }
            .navigationTitle("CortexOS")
            .listStyle(.sidebar)
        } detail: {
            FocusView()
        }
        .environmentObject(engine)
        .frame(minWidth: 800, minHeight: 500)
        #endif
    }
}

#Preview {
    ContentView()
}
