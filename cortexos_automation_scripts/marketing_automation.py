#!/usr/bin/env python3
"""Generate SimpliXio marketing artifacts from real product outputs.

This script is generation-first (safe by default).
Publishing is handled by scripts/publish_outputs.py after quality checks pass.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field


AUTOMATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUTOMATION_ROOT.parent


class Priority(BaseModel):
    title: str
    why: str
    action: str
    ignored: bool = False


class CortexBrief(BaseModel):
    date: str
    priorities: list[Priority]
    ignored_signals_count: int = 0
    project: str = "SimpliXio"
    themes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TrendItem(BaseModel):
    source: str
    title: str
    url: str
    published: str | None = None
    topic: str | None = None


class WeeklyReview(BaseModel):
    week_start: str = ""
    week_end: str = ""
    days_covered: int = 0
    top_priorities: list[dict[str, Any]] = Field(default_factory=list)
    top_signals: list[dict[str, Any]] = Field(default_factory=list)
    total_ignored_signals: int = 0
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)


class DecisionReplay(BaseModel):
    date: str = ""
    signals_reviewed: int = 0
    signals_kept: int = 0
    signals_ignored: int = 0
    summary: str = ""
    final_priorities: list[dict[str, Any]] = Field(default_factory=list)


class ContentPlan(BaseModel):
    angle: str
    score: int
    reason: str
    title: str
    skip_generation: bool = False


class GeneratedPost(BaseModel):
    channel: str
    title: str
    body: str
    url: str | None = None
    tags: list[str] = Field(default_factory=list)


class Config(BaseModel):
    app_name: str = "SimpliXio"
    app_url: str = "https://github.com/SimplixioMindSystem/Thinking-Engine"
    author_name: str = "Pierre-Henry Soria"
    author_url: str = "https://pierrehenry.dev"
    rss_feeds: list[str] = Field(default_factory=list)
    github_token: str | None = None
    github_topics: list[str] = Field(default_factory=lambda: ["ai", "agents", "developer-tools"])
    cortex_outputs_dir: Path = AUTOMATION_ROOT / "output" / "cortex_today"
    output_dir: Path = AUTOMATION_ROOT / "output"
    publish_site: bool = True
    publish_json_log: bool = True


def _resolve_path(value: str, *, default: Path) -> Path:
    cleaned = value.strip()
    if not cleaned:
        return default
    path = Path(cleaned)
    if path.is_absolute():
        return path
    return (AUTOMATION_ROOT / path).resolve()


def load_config() -> Config:
    load_dotenv(AUTOMATION_ROOT / ".env")

    rss_feeds = [x.strip() for x in os.getenv("RSS_FEEDS", "").split(",") if x.strip()]
    github_topics = [x.strip() for x in os.getenv("GITHUB_TOPICS", "ai,agents,developer-tools").split(",") if x.strip()]

    raw_app_name = os.getenv("APP_NAME", "SimpliXio").strip()
    app_name = "SimpliXio" if raw_app_name.lower() in {"cortexos", "cortex os"} else raw_app_name

    raw_app_url = os.getenv(
        "APP_URL", "https://github.com/SimplixioMindSystem/Thinking-Engine"
    ).strip()
    app_url = raw_app_url

    return Config(
        app_name=app_name,
        app_url=app_url,
        author_name=os.getenv("AUTHOR_NAME", "Pierre-Henry Soria"),
        author_url=os.getenv("AUTHOR_URL", "https://pierrehenry.dev"),
        rss_feeds=rss_feeds,
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_topics=github_topics,
        cortex_outputs_dir=_resolve_path(os.getenv("CORTEX_OUTPUTS_DIR", ""), default=AUTOMATION_ROOT / "output" / "cortex_today"),
        output_dir=_resolve_path(os.getenv("OUTPUT_DIR", ""), default=AUTOMATION_ROOT / "output"),
        publish_site=os.getenv("PUBLISH_SITE", "true").lower() == "true",
        publish_json_log=os.getenv("PUBLISH_JSON_LOG", "true").lower() == "true",
    )


def ensure_dirs(cfg: Config) -> None:
    for sub in [
        cfg.output_dir,
        cfg.output_dir / "cards",
        cfg.output_dir / "drafts",
        cfg.output_dir / "logs",
        cfg.output_dir / "site",
        cfg.output_dir / "campaigns",
        cfg.output_dir / "publish",
        cfg.output_dir / "memory",
        cfg.output_dir / "summaries",
    ]:
        sub.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    value = re.sub(r"[\s_-]+", "-", value)
    return value[:80]


def app_slug(value: str) -> str:
    return slugify(value) or "app"


def file_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def read_latest_brief(cfg: Config) -> CortexBrief:
    files = sorted(cfg.cortex_outputs_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No SimpliXio outputs found in {cfg.cortex_outputs_dir}")
    return CortexBrief.model_validate(json.loads(files[-1].read_text(encoding="utf-8")))


def read_weekly_review(cfg: Config) -> WeeklyReview:
    path = cfg.output_dir / "weekly_review" / "latest.json"
    if not path.exists():
        return WeeklyReview()
    return WeeklyReview.model_validate(json.loads(path.read_text(encoding="utf-8")))


def read_decision_replay(cfg: Config) -> DecisionReplay:
    path = cfg.output_dir / "decision_replay" / "latest.json"
    if not path.exists():
        return DecisionReplay()
    return DecisionReplay.model_validate(json.loads(path.read_text(encoding="utf-8")))


def fetch_rss_items(cfg: Config, max_per_feed: int = 5) -> list[TrendItem]:
    items: list[TrendItem] = []
    for feed_url in cfg.rss_feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            # Network/transient feed errors should not fail the whole pipeline.
            continue
        for entry in parsed.entries[:max_per_feed]:
            items.append(
                TrendItem(
                    source=feed_url,
                    title=getattr(entry, "title", "Untitled"),
                    url=getattr(entry, "link", ""),
                    published=getattr(entry, "published", None),
                )
            )
    return items


def fetch_github_topic_repos(cfg: Config, per_topic: int = 4) -> list[TrendItem]:
    items: list[TrendItem] = []
    headers = {"Accept": "application/vnd.github+json"}
    if cfg.github_token:
        headers["Authorization"] = f"Bearer {cfg.github_token}"

    for topic in cfg.github_topics:
        params = {
            "q": f"topic:{topic} stars:>30",
            "sort": "updated",
            "order": "desc",
            "per_page": per_topic,
        }
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            continue

        for repo in payload.get("items", []):
            items.append(
                TrendItem(
                    source="github",
                    title=repo["full_name"],
                    url=repo["html_url"],
                    published=repo.get("updated_at"),
                    topic=topic,
                )
            )
    return items


def load_content_memory(cfg: Config) -> dict[str, Any]:
    path = cfg.output_dir / "memory" / "content_memory.json"
    if not path.exists():
        return {"angles": [], "hashes": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"angles": [], "hashes": []}


def choose_content_plan(
    brief: CortexBrief, weekly: WeeklyReview, replay: DecisionReplay, memory: dict[str, Any]
) -> ContentPlan:
    recent_angles = [str(item.get("angle", "")) for item in memory.get("angles", [])][-6:]
    candidates: list[ContentPlan] = []

    if brief.priorities:
        top = brief.priorities[0]
        candidates.append(
            ContentPlan(
                angle="today_priority",
                score=4,
                reason="Daily top priority exists with why/action context.",
                title=f"{top.title} becomes today's decision anchor",
            )
        )

    if brief.ignored_signals_count > 0:
        candidates.append(
            ContentPlan(
                angle="ignored_signals",
                score=3,
                reason="Ignored signal count provides proof of filtering value.",
                title=f"Ignored {brief.ignored_signals_count} weak signals today",
            )
        )

    if weekly.days_covered >= 3 and weekly.top_priorities:
        repeated = weekly.top_priorities[0]
        candidates.append(
            ContentPlan(
                angle="weekly_repeat",
                score=5,
                reason="Weekly review shows repeated priorities across multiple days.",
                title=f"Weekly repeat: {repeated.get('title', 'Priority')}",
            )
        )

    if weekly.days_covered >= 3 and weekly.recommendations:
        candidates.append(
            ContentPlan(
                angle="weekly_lesson",
                score=4,
                reason="Weekly review contains concrete recommendation.",
                title="What SimpliXio learned this week",
            )
        )

    if replay.signals_reviewed > 0:
        candidates.append(
            ContentPlan(
                angle="decision_replay_proof",
                score=5,
                reason="Decision replay shows reviewed, ignored, and selected counts from real output.",
                title=f"Decision replay: reviewed {replay.signals_reviewed} signals",
            )
        )

    if not candidates:
        return ContentPlan(
            angle="insufficient_signal",
            score=0,
            reason="Not enough artifact data to generate proof-based content.",
            title="Skip generation",
            skip_generation=True,
        )

    # Prefer highest score, avoiding recently used angles.
    candidates.sort(key=lambda item: item.score, reverse=True)
    for candidate in candidates:
        if candidate.angle not in recent_angles:
            return candidate

    # If all are repeated, keep best but skip when weak.
    best = candidates[0]
    if best.score < 3:
        best.skip_generation = True
    return best


def deterministic_posts(
    cfg: Config,
    brief: CortexBrief,
    weekly: WeeklyReview,
    replay: DecisionReplay,
    trends: list[TrendItem],
    plan: ContentPlan,
) -> dict[str, GeneratedPost]:
    active = [p for p in brief.priorities if not p.ignored][:3]
    ignored = brief.ignored_signals_count
    trend_titles = "; ".join(item.title for item in trends[:3])

    if plan.skip_generation:
        return {}

    weekly_line = weekly.summary.strip() if weekly.summary else "Weekly review is building signal history."
    replay_line = (
        replay.summary.strip()
        if replay.summary
        else "Decision replay is not available for this run."
    )
    repeated_priority = ""
    if weekly.top_priorities:
        first = weekly.top_priorities[0]
        repeated_priority = str(first.get("title", "")).strip()

    x_body = textwrap.dedent(
        f"""
        SimpliXio today:

        3 priorities:
        • {active[0].title if len(active) > 0 else 'Reduce noise'}
        • {active[1].title if len(active) > 1 else 'Protect clarity'}
        • {active[2].title if len(active) > 2 else 'Act on what matters'}

        Why it matters:
        {active[0].why if len(active) > 0 else 'Decision quality compounds when weak signals are removed.'}

        Next action:
        {active[0].action if len(active) > 0 else 'Take one concrete action in the next 30 minutes.'}

        Ignored signals: {ignored}
        Decision replay: reviewed {replay.signals_reviewed}, ignored {replay.signals_ignored}, kept {replay.signals_kept}
        {cfg.app_url}
        """
    ).strip()

    linkedin_body = textwrap.dedent(
        f"""
        SimpliXio is a decision system.

        It turns noise into 3 priorities:
        - {active[0].title if len(active) > 0 else 'Reduce noise'}
        - {active[1].title if len(active) > 1 else 'Protect clarity'}
        - {active[2].title if len(active) > 2 else 'Act on what matters'}

        Ignored signals today: {ignored}
        Weekly review: {weekly_line}
        Decision replay: {replay_line}

        Angle: {plan.angle}
        Context signals reviewed: {trend_titles if trend_titles else 'AI, developer tools, context systems'}

        Decide what matters. Turn noise into action.
        {cfg.app_url}
        """
    ).strip()

    blog_body = textwrap.dedent(
        f"""
        # SimpliXio Today: decision loop update

        SimpliXio helps decide what matters.

        ## 3 priorities

        {chr(10).join([f"### {p.title}{chr(10)}Why: {p.why}{chr(10)}Action: {p.action}" for p in active])}

        ## Ignored signals

        - {ignored} weak signals filtered out today

        ## Weekly review

        - Days covered: {weekly.days_covered}
        - Repeated priority: {repeated_priority or 'Not enough history yet'}
        - Summary: {weekly_line}

        ## Decision replay

        - Signals reviewed: {replay.signals_reviewed}
        - Signals kept: {replay.signals_kept}
        - Signals ignored: {replay.signals_ignored}
        - Summary: {replay_line}

        ## Lesson

        - {plan.reason}

        Not another AI app. A decision system for clearer action.
        """
    ).strip()

    return {
        "x": GeneratedPost(channel="x", title="SimpliXio Today: 3 priorities", body=x_body, url=cfg.app_url),
        "linkedin": GeneratedPost(
            channel="linkedin",
            title="SimpliXio: from noise to action",
            body=linkedin_body,
            url=cfg.app_url,
        ),
        "blog": GeneratedPost(channel="blog", title="SimpliXio Today: decision loop update", body=blog_body, url=cfg.app_url),
    }


def save_drafts(cfg: Config, posts: dict[str, GeneratedPost]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    latest_targets = [cfg.output_dir / "drafts" / f"latest-{channel}.md" for channel in ("x", "linkedin", "blog")]
    if not posts:
        for target in latest_targets:
            if target.exists():
                target.unlink()
        return paths

    for channel, post in posts.items():
        path = cfg.output_dir / "drafts" / f"{channel}-{slugify(post.title)}-{file_sha(post.body)}.md"
        markdown = f"# {post.title}\n\n{post.body}\n"
        path.write_text(markdown, encoding="utf-8")
        (cfg.output_dir / "drafts" / f"latest-{channel}.md").write_text(markdown, encoding="utf-8")
        paths[channel] = path
    return paths


def save_campaign_brief(
    cfg: Config,
    brief: CortexBrief,
    weekly: WeeklyReview,
    replay: DecisionReplay,
    plan: ContentPlan,
    posts: dict[str, GeneratedPost],
    trends: list[TrendItem],
) -> Path:
    day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = cfg.output_dir / "campaigns" / f"{app_slug(cfg.app_name)}-campaign-{day_key}.md"

    trend_lines = [f"- {item.title} ({item.url})" for item in trends[:5]] or ["- No external trends captured in this run."]
    active = [p for p in brief.priorities if not p.ignored][:3]
    priority_lines = [f"- {p.title}: {p.action}" for p in active] or ["- No active priorities detected."]

    lines = [
        f"# {cfg.app_name} Campaign Brief · {day_key}",
        "",
        "## Positioning",
        "",
        "Not another AI app. A decision system for clearer action.",
        "",
        "## Core message",
        "",
        "Decide what matters. Turn noise into action.",
        "",
        "## Chosen angle",
        "",
        f"- Angle: {plan.angle}",
        f"- Reason: {plan.reason}",
        f"- Score: {plan.score}",
        f"- Skip generation: {str(plan.skip_generation).lower()}",
        "",
        "## Today's priorities",
        "",
        *priority_lines,
        "",
        "## Weekly context",
        "",
        f"- Days covered: {weekly.days_covered}",
        f"- Ignored signals this week: {weekly.total_ignored_signals}",
        "",
        "## Decision replay context",
        "",
        f"- Signals reviewed: {replay.signals_reviewed}",
        f"- Signals kept: {replay.signals_kept}",
        f"- Signals ignored: {replay.signals_ignored}",
        f"- Summary: {replay.summary or 'Not enough replay data yet.'}",
        "",
        "## Signals reviewed",
        "",
        *trend_lines,
        "",
        "## Draft artifacts",
        "",
    ]

    if posts:
        lines.extend(
            [
                f"- X: {posts['x'].title}",
                f"- LinkedIn: {posts['linkedin'].title}",
                f"- Blog: {posts['blog'].title}",
            ]
        )
    else:
        lines.append("- Skipped: insufficient signal for high-quality draft generation.")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def render_card(cfg: Config, brief: CortexBrief, out_path: Path) -> None:
    width, height = 1280, 640
    img = Image.new("RGB", (width, height), (10, 14, 28))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        h2_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        title_font = ImageFont.load_default()
        h2_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.rounded_rectangle((36, 36, 1244, 604), radius=34, fill=(20, 28, 50))
    draw.text((72, 64), cfg.app_name, font=title_font, fill=(245, 248, 255))
    draw.text((74, 142), "Decide what matters.", font=h2_font, fill=(175, 186, 214))

    y = 220
    for idx, priority in enumerate([p for p in brief.priorities if not p.ignored][:3], start=1):
        draw.rounded_rectangle((72, y, 1208, y + 96), radius=24, outline=(105, 142, 255), width=2)
        draw.text((96, y + 18), f"{idx}. {priority.title}", font=h2_font, fill=(245, 248, 255))
        draw.text((96, y + 52), textwrap.fill(f"Why: {priority.why}", width=70), font=small_font, fill=(175, 186, 214))
        y += 112

    draw.rounded_rectangle((840, 74, 1194, 170), radius=24, fill=(17, 24, 42))
    draw.text((868, 96), f"Ignored today: {brief.ignored_signals_count}", font=small_font, fill=(98, 209, 150))
    draw.text((868, 128), "Noise reduced into action", font=small_font, fill=(175, 186, 214))
    img.save(out_path)


def publish_site(cfg: Config, posts: dict[str, GeneratedPost], brief: CortexBrief, card_path: Path) -> Path | None:
    if not posts:
        return None

    html_path = cfg.output_dir / "site" / f"{app_slug(cfg.app_name)}-today-{brief.date}.html"
    post = posts["blog"]
    body_html = "".join(f"<p>{html.escape(line)}</p>" for line in post.body.splitlines() if line.strip())
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' />
<title>{html.escape(post.title)}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:840px;margin:40px auto;padding:0 20px;line-height:1.6;background:#0b1120;color:#eef2ff}}a{{color:#7aa2ff}}img{{width:100%;border-radius:20px;margin:24px 0}}.meta{{color:#a5b4d6}}</style></head><body>
<h1>{html.escape(post.title)}</h1><p class='meta'>{cfg.app_name} automated brief · {brief.date}</p>
<img src='../cards/{card_path.name}' alt='{cfg.app_name} today' />{body_html}
<p><a href='{cfg.app_url}'>Project</a> · <a href='{cfg.author_url}'>Builder</a></p></body></html>"""
    html_path.write_text(page, encoding="utf-8")
    return html_path


