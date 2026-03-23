//
//  EmptyStateView.swift
//  CortexOS
//
//  Consistent empty state — icon, title, message, optional action.
//

import SwiftUI

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: CortexSpacing.lg) {
            Image(systemName: icon)
                .font(.system(size: 40, weight: .light))
                .foregroundStyle(CortexColor.neutral)

            Text(title)
                .font(CortexFont.headline)
                .foregroundStyle(CortexColor.textPrimary)

            Text(message)
                .font(CortexFont.body)
                .foregroundStyle(CortexColor.textSecondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 280)

            if let actionTitle, let action {
                Button(action: action) {
                    Text(actionTitle)
                        .font(CortexFont.captionMedium)
                        .padding(.horizontal, CortexSpacing.lg)
                        .padding(.vertical, CortexSpacing.sm)
                }
                .buttonStyle(.borderedProminent)
                .tint(CortexColor.accent)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
