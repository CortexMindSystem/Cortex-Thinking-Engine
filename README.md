# CortexOS — Thinking Engine

## Your operating system for thinking

_CortexOS helps ambitious builders think faster by turning personal context into useful output._

> [!Note]
> CortexOS is a context engine for AI-native work. A simple engine for knowledge workers and engineers that turns scattered inputs into grounded actions. The primary feature: **"What should I focus on today?"**

---

## 🏗️ Architecture

CortexOS is a **three-tier system** with a focus-first pipeline:

```
RSS Feeds ─► Ingestion ─► Scoring ─► Context Memory ─► Focus Engine
                                          │
                                    User Profile
                                    (goals, interests,
                                     projects, constraints)

┌─────────────────────────────────┐
│   iOS App  ·  macOS App         │  SwiftUI (shared codebase)
│   Focus · Digest · Knowledge    │
└───────────────┬─────────────────┘
                │ REST API (JSON)
┌───────────────▼─────────────────┐
│   FastAPI Server (port 8420)    │  cortex_core/api/
│   /focus  /profile  /digest     │
│   /notes  /posts  /pipeline     │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────┐
│   Python Core Framework         │  cortex_core/
│   Engine · Focus · Memory       │
│   Scoring · Digest · Knowledge  │
│   Posts · Pipeline · LLM        │
└─────────────────────────────────┘
```

### Core Pipeline

```
RSS Feeds (weekly_digest.py)
    ↓
Digest (Markdown)
    ↓
DigestProcessor → KnowledgeStore (JSON, deduplicated)
    ↓
ScoringEngine (scoring.py)
    ↓  ai_article_ratio, high_signal_ratio, signal_to_noise_ratio,
    ↓  context_keyword_coverage, project_fit_score
    ↓
ContextMemory (memory.py)
    ↓  UserProfile: goals, interests, current_projects, constraints
    ↓  ReadingHistory: what was read, insights, spaced repetition
    ↓
FocusEngine (focus.py)
    ↓  "What should I focus on today?"
    ↓  Ranked FocusItems with why_it_matters + next_action
    ↓
DailyBrief → REST API → iOS / macOS App
    ↓
PostGenerator → Social Posts (optional)
```

### Self-Improvement Loop

CortexOS learns from your activity through a feedback cycle:

1. **Profile** — set goals, interests, projects, constraints
2. **Context** — profile is tokenised into searchable context snippets
3. **Evaluate** — digest articles are scored against your context
4. **Focus** — top articles become actionable focus items
5. **Learn** — marking items as read enriches context for future scoring
6. **Review** — spaced repetition (1, 3, 7, 14, 30 day intervals) resurfaces key insights

---

## 📂 Project Structure

