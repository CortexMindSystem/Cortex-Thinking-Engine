# SimpliXio

*SimpliXio turns scattered thoughts, project noise, and open loops into 3 priorities and one next action.*

![SimpliXio product system](logo.png)

> [!Note]
> Built for founders and builders with too many inputs and not enough clarity.
> SimpliXio answers one daily question: **"What matters now, and what should I do next?"**

## Why SimpliXio

- You capture messy thoughts quickly.
- SimpliXio filters noise into 3 priorities.
- Each priority includes why it matters.
- You get one clear next action.

SimpliXio is not a note backlog, task manager, CRM, ATS, or chatbot. It is the daily decision layer that reduces scattered inputs into what matters now.

## Product Flow

```text
capture -> enrich -> rank -> surface -> act -> review -> learn
```

The visible product stays simple:
- What matters now
- 3 priorities
- Why they matter
- One next action
- Feedback that improves future ranking

## Trust

- Private by default.
- Public content runs through redaction and quality checks.
- Private outreach stays `needs_approval` by default.
- Human judgement stays in control.
- Discord, newsletter, and acquisition outputs are draft-first unless explicitly approved.

---

## Install

**Requirements:** Python 3.11+, macOS 14+ / iOS 17+ (native apps), Xcode 15+ (Swift)

```bash
git clone https://github.com/SimplixioMindSystem/Thinking-Engine.git
cd Thinking-Engine
make install
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/python -m cortex_core pipeline
.venv/bin/python -m cortex_core serve
```

Native app (iOS + macOS + watchOS):

```bash
brew install xcodegen
./generate_xcode_project.sh
open CortexOSApp/CortexOS.xcodeproj
```

Leave server URL empty in Settings to run fully offline.

## API

Server runs on port `8420`.

- `GET /sync/today`: Canonical **SimpliXio Today** output (3 priorities + why + action + ignored)
- `GET /sync/snapshot`: Single-call snapshot for offline-first client hydration
- `POST /integrations/pull`: Pull context from RSS / GitHub / Notion
- `POST /context/signals/capture`: Capture one raw signal into deterministic ranking
- `GET /context/signals/queues`: Ranked queues (`what_matters_now`, decision queue, action-ready queue)

System architecture and scoring model:
- [cortex_os_system.md](cortex_os_system.md)

## TestFlight

```bash
cd CortexOSApp
fastlane ios testflight_release
fastlane mac testflight_release
fastlane watch_testflight
fastlane all_testflight
```

## Growth Automation

```bash
.venv/bin/python scripts/cortex_growth_loop.py
cd cortexos_automation_scripts
python3 scripts/run_weekly_pipeline.py --strict-quality
python3 scripts/run_acquisition_pipeline.py --mode daily --strict-quality
python3 scripts/run_acquisition_pipeline.py --mode weekly --strict-quality
```

What these automation pipelines do:
- Weekly marketing pipeline: builds Today/Weekly Review/Decision Replay/newsletter artifacts from real product output, drafts posts, runs quality gate, and only queues publish when safe flags are enabled.
- Daily acquisition pipeline: collects public lead signals, scores fit, drafts outreach (approval-required), runs compliance checks, and writes CRM logs/summaries.

Detailed runbook:
- [cortexos_automation_scripts/README.md](cortexos_automation_scripts/README.md)
- [cortexos_automation_scripts/AUTOMATION_RUNBOOK.md](cortexos_automation_scripts/AUTOMATION_RUNBOOK.md)

Positioning + trust playbooks:
- [docs/messaging-stack.md](docs/messaging-stack.md)
- [docs/integrated-product-system-2026-04-30.md](docs/integrated-product-system-2026-04-30.md)
- [docs/values-alignment-plan-2026-04-29.md](docs/values-alignment-plan-2026-04-29.md)
- [docs/reorg-plan-2026-04-29.md](docs/reorg-plan-2026-04-29.md)

## Tests

```bash
make test
make test-python
make test-swift
```