def save_log(cfg: Config, payload: dict[str, Any]) -> Path:
    path = cfg.output_dir / "logs" / f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_publish_manifest(
    cfg: Config,
    posts: dict[str, GeneratedPost],
    plan: ContentPlan,
    replay: DecisionReplay,
    quality_gate_passed: bool,
) -> Path:
    manifest = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "quality_gate_passed": quality_gate_passed,
        "plan": plan.model_dump(),
        "decision_replay": {
            "signals_reviewed": replay.signals_reviewed,
            "signals_kept": replay.signals_kept,
            "signals_ignored": replay.signals_ignored,
            "summary": replay.summary,
        },
        "posts": {
            channel: {
                "title": post.title,
                "body": post.body,
                "hash": file_sha(post.body),
                "url": post.url,
            }
            for channel, post in posts.items()
        },
    }
    path = cfg.output_dir / "publish" / "latest_posts.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def run() -> None:
    cfg = load_config()
    ensure_dirs(cfg)

    brief = read_latest_brief(cfg)
    weekly = read_weekly_review(cfg)
    replay = read_decision_replay(cfg)
    trends = fetch_rss_items(cfg) + fetch_github_topic_repos(cfg)
    memory = load_content_memory(cfg)

    plan = choose_content_plan(brief, weekly, replay, memory)
    posts = deterministic_posts(cfg, brief, weekly, replay, trends, plan)

    card_path = cfg.output_dir / "cards" / f"{app_slug(cfg.app_name)}-today-{brief.date}.png"
    render_card(cfg, brief, card_path)

    drafts = save_drafts(cfg, posts)
    campaign_brief = save_campaign_brief(cfg, brief, weekly, replay, plan, posts, trends)

    # Generation step remains dry-run by default. Quality + publish happen later in the pipeline.
    gate_ok = False
    manifest_path = write_publish_manifest(
        cfg, posts, plan, replay, quality_gate_passed=gate_ok
    )

    site_path = publish_site(cfg, posts, brief, card_path) if cfg.publish_site else None

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "brief_date": brief.date,
        "plan": plan.model_dump(),
        "decision_replay": replay.model_dump(),
        "drafts": {k: str(v) for k, v in drafts.items()},
        "latest_drafts": {
            "x": str(cfg.output_dir / "drafts" / "latest-x.md"),
            "linkedin": str(cfg.output_dir / "drafts" / "latest-linkedin.md"),
            "blog": str(cfg.output_dir / "drafts" / "latest-blog.md"),
        },
        "campaign_brief": str(campaign_brief),
        "publish_manifest": str(manifest_path),
        "card": str(card_path),
        "site": str(site_path) if site_path else None,
        "quality_gate_passed": False,
        "publish": {"status": "not-run", "reason": "Quality gate and publish step run later in pipeline."},
    }

    if cfg.publish_json_log:
        results["log"] = str(save_log(cfg, results))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run()
