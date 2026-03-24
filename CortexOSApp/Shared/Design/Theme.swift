//
//  Theme.swift
//  CortexOS
//
//  Single source of truth for all design tokens.
//  Calm. Focused. Premium. Dark-first.
//

import SwiftUI

// MARK: - Colors

enum CortexColor {
    // Backgrounds — adaptive dark-first
    static let bgPrimary   = Color(light: Color(white: 0.98), dark: Color(white: 0.07))
    static let bgSecondary = Color(light: Color(white: 0.94), dark: Color(white: 0.11))
    static let bgSurface   = Color(light: .white, dark: Color(white: 0.14))

    // Text
    static let textPrimary   = Color.primary
    static let textSecondary = Color.secondary
    static let textTertiary  = Color(white: 0.5)

    // Accent — quiet blue-violet, not flashy
    static let accent    = Color(red: 0.38, green: 0.42, blue: 1.0) // #616BFF
    static let accentDim = Color(red: 0.38, green: 0.42, blue: 1.0).opacity(0.15)

    // Semantic
    static let success = Color.green.opacity(0.85)
    static let warning = Color.orange.opacity(0.85)
    static let error   = Color.red.opacity(0.85)
    static let neutral = Color.gray.opacity(0.6)

    // Rank badges
    static func rank(_ position: Int) -> Color {
        switch position {
        case 1:  return accent
        case 2:  return Color(red: 0.45, green: 0.50, blue: 0.90)
        case 3:  return Color(red: 0.55, green: 0.58, blue: 0.78)
        default: return neutral
        }
    }

    // Confidence → color
    static func confidence(_ value: Double) -> Color {
        switch value {
        case 0.7...: return success
        case 0.4...: return warning
        default:     return neutral
        }
    }
}

// MARK: - Color helpers

extension Color {
    /// Adaptive color for light/dark mode.
    init(light: Color, dark: Color) {
        #if os(iOS)
        self.init(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark
                ? UIColor(dark) : UIColor(light)
        })
        #elseif os(macOS)
        self.init(nsColor: NSColor(name: nil) { appearance in
            appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
                ? NSColor(dark) : NSColor(light)
        })
        #endif
    }
}

// MARK: - Typography

enum CortexFont {
    // Hierarchy
    static let largeTitle   = Font.system(.largeTitle, design: .default, weight: .bold)
    static let title        = Font.system(.title2, design: .default, weight: .semibold)
    static let headline     = Font.system(.headline, design: .default, weight: .semibold)
    static let bodyMedium   = Font.system(.body, design: .default, weight: .medium)
    static let body         = Font.system(.body, design: .default)
    static let caption      = Font.system(.caption, design: .default)
    static let captionMedium = Font.system(.caption, design: .default, weight: .medium)
    static let mono         = Font.system(.caption2, design: .monospaced)
}

// MARK: - Spacing (4-point grid)

enum CortexSpacing {
    static let xxs: CGFloat = 2
    static let xs:  CGFloat = 4
    static let sm:  CGFloat = 8
    static let md:  CGFloat = 12
    static let lg:  CGFloat = 16
    static let xl:  CGFloat = 24
    static let xxl: CGFloat = 32
}

// MARK: - Radius

enum CortexRadius {
    static let small: CGFloat = 6
    static let card:  CGFloat = 10
    static let large: CGFloat = 16
}

// MARK: - Shadow modifier

struct CortexShadowModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .shadow(color: .black.opacity(0.06), radius: 4, x: 0, y: 2)
    }
}

extension View {
    func cortexShadow() -> some View {
        modifier(CortexShadowModifier())
    }
}
