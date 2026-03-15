import json

with open("knowledge_notes.json") as f:
    notes = json.load(f)

posts = []

for note in notes[:3]:
    post = f"""
Insight from my CortexOS research:

{note["title"]}

Key idea:
{note["insight"]}

Action:
{note["action"]}

Building an AI context engine for developers.
"""
    posts.append(post.strip())

with open("posts_today.txt", "w") as f:
    f.write("\n\n---\n\n".join(posts))

print("Posts generated.")
