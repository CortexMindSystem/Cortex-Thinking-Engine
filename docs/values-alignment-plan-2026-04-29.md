# SimpliXio Values Alignment Plan (2026-04-29)

## 1) Values-alignment audit

### Aligned
- Core wedge is now present in top-level README and onboarding flow.
- Safety defaults already exist in acquisition + newsletter pipelines (`needs_approval`, redaction, strict gates).
- Product architecture still keeps ranking/decision logic inside SimpliXio backend.

### Drifting
- Public messaging still appears in multiple places with slight wording drift.
- Proof output exists, but Discord/community proof flow was not previously curated by default.
- Some automation naming still reflects "marketing engine" language instead of "proof + trust" framing.

### Actions
- Keep one canonical messaging stack.
- Keep draft-only publishing defaults.
- Keep proof artifacts curated and redacted before public channels.

## 2) Positioning audit

### Current risk
- Message can read as broad system language in some surfaces.

### Target
- "SimpliXio turns scattered thoughts, project noise, and open loops into 3 priorities and one next action."
- Keep all surfaces outcome-first: what matters now, why, next action.

## 3) Strongest wedge recommendation
- **Wedge A (recommended):** Turn scattered thoughts and project noise into 3 priorities and one next action.
- Wedge B: Decide what matters now from your captured signals.
- Wedge C: Reduce open loops into one clear daily move.

Why A: concrete input + concrete output + decision outcome; strongest for screenshots, onboarding, and acquisition.

## 4) Messaging stack rewrite
- One-liner: SimpliXio turns scattered thoughts, project noise, and open loops into 3 priorities and one next action.
- Subtitle: 3 priorities. Why it matters. Next action.
- Onboarding line: Turn scattered thoughts and project noise into 3 priorities and one next action.
- Outreach line: I saw your prioritisation workflow; SimpliXio reduces that signal overload into 3 priorities and one next move.
- Screenshot set:
  1. Decide what matters now.
  2. Turn noise into 3 priorities.
  3. Know why it matters.
  4. Take the next action.
  5. See what was ignored.

## 5) Trust framing improvements
- Private by default across onboarding, README, and automation docs.
- Public outputs remain draft-first with strict quality + safety checks.
- Private outreach remains `needs_approval`.
- New curated Discord drafts are local-only and manual post only.

## 6) Recommended integrations in priority order
1. GitHub (project context + credibility)
2. Notion (long-form context linking)
3. Discord (curated proof distribution)
4. RSS (selective context enrichment)
5. Gmail (later-stage high-signal enrichment)

## 7) Integrations to avoid or postpone
- LinkedIn scraping/automation (non-compliant).
- Full inbox-style Gmail processing.
- Slack/Calendar before Tier 1 shows signal.
- Auto-publish integrations without explicit approval.

## 8) What each recommended integration should power
- GitHub: context pull, release proof, builder relevance.
- Notion: decision memory + project context enrichment.
- Discord: release notes, weekly proof, feedback prompts.
- RSS: external themes for context, not feed overload.
- Gmail: selected communication signals, draft-safe only.

## 9) Discord / build-in-public plan
- Channels: `#announcements`, `#release-notes`, `#build-in-public`, `#weekly-review`, `#feedback`.
- Posting model: draft generation -> manual review -> manual post.
- Each post format:
  - What changed
  - Why it matters
  - One CTA
- Never auto-post internal logs or private details.

## 10) App Store + screenshot improvement plan
- Keep first 3 screenshots outcome-first:
  1. Decide what matters now.
  2. Turn noise into 3 priorities.
  3. Know why and what to do next.
- Ensure trust slide appears in first 5 screenshots.
- Keep subtitle stable for three release cycles to measure conversion impact.

## 11) README / GitHub / OpenClaw credibility improvements
- README now has explicit "Why SimpliXio" and "Trust" sections.
- Keep release notes tied to product outcomes, not feature volume.
- OpenClaw positioning should stay as proof/funnel to SimpliXio wedge, not separate brand message.

## 12) Warm-first acquisition alignment
- Collect compliant public signals only by default.
- Internal artifact ingestion now opt-in via `ACQ_INCLUDE_INTERNAL_SIGNALS=false` default.
- Keep fit scoring + draft-only outreach + quality gate.

## 13) Highest-leverage files/screens/scripts
- `README.md`
- `CortexOSApp/Shared/Views/ContentView.swift`
- `scripts/generate_marketing_screenshots.py`
- `cortexos_automation_scripts/scripts/lead_collector.py`
- `cortexos_automation_scripts/scripts/run_weekly_pipeline.py`
- `cortexos_automation_scripts/scripts/build_discord_proof_drafts.py`
- `cortexos_automation_scripts/README.md`

## 14) Phased implementation plan

### Phase 1 (done in this pass)
- Wedge + trust copy alignment.
- App Store screenshot copy rewrite.
- Warm-first acquisition defaults tightened.
- Draft-only Discord proof generation wired into weekly pipeline.

### Phase 2
- Notion connector ingestion scoped to selected databases only.
- GitHub signal mapping from issue/PR/release into ranking inputs.
- App Store screenshot regeneration and A/B sequence test.

### Phase 3
- Discord approval workflow integration (still manual post).
- Weekly growth scorecard automation tied to channel signals.

## 15) First milestone to execute
- Run weekly pipeline with strict quality.
- Produce curated Discord proof drafts.
- Review generated markdown drafts and manually post best one per channel.
- Measure response quality (replies, saves, DMs, stars).

## 16) What to intentionally postpone
- Broad multi-channel automation.
- Auto-publishing to LinkedIn/X/newsletter.
- Additional integrations that do not directly improve wedge outcomes.
- Any UX surface that increases noise on iPhone home experience.
