"""Unit tests for the context memory system."""

import json

from cortex_core.memory import ContextMemory, ReadingEntry, UserProfile


class TestUserProfile:
    def test_default_values(self):
        p = UserProfile()
        assert p.name == "Builder"
        assert len(p.goals) > 0
        assert len(p.interests) > 0

    def test_context_tokens(self):
        p = UserProfile(goals=["Build AI"], interests=["agents"])
        tokens = p.context_tokens()
        assert "ai" in tokens
        assert "agents" in tokens
        assert "build" in tokens

    def test_context_snippets(self):
        p = UserProfile(
            goals=["Build AI"],
            interests=["retrieval"],
            current_projects=["CortexOS"],
        )
        snippets = p.context_snippets()
        assert "Build AI" in snippets
        assert "retrieval" in snippets
        assert "CortexOS" in snippets

    def test_to_dict_roundtrip(self):
        p = UserProfile(name="Test", goals=["G1"], interests=["I1"])
        d = p.to_dict()
        p2 = UserProfile.from_dict(d)
        assert p2.name == "Test"
        assert p2.goals == ["G1"]

    def test_from_dict_ignores_extra_keys(self):
        data = {"name": "X", "goals": [], "extra_field": True}
        p = UserProfile.from_dict(data)
        assert p.name == "X"


class TestReadingEntry:
    def test_creation(self):
        entry = ReadingEntry(title="AI Agents 101", url="https://example.com")
        assert entry.title == "AI Agents 101"
        assert entry.read_at  # auto-filled

    def test_to_dict_roundtrip(self):
        entry = ReadingEntry(title="T", url="u", score=0.5, tags=["ai"], insight="key")
        d = entry.to_dict()
        e2 = ReadingEntry.from_dict(d)
        assert e2.title == "T"
        assert e2.score == 0.5


class TestContextMemory:
    def test_init_creates_default_profile(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        assert mem.profile.name == "Builder"
        assert mem.history == []

    def test_save_and_reload(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.profile.name = "Pierre"
        mem.save()

        mem2 = ContextMemory(tmp_data_dir)
        assert mem2.profile.name == "Pierre"

    def test_update_profile(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.update_profile(name="Updated", goals=["Goal1"])
        assert mem.profile.name == "Updated"
        assert mem.profile.goals == ["Goal1"]

        # Verify persisted
        mem2 = ContextMemory(tmp_data_dir)
        assert mem2.profile.name == "Updated"

    def test_add_goal(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        original_count = len(mem.profile.goals)
        mem.add_goal("New goal")
        assert "New goal" in mem.profile.goals
        assert len(mem.profile.goals) == original_count + 1

    def test_add_goal_no_duplicates(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.add_goal("Unique goal")
        count = len(mem.profile.goals)
        mem.add_goal("Unique goal")
        assert len(mem.profile.goals) == count

    def test_add_interest(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.add_interest("quantum computing")
        assert "quantum computing" in mem.profile.interests

    def test_add_project(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.add_project("SideProject")
        assert "SideProject" in mem.profile.current_projects

    def test_record_read(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        entry = mem.record_read("Article Title", url="https://example.com", score=0.8)
        assert entry.title == "Article Title"
        assert len(mem.history) == 1

    def test_already_read(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.record_read("Title A")
        assert mem.already_read("Title A")
        assert mem.already_read("title a")  # case insensitive
        assert not mem.already_read("Title B")

    def test_recent_reads(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        for i in range(25):
            mem.record_read(f"Article {i}")
        recent = mem.recent_reads(10)
        assert len(recent) == 10
        assert recent[-1].title == "Article 24"

    def test_get_context_snippets_includes_insights(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.record_read("AI Agents paper", insight="Agents need memory")
        snippets = mem.get_context_snippets()
        assert "Agents need memory" in snippets

    def test_get_context_tokens(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        tokens = mem.get_context_tokens()
        # Should include default profile tokens
        assert "ai" in tokens

    def test_summary(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        mem.record_read("X")
        s = mem.summary()
        assert s["total_reads"] == 1
        assert s["name"] == "Builder"

    def test_loads_existing_profile(self, tmp_data_dir, sample_profile_dict):
        # Pre-seed profile file
        with open(tmp_data_dir / "profile.json", "w") as f:
            json.dump(sample_profile_dict, f)
        mem = ContextMemory(tmp_data_dir)
        assert mem.profile.name == "TestBuilder"

    def test_loads_existing_history(self, tmp_data_dir):
        history = [
            {
                "title": "Saved Article",
                "url": "https://example.com",
                "read_at": "2026-01-01",
                "score": 0.5,
                "tags": [],
                "insight": "",
            }
        ]
        with open(tmp_data_dir / "reading_history.json", "w") as f:
            json.dump(history, f)
        mem = ContextMemory(tmp_data_dir)
        assert len(mem.history) == 1
        assert mem.history[0].title == "Saved Article"
