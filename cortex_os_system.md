# CortexOS System Document

> A context engine for AI-native work. Turns scattered inputs into grounded, actionable focus briefs.

## Architecture

CortexOS is a three-tier system:
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
