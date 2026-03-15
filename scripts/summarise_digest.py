import json
import re
from pathlib import Path

INPUT = sorted(Path(".").glob("weekly_digest_*.md"))[-1]

ARTICLE_PATTERN = re.compile(r"- \[(.*?)\]\((.*?)\)")


def extract_articles(text):
    return ARTICLE_PATTERN.findall(text)


def summarise(title):
    return {
        "title": title,
        "insight": f"{title} highlights a key shift in AI or technology.",
        "implication": "Investigate how this affects CortexOS context ranking.",
        "action": "Add note to research backlog.",
    }


with open(INPUT) as f:
    text = f.read()

articles = extract_articles(text)

notes = [summarise(title) for title, _ in articles]

with open("knowledge_notes.json", "w") as f:
    json.dump(notes, f, indent=2)

print(f"Generated {len(notes)} knowledge notes.")
