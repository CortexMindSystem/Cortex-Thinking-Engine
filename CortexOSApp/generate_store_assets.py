#!/usr/bin/env python3
"""
Generate App Store marketing screenshots for CortexOS (iOS + macOS).

Produces polished dark-theme promotional images with mock UI elements
matching the app's design system. Output: CortexOSApp/store_assets/
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent / "store_assets"

# ── Brand palette (from Theme.swift) ───────────────────────────────────
ACCENT      = (97, 107, 255)    # #616BFF
ACCENT_DIM  = (97, 107, 255, 38)
BG_PRIMARY  = (18, 18, 18)     # ~0.07 white
BG_SURFACE  = (36, 36, 36)     # ~0.14 white
BG_CARD     = (44, 44, 44)
TEXT_PRIMARY = (255, 255, 255)
TEXT_SECOND  = (180, 180, 180)
TEXT_TERTIARY= (128, 128, 128)
SUCCESS      = (52, 199, 89)    # iOS green
WARNING      = (255, 159, 10)   # iOS orange
WHITE        = (255, 255, 255)
GRADIENT_TOP = (20, 20, 40)
GRADIENT_BOT = (10, 10, 18)
BADGE_COLORS = [ACCENT, (115, 128, 230), (140, 148, 199)]

# ── Device sizes for App Store Connect ─────────────────────────────────
SIZES = {
    # iPhone
    "iPhone_6.9":  (1320, 2868),  # iPhone 16 Pro Max
    "iPhone_6.7":  (1290, 2796),  # iPhone 15 Pro Max
    "iPhone_6.5":  (1242, 2688),  # iPhone 11 Pro Max
    "iPhone_5.5":  (1242, 2208),  # iPhone 8 Plus
    # iPad
    "iPad_13":     (2064, 2752),  # iPad Pro 13" (6th gen)
    "iPad_12.9":   (2048, 2732),  # iPad Pro 12.9" (2nd gen)
    # Mac
    "Mac":         (2880, 1800),  # Retina MacBook Pro
}

# ── Screen data ────────────────────────────────────────────────────────
SCREENS = [
    {
        "id": "01_hero",
        "headline": "Your Thinking\nEngine",
        "subhead": "Context, memory, and prioritisation\nfor ambitious builders.",
        "feature_pills": ["Offline-First", "AI-Enhanced", "Privacy-Focused"],
        "type": "hero",
    },
    {
        "id": "02_focus",
        "headline": "Today's Focus",
        "subhead": "Ranked priorities with\nwhy it matters + next action.",
        "type": "focus",
        "items": [
            {"rank": 1, "title": "Review Q2 product roadmap", "why": "Aligns with your OKR to ship v2 by June", "action": "Draft milestone timeline"},
            {"rank": 2, "title": "Anthropic drops Claude 5", "why": "Direct impact on your AI integration layer", "action": "Benchmark against current pipeline"},
            {"rank": 3, "title": "Team standup prep", "why": "Unblock frontend team on API changes", "action": "Share updated schema docs"},
        ],
    },
    {
        "id": "03_insights",
        "headline": "Smart Insights",
        "subhead": "4-dimension scoring surfaces\nwhat actually matters to you.",
        "type": "insights",
        "items": [
            {"title": "WebGPU adoption accelerating", "confidence": 0.87, "tags": ["AI", "Web"]},
            {"title": "EU AI Act enforcement begins", "confidence": 0.72, "tags": ["Policy", "Risk"]},
            {"title": "SwiftUI navigation patterns", "confidence": 0.64, "tags": ["iOS", "UX"]},
        ],
    },
    {
        "id": "04_signals",
        "headline": "Signal Detection",
        "subhead": "Emerging topics across\nyour sources — spotted early.",
        "type": "signals",
        "signals": [
            {"name": "Edge AI", "status": "emerging", "count": 7},
            {"name": "Rust in production", "status": "confirmed", "count": 12},
            {"name": "Ambient computing", "status": "emerging", "count": 4},
            {"name": "LLM agents", "status": "confirmed", "count": 15},
            {"name": "Privacy-first analytics", "status": "emerging", "count": 5},
            {"name": "On-device ML", "status": "confirmed", "count": 9},
        ],
    },
    {
        "id": "05_memory",
        "headline": "4-Layer Memory",
        "subhead": "Your full context persists —\nscoring improves over time.",
        "type": "memory",
        "layers": [
            {"name": "Identity", "icon": "◉", "detail": "Goals · Interests · Role"},
            {"name": "Projects", "icon": "▣", "detail": "Milestones · Blockers · Decisions"},
            {"name": "Research", "icon": "◈", "detail": "Notes · Insights · Signals"},
            {"name": "Working", "icon": "◎", "detail": "Today's priorities · Actions"},
        ],
    },
]


# ── Drawing helpers ────────────────────────────────────────────────────

def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load SF Pro or fall back to system font."""
    sf_paths = [
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/SF-Pro-Display-Regular.otf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/SF-Pro.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in sf_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont:
    """Load SF Pro Bold or equivalent."""
    bold_paths = [
        "/Library/Fonts/SF-Pro-Display-Bold.otf",
        "/System/Library/Fonts/SFNSDisplay-Bold.otf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in bold_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return load_font(size)


def draw_gradient(img: Image.Image, top: tuple, bot: tuple):
    """Vertical linear gradient."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        t = y / h
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_rounded_rect(draw: ImageDraw.Draw, xy, radius, fill, outline=None):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def draw_pill(draw: ImageDraw.Draw, xy, text: str, font, bg_color, text_color=WHITE):
    """Draw a pill-shaped badge with text."""
    x, y = xy
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = int(th * 0.7), int(th * 0.3)
    pill_w = tw + pad_x * 2
    pill_h = th + pad_y * 2
    draw.rounded_rectangle(
        [x, y, x + pill_w, y + pill_h],
        radius=pill_h // 2,
        fill=bg_color,
    )
    draw.text((x + pad_x, y + pad_y - 2), text, fill=text_color, font=font)
    return pill_w


def scale(base: int, w: int, ref_w: int = 1290) -> int:
    """Scale a dimension relative to reference width (iPhone 6.7")."""
    return int(base * w / ref_w)


# ── Screen renderers ───────────────────────────────────────────────────

def render_hero(img: Image.Image, screen: dict, is_landscape: bool = False):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, (25, 25, 55), (10, 10, 20))

    s = lambda v: scale(v, w)

    # Decorative circles
    for i in range(3):
        cx = w // 2 + s(80) * (i - 1)
        cy = int(h * 0.28) if not is_landscape else int(h * 0.35)
        radius = s(160 - i * 30)
        for r in range(radius, 0, -1):
            alpha = int(15 * (r / radius))
            color = (ACCENT[0], ACCENT[1], ACCENT[2], alpha)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # App icon placeholder (rounded square)
    icon_size = s(140)
    ix = (w - icon_size) // 2
    iy = int(h * 0.12) if not is_landscape else int(h * 0.08)
    draw_rounded_rect(draw, [ix, iy, ix + icon_size, iy + icon_size], s(28), ACCENT)
    # "C" letter in icon
    icon_font = load_bold_font(s(80))
    cbox = icon_font.getbbox("C")
    cw, ch = cbox[2] - cbox[0], cbox[3] - cbox[1]
    draw.text((ix + (icon_size - cw) // 2, iy + (icon_size - ch) // 2 - s(8)), "C", fill=WHITE, font=icon_font)

    # Title
    title_font = load_bold_font(s(96))
    title_y = iy + icon_size + s(60)
    for i, line in enumerate(screen["headline"].split("\n")):
        bbox = title_font.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, title_y + i * s(110)), line, fill=WHITE, font=title_font)

    # Subtitle
    sub_font = load_font(s(36))
    sub_y = title_y + s(110) * len(screen["headline"].split("\n")) + s(30)
    for i, line in enumerate(screen["subhead"].split("\n")):
        bbox = sub_font.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, sub_y + i * s(48)), line, fill=TEXT_SECOND, font=sub_font)

    # Feature pills
    pill_font = load_font(s(28))
    pill_y = sub_y + s(48) * len(screen["subhead"].split("\n")) + s(50)
    total_w = 0
    pill_gap = s(16)
    pill_widths = []
    for p in screen["feature_pills"]:
        bbox = pill_font.getbbox(p)
        pw = bbox[2] - bbox[0] + s(40)
        pill_widths.append(pw)
        total_w += pw
    total_w += pill_gap * (len(pill_widths) - 1)
    px = (w - total_w) // 2
    for i, p in enumerate(screen["feature_pills"]):
        pw = draw_pill(draw, (px, pill_y), p, pill_font, (*ACCENT, 60), WHITE)
        px += pw + pill_gap

    # "CortexOS" wordmark at bottom
    wm_font = load_font(s(30))
    wm = "CortexOS"
    bbox = wm_font.getbbox(wm)
    wmw = bbox[2] - bbox[0]
    draw.text(((w - wmw) // 2, h - s(120)), wm, fill=TEXT_TERTIARY, font=wm_font)


def render_focus(img: Image.Image, screen: dict, is_landscape: bool = False):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, GRADIENT_TOP, GRADIENT_BOT)

    s = lambda v: scale(v, w)
    margin = s(80)

    # Header
    title_font = load_bold_font(s(72))
    sub_font = load_font(s(32))
    draw.text((margin, s(140)), screen["headline"], fill=WHITE, font=title_font)
    sub_y = s(140) + s(90)
    for i, line in enumerate(screen["subhead"].split("\n")):
        draw.text((margin, sub_y + i * s(44)), line, fill=TEXT_SECOND, font=sub_font)

    # Focus cards
    card_y = sub_y + s(44) * len(screen["subhead"].split("\n")) + s(60)
    card_margin = margin
    card_w = w - card_margin * 2
    item_font_title = load_bold_font(s(34))
    item_font_body = load_font(s(26))
    item_font_action = load_font(s(24))

    for item in screen["items"]:
        card_h = s(260)
        # Card background
        draw_rounded_rect(draw, [card_margin, card_y, card_margin + card_w, card_y + card_h], s(20), BG_SURFACE)

        # Rank badge
        badge_r = s(28)
        badge_cx = card_margin + s(44)
        badge_cy = card_y + s(44)
        rank_i = min(item["rank"] - 1, 2)
        draw.ellipse(
            [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
            fill=BADGE_COLORS[rank_i],
        )
        rank_font = load_bold_font(s(28))
        rbox = rank_font.getbbox(str(item["rank"]))
        rw = rbox[2] - rbox[0]
        draw.text((badge_cx - rw // 2, badge_cy - s(16)), str(item["rank"]), fill=WHITE, font=rank_font)

        # Title
        tx = badge_cx + badge_r + s(20)
        draw.text((tx, card_y + s(26)), item["title"], fill=WHITE, font=item_font_title)

        # Why
        draw.text((tx, card_y + s(78)), "Why: ", fill=ACCENT, font=item_font_body)
        why_offset = item_font_body.getbbox("Why: ")[2]
        draw.text((tx + why_offset, card_y + s(78)), item["why"], fill=TEXT_SECOND, font=item_font_body)

        # Action
        draw.text((tx, card_y + s(130)), "→  ", fill=SUCCESS, font=item_font_action)
        arr_w = item_font_action.getbbox("→  ")[2]
        draw.text((tx + arr_w, card_y + s(130)), item["action"], fill=TEXT_SECOND, font=item_font_action)

        # Feedback buttons
        fb_font = load_font(s(32))
        draw.text((card_margin + card_w - s(100), card_y + s(180)), "👍", font=fb_font)
        draw.text((card_margin + card_w - s(56), card_y + s(180)), "👎", font=fb_font)

        card_y += card_h + s(20)


def render_insights(img: Image.Image, screen: dict, is_landscape: bool = False):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, GRADIENT_TOP, GRADIENT_BOT)

    s = lambda v: scale(v, w)
    margin = s(80)

    # Header
    title_font = load_bold_font(s(72))
    sub_font = load_font(s(32))
    draw.text((margin, s(140)), screen["headline"], fill=WHITE, font=title_font)
    sub_y = s(140) + s(90)
    for i, line in enumerate(screen["subhead"].split("\n")):
        draw.text((margin, sub_y + i * s(44)), line, fill=TEXT_SECOND, font=sub_font)

    # Insight cards
    card_y = sub_y + s(44) * len(screen["subhead"].split("\n")) + s(60)
    card_margin = margin
    card_w = w - card_margin * 2
    item_font = load_bold_font(s(34))
    body_font = load_font(s(26))
    tag_font = load_font(s(22))

    for item in screen["items"]:
        card_h = s(200)
        draw_rounded_rect(draw, [card_margin, card_y, card_margin + card_w, card_y + card_h], s(20), BG_SURFACE)

        tx = card_margin + s(30)

        # Title + confidence badge
        draw.text((tx, card_y + s(26)), item["title"], fill=WHITE, font=item_font)

        # Confidence pill
        conf_pct = f"{int(item['confidence'] * 100)}%"
        conf_color = SUCCESS if item["confidence"] >= 0.7 else WARNING if item["confidence"] >= 0.4 else TEXT_TERTIARY
        conf_x = card_margin + card_w - s(120)
        draw_pill(draw, (conf_x, card_y + s(22)), conf_pct, tag_font, (*conf_color, 200), WHITE)

        # Tags
        tag_x = tx
        tag_y = card_y + s(90)
        for tag in item["tags"]:
            pw = draw_pill(draw, (tag_x, tag_y), tag, tag_font, BG_CARD, TEXT_SECOND)
            tag_x += pw + s(12)

        # Sparkle + why (simulated)
        draw.text((tx, card_y + s(140)), "✦  ", fill=ACCENT, font=body_font)
        sw = body_font.getbbox("✦  ")[2]
        draw.text((tx + sw, card_y + s(140)), "Matches your active project goals", fill=TEXT_SECOND, font=body_font)

        card_y += card_h + s(20)

    # Score dimensions at bottom
    dim_y = card_y + s(40)
    dim_font = load_font(s(24))
    dims = ["Relevance", "Novelty", "Actionability", "AI Impact"]
    dim_w = (card_w - s(30) * 3) // 4
    for i, dim in enumerate(dims):
        dx = card_margin + i * (dim_w + s(30))
        # Mini bar chart
        bar_h = s(8)
        draw_rounded_rect(draw, [dx, dim_y, dx + dim_w, dim_y + bar_h], s(4), BG_CARD)
        fill_pct = [0.85, 0.72, 0.68, 0.91][i]
        draw_rounded_rect(draw, [dx, dim_y, dx + int(dim_w * fill_pct), dim_y + bar_h], s(4), ACCENT)
        # Label
        bbox = dim_font.getbbox(dim)
        dw = bbox[2] - bbox[0]
        draw.text((dx + (dim_w - dw) // 2, dim_y + s(18)), dim, fill=TEXT_TERTIARY, font=dim_font)


def render_signals(img: Image.Image, screen: dict, is_landscape: bool = False):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, GRADIENT_TOP, GRADIENT_BOT)

    s = lambda v: scale(v, w)
    margin = s(80)

    # Header
    title_font = load_bold_font(s(72))
    sub_font = load_font(s(32))
    draw.text((margin, s(140)), screen["headline"], fill=WHITE, font=title_font)
    sub_y = s(140) + s(90)
    for i, line in enumerate(screen["subhead"].split("\n")):
        draw.text((margin, sub_y + i * s(44)), line, fill=TEXT_SECOND, font=sub_font)

    # Signal cards in a grid
    card_y = sub_y + s(44) * len(screen["subhead"].split("\n")) + s(60)
    card_w = (w - margin * 2 - s(20)) // 2
    card_h = s(200)
    signal_font = load_bold_font(s(30))
    count_font = load_bold_font(s(48))
    status_font = load_font(s(22))

    for i, sig in enumerate(screen["signals"]):
        col = i % 2
        row = i // 2
        cx = margin + col * (card_w + s(20))
        cy = card_y + row * (card_h + s(20))

        # Card
        draw_rounded_rect(draw, [cx, cy, cx + card_w, cy + card_h], s(16), BG_SURFACE)

        # Count
        draw.text((cx + s(24), cy + s(20)), str(sig["count"]), fill=ACCENT, font=count_font)

        # Name
        draw.text((cx + s(24), cy + s(84)), sig["name"], fill=WHITE, font=signal_font)

        # Status pill
        stat_color = SUCCESS if sig["status"] == "confirmed" else WARNING
        draw_pill(draw, (cx + s(24), cy + s(140)), sig["status"].upper(), status_font, (*stat_color, 180), WHITE)


def render_memory(img: Image.Image, screen: dict, is_landscape: bool = False):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, GRADIENT_TOP, GRADIENT_BOT)

    s = lambda v: scale(v, w)
    margin = s(80)

    # Header
    title_font = load_bold_font(s(72))
    sub_font = load_font(s(32))
    draw.text((margin, s(140)), screen["headline"], fill=WHITE, font=title_font)
    sub_y = s(140) + s(90)
    for i, line in enumerate(screen["subhead"].split("\n")):
        draw.text((margin, sub_y + i * s(44)), line, fill=TEXT_SECOND, font=sub_font)

    # Memory layer cards (stacked with connection lines)
    card_y = sub_y + s(44) * len(screen["subhead"].split("\n")) + s(60)
    card_margin = margin
    card_w = w - card_margin * 2
    layer_font = load_bold_font(s(36))
    detail_font = load_font(s(26))
    icon_font = load_bold_font(s(44))
    card_h = s(160)

    layer_colors = [
        (97, 107, 255, 200),   # Identity — accent
        (82, 142, 255, 200),   # Projects — blue
        (72, 187, 210, 200),   # Research — teal
        (100, 210, 150, 200),  # Working — green
    ]

    for i, layer in enumerate(screen["layers"]):
        cy = card_y + i * (card_h + s(24))

        # Connection line between cards
        if i > 0:
            line_x = w // 2
            draw.line([(line_x, cy - s(24)), (line_x, cy)], fill=(*ACCENT, 80), width=s(3))
            # Arrow head
            draw.polygon([
                (line_x - s(8), cy - s(8)),
                (line_x + s(8), cy - s(8)),
                (line_x, cy),
            ], fill=(*ACCENT, 80))

        # Card with subtle left border
        draw_rounded_rect(draw, [card_margin, cy, card_margin + card_w, cy + card_h], s(16), BG_SURFACE)
        # Left accent bar
        lc = layer_colors[i]
        draw_rounded_rect(draw, [card_margin, cy, card_margin + s(6), cy + card_h], s(3), lc[:3])

        # Icon
        draw.text((card_margin + s(30), cy + s(24)), layer["icon"], fill=lc[:3], font=icon_font)

        # Name
        draw.text((card_margin + s(90), cy + s(30)), layer["name"], fill=WHITE, font=layer_font)

        # Detail
        draw.text((card_margin + s(90), cy + s(84)), layer["detail"], fill=TEXT_SECOND, font=detail_font)

    # Bottom tagline
    tag_font = load_font(s(26))
    tagline = "Context grows · Scoring sharpens · You stay focused"
    bbox = tag_font.getbbox(tagline)
    tw = bbox[2] - bbox[0]
    tag_y = card_y + 4 * (card_h + s(24)) + s(30)
    if tag_y < h - s(60):
        draw.text(((w - tw) // 2, tag_y), tagline, fill=TEXT_TERTIARY, font=tag_font)


RENDERERS = {
    "hero": render_hero,
    "focus": render_focus,
    "insights": render_insights,
    "signals": render_signals,
    "memory": render_memory,
}


# ── Main generation ────────────────────────────────────────────────────

def generate_all():
    total = 0
    for size_name, (w, h) in SIZES.items():
        out_dir = ROOT / size_name
        out_dir.mkdir(parents=True, exist_ok=True)

        is_landscape = w > h  # Mac

        for screen in SCREENS:
            img = Image.new("RGBA", (w, h), BG_PRIMARY)
            renderer = RENDERERS[screen["type"]]
            renderer(img, screen, is_landscape)

            # Convert to RGB for PNG (no alpha needed)
            rgb = Image.new("RGB", img.size, BG_PRIMARY)
            rgb.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)

            path = out_dir / f"{screen['id']}.png"
            rgb.save(path, "PNG", optimize=True)
            total += 1

    print(f"\n✅  Generated {total} screenshots across {len(SIZES)} device sizes")
    print(f"📁  Output: {ROOT.resolve()}")
    print()
    for size_name, (w, h) in SIZES.items():
        print(f"   {size_name:>14}  {w}×{h}  →  {len(SCREENS)} screenshots")


if __name__ == "__main__":
    generate_all()
