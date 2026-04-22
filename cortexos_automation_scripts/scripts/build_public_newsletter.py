#!/usr/bin/env python3
"""Compatibility wrapper for newsletter generation.

Use `generate_newsletter.py` for new behavior. This file is kept so existing
pipeline commands and external scripts continue to work.
"""

from __future__ import annotations

import json

from generate_newsletter import run_legacy


def run(days: int = 7) -> dict:
    return run_legacy(days=days)


def main() -> None:
    print(json.dumps(run(days=7), indent=2))


if __name__ == "__main__":
    main()
