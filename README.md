# CortexOS — Your Thinking Engine

### _A context, memory, and prioritisation engine for ambitious builders and AI agents_

![CortexOS Mind System](logo.png)

> [!Note]
> CortexOS turns scattered inputs (RSS feeds, notes, digests) into grounded daily actions — answering **"What should I focus on today?"** using your personal goals, projects, and reading history as context. Works fully offline; LLM is optional.

---

## Install

**Requirements:** Python 3.11+, macOS 14+ / iOS 17+ (native apps), Xcode 15+ (Swift)

```bash
git clone git@github.com:CortexMindSystem/Cortex-Thinking-Engine.git
cd Cortex-Thinking-Engine
make install        # creates .venv and installs deps
```

Or manually:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

```bash
# Run the full pipeline (ingest → score → focus brief)
.venv/bin/python -m cortex_core pipeline

# Start the API server (http://localhost:8420, docs at /docs)
.venv/bin/python -m cortex_core serve

# Other CLI commands
.venv/bin/python -m cortex_core status     # system info
.venv/bin/python -m cortex_core notes      # list knowledge notes
.venv/bin/python -m cortex_core pipeline --llm  # LLM-enhanced summaries
```

**Native app (iOS + macOS):**
```bash
brew install xcodegen
./generate_xcode_project.sh
open CortexOSApp/CortexOS.xcodeproj
# Requires the API server to be running
```

---

## What Makes It Work

| Feature | Detail |
|---------|--------|
| **4-Layer Memory** | Identity → Project → Research → Working memory persist your full context |
| **4-Dimension Scoring** | `project_relevance`, `ai_relevance`, `novelty`, `actionability` per article |
| **Focus Brief** | Ranked daily items with *why it matters* + *next action*, shaped by your profile |
| **Signal Detection** | Emerging topics appearing across multiple sources are surfaced automatically |
| **Decision Engine** | Priorities, what to ignore, what changed since yesterday |
| **Hybrid Retrieval** | Metadata filters → keyword match → recency weighting |
| **Self-Improvement** | Reading history enriches context → scoring improves over time |
| **Why Engine** | Per-item evaluation: why it matters, project impact, contradiction detection, recommended action |
| **Offline-First** | All scoring and focus generation are rule-based; no API key required |
| **Spaced Repetition** | Leitner-style review intervals (1, 3, 7, 14, 30 days) |

---

## API

Server runs on **port 8420**. Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/focus/today` | Today's focus brief |
| `POST` | `/focus/generate` | Generate a new focus brief |
| `GET/PATCH` | `/profile/` | View or update user profile |
| `POST` | `/digest/evaluate` | Score a digest against your context |
| `GET` | `/notes/` | List / search knowledge notes |
| `POST` | `/pipeline/run` | Run the full pipeline |
| `GET` | `/context/goals` | Active goals (agent context API) |
| `GET` | `/context/signals` | Detected signals |
| `POST` | `/context/retrieve` | Hybrid search across notes + insights |
| `POST` | `/why/evaluate` | Per-item decision: why it matters, impact, action, ignore/watch |

Full interactive docs at **http://localhost:8420/docs**.

---

## LLM (Optional)

```bash
export OPENAI_API_KEY="sk-..."      # or ANTHROPIC_API_KEY
```

Configure model in `~/.cortexos/config.json`:
```json
{ "llm": { "provider": "openai", "model": "gpt-4o", "temperature": 0.4 } }
```

---

## Deploy to TestFlight

Requires [Fastlane](https://fastlane.tools) and an App Store Connect API key (`.p8`).

```bash
cd CortexOSApp
fastlane ios testflight_release   # iOS
fastlane mac testflight_release   # macOS
fastlane all_testflight           # both
```

---

## Tests

```bash
make test          # all Python + Swift tests
make test-python   # Python only (276 tests)
make test-swift    # Swift only (47 tests)
make lint          # ruff + security
```

---

## 👨‍🍳 The Cook

Designed & coded with passion by **[Pierre-Henry Soria](https://ph7.me)** — a SUPER passionate Belgian Software Engineer 🍫🍺

[![Pierre-Henry Soria](https://avatars0.githubusercontent.com/u/1325411?s=200)](https://pierrehenry.be "My personal website")

[![@phenrysay](https://img.shields.io/badge/x-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/phenrysay "Follow Me on X")
[![BlueSky](https://img.shields.io/badge/BlueSky-000000?style=for-the-badge&logo=bluesky&logoColor=white)](https://bsky.app/profile/pierrehenry.dev "Follow Me on BlueSky")
[![pH-7](https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pH-7 "Follow Me on GitHub")
[![LinkedIn](https://img.shields.io/badge/LinkedIn-000000?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ph7enry/ "Pierre-Henry Soria on LinkedIn")

Open to exciting opportunities — **[let's chat](https://www.linkedin.com/in/ph7enry/)**.

