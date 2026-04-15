#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, os, re, textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import feedparser, requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field
try:
    from requests_oauthlib import OAuth1
except Exception:
    OAuth1 = None

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
    project: str = "CortexOS"
    themes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

class TrendItem(BaseModel):
    source: str
    title: str
    url: str
    published: str | None = None
    topic: str | None = None

class GeneratedPost(BaseModel):
    channel: str
    title: str
    body: str
    url: str | None = None
    tags: list[str] = Field(default_factory=list)

class Config(BaseModel):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    app_name: str = "CortexOS"
    app_url: str = "https://github.com/CortexMindSystem/Cortex-Thinking-Engine"
    author_name: str = "Pierre-Henry Soria"
    author_url: str = "https://ph7.me"
    site_base_url: str = "https://ph7.me"
    timezone_name: str = "Australia/Sydney"
    rss_feeds: list[str] = Field(default_factory=list)
    github_token: str | None = None
    github_topics: list[str] = Field(default_factory=lambda: ["ai","agents","developer-tools"])
    cortex_outputs_dir: Path = AUTOMATION_ROOT / "output" / "cortex_today"
    auto_approve: bool = True
    publish_x: bool = False
    publish_linkedin: bool = False
    publish_site: bool = True
    publish_json_log: bool = True
    x_api_key: str | None = None
    x_api_secret: str | None = None
    x_access_token: str | None = None
    x_access_secret: str | None = None
    linkedin_access_token: str | None = None
    linkedin_author_urn: str | None = None
    output_dir: Path = AUTOMATION_ROOT / "output"

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
    rss_feeds = [x.strip() for x in os.getenv("RSS_FEEDS","").split(",") if x.strip()]
    github_topics = [x.strip() for x in os.getenv("GITHUB_TOPICS","ai,agents,developer-tools").split(",") if x.strip()]
    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
        app_name=os.getenv("APP_NAME","CortexOS"),
        app_url=os.getenv("APP_URL","https://github.com/CortexMindSystem/Cortex-Thinking-Engine"),
        author_name=os.getenv("AUTHOR_NAME","Pierre-Henry Soria"),
        author_url=os.getenv("AUTHOR_URL","https://ph7.me"),
        site_base_url=os.getenv("SITE_BASE_URL","https://ph7.me"),
        timezone_name=os.getenv("TIMEZONE","Australia/Sydney"),
        rss_feeds=rss_feeds,
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_topics=github_topics,
        cortex_outputs_dir=_resolve_path(
            os.getenv("CORTEX_OUTPUTS_DIR", ""),
            default=AUTOMATION_ROOT / "output" / "cortex_today",
        ),
        auto_approve=os.getenv("AUTO_APPROVE","true").lower()=="true",
        publish_x=os.getenv("PUBLISH_X","false").lower()=="true",
        publish_linkedin=os.getenv("PUBLISH_LINKEDIN","false").lower()=="true",
        publish_site=os.getenv("PUBLISH_SITE","true").lower()=="true",
        publish_json_log=os.getenv("PUBLISH_JSON_LOG","true").lower()=="true",
        x_api_key=os.getenv("X_API_KEY") or None,
        x_api_secret=os.getenv("X_API_SECRET") or None,
        x_access_token=os.getenv("X_ACCESS_TOKEN") or None,
        x_access_secret=os.getenv("X_ACCESS_SECRET") or None,
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN") or None,
        linkedin_author_urn=os.getenv("LINKEDIN_AUTHOR_URN") or None,
        output_dir=_resolve_path(
            os.getenv("OUTPUT_DIR", ""),
            default=AUTOMATION_ROOT / "output",
        ),
    )

def ensure_dirs(cfg: Config) -> None:
    for sub in [cfg.output_dir, cfg.output_dir/"cards", cfg.output_dir/"drafts", cfg.output_dir/"logs", cfg.output_dir/"site"]:
        sub.mkdir(parents=True, exist_ok=True)

def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    value = re.sub(r"[\s_-]+","-",value)
    return value[:80]

def file_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def read_latest_brief(cfg: Config) -> CortexBrief:
    files = sorted(cfg.cortex_outputs_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No CortexOS outputs found in {cfg.cortex_outputs_dir}")
    return CortexBrief.model_validate(json.loads(files[-1].read_text(encoding="utf-8")))

def fetch_rss_items(cfg: Config, max_per_feed: int = 5) -> list[TrendItem]:
    items = []
    for feed_url in cfg.rss_feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:max_per_feed]:
            items.append(TrendItem(
                source=feed_url,
                title=getattr(entry, "title", "Untitled"),
                url=getattr(entry, "link", ""),
                published=getattr(entry, "published", None),
            ))
    return items

