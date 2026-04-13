# CortexOS Backend (Railway)

## Quick Deploy

From the repository root:

```bash
cd /path/to/CortexOSLLM
railway login
railway init
railway up
```

This backend is deployed with:
- `Dockerfile` (root)
- `railway.toml` (root)

Railway injects `PORT`; container startup already uses it:

```bash
uvicorn cortex_core.api.server:app --host 0.0.0.0 --port ${PORT:-8420}
```

## Verify After Deploy

Replace `<your-railway-domain>` with your Railway URL:

```bash
curl https://<your-railway-domain>/health
```

Expected response includes:
- `status: "ok"`
- `timestamp`

## Notes

- Data is stored in container home (`~/.cortexos`) and is ephemeral unless you attach a Railway volume.
- CORS is currently open (`allow_origins=["*"]`) in `cortex_core/api/server.py`.
