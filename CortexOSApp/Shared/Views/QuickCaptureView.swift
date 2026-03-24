//
//  QuickCaptureView.swift
//  CortexOS
//
//  Zero friction capture. Type a thought, paste a link, hit return.
//  No fields, no labels, no categories. Just capture.
//

import SwiftUI

struct QuickCaptureView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var text = ""
    @State private var saved = false

    private var canSave: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// Detect if the text contains a URL
    private var detectedURL: String? {
        let words = text.split(separator: " ").map(String.init)
        return words.first { $0.hasPrefix("http://") || $0.hasPrefix("https://") }
    }

    var body: some View {
        VStack(spacing: CortexSpacing.lg) {
            Spacer()

            // Single input — thought or link
            TextField("What's on your mind?", text: $text, axis: .vertical)
                .font(CortexFont.body)
                .lineLimit(1...6)
                .textFieldStyle(.plain)
                .padding(CortexSpacing.md)
                .background(CortexColor.bgSurface)
                .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
                .cortexShadow()
                .onSubmit { if canSave { Task { await save() } } }
                #if os(iOS)
                .textInputAutocapitalization(.sentences)
                #endif

            // Link indicator (auto-detected, no input needed)
            if let url = detectedURL {
                HStack(spacing: CortexSpacing.xs) {
                    Image(systemName: "link")
                        .font(.caption2)
                    Text(url)
                        .font(CortexFont.caption)
                        .lineLimit(1)
                }
                .foregroundStyle(CortexColor.accent)
                .transition(.opacity)
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
            .disabled(!canSave)

            // Saved confirmation
            if saved {
                Label("Saved", systemImage: "checkmark.circle.fill")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.success)
                    .transition(.opacity)
            }

            // Link to summary ingestion
            NavigationLink {
                SummaryIngestView()
            } label: {
                Label("Ingest a longer summary", systemImage: "square.and.arrow.down")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)
            }

            Spacer()
        }
        .padding(.horizontal, CortexSpacing.xl)
        .background(CortexColor.bgPrimary)
        .navigationTitle("Capture")
    }

    private func save() async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let note = NoteCreateRequest(
            title: trimmed,
            insight: "",
            sourceURL: detectedURL ?? "",
            tags: []
        )

        let success = await engine.createNote(note)
        guard success else { return }

        withAnimation {
            saved = true
            text = ""
        }

        try? await Task.sleep(for: .seconds(2))
        withAnimation { saved = false }
    }
}
