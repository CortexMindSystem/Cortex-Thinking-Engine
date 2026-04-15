# CortexOS Automation (Monorepo)

This folder is the automation engine for marketing + weekly learning loops.

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
    marketing_quality_gate.py
    build_weekly_review.py
    run_weekly_pipeline.py
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

## Daily run order

```bash
python3 scripts/filter_signals.py
python3 scripts/build_cortex_today.py
python3 marketing_automation.py
python3 scripts/marketing_quality_gate.py --strict
python3 scripts/build_weekly_review.py
```

## Weekly pipeline

```bash
python3 scripts/run_weekly_pipeline.py --strict-quality
```

## Notes

- `build_cortex_today.py` uses the latest `../growth_output/*/(ready_to_publish|pending_approval).json` as primary source.
- If growth output is missing, it attempts one fallback run of `../scripts/cortex_growth_loop.py`.
- Social publish in `marketing_automation.py` is gated by `quality_report.json` when present.
