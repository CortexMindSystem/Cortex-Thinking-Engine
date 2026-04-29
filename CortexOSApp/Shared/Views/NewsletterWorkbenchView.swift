import SwiftUI

struct NewsletterWorkbenchView: View {
    @EnvironmentObject private var engine: CortexEngine

    @State private var selectedSource: SourcePreset = .thisWeek
    @State private var selectedMode: DraftMode = .weeklyLessons

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: CortexSpacing.lg) {
                header
                sourceControls
                safetyCard
                previewCard
                actions
            }
            .padding(CortexSpacing.xl)
            .frame(maxWidth: 900, alignment: .leading)
        }
        .background(CortexColor.bgPrimary)
        .navigationTitle("Newsletter")
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.xs) {
            Text("Newsletter")
                .font(CortexFont.title)
                .foregroundStyle(CortexColor.textPrimary)

            Text("Turn selected thoughts and decisions into a public-safe draft.")
                .font(CortexFont.body)
                .foregroundStyle(CortexColor.textSecondary)
        }
    }

    private var sourceControls: some View {
        VStack(alignment: .leading, spacing: CortexSpacing.md) {
            VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                Text("Source")
                    .cortexFieldLabel()
                Picker("Source", selection: $selectedSource) {
                    ForEach(SourcePreset.allCases) { source in
                        Text(source.label).tag(source)
                    }
                }
                .pickerStyle(.segmented)
            }

            VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                Text("Mode")
                    .cortexFieldLabel()
                Picker("Mode", selection: $selectedMode) {
                    ForEach(DraftMode.allCases) { mode in
                        Text(mode.label).tag(mode)
                    }
                }
                .pickerStyle(.menu)
            }

            Label("Strict safety enabled", systemImage: "checkmark.shield")
                .font(CortexFont.caption)
                .foregroundStyle(CortexColor.textSecondary)
        }
        .padding(CortexSpacing.lg)
        .background(CortexColor.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
    }

    @ViewBuilder
    private var previewCard: some View {
        if let newsletter = engine.snapshot?.newsletter {
            VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                Text(newsletter.title.isEmpty ? "Latest draft" : newsletter.title)
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)

                if !newsletter.subtitle.isEmpty {
                    Text(newsletter.subtitle)
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textSecondary)
                }

                if !newsletter.preview.isEmpty {
                    Text(newsletter.preview)
                        .font(CortexFont.body)
                        .foregroundStyle(CortexColor.textSecondary)
                        .lineLimit(5)
                }

                Text("Status: \(newsletter.status)")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)
            }
            .padding(CortexSpacing.lg)
            .background(CortexColor.bgSurface)
            .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        } else {
            VStack(alignment: .leading, spacing: CortexSpacing.sm) {
                Text("Not enough public-safe material yet")
                    .font(CortexFont.bodyMedium)
                    .foregroundStyle(CortexColor.textPrimary)
                Text("Capture a thought, add a decision, then run Weekly Review.")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textSecondary)
            }
            .padding(CortexSpacing.lg)
            .background(CortexColor.bgSurface)
            .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        }
    }

    @ViewBuilder
    private var safetyCard: some View {
        if let newsletter = engine.snapshot?.newsletter {
            VStack(alignment: .leading, spacing: CortexSpacing.xs) {
                Text("Safety")
                    .font(CortexFont.captionMedium)
                    .foregroundStyle(CortexColor.textTertiary)
                Text(newsletter.safeToPublish ? "Safe to publish: yes" : "Safe to publish: no")
                    .font(CortexFont.caption)
                    .foregroundStyle(newsletter.safeToPublish ? CortexColor.success : CortexColor.warning)

                if let reasons = newsletter.tasteGate?.reasons, !reasons.isEmpty {
                    Text("Taste gate: \(reasons.joined(separator: ", "))")
                        .font(CortexFont.caption)
                        .foregroundStyle(CortexColor.textSecondary)
                }
            }
            .padding(CortexSpacing.lg)
            .background(CortexColor.bgSurface)
            .clipShape(RoundedRectangle(cornerRadius: CortexRadius.card, style: .continuous))
        }
    }

    private var actions: some View {
        HStack(spacing: CortexSpacing.sm) {
            Button {
                Task {
                    _ = await engine.generateNewsletterDraft(
                        period: selectedSource.periodValue,
                        mode: selectedMode.modeValue
                    )
                }
            } label: {
                Label("Generate Draft", systemImage: "wand.and.stars")
            }
            .buttonStyle(CortexPrimaryButtonStyle())
            .disabled(!canGenerate)

            if let newsletter = engine.snapshot?.newsletter,
               !newsletter.markdownPath.isEmpty {
                let url = URL(fileURLWithPath: newsletter.markdownPath)
                ShareLink(item: url) {
                    Label("Share", systemImage: "square.and.arrow.up")
                }
                .buttonStyle(CortexSecondaryButtonStyle())
            }

            if let status = engine.newsletterStatus, !status.isEmpty {
                Text("Status: \(status)")
                    .font(CortexFont.caption)
                    .foregroundStyle(CortexColor.textTertiary)
            }
        }
    }

    private var canGenerate: Bool {
        if engine.isSyncing {
            return false
        }
        if let count = engine.snapshot?.newsletter?.sourceCountTotal {
            return count > 0
        }
        return true
    }
}

private extension NewsletterWorkbenchView {
    enum SourcePreset: String, CaseIterable, Identifiable {
        case thisWeek
        case lastWeek
        case thisMonth

        var id: String { rawValue }

        var label: String {
            switch self {
            case .thisWeek: "This Week"
            case .lastWeek: "Last Week"
            case .thisMonth: "This Month"
            }
        }

        var periodValue: String {
            switch self {
            case .thisWeek: "weekly"
            case .lastWeek: "weekly"
            case .thisMonth: "monthly"
            }
        }
    }

    enum DraftMode: String, CaseIterable, Identifiable {
        case personalReflection
        case productBuilderNotes
        case weeklyLessons
        case technicalEssay

        var id: String { rawValue }

        var label: String {
            switch self {
            case .personalReflection: "Personal Reflection"
            case .productBuilderNotes: "Product Builder Notes"
            case .weeklyLessons: "Weekly Lessons"
            case .technicalEssay: "Technical Essay"
            }
        }

        var modeValue: String {
            switch self {
            case .personalReflection: "personal-reflection"
            case .productBuilderNotes: "product-builder-notes"
            case .weeklyLessons: "weekly-lessons"
            case .technicalEssay: "technical-essay"
            }
        }
    }
}
