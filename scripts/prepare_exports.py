#!/usr/bin/env python3
"""Prepare ISRL exports without changing the published dashboard.

Raw exports remain in the supplied directory. Prepared records are local-only.
Substack provenance and all-player podcast scope were confirmed by the user.
YouTube reporting scope is pending.
"""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path


YT_FIELDS = {
    "views": "Views",
    "watch_hours": "Watch time (hours)",
    "subscribers_gained": "Subscribers gained",
    "subscribers": "Subscribers",
    "likes": "Likes",
    "shares": "Shares",
    "comments": "Comments added",
    "impressions": "Thumbnail impressions",
    "ctr_pct": "Thumbnail click-through rate (%)",
    "average_pct_viewed": "Average percentage viewed (%)",
}
ADDITIVE = [key for key in YT_FIELDS if key not in {"ctr_pct", "average_pct_viewed"}]


def number(value):
    return Decimal(value.strip()) if value and value.strip() else None


def monday(day):
    return (day - timedelta(days=day.weekday())).isoformat()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metadata(path):
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def numeric_sum(rows, key):
    return sum((row[key] for row in rows if row[key] is not None), Decimal(0))


def youtube(path, product):
    raw = read_csv(path)
    totals = [r for r in raw if r["Content"].strip() == "Total"]
    if len(totals) != 1:
        raise ValueError(f"{path.name}: expected one export Total row")
    rows = []
    for line, row in enumerate(raw, start=2):
        video_id = row["Content"].strip()
        if video_id == "Total":
            continue
        published = row["Video publish time"].strip()
        day = datetime.strptime(published, "%b %d, %Y").date() if published else None
        record = {
            "platform": "YouTube", "product": product, "id": video_id,
            "title": row["Video title"], "url": f"https://www.youtube.com/watch?v={video_id}",
            "publish_date": day.isoformat() if day else None,
            "week_start": monday(day) if day else None,
            "source_file": path.name, "source_row": line,
            **{key: number(row.get(field)) for key, field in YT_FIELDS.items()},
        }
        parts = [record[key] for key in ("likes", "shares", "comments")]
        record["engagements"] = sum(parts) if all(v is not None for v in parts) else None
        record["weekly_eligible"] = day is not None
        rows.append(record)
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: duplicate video IDs")
    dated = [r for r in rows if r["weekly_eligible"]]
    reconciliation = {}
    for key in ADDITIVE:
        source_total = number(totals[0].get(YT_FIELDS[key]))
        detail_sum = numeric_sum(rows, key)
        reconciliation[key] = {
            "export_total": source_total,
            "detail_sum": detail_sum,
            "dated_sum": numeric_sum(dated, key),
            "undated_sum": numeric_sum([r for r in rows if not r["weekly_eligible"]], key),
            "export_minus_detail": source_total - detail_sum if source_total is not None else None,
            "missing_detail_values": sum(r[key] is None for r in rows),
        }
    return rows, {
        **metadata(path), "product": product, "records": len(rows),
        "dated_records": len(dated), "undated_records": len(rows)-len(dated),
        "publish_start": min(r["publish_date"] for r in dated),
        "publish_end": max(r["publish_date"] for r in dated),
        "reporting_range": None,
        "cutoff_hint_from_filename": "2026-09-17",
        "reconciliation": reconciliation,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("work/intake-2026-09-18"))
    args = parser.parse_args()
    inputs = args.source_directory
    records, sources = [], []
    for filename, product in [
        ("isrl youtube video -26-9-17.csv", "Long-form"),
        ("isrl youtube shorts -26-9-17.csv", "Shorts"),
    ]:
        rows, source = youtube(inputs / filename, product)
        records.extend(rows)
        sources.append(source)
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Video IDs overlap between YouTube format exports")

    weekly = defaultdict(list)
    for row in records:
        if row["weekly_eligible"]:
            weekly[(row["week_start"], row["product"])].append(row)
    weekly_rows = [{
        "week_start": week, "product": product, "videos": len(rows),
        **{key: numeric_sum(rows, key) for key in ADDITIVE + ["engagements"]},
        "missing_counts": {key: sum(r[key] is None for r in rows) for key in ADDITIVE},
        "top_five_ids": [r["id"] for r in sorted(
            [r for r in rows if r["views"] is not None],
            key=lambda r: (-r["views"], r["id"]))[:5]],
    } for (week, product), rows in sorted(weekly.items())]

    podcast_path = inputs / "is this really legal padcast numbers 26-9-18.csv"
    episodes = []
    for line, row in enumerate(read_csv(podcast_path), start=2):
        day = datetime.fromisoformat(row["Date"]).date()
        episodes.append({
            "platform": "Substack",
            "title": row["Title"], "published_at_source": row["Date"],
            "publish_date": day.isoformat(), "week_start": monday(day),
            "downloads_total": number(row["Total"]),
            "downloads_first_30_days": number(row["Downloads (first 30d)"]),
            "previews_first_30_days": number(row["Previews (first 30d)"]),
            "previews_total": number(row["Previews (total)"]),
            "paid_subscriptions_first_24_hours": number(row["Paid subs (first 24h)"]),
            "shares": number(row["Shares"]),
            "source_file": podcast_path.name, "source_row": line,
        })
    report = {
        "status": "prepared_youtube_reporting_range_unconfirmed",
        "youtube_sources": sources,
        "podcast_source": {
            **metadata(podcast_path), "service": "Substack", "service_confirmed_by": "user",
            "player_scope": "All podcast players", "scope_confirmed_by": "user",
            "episodes": len(episodes),
            "downloads_total": numeric_sum(episodes, "downloads_total"),
            "note": "Use this export for all-player podcast downloads. Replace the older, overlapping Apple-only series; do not add its plays or listener counts.",
        },
        "pending": [
            "Confirm YouTube analytics reporting range before labeling metrics lifetime or year-to-date.",
        ],
        "rules": [
            "Total rows are reconciliation controls, never content records.",
            "Missing dates are excluded from weekly allocation; missing metrics remain null.",
            "Weekly values are exported video metrics grouped by publish date, not weekly-earned activity.",
            "Subscribers and Subscribers gained remain separate source fields.",
            "Source discrepancies are retained; no residual is assigned to a video or week.",
            "Distinct video IDs remain separate even when titles match.",
        ],
    }
    def encode(value):
        if isinstance(value, Decimal):
            return int(value) if value == value.to_integral_value() else float(value)
        raise TypeError(type(value).__name__)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in [
        ("youtube_records.json", records), ("youtube_weekly.json", weekly_rows),
        ("substack_episodes.json", episodes), ("intake_report.json", report),
    ]:
        (args.output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=encode) + "\n")
    assert sum(r["views"] for r in weekly_rows) == numeric_sum(
        [r for r in records if r["weekly_eligible"]], "views")
    print(json.dumps({"youtube_records": len(records), "dated_youtube_records": sum(r["weekly_eligible"] for r in records),
                      "podcast_episodes": len(episodes), "status": report["status"]}))


if __name__ == "__main__":
    main()
