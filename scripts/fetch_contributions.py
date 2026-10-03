from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Ranjit-copilot"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parents[1] / "data" / "contributions.json"


def parse_count(title: str) -> int:
    match = re.search(r"(\d+) contribution", title or "")
    return int(match.group(1)) if match else 0


def main() -> None:
    response = requests.get(
        URL,
        headers={"User-Agent": "Technical-Ranjit-GitHub-Profile/1.0"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    days = []

    for cell in soup.select("td.ContributionCalendar-day"):
        day = cell.get("data-date")
        level = cell.get("data-level")
        if not day:
            continue
        title_node = cell.find("title")
        title = title_node.get_text(" ", strip=True) if title_node else ""
        count = parse_count(title)
        days.append({"date": day, "count": count, "level": int(level or 0)})

    if not days:
        raise RuntimeError("GitHub contribution cells were not found.")

    days.sort(key=lambda item: item["date"])

    total = sum(item["count"] for item in days)
    best = max(days, key=lambda item: (item["count"], item["date"]))

    day_map = {date.fromisoformat(item["date"]): item["count"] for item in days}
    all_dates = sorted(day_map)

    current = 0
    cursor = all_dates[-1]
    while day_map.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    run = 0
    for d in all_dates:
        if day_map[d] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    monthly = defaultdict(int)
    for item in days:
        monthly[item["date"][:7]] += item["count"]

    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(sorted(monthly.items())),
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(days)} days and {total} contributions to {OUT}")


if __name__ == "__main__":
    main()
