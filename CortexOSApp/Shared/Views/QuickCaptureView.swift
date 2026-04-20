//
//  QuickCaptureView.swift
//  CortexOS
//
//  Capture a thought or decision in seconds.
//  Built for fast input, large writing surfaces, and reliable offline flow.
//

import SwiftUI

struct QuickCaptureView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var text = ""
    @State private var mode: CaptureMode = .thought
    @State private var reason = ""
    @State private var saved = false

    @FocusState private var focusedField: FocusField?

    private var canSave: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// Auto-detect URL in the text.
    private var detectedURL: String? {
        text.split(separator: " ").map(String.init)
            .first { $0.hasPrefix("http://") || $0.hasPrefix("https://") }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                Picker("", selection: $mode) {
                    Text("Thought").tag(CaptureMode.thought)
                    Text("Decision").tag(CaptureMode.decision)
                }
                .pickerStyle(.segmented)

                CaptureEditorCard(
                    title: mode == .thought ? "Thought" : "Decision",
                    placeholder: mode == .thought ? "What matters right now?" : "What did you decide?",
                    text: $text,
                    minHeight: 190,
                    focused: _focusedField,
                    field: .text
                )

                if mode == .decision {
                    CaptureEditorCard(
                        title: "Why",
                        placeholder: "Why this decision?",
                        text: $reason,
                        minHeight: 130,
                        focused: _focusedField,
                        field: .reason
                    )
                    .transition(.opacity.combined(with: .move(edge: .top)))
                }

                if let url = detectedURL {
                    HStack(spacing: CortexSpacing.xs) {
                        Image(systemName: "link")
                            .font(.caption2)
                        Text(url)
                            .font(CortexFont.caption)
                            .lineLimit(1)
                    }
                    .foregroundStyle(CortexColor.accent)
                }

                if saved {
                    Label(
                        engine.isConnected ? "Saved" : "Saved offline",
                        systemImage: engine.isConnected ? "checkmark.circle.fill" : "arrow.clockwise.circle"
                    )
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.success)
                    .transition(.opacity)
                }
            }
            .padding(CortexSpacing.xl)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Capture")
        .scrollDismissesKeyboard(.interactively)
        .safeAreaInset(edge: .bottom) {
            HStack(spacing: CortexSpacing.md) {
                if focusedField != nil {
                    Button {
                        focusedField = nil
                    } label: {
                        Label("Done", systemImage: "keyboard.chevron.compact.down")
                            .font(CortexFont.captionMedium)
                    }
                    .buttonStyle(.bordered)
                } else if canSave {
                    Button {
                        text = ""
                        reason = ""
                    } label: {
                        Label("Clear", systemImage: "xmark.circle")
                            .font(CortexFont.captionMedium)
                    }
                    .buttonStyle(.bordered)
                }

                Button {
                    Task { await save() }
                } label: {
                    HStack {
                        Spacer()
                        Text("Save")
                            .font(CortexFont.bodyMedium)
                        Spacer()
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(CortexColor.accent)
                .disabled(!canSave)
            }
            .padding(.horizontal, CortexSpacing.xl)
            .padding(.vertical, CortexSpacing.sm)
            .background(.ultraThinMaterial)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                if focusedField != nil {
                    Button("Done") {
                        focusedField = nil
                    }
                }
            }
        }
        .animation(.easeInOut(duration: 0.2), value: mode)
        .animation(.easeInOut(duration: 0.2), value: saved)
        .onTapGesture {
            focusedField = nil
        }
    }

    private func save() async {
        focusedField = nil

        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let success: Bool

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

private struct CaptureEditorCard: View {
    let title: String
    let placeholder: String
    @Binding var text: String
    let minHeight: CGFloat
    @FocusState var focused: FocusField?
    let field: FocusField

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xs) {
            Text(title)
                .font(CortexFont.captionMedium)
                .foregroundStyle(CortexColor.textSecondary)

            ZStack(alignment: .topLeading) {
                TextEditor(text: $text)
                    .font(CortexFont.body)
                    .scrollContentBackground(.hidden)
                    .frame(minHeight: minHeight)
                    .padding(CortexSpacing.sm)
                    .focused($focused, equals: field)
                    #if os(iOS)
                    .textInputAutocapitalization(.sentences)
                    #endif

                if text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    Text(placeholder)
                        .font(CortexFont.body)
                        .foregroundStyle(CortexColor.textTertiary)
                        .padding(.top, CortexSpacing.md)
                        .padding(.leading, CortexSpacing.md)
                        .allowsHitTesting(false)
                }
            }
            .background(CortexColor.bgSurface)
            .clipShape(RoundedRectangle(cornerRadius: CortexRadius.large, style: .continuous))
            .cortexShadow()
        }
    }
}

private enum CaptureMode {
    case thought
    case decision
}

private enum FocusField: Hashable {
    case text
    case reason
}