def fetch_github_topic_repos(cfg: Config, per_topic: int = 4) -> list[TrendItem]:
    items = []
    headers = {"Accept": "application/vnd.github+json"}
    if cfg.github_token:
        headers["Authorization"] = f"Bearer {cfg.github_token}"
    for topic in cfg.github_topics:
        params = {"q": f"topic:{topic} stars:>30", "sort":"updated", "order":"desc", "per_page": per_topic}
        try:
            resp = requests.get("https://api.github.com/search/repositories", headers=headers, params=params, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            continue
        for repo in payload.get("items", []):
            items.append(TrendItem(source="github", title=repo["full_name"], url=repo["html_url"], published=repo.get("updated_at"), topic=topic))
    return items

def deterministic_posts(cfg: Config, brief: CortexBrief, trends: list[TrendItem]) -> dict[str, GeneratedPost]:
    active = [p for p in brief.priorities if not p.ignored][:3]
    ignored = brief.ignored_signals_count
    trend_titles = "; ".join(item.title for item in trends[:3])
    x_body = textwrap.dedent(f"""
    CortexOS today:

    • {active[0].title if len(active) > 0 else 'Reduce noise'}
    • {active[1].title if len(active) > 1 else 'Protect clarity'}
    • {active[2].title if len(active) > 2 else 'Act on what matters'}

    Ignored {ignored} weak signals.
    Keeping the product focused on decision quality, not noise.

    {cfg.app_url}
    """).strip()
    linkedin_body = textwrap.dedent(f"""
    Most tools add information.
    {cfg.app_name} removes noise.

    Today the system compressed a noisy input stream into 3 priorities:
    - {active[0].title if len(active) > 0 else 'Reduce noise'}
    - {active[1].title if len(active) > 1 else 'Protect clarity'}
    - {active[2].title if len(active) > 2 else 'Act on what matters'}

    Why this matters:
    decision systems should help people think clearly and act decisively, not consume more feeds.

    Signals reviewed today included:
    {trend_titles if trend_titles else 'AI, developer tools, and context systems'}

    Project: {cfg.app_name}
    {cfg.app_url}
    """).strip()
    blog_body = textwrap.dedent(f"""
    # {cfg.app_name}: today’s decision brief

    {cfg.app_name} is being built as a system that decides what actually matters.

    Today’s active priorities were:

    {chr(10).join([f"## {p.title}{chr(10)}Why it matters: {p.why}{chr(10)}Next action: {p.action}" for p in active])}

    Ignored signals today: {ignored}

    Themes:
    {chr(10).join([f"- {theme}" for theme in brief.themes])}

    Notes:
    {chr(10).join([f"- {note}" for note in brief.notes])}

    The goal is simple: compress chaos into clarity, then turn clarity into action.
    """).strip()
    return {
        "x": GeneratedPost(channel="x", title=f"{cfg.app_name} today", body=x_body, url=cfg.app_url),
        "linkedin": GeneratedPost(channel="linkedin", title=f"{cfg.app_name}: fewer signals, better decisions", body=linkedin_body, url=cfg.app_url),
        "blog": GeneratedPost(channel="blog", title=f"{cfg.app_name}: today’s decision brief", body=blog_body, url=cfg.app_url),
    }

def save_drafts(cfg: Config, posts: dict[str, GeneratedPost]) -> dict[str, Path]:
    paths = {}
    for channel, post in posts.items():
        path = cfg.output_dir/"drafts"/f"{channel}-{slugify(post.title)}-{file_sha(post.body)}.md"
        path.write_text(f"# {post.title}\n\n{post.body}\n", encoding="utf-8")
        paths[channel] = path
    return paths

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
    draw.rounded_rectangle((36,36,1244,604), radius=34, fill=(20,28,50))
    draw.text((72,64), cfg.app_name, font=title_font, fill=(245,248,255))
    draw.text((74,142), "Decides what matters", font=h2_font, fill=(175,186,214))
    y = 220
    for idx, priority in enumerate([p for p in brief.priorities if not p.ignored][:3], start=1):
        draw.rounded_rectangle((72,y,1208,y+96), radius=24, outline=(105,142,255), width=2)
        draw.text((96, y+18), f"{idx}. {priority.title}", font=h2_font, fill=(245,248,255))
        draw.text((96, y+52), textwrap.fill(f"Why: {priority.why}", width=70), font=small_font, fill=(175,186,214))
        y += 112
    draw.rounded_rectangle((840,74,1194,170), radius=24, fill=(17,24,42))
    draw.text((868,96), f"Ignored today: {brief.ignored_signals_count}", font=small_font, fill=(98,209,150))
    draw.text((868,128), "Noise reduced into action", font=small_font, fill=(175,186,214))
    img.save(out_path)

def publish_site(cfg: Config, posts: dict[str, GeneratedPost], brief: CortexBrief, card_path: Path) -> Path:
    html_path = cfg.output_dir/"site"/f"cortexos-today-{brief.date}.html"
    post = posts["blog"]
    body_html = "".join(f"<p>{html.escape(line)}</p>" for line in post.body.splitlines() if line.strip())
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>{html.escape(post.title)}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:840px;margin:40px auto;padding:0 20px;line-height:1.6;background:#0b1120;color:#eef2ff}}a{{color:#7aa2ff}}img{{width:100%;border-radius:20px;margin:24px 0}}.meta{{color:#a5b4d6}}</style></head><body>
    <h1>{html.escape(post.title)}</h1><p class='meta'>{cfg.app_name} automated brief · {brief.date}</p>
    <img src='../cards/{card_path.name}' alt='{cfg.app_name} today' />{body_html}
    <p><a href='{cfg.app_url}'>Project</a> · <a href='{cfg.author_url}'>Builder</a></p></body></html>"""
    html_path.write_text(page, encoding="utf-8")
    return html_path

def publish_x(cfg: Config, post: GeneratedPost) -> dict[str, Any]:
    if not (cfg.x_api_key and cfg.x_api_secret and cfg.x_access_token and cfg.x_access_secret):
        return {"status":"skipped","reason":"Missing X credentials"}
    if OAuth1 is None:
        return {"status":"skipped","reason":"requests-oauthlib not available"}
    auth = OAuth1(cfg.x_api_key, cfg.x_api_secret, cfg.x_access_token, cfg.x_access_secret)
    resp = requests.post("https://api.x.com/2/tweets", json={"text": post.body[:280]}, auth=auth, timeout=30)
    return {"status_code": resp.status_code, "body": resp.text}

def publish_linkedin(cfg: Config, post: GeneratedPost) -> dict[str, Any]:
    if not (cfg.linkedin_access_token and cfg.linkedin_author_urn):
        return {"status":"skipped","reason":"Missing LinkedIn credentials"}
    payload = {
        "author": cfg.linkedin_author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": post.body},
            "shareMediaCategory": "ARTICLE",
            "media": [{"status": "READY", "originalUrl": cfg.app_url}],
        }},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    headers = {
        "Authorization": f"Bearer {cfg.linkedin_access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    resp = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload, timeout=30)
    return {"status_code": resp.status_code, "body": resp.text}

def save_log(cfg: Config, payload: dict[str, Any]) -> Path:
    path = cfg.output_dir/"logs"/f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path

def quality_gate_passed(cfg: Config) -> bool:
    report_path = cfg.output_dir / "quality_gate" / "quality_report.json"
    if not report_path.exists():
        return True
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    summary = payload.get("summary", {})
    failed = int(summary.get("failed", 0))
    drafts = int(summary.get("drafts", 0))
    return drafts > 0 and failed == 0

def run() -> None:
    cfg = load_config()
    ensure_dirs(cfg)
    brief = read_latest_brief(cfg)
    trends = fetch_rss_items(cfg) + fetch_github_topic_repos(cfg)
    posts = deterministic_posts(cfg, brief, trends)
    card_path = cfg.output_dir/"cards"/f"cortexos-today-{brief.date}.png"
    render_card(cfg, brief, card_path)
    drafts = save_drafts(cfg, posts)
    gate_ok = quality_gate_passed(cfg)
    results = {"generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "brief_date": brief.date, "drafts": {k:str(v) for k,v in drafts.items()}, "card": str(card_path), "site": None, "x":{"status":"not-run"}, "linkedin":{"status":"not-run"}, "quality_gate_passed": gate_ok}
    if cfg.publish_site:
        results["site"] = str(publish_site(cfg, posts, brief, card_path))
    if cfg.auto_approve and cfg.publish_x and gate_ok:
        results["x"] = publish_x(cfg, posts["x"])
    if cfg.auto_approve and cfg.publish_linkedin and gate_ok:
        results["linkedin"] = publish_linkedin(cfg, posts["linkedin"])
    if cfg.publish_json_log:
        results["log"] = str(save_log(cfg, results))
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run()
