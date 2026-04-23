# SimpliXio System Document

> SimpliXio helps you reduce noise, understand what matters, and take clear action.

## Architecture

SimpliXio is a three-tier system:
1. **Python Core Framework** (`cortex_core/`) — engine, focus engine, context memory, scoring, knowledge store, LLM abstraction, pipeline
2. **REST API** (`cortex_core/api/`) — FastAPI server exposing all operations over HTTP (port 8420)
3. **Native Apps** (`CortexOSApp/`) — SwiftUI multiplatform (iOS 17+ / macOS 14+), focus-first UX

## Core Pipeline

```
RSS Feeds (weekly_digest.py)             User Summaries (markdown)
    ↓                                        ↓
Digest (Markdown)                        extract_items_from_summary()
    ↓                                        ↓
DigestProcessor → KnowledgeStore         Items + KnowledgeNotes
    ↓                                        ↓
ScoringEngine (scoring.py)          ←── unified Item pool
    ↓  ai_article_ratio, high_signal_ratio, signal_to_noise_ratio,
    ↓  context_keyword_coverage, project_fit_score
    ↓
ContextMemory (memory.py)
    ↓  UserProfile: goals, interests, current_projects, constraints
    ↓  ReadingHistory: what was read, what was skipped
    ↓
FocusEngine (focus.py)
    ↓  "What should I focus on today?"
    ↓  Ranked FocusItems with why_it_matters + next_action
    ↓
DailyBrief → REST API → iOS / macOS App
    ↓
PostGenerator → Social Posts (optional)
```

## Modules

| Module          | Purpose                                                |
|-----------------|--------------------------------------------------------|
| `engine.py`     | Top-level facade wiring all components                 |
| `focus.py`      | Daily focus brief — ranked items with next actions     |
| `memory.py`     | User profile + reading history (context memory)        |
| `scoring.py`    | Article & digest quality scoring (weighted composite)  |
| `knowledge.py`  | Knowledge note CRUD with search and tagging            |
| `digest.py`     | Parse markdown digests into knowledge notes            |
| `items.py`      | Structured items + markdown parser (digest & summary)  |
| `posts.py`      | Generate social posts from knowledge notes             |
| `pipeline.py`   | Step-based pipeline with status tracking               |
| `llm.py`        | LLM provider abstraction (OpenAI, Anthropic, offline)  |
| `config.py`     | Runtime config with JSON persistence                   |

## Design Principles

- **Maximum impact, minimum effort, simplest code debt**
- AI-maintainable: small, modular, typed, testable, boring
- Every module is a single file < 200 lines
- No complex inheritance trees — dataclasses + functions
- JSON storage — no database dependencies until needed
- Works offline (scoring + focus are rule-based by default, LLM is optional)

---

## Signal Matching Engine (V1)

SimpliXio now treats each capture as a **signal**, not a loose note.

### Backend-first architecture

- Ingestion: `CortexEngine.capture_signal()` and `SignalMatcher.ingest()`
- Normalization: deterministic metadata inference in `cortex_core/signal_matching.py`
- Scoring: explicit inspectable score bundle per signal
- Ranking: `build_ranked_output()` returns all product surfaces
- Feedback: `apply_feedback()` updates score behavior loops
- Human override: `apply_override()` supports pin/snooze/irrelevant/convert
- Persistence: JSON files in `data_dir` (`signal_events`, `signal_records`, `signal_feedback`, `signal_overrides`, `signal_links`)
- Distribution: embedded in `/sync/snapshot` + context signal endpoints

### Core entities

- `SignalEvent`: raw capture event (`source`, `source_id`, timestamp, text, project, tags)
- `SignalRecord`: normalized signal + inferred attributes + score bundle + status
- `FeedbackEvent`: user behavior (`acted_on`, `ignored`, `snoozed`, etc.)
- `OverrideEvent`: manual override actions (`pin`, `snooze`, `convert_to_decision`, etc.)

### Deterministic metadata inferred per signal

- Type: thought / decision / task / question / tension / reflection / idea / content_seed
- Topics/tags
- Linked project
- Emotional tone
- Clarity / ambiguity
- Actionability
- Decision readiness
- Recurrence likelihood
- Dependencies
- Contradiction flag
- Sensitivity class: private / sensitive / internal / public_safe / public_ready

### Score model (0-100)

- Importance Score
- Clarity Score
- Decision Readiness Score
- Action Readiness Score
- Recurrence Score
- Emotional Intensity Score
- Publishability Score
- Staleness Score

Score inputs are explicit: recency decay, source weighting, recurrence boosts, dependency penalties, ambiguity penalties, sensitivity constraints.

### Ranking model

- Global rank score (weighted):
  - importance (40%)
  - action readiness (25%)
  - decision readiness (20%)
  - recurrence (10%)
  - staleness penalty (-5%)
- Behavior modifiers:
  - acted_on boost
  - reopened boost
  - ignored penalty
  - snoozed penalty
  - marked_irrelevant hard penalty
  - contradiction penalty
  - unresolved tension boost

### Readiness model

- `decision_readiness` and `action_readiness` are deterministic heuristic scores
- Inputs: clarity, ambiguity, dependencies, recurrence, action verbs, recency
- Designed for inspectability first (no opaque model dependency in v1)

### Time horizons

- `now`, `today`, `this_week`, `later`
- Derived from rank + readiness + status overrides

### Product surfaces powered by ranking

- Top 3 priorities (`signal_top_priorities`)
- What matters now (`what_matters_now`)
- Decision queue (`decision_queue`)
- Action-ready queue (`action_ready_queue`)
- Recurring patterns (`recurring_patterns`)
- Unresolved tensions (`unresolved_tensions`)
- Content candidates (`content_candidates`)
- Signal graph (`signal_graph`)

### Calm queue defaults (V1)

- `what_matters_now`: max 3
- `decision_queue`: max 5
- `action_ready_queue`: max 5
- `recurring_patterns`: max 5
- `unresolved_tensions`: max 5
- `content_candidates`: max 5

These limits are enforced in backend ranking output to keep default surfaces curated.

### Explainability contract

Each ranked item includes:

- why it surfaced
- top contributors
- lowered confidence factors
- missing items before readiness improves
- rank score

### Privacy and publishability guardrails

- Sensitivity labels are assigned at ingestion time.
- Content candidates require public-safe/public-ready sensitivity plus publishability threshold.
- Private/internal signals are not automatically surfaced as publish candidates.

### Platform mapping

- iPhone: top priorities, quick capture, compact replay
- macOS: deep workbench (queues, replay, weekly review, newsletter)
- Watch: thin decision glance (top priority, next action, capture, feedback)

### Current implementation milestone (V1)

- Deterministic ingest → normalize → score → rank loop
- Snapshot integration and API routes
- Basic feedback loop and manual overrides
- Lightweight graph relationships

### Intentionally postponed (V2+)

- Richer graph clustering and contradiction reasoning
- Stronger probabilistic readiness model
- Advanced personalization over long behavioral history
- Complex timeline explainability UI
