//
//  KnowledgeListView.swift
//  CortexOS
//
//  Browse, search, and manage knowledge notes.
//

import SwiftUI

struct KnowledgeListView: View {
    @EnvironmentObject private var engine: CortexEngine
    @State private var searchText = ""
    @State private var showingCreateSheet = false
    @State private var selectedNote: KnowledgeNote?

    var body: some View {
        List {
            if engine.isLoading {
                HStack {
                    Spacer()
                    ProgressView("Loading notes…")
                    Spacer()
                }
            } else if engine.notes.isEmpty {
                ContentUnavailableView(
                    "No Notes",
                    systemImage: "doc.text",
                    description: Text("Add a note or run the pipeline to populate your knowledge base.")
                )
            } else {
                ForEach(engine.notes) { note in
                    NavigationLink(value: note) {
                        NoteRowView(note: note)
                    }
                }
                .onDelete(perform: deleteNotes)
            }
        }
        .navigationTitle("Knowledge Notes")
        .navigationDestination(for: KnowledgeNote.self) { note in
            NoteDetailView(note: note)
        }
        .searchable(text: $searchText, prompt: "Search notes…")
        .onChange(of: searchText) { _, newValue in
            Task { await engine.searchNotes(query: newValue) }
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showingCreateSheet = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showingCreateSheet) {
            CreateNoteView()
        }
        .task {
            if engine.notes.isEmpty {
                await engine.fetchNotes()
            }
        }
        .refreshable {
            await engine.fetchNotes()
        }
    }

    private func deleteNotes(at offsets: IndexSet) {
        for index in offsets {
            let note = engine.notes[index]
            Task { await engine.deleteNote(note.id) }
        }
    }
}

// MARK: - Note Detail

struct NoteDetailView: View {
    let note: KnowledgeNote

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Title
                Text(note.title)
                    .font(.title2.bold())

                // Tags
                if !note.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(note.tags, id: \.self) { tag in
                                Text("#\(tag)")
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(.blue.opacity(0.1), in: Capsule())
                                    .foregroundStyle(.blue)
                            }
                        }
                    }
                }

                Divider()

                // Sections
                DetailSection(title: "Insight", icon: "lightbulb.fill", text: note.insight)
                DetailSection(title: "Implication", icon: "arrow.right.circle.fill", text: note.implication)
                DetailSection(title: "Action", icon: "checkmark.circle.fill", text: note.action)

                if !note.sourceURL.isEmpty {
                    DetailSection(title: "Source", icon: "link", text: note.sourceURL)
                }

                // Metadata
                Divider()
                HStack {
                    Label(note.createdAt.prefix(10).description, systemImage: "calendar")
                    Spacer()
                    Text("ID: \(note.id)")
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
            .padding()
        }
        .navigationTitle("Note")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}

struct DetailSection: View {
    let title: String
    let icon: String
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label(title, systemImage: icon)
                .font(.headline)
            Text(text)
                .font(.body)
                .foregroundStyle(.secondary)
        }
    }
}

// MARK: - Create Note

struct CreateNoteView: View {
    @EnvironmentObject private var engine: CortexEngine
    @Environment(\.dismiss) private var dismiss

    @State private var title = ""
    @State private var insight = ""
    @State private var implication = ""
    @State private var action = ""
    @State private var sourceURL = ""
    @State private var tagsText = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Title") {
                    TextField("Note title", text: $title)
                }
                Section("Insight") {
                    TextEditor(text: $insight)
                        .frame(minHeight: 60)
                }
                Section("Implication") {
                    TextEditor(text: $implication)
                        .frame(minHeight: 60)
                }
                Section("Action") {
                    TextField("Next action", text: $action)
                }
                Section("Source URL") {
                    TextField("https://…", text: $sourceURL)
                        #if os(iOS)
                        .keyboardType(.URL)
                        .textInputAutocapitalization(.never)
                        #endif
                }
                Section("Tags (comma-separated)") {
                    TextField("AI, retrieval, context", text: $tagsText)
                }
            }
            .navigationTitle("New Note")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task { await save() }
                    }
                    .disabled(title.isEmpty)
                }
            }
        }
    }

    private func save() async {
        let tags = tagsText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
        let request = NoteCreateRequest(
            title: title,
            insight: insight,
            implication: implication,
            action: action,
            sourceURL: sourceURL,
            tags: tags
        )
        if await engine.createNote(request) {
            dismiss()
        }
    }
}

#Preview {
    NavigationStack {
        KnowledgeListView()
            .environmentObject(CortexEngine())
    }
}
