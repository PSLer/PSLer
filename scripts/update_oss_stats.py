import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

USERNAME = "PSLer"

REPOS = [
    "3D-TSV",
    "TOP3D_XL",
    "SGLDBench",
    "PSLshell",
    "Infill_plus",
    "TopRank3",
    "MiniFEM",
]

README = Path("README.md")
HISTORY = Path("oss_traffic_history.json")

token = os.environ["GH_TRAFFIC_TOKEN"]

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

today = datetime.now(timezone.utc).date().isoformat()

current = {
    "date": today,
    "repos": {},
    "total_14d_clones": 0,
    "total_14d_unique_clones": 0,
}

for repo in REPOS:
    url = f"https://api.github.com/repos/{USERNAME}/{repo}/traffic/clones"
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    clones = data.get("count", 0)
    uniques = data.get("uniques", 0)

    current["repos"][repo] = {
        "clones": clones,
        "unique_clones": uniques,
    }

    current["total_14d_clones"] += clones
    current["total_14d_unique_clones"] += uniques

history = []
if HISTORY.exists():
    history = json.loads(HISTORY.read_text(encoding="utf-8"))

if not history or history[-1]["date"] != today:
    history.append(current)

HISTORY.write_text(json.dumps(history, indent=2), encoding="utf-8")

annual_estimate = current["total_14d_unique_clones"] * 26

repo_lines = "\n".join(
    f"- `{repo}`: {stats['unique_clones']} unique clones / 14 days"
    for repo, stats in current["repos"].items()
)

block = f"""<!-- OSS-STATS:START -->
Across my open-source research tools:

- **Unique clones, latest 14-day GitHub traffic window:** {current["total_14d_unique_clones"]}+
- **Estimated annual unique clones:** ~{annual_estimate}
- **Tracked repositories:** {len(REPOS)}
- **Last updated:** {today}

Repository breakdown:

{repo_lines}

These tools support structural optimization, stress tensor visualization, and lightweight computational mechanics workflows.
<!-- OSS-STATS:END -->"""

text = README.read_text(encoding="utf-8")

start_marker = "<!-- OSS-STATS:START -->"
end_marker = "<!-- OSS-STATS:END -->"

start = text.index(start_marker)
end = text.index(end_marker) + len(end_marker)

README.write_text(text[:start] + block + text[end:], encoding="utf-8")