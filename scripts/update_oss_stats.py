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

tracking_since = history[0]["date"]
cumulative_usage_events = sum(
    item.get("total_14d_unique_clones", 0) for item in history
)

annual_usage_events = current["total_14d_unique_clones"] * 26

repo_lines = "\n".join(
    f"- `{repo}`: {stats['unique_clones']} unique clones / 14 days"
    for repo, stats in current["repos"].items()
)

block = f"""<!-- OSS-STATS:START -->
### Open-source tool usage

- **Unique clones, latest 14-day GitHub traffic window:** {current["total_14d_unique_clones"]}+
- **Estimated annual usage events:** ~{annual_usage_events}
- **Cumulative usage events since {tracking_since}:** {cumulative_usage_events}+
- **Tracked repositories:** {len(REPOS)}
- **Last updated:** {today}

Repository breakdown:

{repo_lines}

_Note: GitHub traffic data is available as a rolling 14-day window. “Usage events” are estimated from unique clone counts and are not equivalent to globally deduplicated users._
<!-- OSS-STATS:END -->"""

text = README.read_text(encoding="utf-8")

start_marker = "<!-- OSS-STATS:START -->"
end_marker = "<!-- OSS-STATS:END -->"

if start_marker in text and end_marker in text:
    start = text.index(start_marker)
    end = text.index(end_marker) + len(end_marker)
    new_text = text[:start] + block + text[end:]
else:
    # 如果找不到，就直接 append（防止报错）
    new_text = text + "\n\n" + block

README.write_text(new_text, encoding="utf-8")