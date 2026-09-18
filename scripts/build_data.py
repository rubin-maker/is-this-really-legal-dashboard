#!/usr/bin/env python3
"""Build the public ISRL dashboard data from ISRL-only exports.

Raw source files stay outside the repository. Substack is staged separately and
is not silently relabeled as Apple Podcasts. Weekly charts group exported
content metrics by publication week, not by the week activity was earned.
"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORICAL = Path(
    "/Users/barryrubin/Library/Mobile Documents/com~apple~CloudDocs/Video Projects/ISRL Data/Aug 28th"
)
ADDITIVE = (
    "value", "views", "plays", "engagements", "watch_hours", "subscribers_gained",
    "subscribers", "likes", "shares", "comments", "saves", "follows", "reach", "impressions",
)


def number(raw):
    if raw is None or str(raw).strip() in {"", "NaN", "nan"}:
        return None
    result = Decimal(str(raw).replace(",", ""))
    return int(result) if result == result.to_integral_value() else float(result)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def monday(day):
    if isinstance(day, str):
        day = date.fromisoformat(day)
    return day - timedelta(days=day.weekday())


def sum_known(rows, key, empty=0):
    values = [Decimal(str(row[key])) for row in rows if row.get(key) is not None]
    if not values:
        return empty
    return number(sum(values))


def apple_records(path):
    records = []
    for raw in read_csv(path):
        records.append({
            "id": raw["Episode ID"], "title": raw["Episode Title"],
            "date": raw["Release Date"], "week_start": monday(raw["Release Date"]).isoformat(),
            "url": None, "category": "Episodes", "value": number(raw["Plays"]),
            "plays": number(raw["Plays"]), "listeners": number(raw["Unique Listeners"]),
            "engaged_listeners": number(raw["Unique Engaged Listeners"]),
            "average_consumption": number(raw["Average Consumption"]),
            "engagements": None, "weekly_eligible": True,
        })
    return records


def instagram_records(path):
    records = []
    for raw in read_csv(path):
        published = datetime.strptime(raw["Publish time"], "%m/%d/%y %H:%M").date()
        metrics = {key: number(raw[field]) for key, field in {
            "views": "Views", "reach": "Reach", "likes": "Likes", "shares": "Shares",
            "follows": "Follows", "comments": "Comments", "saves": "Saves",
        }.items()}
        parts = [metrics[key] for key in ("likes", "shares", "comments", "saves")]
        records.append({
            "id": raw["Permalink"].rstrip("/").rsplit("/", 1)[-1],
            "title": raw["Description"].replace("\\n", "\n"),
            "date": published.isoformat(), "week_start": monday(published).isoformat(),
            "url": raw["Permalink"], "category": raw["Post type"],
            "value": metrics["views"], **metrics,
            "engagements": sum(parts) if all(x is not None for x in parts) else None,
            "weekly_eligible": True,
        })
    return records


def youtube_records(path):
    records = []
    for raw in json.loads(path.read_text()):
        native = {key: raw.get(key) for key in (
            "views", "watch_hours", "subscribers_gained", "subscribers", "likes", "shares",
            "comments", "impressions", "ctr_pct", "average_pct_viewed", "engagements",
        )}
        records.append({
            "id": raw["id"], "title": raw["title"], "date": raw["publish_date"],
            "week_start": raw["week_start"], "url": raw["url"], "category": raw["product"],
            "value": raw["views"], **native, "weekly_eligible": raw["weekly_eligible"],
        })
    return records


def summarize(records, supported):
    dated = [r for r in records if r["weekly_eligible"]]
    undated = [r for r in records if not r["weekly_eligible"]]
    return {
        **{key: sum_known(records, key, None if records else 0) if key in supported else None
           for key in ADDITIVE},
        "posts": len(records), "dated_posts": len(dated), "undated_posts": len(undated),
        "measured_posts": sum(r["value"] is not None for r in records),
        "weekly_value": sum_known(dated, "value"), "undated_value": sum_known(undated, "value"),
        "missing_counts": {key: sum(r.get(key) is None for r in records) for key in supported},
    }


def assemble_platform(platform, weeks):
    records = platform["records"]
    supported = platform.pop("supported_metrics")
    assert len({r["id"] for r in records}) == len(records), "Duplicate source identifiers"
    dated = [r for r in records if r["weekly_eligible"]]
    first_week = min(r["week_start"] for r in dated)
    last_week = monday(platform["cutoff"]).isoformat()
    platform["coverage_start"] = min(r["date"] for r in dated)
    platform["categories"] = sorted({r["category"] for r in records})
    platform["totals"] = summarize(records, supported)
    platform["weekly"] = []
    grouped = defaultdict(list)
    for record in dated:
        grouped[record["week_start"]].append(record)
    for week in weeks:
        available = first_week <= week["start"] <= last_week
        rows = grouped[week["start"]]
        point = {
            "start": week["start"], "end": week["end"], "label": week["label"],
            "available": available,
            "partial": available and week["start"] <= platform["cutoff"] < week["end"],
            "posts": len(rows) if available else None,
            **{key: sum_known(rows, key, None if rows else 0)
               if available and key in supported else None for key in ADDITIVE},
            "missing_counts": {key: sum(r.get(key) is None for r in rows) for key in supported},
        }
        platform["weekly"].append(point)
    assert sum_known(platform["weekly"], "value") == sum_known(dated, "value")
    assert sum(w["posts"] or 0 for w in platform["weekly"]) == len(dated)
    return platform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--intake", type=Path, default=ROOT / "work/intake-2026-09-18")
    parser.add_argument("--output", type=Path, default=ROOT / "data/dashboard.json")
    args = parser.parse_args()

    apple = apple_records(args.historical / "apple podcast.csv")
    instagram = instagram_records(args.historical / "instagram is this really legal.csv")
    youtube = youtube_records(args.intake / "youtube_records.json")
    intake = json.loads((args.intake / "intake_report.json").read_text())
    # Reconcile the complete historical source rows with the previous dashboard.
    assert len(apple) == 10 and sum_known(apple, "plays") == 61513
    assert len(instagram) == 20 and sum_known(instagram, "views") == 1735711
    assert sum_known(instagram, "engagements") == 180153
    assert sum_known(instagram, "follows") == 43166
    assert len(youtube) == 51 and sum_known(youtube, "views") == 779138
    assert sum(r["weekly_eligible"] for r in youtube) == 41

    updated = "2026-09-18"
    first = monday(min(r["date"] for r in apple + instagram + youtube if r["date"]))
    final = monday(updated)
    weeks = []
    while first <= final:
        end = first + timedelta(days=6)
        weeks.append({
            "start": first.isoformat(), "end": end.isoformat(),
            "label": f"{first.strftime('%b')} {first.day} – {end.strftime('%b')} {end.day}",
            "iso_week": first.isocalendar().week,
        })
        first += timedelta(days=7)

    platforms = [
        {
            "id": "youtube", "label": "YouTube", "color": "#fb7185", "metric": "Exported views",
            "cutoff": "2026-09-17", "cutoff_confirmed": False, "freshness": "Updated export",
            "coverage_note": "September 17 cutoff inferred from filenames; the analytics reporting range is unconfirmed. Ten Shorts have no publish date and are excluded from weekly charts and rankings.",
            "records_complete": True, "weekly_records_complete": False,
            "records": youtube,
            "supported_metrics": ["value", "views", "engagements", "watch_hours", "subscribers_gained", "subscribers", "likes", "shares", "comments", "impressions"],
        },
        {
            "id": "instagram", "label": "Instagram", "color": "#c084fc", "metric": "Views",
            "cutoff": "2026-08-28", "cutoff_confirmed": True, "freshness": "Refresh pending",
            "coverage_note": "Complete 20-post export from August 28. September data is unavailable while the refreshed Instagram export is pending.",
            "records_complete": True, "weekly_records_complete": True,
            "records": instagram,
            "supported_metrics": ["value", "views", "engagements", "reach", "likes", "shares", "comments", "saves", "follows"],
        },
        {
            "id": "apple", "label": "Apple Podcasts", "color": "#38bdf8", "metric": "Plays",
            "cutoff": "2026-08-28", "cutoff_confirmed": True, "freshness": "August 28 snapshot",
            "coverage_note": "Complete 10-episode Apple export from August 28. Plays are additive; episode unique listeners must not be added as an account audience total.",
            "records_complete": True, "weekly_records_complete": True,
            "records": apple, "supported_metrics": ["value", "plays"],
        },
    ]
    platforms = [assemble_platform(p, weeks) for p in platforms]
    platforms[2]["totals"]["median_episode_listeners"] = median(r["listeners"] for r in apple)
    sources = []
    for source in intake["youtube_sources"]:
        sources.append({
            "platform": "youtube", "file": source["file"], "category": source["product"],
            "records": source["records"], "dated_records": source["dated_records"],
            "undated_records": source["undated_records"], "reporting_range": None,
            "reconciliation": source["reconciliation"],
        })
    data = {
        "version": 1, "updated": updated, "weeks": weeks, "platforms": platforms,
        "notes": [
            "Weekly charts group exported content performance by its publication week. They do not measure activity earned during that week.",
            "Instagram uses lifetime post metrics. YouTube is labeled exported views because its analytics reporting range has not been confirmed.",
            "Each platform keeps its own metric. YouTube and Instagram views are not added to Apple plays, and episode unique listeners are not deduplicated across episodes.",
            "Instagram reach is summed across posts and is not a deduplicated account audience count.",
            "Apple and Instagram retain the August 28 snapshot. Weeks beyond their cutoff are unavailable, not zero. The cutoff week may be partial.",
            "YouTube includes 51 export rows: 41 dated videos and 10 Shorts without publish dates. The undated Shorts account for four known views; three also have missing view metrics.",
            "YouTube headline and weekly views use 779,134 views from 41 dated videos. All 51 detail rows contain 779,138 known views, including four views on undated Shorts. Export Total rows report 779,159 views; the 21-view discrepancy is not assigned to content or weeks.",
            "The supplied podcast refresh is Substack data and remains staged separately. It is not substituted for Apple Podcasts metrics.",
        ],
        "qa": {
            "sources": sources,
            "historical_source_checks": {
                "apple_records": len(apple), "apple_plays": sum_known(apple, "plays"),
                "instagram_records": len(instagram), "instagram_views": sum_known(instagram, "views"),
                "instagram_engagements": sum_known(instagram, "engagements"),
            },
            "youtube_undated_ids": [r["id"] for r in youtube if not r["weekly_eligible"]],
            "youtube_missing_value_ids": [r["id"] for r in youtube if r["value"] is None],
            "substack_staged": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({
        "output": str(args.output), "weeks": len(weeks),
        "platforms": [{"id": p["id"], "records": len(p["records"]), "value": p["totals"]["value"],
                       "weekly_value": p["totals"]["weekly_value"]} for p in platforms],
    }, indent=2))


if __name__ == "__main__":
    main()
