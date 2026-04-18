"""Notion to CortexOS context mapping."""

from __future__ import annotations

from cortex_core.integrations.schemas import CortexContextItem, RawNotionItem, fingerprint_from_parts


def map_notion_to_context(item: RawNotionItem) -> CortexContextItem:
    return CortexContextItem(
        id=fingerprint_from_parts("notion", item.fingerprint()),
        source="notion",
        title=item.title,
        content=item.summary or "Imported from Notion.",
        url=item.url,
        tags=["notion", "context", item.source_id],
        updated_at=item.last_edited_time or "",
    )

