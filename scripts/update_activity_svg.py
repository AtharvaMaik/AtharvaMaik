import base64
import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = os.environ.get("PROFILE_USERNAME", "AtharvaMaik")
OUTPUT_PATH = os.environ.get("ACTIVITY_SVG_PATH", "assets/activity-2026.svg")
TOKEN = os.environ["GITHUB_TOKEN"]
NOW = datetime.now(timezone.utc)
YEAR = int(os.environ.get("PROFILE_STATS_YEAR", NOW.year))
START = f"{YEAR}-01-01T00:00:00Z"
END = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY = NOW.strftime("%Y-%m-%d")

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
      }
    }
  }
}
"""


def graphql(query, variables):
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats-generator",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=2))
    return data["data"]


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


data = graphql(QUERY, {"login": USERNAME, "from": START, "to": END})
user = data["user"]
collection = user["contributionsCollection"]
calendar = collection["contributionCalendar"]
active_days = []
for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        if day["contributionCount"] > 0:
            active_days.append(day)

best_day = max(active_days, key=lambda day: day["contributionCount"], default={"date": "n/a", "contributionCount": 0})
stars = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
repos = user["repositories"]["totalCount"]
total = calendar["totalContributions"]
commits = collection["totalCommitContributions"]
repo_contribs = collection["totalRepositoryContributions"]
active = len(active_days)
best_date = best_day["date"]
best_count = best_day["contributionCount"]

bar_total = min(max(total / 100, 0.18), 1.0)
bar_commits = min(max(commits / 100, 0.18), 1.0)
bar_repo = min(max(repo_contribs / 25, 0.12), 1.0)

svg = f'''<svg width="900" height="360" viewBox="0 0 900 360" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{esc(USERNAME)} {YEAR} GitHub activity terminal</title>
  <desc id="desc">Animated terminal panel showing {total} total contributions, {commits} commits, {repo_contribs} repository contributions, {active} active days, best day {best_date} with {best_count} contributions, {repos} public repositories, and {stars} public stars.</desc>
  <defs>
    <linearGradient id="panel" x1="0" x2="900" y1="0" y2="360" gradientUnits="userSpaceOnUse">
      <stop stop-color="#00040b"/>
      <stop offset="0.52" stop-color="#020812"/>
      <stop offset="1" stop-color="#050b16"/>
    </linearGradient>
    <linearGradient id="line" x1="0" x2="1" y1="0" y2="0">
      <stop stop-color="#0e7490" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#14b8a6" stop-opacity="0.48"/>
      <stop offset="1" stop-color="#1d4ed8" stop-opacity="0"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.2" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }}
      .label {{ fill: #67e8f9; font-size: 15px; font-weight: 600; }}
      .value {{ fill: #f8fafc; font-size: 28px; font-weight: 800; }}
      .muted {{ fill: #7f8ea3; font-size: 13px; }}
      .prompt {{ fill: #2dd4bf; font-size: 15px; font-weight: 700; }}
      .cmd {{ fill: #cbd5e1; font-size: 15px; }}
      .scan {{ animation: scan 7.8s linear infinite; }}
      .pulse {{ animation: pulse 4.8s ease-in-out infinite; }}
      .blink {{ animation: blink 1.35s steps(2, start) infinite; }}
      .float1 {{ animation: float 9s ease-in-out infinite; }}
      .float2 {{ animation: float 10.5s ease-in-out infinite reverse; }}
      .draw {{ stroke-dasharray: 520; stroke-dashoffset: 520; animation: draw 8.5s ease-in-out infinite; }}
      .bar1 {{ animation: grow1 7.2s ease-in-out infinite; transform-origin: 154px 0; }}
      .bar2 {{ animation: grow2 7.2s ease-in-out infinite; transform-origin: 154px 0; }}
      .bar3 {{ animation: grow3 7.2s ease-in-out infinite; transform-origin: 154px 0; }}
      @keyframes scan {{ from {{ transform: translateY(-80px); opacity: .03; }} 35% {{ opacity: .32; }} to {{ transform: translateY(390px); opacity: .03; }} }}
      @keyframes pulse {{ 0%,100% {{ opacity: .68; }} 50% {{ opacity: .95; }} }}
      @keyframes blink {{ 0%,45% {{ opacity: 1; }} 46%,100% {{ opacity: 0; }} }}
      @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
      @keyframes draw {{ 0% {{ stroke-dashoffset: 520; opacity:.18; }} 45%,65% {{ stroke-dashoffset: 0; opacity:.82; }} 100% {{ stroke-dashoffset: -520; opacity:.18; }} }}
      @keyframes grow1 {{ 0%,100% {{ transform: scaleX(.18); }} 45%,70% {{ transform: scaleX({bar_total:.2f}); }} }}
      @keyframes grow2 {{ 0%,100% {{ transform: scaleX(.16); }} 45%,70% {{ transform: scaleX({bar_commits:.2f}); }} }}
      @keyframes grow3 {{ 0%,100% {{ transform: scaleX(.10); }} 45%,70% {{ transform: scaleX({bar_repo:.2f}); }} }}
    </style>
  </defs>

  <rect width="900" height="360" rx="18" fill="url(#panel)"/>
  <rect x="1" y="1" width="898" height="358" rx="17" stroke="#0f1a2a" stroke-width="2"/>
  <g opacity="0.11">
    <path d="M0 52H900M0 104H900M0 156H900M0 208H900M0 260H900M0 312H900" stroke="#155e75" stroke-width="0.6"/>
    <path d="M75 0V360M150 0V360M225 0V360M300 0V360M375 0V360M450 0V360M525 0V360M600 0V360M675 0V360M750 0V360M825 0V360" stroke="#115e59" stroke-width="0.45"/>
  </g>
  <rect class="scan" x="0" y="0" width="900" height="78" fill="url(#line)"/>

  <g transform="translate(26 22)">
    <rect width="848" height="316" rx="14" fill="#010711" stroke="#172033"/>
    <rect width="848" height="42" rx="14" fill="#040b16"/>
    <circle cx="24" cy="21" r="6" fill="#7f1d1d"/>
    <circle cx="45" cy="21" r="6" fill="#854d0e"/>
    <circle cx="66" cy="21" r="6" fill="#166534"/>
    <text x="96" y="27" class="mono muted">{esc(USERNAME.lower())}@github: ~/activity_{YEAR}</text>

    <g transform="translate(28 70)">
      <text x="0" y="0" class="mono prompt">$ gh activity --year {YEAR} --live</text>
      <rect class="blink" x="282" y="-15" width="9" height="19" rx="2" fill="#67e8f9"/>
      <text x="0" y="34" class="mono cmd">streaming contribution telemetry...</text>
      <text x="0" y="62" class="mono muted">last generated: {TODAY} UTC</text>
    </g>

    <g transform="translate(28 168)">
      <text x="0" y="0" class="mono label">total_contributions</text>
      <text x="0" y="38" class="mono value">{total}</text>
      <rect x="154" y="14" width="250" height="10" rx="5" fill="#071627"/>
      <rect class="bar1" x="154" y="14" width="250" height="10" rx="5" fill="#0891b2" filter="url(#glow)"/>
      <text x="0" y="78" class="mono label">commit_contributions</text>
      <text x="0" y="116" class="mono value">{commits}</text>
      <rect x="154" y="92" width="250" height="10" rx="5" fill="#071627"/>
      <rect class="bar2" x="154" y="92" width="250" height="10" rx="5" fill="#0f766e" filter="url(#glow)"/>
    </g>

    <g transform="translate(492 82)">
      <rect class="float1" x="0" y="0" width="140" height="86" rx="12" fill="#07111f" stroke="#1e3a8a"/>
      <text x="18" y="30" class="mono label">active_days</text>
      <text x="18" y="66" class="mono value">{active}</text>

      <rect class="float2" x="162" y="0" width="158" height="86" rx="12" fill="#07111f" stroke="#115e59"/>
      <text x="180" y="30" class="mono label">best_day</text>
      <text x="180" y="63" class="mono" fill="#e5f3ff" font-size="19" font-weight="800">{esc(best_date)}</text>

      <rect class="float2" x="0" y="108" width="140" height="86" rx="12" fill="#07111f" stroke="#115e59"/>
      <text x="18" y="138" class="mono label">best_count</text>
      <text x="18" y="174" class="mono value">{best_count}</text>

      <rect class="float1" x="162" y="108" width="158" height="86" rx="12" fill="#07111f" stroke="#1e3a8a"/>
      <text x="180" y="138" class="mono label">public_repos</text>
      <text x="180" y="174" class="mono value">{repos}</text>
    </g>

    <path class="draw" d="M31 298 C132 252, 212 318, 312 268 S492 234, 590 270 S721 326, 818 258" stroke="#22d3ee" stroke-width="3" fill="none" filter="url(#glow)"/>
    <text x="28" y="292" class="mono muted">repo_contributions={repo_contribs}</text>
    <text x="702" y="292" class="mono muted">stars={stars}</text>
  </g>
</svg>
'''

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(svg)
print(f"Updated {OUTPUT_PATH} for {USERNAME} with {total} contributions in {YEAR}.")