```
CortexOSLLM/
├── cortex_core/                 # 🐍 Python core framework
│   ├── __init__.py
│   ├── __main__.py              # CLI entrypoint
│   ├── engine.py                # Central orchestrator
│   ├── focus.py                 # Daily focus brief generator
│   ├── memory.py                # User profile, context memory & spaced repetition
│   ├── scoring.py               # Article & digest quality scoring
│   ├── knowledge.py             # Knowledge note CRUD, search & deduplication
│   ├── pipeline.py              # Step-based pipeline runner
│   ├── digest.py                # Digest → knowledge notes (with tag inference)
│   ├── posts.py                 # Social post generator
│   ├── llm.py                   # LLM provider abstraction
│   ├── config.py                # Runtime configuration
│   └── api/                     # FastAPI REST server
│       ├── server.py
│       ├── models.py
│       └── routes/
│           ├── health.py
│           ├── focus.py         # GET /focus/today, POST /focus/generate
│           ├── profile.py       # GET/PATCH /profile
│           ├── digest.py        # POST /digest/evaluate
│           ├── knowledge.py
│           ├── pipeline.py
│           └── posts.py
│
├── CortexOSApp/                 # 📱 SwiftUI multiplatform app
│   ├── Shared/                  # Shared iOS + macOS code
│   │   ├── CortexOSApp.swift    # @main entry point
│   │   ├── Models/
│   │   │   ├── FocusBrief.swift       # Focus items & daily brief
│   │   │   ├── UserProfile.swift      # User context profile
│   │   │   ├── DigestScore.swift      # Digest evaluation metrics
│   │   │   ├── KnowledgeNote.swift
│   │   │   ├── PipelineStatus.swift
│   │   │   ├── SocialPost.swift
│   │   │   └── ServerStatus.swift
│   │   ├── Services/
│   │   │   ├── APIService.swift       # Networking layer
│   │   │   └── CortexEngine.swift     # Observable state
│   │   ├── Views/
│   │   │   ├── ContentView.swift      # Root navigation (focus-first)
│   │   │   ├── FocusView.swift        # ★ PRIMARY — daily brief
│   │   │   ├── ProfileView.swift      # Edit goals & interests
│   │   │   ├── DigestView.swift       # Digest quality metrics
│   │   │   ├── DashboardView.swift    # Overview & stats
│   │   │   ├── KnowledgeListView.swift
│   │   │   ├── PipelineView.swift
│   │   │   ├── PostsView.swift
│   │   │   └── SettingsView.swift
│   │   └── Assets.xcassets/
│   ├── iOS/Info.plist
│   └── macOS/
│       ├── Info.plist
│       └── CortexOS.entitlements
│
├── tests/                       # 🧪 Python test suite (155 tests)
│   ├── conftest.py              # Shared fixtures
│   ├── test_integration.py      # End-to-end self-improvement loop
│   ├── test_engine.py
│   ├── test_focus.py
│   ├── test_memory.py
│   ├── test_scoring.py
│   ├── test_knowledge.py
│   ├── test_pipeline.py
│   ├── test_config.py
│   └── test_api.py
│
├── Tests/                       # 🧪 Swift test suite (47 tests)
│   └── CortexOSKitTests/
│       ├── ModelDecodingTests.swift
│       ├── PipelineModelTests.swift
│       └── APIServiceTests.swift
│
├── scripts/                     # 🔧 Pipeline & utility scripts
│   ├── weekly_digest.py         # RSS feed ingestion
│   ├── Evaluate-AI-responses.py # Digest quality evaluator
│   ├── cortex_pipeline.py       # Full pipeline runner
│   ├── summarise_digest.py      # Digest summarisation
│   ├── generate_posts.py        # Social post generator
│   ├── test_full_loop.py        # Self-improvement loop validator (34 checks)
│   └── generate_coupons.py
│
├── .github/workflows/           # CI/CD
│   ├── python.yml               # Lint + security + tests (Python 3.11-3.13)
│   └── swift.yml                # Build + test (macOS, SwiftPM)
│
├── requirements.txt
├── pyproject.toml               # Ruff configuration
├── pytest.ini
├── Makefile                     # Dev commands: make install, make test, etc.
├── setup.py
├── Package.swift                # SwiftPM package definition
└── generate_xcode_project.sh    # Xcode project generator
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.13 recommended)
- macOS 14+ / iOS 17+ (for the native apps)
- Xcode 15+ (for Swift development)

### 1. Install & Setup

```bash
# Clone the repository
git clone git@github.com:CortexMindSystem/Cortex-Thinking-Engine.git
cd Cortex-Thinking-Engine

# Set up Python environment
make install
# or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
# Generate a weekly digest from RSS feeds
.venv/bin/python scripts/weekly_digest.py

# Copy digest to data directory
cp weekly_digest_*.md ~/.cortexos/

# Run the full CortexOS pipeline
.venv/bin/python -m cortex_core pipeline
```

### 3. CLI Commands

```bash
.venv/bin/python -m cortex_core status      # Show system info
.venv/bin/python -m cortex_core notes       # List knowledge notes
.venv/bin/python -m cortex_core pipeline    # Run the full pipeline
.venv/bin/python -m cortex_core pipeline --llm  # With LLM-powered summaries
```

### 4. API Server

```bash
# Start the server
.venv/bin/python -m cortex_core serve

# Or with auto-reload during development
.venv/bin/python -m cortex_core serve --reload
```

The API is available at **http://localhost:8420** with interactive docs at **/docs**.

### 5. iOS & macOS App

```bash
# Option A: Using xcodegen (recommended)
brew install xcodegen
./generate_xcode_project.sh
open CortexOSApp/CortexOS.xcodeproj

# Option B: Manual Xcode setup
# Open Xcode → New Multiplatform App → drag Shared/ folder in
```

> Make sure the Python API server is running before launching the app.

### 6. Validate the Self-Improvement Loop

```bash
# Run the 34-check end-to-end validator
.venv/bin/python scripts/test_full_loop.py
```

This tests: profile setup → context enrichment → digest evaluation → focus generation → learning → spaced repetition → deduplication.

---

## 🧪 Testing

```bash
# Run all Python tests (155 tests)
make test-python

