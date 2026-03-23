//
//  ContextTag.swift
//  CortexOS
//
//  Minimal pill tag for topics, interests, signals.
//

import SwiftUI

struct ContextTag: View {
    let text: String

    var body: some View {
        Text(text)
            .font(CortexFont.mono)
            .foregroundStyle(CortexColor.accent)
            .padding(.horizontal, CortexSpacing.sm)
            .padding(.vertical, CortexSpacing.xxs)
            .background(CortexColor.accentDim)
            .clipShape(Capsule())
    }
}
