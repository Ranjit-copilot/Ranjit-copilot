from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def weeks_from_days(days):
    if not days:
        return []

    by_date = {date.fromisoformat(d["date"]): d for d in days}
    start = min(by_date)
    end = max(by_date)

    start -= timedelta(days=(start.weekday() + 1) % 7)
    end += timedelta(days=(6 - ((end.weekday() + 1) % 7)))

    cells = []
    cursor = start
    while cursor <= end:
        week = (cursor - start).days // 7
        weekday = (cursor.weekday() + 1) % 7
        item = by_date.get(cursor, {"count": 0, "level": 0})
        cells.append((week, weekday, item["level"], item["count"], cursor.isoformat()))
        cursor += timedelta(days=1)
    return cells


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload.get("days", [])
    cells = weeks_from_days(days)
    weeks = max((w for w, *_ in cells), default=52) + 1

    cell_w = 13
    cell_h = 13
    left = 28
    top = 74

    rects = []
    for i, (week, weekday, level, count, day) in enumerate(cells):
        x = left + week * cell_w
        y = top + weekday * cell_h
        fill = PALETTE[min(max(int(level), 0), 5)]
        delay = min(i * 0.012, 4.0)
        label = f"{day}: {count} contribution" + ("" if count == 1 else "s")
        rects.append(
            f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{fill}" opacity="0" '
            f'aria-label="{esc(label)}"><animate attributeName="opacity" from="0" to="1" '
            f'dur=".28s" begin="{delay:.3f}s" fill="freeze"/></rect>'
        )

    width = max(860, left + weeks * cell_w + 25)
    total = payload.get("total", 0)
    current = payload.get("current_streak", 0)
    longest = payload.get("longest_streak", 0)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 205" role="img" aria-labelledby="title desc">
  <title id="title">Ranjit-copilot GitHub contribution activity</title>
  <desc id="desc">Contribution calendar for the last year, regenerated daily from GitHub public contribution data.</desc>
  <rect width="{width}" height="205" rx="16" fill="#0d1117" stroke="#30363d"/>
  <text x="24" y="30" fill="#e6edf3" font-family="monospace" font-size="15" font-weight="700">ranjit@github ~ $ ./contributions.sh</text>
  <text x="24" y="51" fill="#8b949e" font-family="monospace" font-size="11">{total:,} contributions in the last year</text>
  {''.join(rects)}
  <text x="24" y="180" fill="#8b949e" font-family="monospace" font-size="10">Less</text>
  <rect x="55" y="171" width="10" height="10" rx="2" fill="{PALETTE[0]}"/>
  <rect x="70" y="171" width="10" height="10" rx="2" fill="{PALETTE[1]}"/>
  <rect x="85" y="171" width="10" height="10" rx="2" fill="{PALETTE[2]}"/>
  <rect x="100" y="171" width="10" height="10" rx="2" fill="{PALETTE[3]}"/>
  <rect x="115" y="171" width="10" height="10" rx="2" fill="{PALETTE[4]}"/>
  <rect x="130" y="171" width="10" height="10" rx="2" fill="{PALETTE[5]}"/>
  <text x="148" y="180" fill="#8b949e" font-family="monospace" font-size="10">More</text>
  <text x="{max(500, width-330)}" y="180" fill="#8b949e" font-family="monospace" font-size="10">streak: {current}d • longest: {longest}d</text>
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Rendered {OUT}")


if __name__ == "__main__":
    main()
