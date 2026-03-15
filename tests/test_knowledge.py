"""Unit tests for the knowledge store."""

from cortex_core.knowledge import KnowledgeNote, KnowledgeStore


class TestKnowledgeNote:
    def test_auto_generated_id(self):
        n = KnowledgeNote(title="Test")
        assert len(n.id) == 12

    def test_to_dict(self):
        n = KnowledgeNote(title="T", insight="I", tags=["ai"])
        d = n.to_dict()
        assert d["title"] == "T"
        assert d["insight"] == "I"
        assert d["tags"] == ["ai"]

    def test_from_dict(self):
        data = {"id": "abc123", "title": "T", "insight": "I", "tags": []}
        n = KnowledgeNote.from_dict(data)
        assert n.id == "abc123"
        assert n.title == "T"


class TestKnowledgeStore:
    def test_add_and_get(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        note = KnowledgeNote(title="AI Agents Overview", insight="Agents need memory")
        added = store.add(note)
        assert added.title == "AI Agents Overview"
        assert store.count == 1
        fetched = store.get(note.id)
        assert fetched is not None
        assert fetched.title == "AI Agents Overview"

    def test_list_notes_excludes_archived(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        store.add(KnowledgeNote(title="Active"))
        n2 = KnowledgeNote(title="Old", archived=True)
        store.add(n2)
        assert store.count == 1  # only non-archived
        assert len(store.all_notes) == 2

    def test_update(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        note = store.add(KnowledgeNote(title="Before"))
        updated = store.update(note.id, title="After")
        assert updated is not None
        assert updated.title == "After"
        assert updated.updated_at != ""

    def test_update_nonexistent(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        assert store.update("nonexistent", title="X") is None

    def test_delete(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        note = store.add(KnowledgeNote(title="ToDelete"))
        assert store.delete(note.id) is True
        assert store.count == 0
        assert store.get(note.id) is None

    def test_delete_nonexistent(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        assert store.delete("nope") is False

    def test_archive(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        note = store.add(KnowledgeNote(title="ArchiveMe"))
        assert store.archive(note.id) is True
        assert store.count == 0  # archived excludes
        assert len(store.all_notes) == 1

    def test_search(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        store.add(KnowledgeNote(title="AI Agents", insight="Agents need context"))
        store.add(KnowledgeNote(title="Cooking Recipe", insight="Pasta is easy"))
        results = store.search("agents")
        assert len(results) == 1
        assert results[0].title == "AI Agents"

    def test_search_by_tag(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        store.add(KnowledgeNote(title="N1", tags=["ai"]))
        store.add(KnowledgeNote(title="N2", tags=["cooking"]))
        assert len(store.by_tag("ai")) == 1

    def test_persistence(self, tmp_data_dir):
        path = tmp_data_dir / "notes.json"
        store = KnowledgeStore(path)
        store.add(KnowledgeNote(title="Persisted"))

        # Reload from disk
        store2 = KnowledgeStore(path)
        assert store2.count == 1
        assert store2.notes[0].title == "Persisted"

    def test_summary(self, tmp_data_dir):
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        store.add(KnowledgeNote(title="N1", tags=["ai"]))
        store.add(KnowledgeNote(title="N2", tags=["ai", "retrieval"]))
        s = store.summary()
        assert s["total"] == 2
        assert s["tags"]["ai"] == 2
        assert s["tags"]["retrieval"] == 1
