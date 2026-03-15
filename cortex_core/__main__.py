"""
CortexOS CLI
-------------
Quick command-line interface for common operations.
Run: python -m cortex_core [command]
"""

import argparse
import json


def cmd_serve(args):
    """Start the API server."""
    import uvicorn

    from cortex_core.config import CortexConfig

    config = CortexConfig.load()
    print(f"🧠 Starting CortexOS API on http://{config.api_host}:{config.api_port}")
    print(f"📖 Docs: http://localhost:{config.api_port}/docs")
    uvicorn.run(
        "cortex_core.api.server:app",
        host=config.api_host,
        port=config.api_port,
        reload=args.reload,
    )


def cmd_pipeline(args):
    """Run the full pipeline."""
    from cortex_core.engine import CortexEngine

    engine = CortexEngine()
    result = engine.run_pipeline(use_llm=args.llm)
    print(json.dumps(result, indent=2))


def cmd_notes(args):
    """List knowledge notes."""
    from cortex_core.engine import CortexEngine

    engine = CortexEngine()
    notes = engine.list_notes()
    for n in notes:
        print(f"  [{n['id']}] {n['title']}")
        if n.get("insight"):
            print(f"           {n['insight'][:80]}")
    print(f"\n  Total: {len(notes)} notes")


def cmd_status(args):
    """Show system status."""
    from cortex_core.engine import CortexEngine

    engine = CortexEngine()
    status = engine.status()
    print(json.dumps(status, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="cortexos",
        description="CortexOS – Your operating system for thinking",
    )
    sub = parser.add_subparsers(dest="command")

    # serve
    p_serve = sub.add_parser("serve", help="Start the API server")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload")
    p_serve.set_defaults(func=cmd_serve)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Run the full pipeline")
    p_pipe.add_argument("--llm", action="store_true", help="Use LLM for processing")
    p_pipe.set_defaults(func=cmd_pipeline)

    # notes
    p_notes = sub.add_parser("notes", help="List knowledge notes")
    p_notes.set_defaults(func=cmd_notes)

    # status
    p_status = sub.add_parser("status", help="Show system status")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
