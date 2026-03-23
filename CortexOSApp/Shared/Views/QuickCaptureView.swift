//
//  QuickCaptureView.swift
//  CortexOS
//
//  Minimal friction capture — add a note, link, or thought.
//  Almost zero UI. Submit and done.
//

import SwiftUI

struct QuickCaptureView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var title = ""
    @State private var insight = ""
    @State private var url = ""
    @State private var tags = ""
    @State private var saved = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                // Title (required)
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Title")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textSecondary)
                    TextField("What did you learn?", text: $title)
                        .textFieldStyle(.roundedBorder)
                }

                // Insight
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Insight")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textSecondary)
                    TextField("Key takeaway...", text: $insight, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .lineLimit(3...6)
                }

                // URL (optional)
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Source URL")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textSecondary)
                    TextField("https://...", text: $url)
                        .textFieldStyle(.roundedBorder)
                        #if os(iOS)
                        .keyboardType(.URL)
                        .textInputAutocapitalization(.never)
                        #endif
                }

                // Tags
                VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                    Text("Tags")
                        .font(CortexFont.captionMedium)
                        .foregroundStyle(CortexColor.textSecondary)
                    TextField("ai, memory, signals", text: $tags)
                        .textFieldStyle(.roundedBorder)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        #endif
                }

                // Save
                Button {
                    Task { await save() }
                } label: {
                    HStack {
                        Spacer()
                        Label("Save", systemImage: "plus.circle.fill")
                            .font(CortexFont.bodyMedium)
                        Spacer()
                    }
                    .padding(.vertical, CortexSpacing.md)
                }
                .buttonStyle(.borderedProminent)
                .tint(CortexColor.accent)
                .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)

                // Success
                if saved {
                    Label("Saved", systemImage: "checkmark.circle.fill")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.success)
                        .transition(.opacity)
                }
            }
            .padding(CortexSpacing.xl)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Capture")
    }

    private func save() async {
        let parsedTags = tags
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }

        let note = NoteCreateRequest(
            title: title.trimmingCharacters(in: .whitespaces),
            insight: insight,
            sourceURL: url,
            tags: parsedTags
        )

        await engine.createNote(note)

        withAnimation {
            saved = true
            title = ""
            insight = ""
            url = ""
            tags = ""
        }

        // Auto-dismiss success after 2s
        try? await Task.sleep(for: .seconds(2))
        withAnimation { saved = false }
    }
}
