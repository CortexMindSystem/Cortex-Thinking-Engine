//
//  FocusView.swift
//  CortexOS
//
//  The PRIMARY CortexOS view — answers "What should I focus on today?"
//  Shows the daily brief with ranked focus items, relevance scores,
//  and actionable next steps.
//

import SwiftUI

struct FocusView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var isGenerating = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                headerSection
                if let brief = engine.dailyBrief {
                    briefContent(brief)
                } else {
                    emptyState
                }
            }
            .padding()
        }
        .navigationTitle("Focus")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    Task { await generate() }
                } label: {
                    if isGenerating {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Label("Generate", systemImage: "sparkles")
                    }
                }
                .disabled(isGenerating)
            }
        }
        .task {
            await engine.fetchTodayBrief()
        }
    }

    // MARK: - Sections

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("What should I focus on today?")
                .font(.title2)
                .fontWeight(.semibold)

            if let brief = engine.dailyBrief {
                Text(brief.date)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    @ViewBuilder
    private func briefContent(_ brief: DailyBrief) -> some View {
        if !brief.profileSummary.isEmpty {
            profileSummaryCard(brief.profileSummary)
        }

        ForEach(brief.focusItems) { item in
            focusItemCard(item)
        }

        if !brief.digestQuality.isEmpty {
            digestQualitySection(brief.digestQuality)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "sparkles")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)

            Text("No focus brief yet")
                .font(.headline)

            Text("Tap **Generate** to create your daily brief from the latest digest.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button("Generate Focus Brief") {
                Task { await generate() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(isGenerating)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Cards

    private func focusItemCard(_ item: FocusItem) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("#\(item.rank)")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(rankColor(item.rank))
                    .clipShape(Capsule())

                Text(item.title)
                    .font(.headline)

                Spacer()

                Text("\(Int(item.relevanceScore * 100))%")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
            }

            Text(item.whyItMatters)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack {
                Image(systemName: "arrow.right.circle.fill")
                    .foregroundStyle(.blue)
                Text(item.nextAction)
                    .font(.subheadline)
                    .fontWeight(.medium)
            }

            if !item.tags.isEmpty {
                HStack {
                    ForEach(item.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(.blue.opacity(0.1))
                            .clipShape(Capsule())
                    }
                }
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }

    private func profileSummaryCard(_ summary: [String: String]) -> some View {
        HStack {
            Image(systemName: "person.crop.circle")
                .foregroundStyle(.purple)
            Text(summary.map { "\($0.key): \($0.value)" }.joined(separator: " · "))
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.purple.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    private func digestQualitySection(_ quality: [String: Double]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Digest Quality")
                .font(.subheadline)
                .fontWeight(.semibold)

            let metrics = quality.sorted(by: { $0.key < $1.key })
            ForEach(metrics, id: \.key) { key, value in
                HStack {
                    Text(formatMetricName(key))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(String(format: "%.1f%%", value * 100))
                        .font(.caption)
                        .fontWeight(.medium)
                }
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    // MARK: - Helpers

    private func generate() async {
        isGenerating = true
        defer { isGenerating = false }
        await engine.generateFocusBrief()
    }

    private func rankColor(_ rank: Int) -> Color {
        switch rank {
        case 1: return .blue
        case 2: return .purple
        case 3: return .orange
        default: return .gray
        }
    }

    private func formatMetricName(_ key: String) -> String {
        key.replacingOccurrences(of: "_", with: " ").capitalized
    }
}

#Preview {
    NavigationStack {
        FocusView()
    }
    .environmentObject(CortexEngine())
}
