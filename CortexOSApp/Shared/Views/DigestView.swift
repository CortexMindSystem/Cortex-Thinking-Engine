//
//  DigestView.swift
//  CortexOS
//
//  Displays digest evaluation metrics — shows how well the
//  latest RSS digest aligns with the user's context.
//

import SwiftUI

struct DigestView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var isEvaluating = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                headerSection

                if let score = engine.digestScore {
                    metricsGrid(score)
                    topArticlesSection(score.topArticles)
                } else {
                    emptyState
                }
            }
            .padding()
        }
        .navigationTitle("Digest")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    Task { await evaluate() }
                } label: {
                    if isEvaluating {
                        ProgressView().controlSize(.small)
                    } else {
                        Label("Evaluate", systemImage: "chart.bar.xaxis")
                    }
                }
                .disabled(isEvaluating)
            }
        }
    }

    // MARK: - Sections

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Digest Quality")
                .font(.title2)
                .fontWeight(.semibold)
            Text("How well does your latest digest match your context?")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    private func metricsGrid(_ score: DigestScore) -> some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible()),
        ], spacing: 12) {
            metricCard("Articles", value: "\(score.totalArticles)", icon: "doc.text")
            metricCard("AI Ratio", value: pct(score.aiArticleRatio), icon: "brain")
            metricCard("High Signal", value: pct(score.highSignalRatio), icon: "antenna.radiowaves.left.and.right")
            metricCard("S/N Ratio", value: pct(score.signalToNoiseRatio), icon: "waveform")
            metricCard("Context Fit", value: pct(score.contextKeywordCoverage), icon: "person.crop.circle")
            metricCard("Project Fit", value: pct(score.projectFitScore), icon: "target")
        }
    }

    private func topArticlesSection(_ articles: [ArticleScoreItem]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Top Articles")
                .font(.headline)

            if articles.isEmpty {
                Text("No articles scored yet.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(articles) { article in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(article.title)
                                .font(.subheadline)
                                .lineLimit(2)
                        }
                        Spacer()
                        Text(String(format: "%.0f", article.score * 100))
                            .font(.title3)
                            .fontWeight(.bold)
                            .foregroundStyle(scoreColor(article.score))
                    }
                    .padding(.vertical, 4)
                    Divider()
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)

            Text("No evaluation yet")
                .font(.headline)

            Text("Tap **Evaluate** to score your latest digest against your profile.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button("Evaluate Digest") {
                Task { await evaluate() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(isEvaluating)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Components

    private func metricCard(_ label: String, value: String, icon: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.blue)
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.04), radius: 3, y: 1)
    }

    // MARK: - Helpers

    private func evaluate() async {
        isEvaluating = true
        defer { isEvaluating = false }
        await engine.evaluateDigest()
    }

    private func pct(_ val: Double) -> String {
        String(format: "%.0f%%", val * 100)
    }

    private func scoreColor(_ score: Double) -> Color {
        switch score {
        case 0.7...: return .green
        case 0.4...: return .orange
        default: return .red
        }
    }
}

#Preview {
    NavigationStack {
        DigestView()
    }
    .environmentObject(CortexEngine())
}
