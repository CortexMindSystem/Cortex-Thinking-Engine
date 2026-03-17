"""Tests for structured Item extraction and ItemStore."""

import pytest

from cortex_core.items import (
    Item,
    ItemStore,
    extract_items_from_digest,
    extract_items_from_notes,
)

SAMPLE_DIGEST = """# AI News

- [GPT-5 Released By OpenAI](https://example.com/gpt5)
- [New Robotics Framework Launched](https://example.com/robotics)

## Developer Tools

- [GitHub Copilot Agent Mode](https://example.com/copilot)
- [Docker Desktop AI Integration](https://example.com/docker)
"""


class TestItemExtraction:
    def test_extract_items_from_digest(self):
        items = extract_items_from_digest(SAMPLE_DIGEST)
        assert len(items) == 4
        assert items[0].title == "GPT-5 Released By OpenAI"
        assert items[0].url == "https://example.com/gpt5"
        assert items[0].source_type == "digest"
        assert items[0].section == "AI News"

    def test_section_tracking(self):
        items = extract_items_from_digest(SAMPLE_DIGEST)
        assert items[2].section == "Developer Tools"
        assert items[3].section == "Developer Tools"

    def test_content_hash_dedup(self):
        items = extract_items_from_digest(SAMPLE_DIGEST)
        a = items[0]
        b = Item(title=a.title, url=a.url, source_type="digest")
        assert a.content_hash == b.content_hash

    def test_different_items_different_hash(self):
        items = extract_items_from_digest(SAMPLE_DIGEST)
        assert items[0].content_hash != items[1].content_hash

    def test_extract_from_notes(self):
        notes = [
            {"title": "Test Note", "source_url": "https://x.com", "insight": "Key point", "tags": ["ai"]},
        ]
        items = extract_items_from_notes(notes)
        assert len(items) == 1
        assert items[0].source_type == "note"
        assert items[0].content == "Key point"

    def test_item_to_dict_roundtrip(self):
        item = Item(title="Test", url="https://x.com", source_type="manual", tags=["ai"])
        d = item.to_dict()
        restored = Item.from_dict(d)
        assert restored.title == item.title
        assert restored.tags == item.tags


class TestItemStore:
    @pytest.fixture()
    def store_path(self, tmp_path):
        return tmp_path / "items.json"

    def test_add_and_get(self, store_path):
        store = ItemStore(store_path)
        item = Item(title="Test Item", url="https://x.com")
        added = store.add(item)
        assert added.id == item.id
        assert store.count == 1
        assert store.get(item.id) is not None

    def test_deduplication(self, store_path):
        store = ItemStore(store_path)
        item1 = Item(title="Test Item", url="https://x.com")
        item2 = Item(title="Test Item", url="https://x.com")
        store.add(item1)
        store.add(item2)
        assert store.count == 1

    def test_batch_add(self, store_path):
        store = ItemStore(store_path)
        items = extract_items_from_digest(SAMPLE_DIGEST)
        store.add_batch(items)
        assert store.count == 4

    def test_batch_dedup(self, store_path):
        store = ItemStore(store_path)
        items = extract_items_from_digest(SAMPLE_DIGEST)
        store.add_batch(items)
        store.add_batch(items)  # same items again
        assert store.count == 4

    def test_search(self, store_path):
        store = ItemStore(store_path)
        store.add(Item(title="AI Agent Framework", tags=["ai"]))
        store.add(Item(title="Cooking Recipe"))
        results = store.search("agent")
        assert len(results) == 1
        assert results[0].title == "AI Agent Framework"

    def test_by_source_type(self, store_path):
        store = ItemStore(store_path)
        store.add(Item(title="Digest Item", source_type="digest"))
        store.add(Item(title="Manual Item", source_type="manual"))
        assert len(store.by_source_type("digest")) == 1

    def test_by_tag(self, store_path):
        store = ItemStore(store_path)
        store.add(Item(title="Tagged", tags=["ai", "agents"]))
        store.add(Item(title="Untagged"))
        assert len(store.by_tag("ai")) == 1

    def test_persistence(self, store_path):
        store = ItemStore(store_path)
        store.add(Item(title="Persisted", url="https://x.com"))
        store2 = ItemStore(store_path)
        assert store2.count == 1
        assert store2.items[0].title == "Persisted"

    def test_recent(self, store_path):
        store = ItemStore(store_path)
        for i in range(10):
            store.add(Item(title=f"Item {i}", url=f"https://x.com/{i}"))
        recent = store.recent(5)
        assert len(recent) == 5
