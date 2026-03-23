//
//  InsightCard.swift
//  CortexOS
//
//  Single insight card — summary, why it matters, action, tags.
//  Scannable. Not overwhelming.
//

import SwiftUI

struct InsightCard: View {
    let insight: SyncInsight

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            // Title + confidence
            HStack {
                Text(insight.title)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)
                    .lineLimit(2)

                Spacer(minLength: 0)

                ConfidenceIndicator(value: insight.confidence)
            }

            // Summary
            if !insight.summary.isEmpty {
                Text(insight.summary)
                    .font(CortexFont.body)
                    .foregroundStyle(CortexColor.textSecondary)
                    .lineLimit(3)
            }

            // Why it matters
            if !insight.whyItMatters.isEmpty {
                Label {
                    Text(insight.whyItMatters)
                        .lineLimit(2)
                } icon: {
                    Image(systemName: "sparkle")
                }
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.accent)
            }

            // Next action
            if !insight.nextAction.isEmpty {
                Label {
                    Text(insight.nextAction)
                        .lineLimit(1)
                } icon: {
                    Image(systemName: "arrow.right.circle.fill")
                }
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.textSecondary)
            }

            // Tags
            if !insight.tags.isEmpty {
                HStack(spacing: CortexSpacing.xs) {
                    ForEach(insight.tags.prefix(4), id: \.self) { tag in
                        ContextTag(text: tag)
                    }
                }
            }
        }
        .padding(CortexSpacing.lg)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }
}
