"""
Social Post Generator
----------------------
Turns knowledge notes into platform-ready social media posts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cortex_core.knowledge import KnowledgeNote, KnowledgeStore
from cortex_core.llm import LLMProvider


@dataclass
class SocialPost:
    """A generated social media post."""

    text: str
    source_note_id: str = ""
    platform: str = "general"  # general | twitter | linkedin | bluesky
    hashtags: list[str] = field(default_factory=list)


class PostGenerator:
    """Generate social posts from knowledge notes."""

    TEMPLATE = (
        "Insight from my CortexOS research:\n\n"
        "{title}\n\n"
        "Key idea:\n{insight}\n\n"
        "Action:\n{action}\n\n"
        "Building an AI context engine for developers."
    )

    TWITTER_TEMPLATE = "💡 {title}\n\n{insight}\n\n→ {action}\n\n#CortexOS #AI #BuildInPublic"

    LINKEDIN_TEMPLATE = (
        "🔬 Research insight from CortexOS:\n\n"
        "**{title}**\n\n"
        "{insight}\n\n"
        "Implication: {implication}\n\n"
        "Next step: {action}\n\n"
        "Building an AI context engine for developers and knowledge workers.\n\n"
        "#AI #ProductDevelopment #KnowledgeManagement"
    )

    def __init__(
        self,
        store: KnowledgeStore,
        llm: LLMProvider | None = None,
    ):
        self.store = store
        self.llm = llm

    # ------------------------------------------------------------- generate

    def generate(
        self,
        *,
        limit: int = 3,
        platform: str = "general",
        use_llm: bool = False,
    ) -> list[SocialPost]:
        """Create posts from the latest knowledge notes."""
        notes = self.store.notes[:limit]
        posts: list[SocialPost] = []
        for note in notes:
            post = self._llm_post(note, platform) if use_llm and self.llm else self._template_post(note, platform)
            posts.append(post)
        return posts

    def generate_from_note(
        self, note_id: str, *, platform: str = "general", use_llm: bool = False
    ) -> SocialPost | None:
        """Generate a post for a specific note."""
        note = self.store.get(note_id)
        if not note:
            return None
        if use_llm and self.llm:
            return self._llm_post(note, platform)
        return self._template_post(note, platform)

    # ------------------------------------------------------------ strategies

    def _template_post(self, note: KnowledgeNote, platform: str) -> SocialPost:
        templates = {
            "twitter": self.TWITTER_TEMPLATE,
            "linkedin": self.LINKEDIN_TEMPLATE,
            "general": self.TEMPLATE,
        }
        tpl = templates.get(platform, self.TEMPLATE)
        text = tpl.format(
            title=note.title,
            insight=note.insight,
            implication=note.implication,
            action=note.action,
        )
        return SocialPost(
            text=text,
            source_note_id=note.id,
            platform=platform,
            hashtags=note.tags,
        )

    def _llm_post(self, note: KnowledgeNote, platform: str) -> SocialPost:
        prompt = (
            f"Write a {platform} social media post based on this research note.\n"
            f"Title: {note.title}\n"
            f"Insight: {note.insight}\n"
            f"Action: {note.action}\n\n"
            "Keep it concise, engaging, and professional."
        )
        resp = self.llm.generate(prompt)  # type: ignore[union-attr]
        return SocialPost(
            text=resp.text,
            source_note_id=note.id,
            platform=platform,
            hashtags=note.tags,
        )

    # ---------------------------------------------------------------- export

    @staticmethod
    def format_posts(posts: list[SocialPost], separator: str = "\n\n---\n\n") -> str:
        """Join posts into a single string for file export."""
        return separator.join(p.text for p in posts)

    def export(self, posts: list[SocialPost], path) -> None:
        """Write posts to a text file."""
        Path(path).write_text(self.format_posts(posts))
