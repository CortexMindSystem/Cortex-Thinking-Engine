//
//  ConfidenceIndicator.swift
//  CortexOS
//
//  Subtle confidence badge — shows 0.0–1.0 as styled percentage.
//

import SwiftUI

struct ConfidenceIndicator: View {
    let value: Double

    var body: some View {
        Text("\(Int(value * 100))%")
            .font(CortexFont.mono)
            .foregroundStyle(CortexColor.confidence(value))
            .padding(.horizontal, CortexSpacing.sm)
            .padding(.vertical, CortexSpacing.xxs)
            .background(CortexColor.confidence(value).opacity(0.12))
            .clipShape(Capsule())
    }
}
