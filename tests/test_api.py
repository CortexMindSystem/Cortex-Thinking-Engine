"""Unit tests for the FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

import cortex_core.api.server as server_module
from cortex_core.api.server import create_app
from cortex_core.config import CortexConfig
from cortex_core.engine import CortexEngine


@pytest.fixture
def client(tmp_data_dir):
    """Create a test client with an isolated data directory."""
    config = CortexConfig(data_dir=tmp_data_dir)
    engine = CortexEngine(config)
    # Override the global engine singleton
    server_module._engine = engine
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset the global engine after each test."""
    yield
    server_module._engine = None


# ── Health ──────────────────────────────────────────────────────


class TestHealthEndpoints:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_status(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data


# ── Knowledge Notes ─────────────────────────────────────────────


class TestKnowledgeEndpoints:
    def test_list_notes_empty(self, client):
        resp = client.get("/notes/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_note(self, client):
        resp = client.post("/notes/", json={"title": "Test", "insight": "Key"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test"
        assert data["id"]

    def test_get_note(self, client):
        create_resp = client.post("/notes/", json={"title": "Find Me"})
        note_id = create_resp.json()["id"]
        resp = client.get(f"/notes/{note_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Find Me"

    def test_get_note_not_found(self, client):
        resp = client.get("/notes/nonexistent")
        assert resp.status_code == 404

    def test_update_note(self, client):
        create_resp = client.post("/notes/", json={"title": "Before"})
        note_id = create_resp.json()["id"]
        resp = client.patch(f"/notes/{note_id}", json={"title": "After"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "After"

    def test_delete_note(self, client):
        create_resp = client.post("/notes/", json={"title": "Delete"})
        note_id = create_resp.json()["id"]
        resp = client.delete(f"/notes/{note_id}")
        assert resp.status_code == 204
        # Verify gone
        assert client.get(f"/notes/{note_id}").status_code == 404

    def test_search_notes(self, client):
        client.post("/notes/", json={"title": "AI Agents"})
        client.post("/notes/", json={"title": "Cooking"})
        resp = client.get("/notes/search?q=agents")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ── Focus ───────────────────────────────────────────────────────


class TestFocusEndpoints:
    def test_today_brief_not_found(self, client):
        resp = client.get("/focus/today")
        assert resp.status_code == 404

    def test_generate_brief(self, client, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        resp = client.post("/focus/generate", json={"digest_path": str(digest_path)})
        assert resp.status_code == 200
        data = resp.json()
        assert "focus_items" in data
        assert "date" in data


# ── Profile ─────────────────────────────────────────────────────


class TestProfileEndpoints:
    def test_get_profile(self, client):
        resp = client.get("/profile/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "goals" in data

    def test_update_profile(self, client):
        resp = client.patch("/profile/", json={"name": "Pierre"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Pierre"


# ── Digest ──────────────────────────────────────────────────────


class TestDigestEndpoints:
    def test_evaluate_digest(self, client, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        resp = client.post("/digest/evaluate", json={"path": str(digest_path)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_articles"] > 0
        assert "ai_article_ratio" in data


# ── Pipeline ────────────────────────────────────────────────────


class TestPipelineEndpoints:
    def test_run_pipeline(self, client, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        resp = client.post("/pipeline/run", json={"use_llm": False})
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data
