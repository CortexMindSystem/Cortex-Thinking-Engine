//
//  PipelineView.swift
//  CortexOS
//
//  Run and monitor the CortexOS processing pipeline.
//

import SwiftUI

struct PipelineView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var useLLM = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                controlSection
                resultsSection
            }
            .padding()
        }
        .navigationTitle("Pipeline")
    }

    // MARK: - Controls

    private var controlSection: some View {
        VStack(spacing: 16) {
            Image(systemName: "arrow.triangle.branch")
                .font(.system(size: 44))
                .foregroundStyle(.orange)

            Text("CortexOS Pipeline")
                .font(.title2.bold())

            Text("Process digests → Generate notes → Create posts")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Toggle("Use LLM for summarisation", isOn: $useLLM)
                .padding(.horizontal)

            Button {
                Task { await engine.runPipeline(useLLM: useLLM) }
            } label: {
                HStack {
                    if engine.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    }
                    Text(engine.isLoading ? "Running…" : "Run Pipeline")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.orange)
            .disabled(engine.isLoading)
            .controlSize(.large)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Results

    private var resultsSection: some View {
        Group {
            if let result = engine.pipelineResult {
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        Text("Last Run")
                            .font(.headline)
                        Spacer()
                        Image(systemName: result.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundStyle(result.success ? .green : .red)
                        Text(result.success ? "Success" : "Failed")
                            .foregroundStyle(result.success ? .green : .red)
                            .font(.subheadline.bold())
                    }

                    HStack {
                        Label(String(format: "%.2fs", result.durationS), systemImage: "clock")
                        Spacer()
                        Text("\(result.steps.count) steps")
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)

                    Divider()

                    ForEach(result.steps) { step in
                        StepRow(step: step)
                    }
                }
                .padding()
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "tray")
                        .font(.title)
                        .foregroundStyle(.secondary)
                    Text("No pipeline results yet")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 32)
            }
        }
    }
}

struct StepRow: View {
    let step: PipelineStepResult

    var body: some View {
        HStack {
            Image(systemName: step.statusIcon)
                .foregroundStyle(colorForStatus)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(step.name)
                    .font(.subheadline.bold())
                if let error = step.error {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                }
            }

            Spacer()

            if step.durationS > 0 {
                Text(String(format: "%.2fs", step.durationS))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    private var colorForStatus: Color {
        switch step.status {
        case "success": return .green
        case "running": return .blue
        case "failed":  return .red
        case "skipped": return .gray
        default:        return .secondary
        }
    }
}

#Preview {
    NavigationStack {
        PipelineView()
            .environmentObject(CortexEngine())
    }
}
