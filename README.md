# SimpliXio

Decide what matters.

Most tools add information.  
SimpliXio removes noise:

- what matters
- why
- what to do

3 priorities. Clear action.

Not another AI app.  
A layer between information, decision, and execution.

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
```

## Tests

```bash
make test
make test-python
make test-swift
```
