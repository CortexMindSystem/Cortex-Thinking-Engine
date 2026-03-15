//
//  PostsView.swift
//  CortexOS
//
//  Generate and preview social media posts.
//

import SwiftUI

struct PostsView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var limit = 3
    @State private var selectedPlatform = "general"
    @State private var useLLM = false

    private let platforms = ["general", "twitter", "linkedin", "bluesky"]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                configSection
                postsSection
            }
            .padding()
        }
        .navigationTitle("Social Posts")
    }

    // MARK: - Config

    private var configSection: some View {
        VStack(spacing: 12) {
            Picker("Platform", selection: $selectedPlatform) {
                ForEach(platforms, id: \.self) { platform in
                    Text(platform.capitalized).tag(platform)
                }
            }
            .pickerStyle(.segmented)

            Stepper("Posts: \(limit)", value: $limit, in: 1...10)

            Toggle("Use LLM generation", isOn: $useLLM)

            Button {
                Task {
                    await engine.generatePosts(
                        limit: limit,
                        platform: selectedPlatform,
                        useLLM: useLLM
                    )
                }
            } label: {
                HStack {
                    if engine.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    }
                    Text(engine.isLoading ? "Generating…" : "Generate Posts")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.purple)
            .disabled(engine.isLoading)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Posts

    private var postsSection: some View {
        Group {
            if engine.posts.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "text.bubble")
                        .font(.title)
                        .foregroundStyle(.secondary)
                    Text("Generate posts from your knowledge notes")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 32)
            } else {
                LazyVStack(spacing: 16) {
                    ForEach(engine.posts) { post in
                        PostCard(post: post)
                    }
                }
            }
        }
    }
}

struct PostCard: View {
    let post: SocialPost
    @State private var copied = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: post.platformIcon)
                    .foregroundStyle(.purple)
                Text(post.platform.capitalized)
                    .font(.caption.bold())
                    .foregroundStyle(.purple)
                Spacer()
                Button {
                    copyToClipboard()
                } label: {
                    Image(systemName: copied ? "checkmark" : "doc.on.doc")
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }

            Text(post.text)
                .font(.body)
                .textSelection(.enabled)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private func copyToClipboard() {
        #if os(iOS)
        UIPasteboard.general.string = post.text
        #elseif os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(post.text, forType: .string)
        #endif
        copied = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            copied = false
        }
    }
}

#Preview {
    NavigationStack {
        PostsView()
            .environmentObject(CortexEngine())
    }
}
