//
//  PriorityList.swift
//  CortexOS
//
//  Ranked list of today's priorities — the heart of the Daily Focus screen.
//  Shows rank badge, title, why, and next step. No scrolling if ≤ 3 items.
//

import SwiftUI

struct PriorityList: View {
    let priorities: [SyncPriority]

    var body: some View {
        VStack(spacing: CortexSpacing.md) {
            ForEach(Array(priorities.prefix(5).enumerated()), id: \.element.title) { index, priority in
                PriorityRow(priority: priority, position: index + 1)
            }
        }
    }
}

// MARK: - Row

struct PriorityRow: View {
    let priority: SyncPriority
    let position: Int

    var body: some View {
        HStack(alignment: .top, spacing: CortexSpacing.md) {
            // Rank badge
            Text("\(position)")
                .font(CortexFont.captionMedium)
                .foregroundStyle(.white)
                .frame(width: 24, height: 24)
                .background(CortexColor.rank(position))
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                // Title
                Text(priority.title)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)

                // Why it matters
                if !priority.whyItMatters.isEmpty {
                    Text(priority.whyItMatters)
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textSecondary)
                        .lineLimit(2)
                }

                // Next step
                if !priority.nextStep.isEmpty {
                    Label {
                        Text(priority.nextStep)
                            .lineLimit(1)
                    } icon: {
                        Image(systemName: "arrow.right.circle.fill")
                    }
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.accent)
                }
            }

            Spacer(minLength: 0)
        }
        .padding(CortexSpacing.md)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        .cortexShadow()
    }
}
