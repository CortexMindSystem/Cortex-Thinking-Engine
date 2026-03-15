//
//  ProfileView.swift
//  CortexOS
//
//  Manage the user profile that drives CortexOS focus recommendations.
//  Goals, interests, projects, and constraints shape what matters.
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var editingProfile: EditableProfile = .init()
    @State private var isSaving = false
    @State private var hasChanges = false

    var body: some View {
        Form {
            Section("Identity") {
                TextField("Name", text: $editingProfile.name)
                    .onChange(of: editingProfile.name) { hasChanges = true }
            }

            editableListSection(
                title: "Goals",
                hint: "What are you trying to achieve?",
                items: $editingProfile.goals
            )

            editableListSection(
                title: "Interests",
                hint: "Topics you follow",
                items: $editingProfile.interests
            )

            editableListSection(
                title: "Current Projects",
                hint: "What you're building right now",
                items: $editingProfile.projects
            )

            editableListSection(
                title: "Constraints",
                hint: "Time, energy, or scope limits",
                items: $editingProfile.constraints
            )

            editableListSection(
                title: "Ignored Topics",
                hint: "Topics to filter out",
                items: $editingProfile.ignoredTopics
            )
        }
        .formStyle(.grouped)
        .navigationTitle("Profile")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    Task { await save() }
                } label: {
                    if isSaving {
                        ProgressView().controlSize(.small)
                    } else {
                        Text("Save")
                    }
                }
                .disabled(!hasChanges || isSaving)
            }
        }
        .task {
            await engine.fetchProfile()
            loadFromEngine()
        }
    }

    // MARK: - Editable list section

    @ViewBuilder
    private func editableListSection(
        title: String,
        hint: String,
        items: Binding<[String]>
    ) -> some View {
        Section {
            ForEach(items.wrappedValue.indices, id: \.self) { idx in
                TextField(hint, text: Binding(
                    get: { items.wrappedValue[idx] },
                    set: { newVal in
                        items.wrappedValue[idx] = newVal
                        hasChanges = true
                    }
                ))
            }
            .onDelete { offsets in
                items.wrappedValue.remove(atOffsets: offsets)
                hasChanges = true
            }

            Button {
                items.wrappedValue.append("")
                hasChanges = true
            } label: {
                Label("Add", systemImage: "plus.circle")
                    .font(.subheadline)
            }
        } header: {
            Text(title)
        }
    }

    // MARK: - Helpers

    private func loadFromEngine() {
        let p = engine.profile
        editingProfile = EditableProfile(
            name: p.name,
            goals: p.goals.isEmpty ? [""] : p.goals,
            interests: p.interests.isEmpty ? [""] : p.interests,
            projects: p.currentProjects.isEmpty ? [""] : p.currentProjects,
            constraints: p.constraints.isEmpty ? [""] : p.constraints,
            ignoredTopics: p.ignoredTopics.isEmpty ? [""] : p.ignoredTopics
        )
        hasChanges = false
    }

    private func save() async {
        isSaving = true
        defer { isSaving = false }

        let update = ProfileUpdate(
            name: editingProfile.name,
            goals: editingProfile.goals.filter { !$0.isEmpty },
            interests: editingProfile.interests.filter { !$0.isEmpty },
            currentProjects: editingProfile.projects.filter { !$0.isEmpty },
            constraints: editingProfile.constraints.filter { !$0.isEmpty },
            ignoredTopics: editingProfile.ignoredTopics.filter { !$0.isEmpty }
        )

        if await engine.saveProfile(update) {
            hasChanges = false
        }
    }
}

// MARK: - Local edit state

private struct EditableProfile {
    var name: String = ""
    var goals: [String] = [""]
    var interests: [String] = [""]
    var projects: [String] = [""]
    var constraints: [String] = [""]
    var ignoredTopics: [String] = [""]
}

#Preview {
    NavigationStack {
        ProfileView()
    }
    .environmentObject(CortexEngine())
}
