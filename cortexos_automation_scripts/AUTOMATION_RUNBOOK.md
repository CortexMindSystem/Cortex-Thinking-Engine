# SimpliXio Automation Runbook

Use this file as the single source of truth for growth automation runs.

## Safe Defaults

- Private outreach is draft-only (`needs_approval`).
- Public posting is disabled unless publish flags are explicitly enabled.
- Quality gates run before publish steps.

## Daily Commands

Run from repo root:

```bash
make autopilot-acq-daily
```

Direct command:

```bash
cd cortexos_automation_scripts
python3 scripts/run_acquisition_pipeline.py --mode daily --strict-quality
```

Outputs:

- JSON log: `output/acquisition/logs/`
- Markdown summary: `output/acquisition/summaries/`
- Lead shortlist: `output/acquisition/drafts/latest_lead_shortlist.md`
- Outreach drafts: `output/acquisition/drafts/latest_outreach.md`

## Weekly Commands

Run full marketing + acquisition weekly review:

```bash
make autopilot-all
```

Or run individually:

```bash
make autopilot-weekly
make autopilot-acq-weekly
```

## Publish Safety

Publishing remains opt-in.

Required env flags for public queueing:

- `PUBLISH_PUBLIC=true`
- `PUBLISH_DRY_RUN=false`

Optional channel toggles:

- `PUBLISH_X=true`
- `PUBLISH_LINKEDIN=true`

If quality fails, publish is skipped automatically.

## Recommended Cron

From repo root, daily at 8:00 and weekly on Monday at 9:00:

```cron
0 8 * * * cd /Users/pierre/Code/CortexOSLLM && make autopilot-acq-daily
0 9 * * 1 cd /Users/pierre/Code/CortexOSLLM && make autopilot-all
```

## Compliance Rules

- Do not scrape LinkedIn.
- Do not auto-send private outreach.
- Keep private outreach in `needs_approval` until manual approval.
- Do not claim traction/revenue/users unless verified in source artifacts.
