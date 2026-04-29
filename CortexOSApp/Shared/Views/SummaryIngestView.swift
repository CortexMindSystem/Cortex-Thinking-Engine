//
//  SummaryIngestView.swift
//  CortexOS
//
//  Paste a summary, analysis, or reflection. CortexOS breaks it
//  into structured Items and KnowledgeNotes that feed your
//  focus briefs, signals, and decisions.
//
//  Your thinking becomes part of the system.
//

import SwiftUI

struct SummaryIngestView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var content = ""
    @State private var source = ""
    @State private var ingested = false

    private var canSubmit: Bool {
        !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.lg) {
            // Summary input
            VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                Text("Paste your summary")
                    .cortexFieldLabel()

                TextEditor(text: $content)
                    .scrollContentBackground(.hidden)
                    .cortexInputSurface(minHeight: 170)
            }

            // Source label (optional — where did this come from?)
            TextField("Source (optional)", text: $source)
                .textFieldStyle(.plain)
                .cortexInputSurface()

            // Submit
            Button {
                Task { await submit() }
            } label: {
                HStack {
                    Spacer()
                    if engine.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Label("Process", systemImage: "square.and.arrow.down.fill")
                            .font(CortexFont.bodyMedium)
                    }
                    Spacer()
                }
                .padding(.vertical, CortexSpacing.md)
            }
            .buttonStyle(CortexPrimaryButtonStyle(fullWidth: true))
            .disabled(!canSubmit || engine.isLoading)

            // Result
            if ingested, let result = engine.lastIngestResult {
                HStack(spacing: CortexSpacing.sm) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(CortexColor.success)
                    Text("\(result.itemsIngested) items, \(result.notesCreated) notes created")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textSecondary)
                }
                .transition(.opacity)
            }

            Spacer()
        }
        .padding(CortexSpacing.xl)
        .background(CortexColor.bgPrimary)
        .navigationTitle("Process")
    }

    private func submit() async {
        let success = await engine.ingestSummary(
            content: content,
            source: source.trimmingCharacters(in: .whitespacesAndNewlines)
        )

        if success {
            withAnimation {
                ingested = true
                content = ""
                source = ""
            }

            try? await Task.sleep(for: .seconds(3))
            withAnimation { ingested = false }
        }
    }
}
