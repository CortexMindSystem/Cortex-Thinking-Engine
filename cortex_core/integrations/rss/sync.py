"""RSS sync orchestration."""

from __future__ import annotations

from cortex_core.integrations.repositories import IntegrationRepository
from cortex_core.integrations.rss.client import RSSClient
from cortex_core.integrations.rss.mapper import map_rss_to_signal
from cortex_core.integrations.schemas import fingerprint_from_parts


class RSSSync:
    def __init__(self, repository: IntegrationRepository, client: RSSClient | None = None):
        self.repository = repository
        self.client = client or RSSClient()

    def run(self, *, feeds: list[str], max_items: int, active_projects: list[str]) -> dict:
        raw_items = self.client.fetch(feeds, max_items=max_items)

        mapped_signals: list[dict] = []
        duplicates = 0
        for item in raw_items:
            dedupe_keys = [
                fingerprint_from_parts("rss", "guid", item.guid),
                fingerprint_from_parts("rss", "url", item.url),
                fingerprint_from_parts("rss", "title", item.title),
            ]
            dedupe_keys = [key for key in dedupe_keys if key]
            if any(self.repository.has_seen("rss", key) for key in dedupe_keys):
                duplicates += 1
                continue
            fingerprint = dedupe_keys[0] if dedupe_keys else item.fingerprint()
            self.repository.append_raw(
                source="rss",
                kind="feed_item",
                external_id=item.guid or item.url,
                fingerprint=fingerprint,
                payload=item.to_dict(),
            )
            for key in dedupe_keys[1:]:
                self.repository.mark_seen("rss", key)
            mapped_signals.append(map_rss_to_signal(item, active_projects).to_dict())

        self.repository.mark_synced("rss")
        return {
            "source": "rss",
            "fetched": len(raw_items),
            "raw_saved": len(raw_items) - duplicates,
            "duplicates": duplicates,
            "signals": mapped_signals,
            "context_items": [],
        }