# Run all Swift tests (47 tests)
make test-swift

# Run everything
make test

# Lint & security
make lint
make security

# All Makefile targets
make help
```

---

## 🔌 API Endpoints

| Method   | Endpoint              | Description                        |
|----------|-----------------------|------------------------------------|
| `GET`    | `/health`             | Health check                       |
| `GET`    | `/status`             | System status & config             |
| **`GET`**| **`/focus/today`**    | **Today's focus brief**            |
| **`POST`**| **`/focus/generate`**| **Generate a new focus brief**     |
| `GET`    | `/profile/`           | Get user profile                   |
| `PATCH`  | `/profile/`           | Update profile fields              |
| `POST`   | `/digest/evaluate`    | Evaluate digest quality            |
| `GET`    | `/notes/`             | List all knowledge notes           |
| `GET`    | `/notes/search?q=`    | Search notes                       |
| `POST`   | `/notes/`             | Create a note                      |
| `PATCH`  | `/notes/{id}`         | Update a note                      |
| `DELETE` | `/notes/{id}`         | Delete a note                      |
| `POST`   | `/posts/generate`     | Generate social posts              |
| `POST`   | `/posts/export`       | Export posts to file               |
| `POST`   | `/pipeline/run`       | Run the full pipeline              |
| `POST`   | `/pipeline/digest`    | Process a digest file              |
| `GET`    | `/pipeline/steps`     | List pipeline step names           |

---

## 🧠 Key Features

| Feature | Description |
|---------|-------------|
| **Focus Brief** | Ranked daily recommendations with "why it matters" + "next action" |
| **Context Memory** | User profile (goals, interests, projects) shapes all scoring |
| **Digest Scoring** | AI relevance, signal-to-noise, context overlap, project fit |
| **Knowledge Deduplication** | Re-running the pipeline never creates duplicate notes |
| **Smart Tag Inference** | Articles auto-tagged (ai, agents, retrieval, health, safety, etc.) |
| **Spaced Repetition** | Leitner-style review intervals (1, 3, 7, 14, 30 days) |
| **Self-Improvement** | Reading history enriches context → better scoring over time |
| **Offline-First** | Scoring and focus are rule-based; LLM is optional enhancement |
| **Social Posts** | Generate platform-ready posts from knowledge notes |

---

## ⚙️ LLM Configuration

CortexOS supports **OpenAI** and **Anthropic** out of the box. Set your API key:

```bash
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

Configure in `~/.cortexos/config.json`:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.4
  }
}
```

> CortexOS works fully offline without an API key — scoring, focus, and tag inference are all rule-based by default. LLM mode enhances summaries and focus item descriptions.

---

## 📅 Weekly Operating Cadence

| Day       | Action                      |
|-----------|-----------------------------|
| Monday    | `weekly_digest.py` → ingest RSS feeds |
| Mon–Fri   | `python -m cortex_core pipeline` → daily focus brief |
| Wednesday | Review spaced repetition items |
| Friday    | `generate_posts.py` → export social content |
| Saturday  | Review knowledge store, archive stale notes |

---

## 👨‍🍳 The Cook

Designed & Coded with LOTS of PASSION by **[Pierre-Henry Soria](https://ph7.me)**. A **SUPER Passionate** Belgian Software Engineer 🍫🍺

[![Pierre-Henry Soria](https://avatars0.githubusercontent.com/u/1325411?s=200)](https://pierrehenry.be "My personal website :-)")

[![@phenrysay][x-badge]](https://x.com/phenrysay) [![BlueSky][bsky-badge]](https://bsky.app/profile/pierrehenry.dev "Follow Me on BlueSky") [![pH-7][github-badge]](https://github.com/pH-7) [![PayPal][paypal-badge]](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=X457W3L7DAPC6)


## 🤝 Hire Me At Your Startup?

Are you building a scalable social/dating Web application?

Do you think you might need a software engineer like me at your company? (who could even be willing to relocate) 👉 **[Let's chat together](https://www.linkedin.com/in/ph7enry/)**! 😊

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ph7enry/ "Pierre-Henry Soria LinkedIn")