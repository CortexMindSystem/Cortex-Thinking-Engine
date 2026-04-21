# SimpliXio Automation (Monorepo)

This folder is the automation engine for marketing + weekly learning loops.
It now also includes acquisition research + drafting automation with compliance gates.

It is monorepo-aware:
- reads source data from the main repo (`../growth_output`, `../weekly_digest_*.md`)
- writes automation artifacts to `cortexos_automation_scripts/output/`

## Structure

```text
cortexos_automation_scripts/
  marketing_automation.py
  scripts/
    filter_signals.py
    build_cortex_today.py
    build_weekly_review.py
    build_decision_replay.py
    marketing_quality_gate.py
    publish_outputs.py
    run_weekly_pipeline.py
    acquisition_crm.py
    lead_collector.py
    lead_scorer.py
    outreach_drafter.py
    content_engine.py
    acquisition_quality_gate.py
    run_acquisition_pipeline.py
  output/
    cortex_today/
      cortex_today.json
      cortex_today.md
      cortex_today.html
      archive/
    filtered_signals/
    weekly_review/
      latest.json
      latest.md
      latest.html
      archive/
    decision_replay/
      latest.json
      latest.md
      latest.html
      archive/
    drafts/
    quality_gate/
    logs/
```

## Local setup

```bash
cd cortexos_automation_scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Daily run order (artifact-first)

```bash
python3 scripts/filter_signals.py
python3 scripts/build_cortex_today.py
python3 scripts/build_weekly_review.py
python3 scripts/build_decision_replay.py
python3 marketing_automation.py
python3 scripts/marketing_quality_gate.py --strict
python3 scripts/publish_outputs.py
```

## Weekly pipeline

```bash
python3 scripts/run_weekly_pipeline.py --strict-quality
```

## Fastest way (recommended)

From repo root (`/Users/pierre/Code/CortexOSLLM`), use the Makefile wrappers:

```bash
make autopilot-weekly
make autopilot-acq-daily
make autopilot-acq-weekly
make autopilot-all
```

Why this helps:
- avoids forgetting command order
- keeps strict quality checks on by default
- reduces copy/paste mistakes during releases

Canonical runbook:
- `/Users/pierre/Code/CortexOSLLM/cortexos_automation_scripts/AUTOMATION_RUNBOOK.md`

The pipeline writes:
- JSON run log: `output/logs/weekly-pipeline-*.json`
- Markdown summary: `output/summaries/weekly-pipeline-*.md`

## Acquisition automation

Daily:

```bash
python3 scripts/run_acquisition_pipeline.py --mode daily --strict-quality
```

Weekly:

```bash
python3 scripts/run_acquisition_pipeline.py --mode weekly
```

Acquisition outputs:
- SQLite CRM: `output/acquisition/acquisition.sqlite3`
- Raw lead signals: `output/acquisition/raw/lead_signals_*.json`
- Lead shortlist: `output/acquisition/drafts/latest_lead_shortlist.md`
- Outreach drafts: `output/acquisition/drafts/latest_outreach.md`
- Acquisition quality report: `output/acquisition/quality_report.json`
- Pipeline logs: `output/acquisition/logs/acquisition-*.json`
- Pipeline summaries: `output/acquisition/summaries/acquisition-*.md`

Lead scoring tiers:
- `fit`: high-confidence prospect, drafted for manual approval
- `candidate`: near-threshold prospect, held for manual review (not drafted automatically)
- `not_fit`: archived for now

Safety defaults:
- private outreach is always saved as `needs_approval`
- no LinkedIn scraping
- no outbound sending in these scripts
- public publish queue requires `PUBLISH_PUBLIC=true` and quality pass

## Notes

- `build_cortex_today.py` uses the latest `../growth_output/*/(ready_to_publish|pending_approval).json` as primary source.
- If growth output is missing, it attempts one fallback run of `../scripts/cortex_growth_loop.py`.
- `marketing_automation.py` generates drafts and artifacts only.
- `publish_outputs.py` is safe by default (`PUBLISH_DRY_RUN=true`), and updates content memory only when quality passes.
