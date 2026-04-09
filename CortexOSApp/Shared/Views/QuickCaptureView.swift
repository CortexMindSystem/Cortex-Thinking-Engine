//
//  QuickCaptureView.swift
//  CortexOS
//
//  Capture a thought, link, or decision in seconds.
//  One input. No unnecessary fields. Always works offline.
//

import SwiftUI

struct QuickCaptureView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var text = ""
    @State private var mode: CaptureMode = .thought
    @State private var reason = ""
    @State private var saved = false

    private var canSave: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// Auto-detect URL in the text
    private var detectedURL: String? {
        text.split(separator: " ").map(String.init)
            .first { $0.hasPrefix("http://") || $0.hasPrefix("https://") }
    }

    var body: some View {
        VStack(spacing: CortexSpacing.lg) {
            Spacer()

            // Mode picker — minimal
            Picker("", selection: $mode) {
                Text("Thought").tag(CaptureMode.thought)
                Text("Decision").tag(CaptureMode.decision)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, CortexSpacing.xl)

            // Main input
            TextField(
                mode == .thought ? "What's on your mind?" : "What did you decide?",
                text: $text,
                axis: .vertical
            )
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
            .padding(.horizontal, CortexSpacing.xl)

            // Reason field — only for decisions, collapsed by default
            if mode == .decision {
                TextField("Why?", text: $reason, axis: .vertical)
                    .font(CortexFont.caption)
                    .lineLimit(1...3)
                    .textFieldStyle(.plain)
                    .padding(CortexSpacing.sm)
                    .background(CortexColor.bgSurface)
                    .clipShape(RoundedRectangle(cornerRadius: CortexRadius.small, style: .continuous))
                    .padding(.horizontal, CortexSpacing.xl)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }

            // Link indicator (auto-detected)
            if let url = detectedURL {
                HStack(spacing: CortexSpacing.xs) {
                    Image(systemName: "link")
                        .font(.caption2)
                    Text(url)
                        .font(CortexFont.caption)
                        .lineLimit(1)
                }
                .foregroundStyle(CortexColor.accent)
                .padding(.horizontal, CortexSpacing.xl)
                .transition(.opacity)
            }

            // Save
            Button {
                Task { await save() }
            } label: {
                HStack {
                    Spacer()
                    Text("Save")
                        .font(CortexFont.bodyMedium)
                    Spacer()
                }
                .padding(.vertical, CortexSpacing.md)
            }
            .buttonStyle(.borderedProminent)
            .tint(CortexColor.accent)
            .disabled(!canSave)
            .padding(.horizontal, CortexSpacing.xl)

            // Confirmation
            if saved {
                Label(
                    engine.isConnected ? "Saved" : "Saved offline",
                    systemImage: engine.isConnected ? "checkmark.circle.fill" : "arrow.clockwise.circle"
                )
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.success)
                .transition(.opacity)
            }

            Spacer()
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Capture")
        .animation(.easeInOut(duration: 0.2), value: mode)
    }

    private func save() async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        var success = false

        switch mode {
        case .thought:
            let note = NoteCreateRequest(
                title: trimmed,
                insight: "",
                sourceURL: detectedURL ?? "",
                tags: []
            )
            success = await engine.createNote(note)

        case .decision:
            let request = DecisionCreateRequest(
                decision: trimmed,
                reason: reason.trimmingCharacters(in: .whitespacesAndNewlines)
            )
            success = await engine.recordDecision(request)
        }

        guard success else { return }

        withAnimation {
            saved = true
            text = ""
            reason = ""
        }

        try? await Task.sleep(for: .seconds(2))
        withAnimation { saved = false }
    }
}

// MARK: - Mode

private enum CaptureMode {
    case thought, decision
}
