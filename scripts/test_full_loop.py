#!/usr/bin/env python3
"""
End-to-end self-improvement loop test.
Validates the full CortexOS cycle:
  profile → context → digest → score → focus → learn → improve
  + deduplication, tag inference, spaced repetition
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cortex_core.engine import CortexEngine

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    icon = "✓" if condition else "✗"
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    msg = f"  {icon} [{status}] {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    engine = CortexEngine()

    # ── 1. Profile: set user context ────────────────────────
    section("1. SET USER PROFILE")
    engine.update_profile(
        name="Pierre-Henry Soria",
        goals=[
            "Ship CortexOS as flagship project",
            "Build AI-native productivity tools",
            "Become visible as AI systems engineer",
        ],
        interests=[
            "AI systems",
            "context engines",
            "retrieval augmented generation",
            "developer productivity",
            "healthy living",
            "Swift",
            "Python",
        ],
        current_projects=["CortexOS", "pH7Programming YouTube", "pierrewriter.com"],
        constraints=["Solo founder", "Sydney timezone"],
        ignored_topics=["crypto", "NFT", "meme stocks"],
    )
    profile = engine.get_profile()
    check("Profile name set", profile["name"] == "Pierre-Henry Soria")
    check("Goals set", len(profile["goals"]) == 3)
    check("Interests set", len(profile["interests"]) == 7)
    check("Projects set", len(profile["current_projects"]) == 3)

    # ── 2. Context: check what the memory knows ──────────────
    section("2. CONTEXT MEMORY")
    ctx = engine.memory.get_context_snippets()
    check("Context snippets populated", len(ctx) > 0, f"{len(ctx)} snippets")
    tokens = engine.memory.get_context_tokens()
    check("Context tokens populated", len(tokens) > 10, f"{len(tokens)} tokens")

    # ── 3. Pipeline: run full pipeline ──────────────────────
    section("3. FULL PIPELINE RUN")
    notes_before = engine.store.count
    result = engine.run_pipeline()
    notes_after = engine.store.count
    check("Pipeline succeeded", result["success"])
    for step in result["steps"]:
        check(f"Step: {step['name']}", step["status"] == "success")
    print(f"  Notes: {notes_before} → {notes_after}")

    # ── 4. Deduplication: re-running should NOT duplicate ───
    section("4. DEDUPLICATION TEST")
    result2 = engine.run_pipeline()
    notes_after_rerun = engine.store.count
    check("Pipeline re-run succeeded", result2["success"])
    check(
        "No duplicate notes added",
        notes_after_rerun == notes_after,
        f"before={notes_after}, after={notes_after_rerun}",
    )

    # ── 5. Tag inference: notes should have rich tags ───────
    section("5. TAG INFERENCE")
    all_tags = set()
    for n in engine.list_notes():
        all_tags.update(n.get("tags", []))
    check("Multiple tag categories", len(all_tags) > 2, f"{len(all_tags)} unique tags: {sorted(all_tags)[:10]}")
    check("AI tag present", "ai" in all_tags or "AI" in {t.lower() for t in all_tags})

    # ── 6. Evaluate digest ──────────────────────────────────
    section("6. EVALUATE DIGEST")
    eval_result = engine.evaluate_digest()
    check("Digest evaluated", "error" not in eval_result)
    check("Articles found", eval_result.get("total_articles", 0) > 0, f"{eval_result.get('total_articles')} articles")
    check("AI ratio > 0", eval_result.get("ai_article_ratio", 0) > 0, f"{eval_result.get('ai_article_ratio', 0):.1%}")
    check(
        "Project fit > 0", eval_result.get("project_fit_score", 0) > 0, f"{eval_result.get('project_fit_score', 0):.1%}"
    )
    fit_before = eval_result["project_fit_score"]

    # ── 7. Focus brief ──────────────────────────────────────
    section("7. GENERATE FOCUS BRIEF")
    brief = engine.generate_focus_brief()
    check("Brief generated", brief.get("date") is not None)
    check("Focus items present", len(brief.get("focus_items", [])) > 0, f"{len(brief.get('focus_items', []))} items")
    check("Digest quality included", brief.get("digest_quality") is not None)

    # ── 8. Self-improvement: learn + context enrichment ─────
    section("8. SELF-IMPROVEMENT LOOP")

    # Mark focus items as read
    for item in brief.get("focus_items", [])[:2]:
        engine.focus.mark_read(item["title"])

    # Record a reading with insight
    engine.memory.record_read(
        title="Context-Aware Retrieval for AI Systems",
        url="https://example.com/context-retrieval",
        score=0.9,
        tags=["ai", "retrieval", "context"],
        insight="Context windows improve retrieval by 40%.",
    )

    # Record another with AI-relevant insight
    engine.memory.record_read(
        title="Building AI Agent Architectures",
        url="https://example.com/agent-arch",
        score=0.85,
        tags=["ai", "agents", "architecture"],
        insight="Multi-agent systems with shared context outperform single agents.",
    )
    check("Reading entries recorded", len(engine.memory.history) >= 2)

    # Re-evaluate — context should now be richer
    ctx_after = engine.memory.get_context_snippets()
    tokens_after = engine.memory.get_context_tokens()
    check("Context snippets grew", len(ctx_after) > len(ctx), f"{len(ctx)} → {len(ctx_after)}")
    check("Context tokens grew", len(tokens_after) > len(tokens), f"{len(tokens)} → {len(tokens_after)}")

    eval_after = engine.evaluate_digest()
    fit_after = eval_after["project_fit_score"]
    check(
        "Context coverage increased",
        eval_after["context_keyword_coverage"] >= eval_result.get("context_keyword_coverage", 0),
        f"{eval_result.get('context_keyword_coverage', 0):.3f} → {eval_after['context_keyword_coverage']:.3f}",
    )
    print(f"  Project fit: {fit_before:.1%} → {fit_after:.1%}")

    # ── 9. Spaced repetition ────────────────────────────────
    section("9. SPACED REPETITION")
    due = engine.due_for_review()
    check("Due-for-review returns list", isinstance(due, list))

    # Advance a review
    advanced = engine.advance_review("Context-Aware Retrieval for AI Systems")
    check("Review advanced", advanced is not None)
    if advanced:
        check("Review level incremented", advanced["review_level"] >= 1, f"level={advanced['review_level']}")
        check("Next review scheduled", advanced["next_review"] != "")

    # ── 10. System status ───────────────────────────────────
    section("10. SYSTEM STATUS")
    status = engine.status()
    check("Version present", status.get("version") == "0.1.0")
    check("Notes count > 0", status.get("notes_count", 0) > 0, f"{status.get('notes_count')} notes")
    check("Profile loaded", status.get("profile_loaded") is True)
    print(f"  {json.dumps(status, indent=2)}")

    # ── Summary ─────────────────────────────────────────────
    section("RESULTS")
    total = PASS + FAIL
    print(f"  {PASS}/{total} checks passed, {FAIL} failed")
    if FAIL == 0:
        print("  ALL CHECKS PASSED — CortexOS self-improvement loop verified ✓")
    else:
        print(f"  WARNING: {FAIL} checks failed — review above output")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
