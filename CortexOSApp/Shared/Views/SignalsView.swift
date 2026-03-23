//
//  SignalsView.swift
//  CortexOS
//
//  Emerging topics appearing across multiple sources.
//  Filter by status, see strength and frequency.
//

import SwiftUI

struct SignalsView: View {
    @EnvironmentObject private var engine: CortexEngine

    var body: some View {
        Group {
            if let signals = engine.snapshot?.signals, !signals.isEmpty {
                List {
                    ForEach(signals) { signal in
                        SignalRow(signal: signal)
                    }
                }
                .listStyle(.plain)
            } else {
                EmptyStateView(
                    icon: "antenna.radiowaves.left.and.right",
                    title: "No signals detected",
                    message: "Signals emerge when topics appear across multiple sources.",
                    actionTitle: "Refresh",
                    action: { Task { await engine.sync() } }
                )
            }
        }
        .navigationTitle("Signals")
        .refreshable { await engine.sync() }
    }
}

// MARK: - Row

private struct SignalRow: View {
    let signal: SyncSignal

    var body: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.sm) {
            HStack {
                Text(signal.topic)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)

                Spacer()

                StatusBadge(status: signal.status)
            }

            HStack(spacing: CortexSpacing.lg) {
                Label("×\(signal.frequency)", systemImage: "number")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textSecondary)

                Label(String(format: "%.0f%%", signal.strength * 100), systemImage: "waveform")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.confidence(signal.strength))

                if !signal.firstSeen.isEmpty {
                    Label(signal.firstSeen.prefix(10).description, systemImage: "calendar")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                }
            }

            if !signal.sourceTitles.isEmpty {
                ForEach(signal.sourceTitles.prefix(3), id: \.self) { title in
                    Text("• \(title)")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textTertiary)
                        .lineLimit(1)
                }
            }
        }
        .padding(.vertical, CortexSpacing.xs)
    }
}

// MARK: - Status badge

private struct StatusBadge: View {
    let status: String

    private var color: Color {
        switch status {
        case "confirmed": CortexColor.success
        case "emerging":  CortexColor.accent
        case "fading":    CortexColor.warning
        default:          CortexColor.neutral
        }
    }

    var body: some View {
        Text(status)
            .font(CortexFont.mono)
            .foregroundStyle(color)
            .padding(.horizontal, CortexSpacing.sm)
            .padding(.vertical, CortexSpacing.xxs)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }
}
