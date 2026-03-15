#!/usr/bin/env python3

import datetime
import subprocess

STEPS = [
    ("Generate digest", "python3 weekly_digest.py"),
    ("Evaluate digest", "python3 Evaluate-AI-responses.py"),
    ("Generate summaries", "python3 summarise_digest.py"),
    ("Generate social posts", "python3 generate_posts.py"),
]


def run_step(name, command):
    print(f"\n--- {name} ---")
    subprocess.run(command, shell=True)


def main():
    today = datetime.date.today()
    print(f"CortexOS Daily Pipeline — {today}")

    for name, command in STEPS:
        run_step(name, command)

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
