//
//  InsightFeedView.swift
//  CortexOS
//
//  Scannable feed of processed insights — not overwhelming.
//  Each item: summary, why it matters, action.
//

import SwiftUI

struct InsightFeedView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let insights = engine.snapshot?.insights, !insights.isEmpty {
                ScrollView {
                    LazyVStack(spacing: CortexSpacing.md) {
                        ForEach(insights) { insight in
                            InsightCard(insight: insight)
                        }
                    }
                    .padding(CortexSpacing.xl)
                }
            } else {
                EmptyStateView(
                    icon: "lightbulb",
                    title: "No insights yet",
                    message: "Insights are generated when you process digests or notes.",
                    actionTitle: "Refresh",
                    action: { Task { await engine.sync() } }
                )
            }
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Insights")
        .refreshable { await engine.sync() }
    }
}
