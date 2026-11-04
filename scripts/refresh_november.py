#!/usr/bin/env python3
"""Build the November 4 ISRL snapshot from the five user-named CSV exports."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from build_data import assemble_platform, instagram_records, number, monday, sum_known

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path('/Users/barryrubin/Downloads')


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def provenance(path, **extra):
    return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **extra}


def daily_series(identifier, label, kind, records, metrics, note, color):
    assert len({r['date'] for r in records}) == len(records)
    assert records == sorted(records, key=lambda r: r['date'])
    if kind == 'activity':
        assert all((date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days == 1 for a, b in zip(records, records[1:]))
    grouped = defaultdict(list)
    for r in records:
        grouped[monday(r['date']).isoformat()].append(r)
    weekly = []
    prior = None
    for start, rr in sorted(grouped.items()):
        values = {m: sum_known(rr, m) if kind == 'activity' else rr[-1][m] for m in metrics}
        weekly.append({'start': start, 'end': (date.fromisoformat(start)+timedelta(days=6)).isoformat(),
                       'observed_start': rr[0]['date'], 'observed_end': rr[-1]['date'], 'days': len(rr),
                       'partial': len(rr) != 7, 'values': values,
                       'change': {m: values[m]-prior[m] if prior is not None and kind == 'snapshot' else None for m in metrics}})
        prior = values
    return {'id': identifier, 'label': label, 'kind': kind, 'color': color, 'start': records[0]['date'],
            'end': records[-1]['date'], 'rows': records, 'weekly': weekly, 'metrics': metrics, 'note': note}


def main():
    parser = argparse.ArgumentParser()
    for name, default in [('youtube', DOWNLOADS/'yt (1)/youtube.csv'), ('instagram', DOWNLOADS/'ig (1).csv'),
                          ('apple', DOWNLOADS/'apple pod (1).csv'), ('substack', DOWNLOADS/'substack (1).csv'),
                          ('tiktok', DOWNLOADS/'tiktok (1).csv')]:
        parser.add_argument('--'+name, type=Path, default=default)
    args = parser.parse_args()
    baseline = json.loads((ROOT/'data/history/2026-09-18.json').read_text())
    previous = {p['id']: p for p in baseline['platforms']}
    raw = rows(args.youtube)
    control = [r for r in raw if r['Content'].strip() == 'Total']
    assert len(control) == 1
    old = {r['id']: r for r in previous['youtube']['records']}
    yt = []
    fields = {'views': 'Views', 'watch_hours': 'Watch time (hours)', 'subscribers': 'Subscribers', 'likes': 'Likes',
              'comments': 'Comments added', 'impressions': 'Thumbnail impressions', 'ctr_pct': 'Thumbnail click-through rate (%)',
              'engaged_views': 'Engaged views', 'dislikes': 'Dislikes'}
    for r in raw:
        vid = r['Content'].strip()
        if vid == 'Total':
            continue
        day = datetime.strptime(r['Video publish time'], '%b %d, %Y').date() if r['Video publish time'].strip() else None
        values = {key: number(r[field]) for key, field in fields.items()}
        yt.append({'id': vid, 'title': r['Video title'], 'date': day.isoformat() if day else None,
                   'week_start': monday(day).isoformat() if day else None, 'url': f'https://www.youtube.com/watch?v={vid}',
                   'category': old.get(vid, {}).get('category', 'Format not supplied'), 'value': values['views'], **values,
                   'engagements': None, 'subscribers_gained': None, 'shares': None, 'weekly_eligible': day is not None})
    reconciliation = {key: {'export_total': number(control[0][field]), 'detail_sum': sum_known(yt, key),
                           'export_minus_detail': number(control[0][field])-sum_known(yt, key)}
                      for key, field in fields.items() if key != 'ctr_pct'}
    missing_old = sorted(set(old)-{r['id'] for r in yt})
    yt_platform = {'id': 'youtube', 'label': 'YouTube', 'color': '#fb7185', 'metric': 'Exported views', 'unit': 'views',
      'cutoff': '2026-11-04', 'cutoff_confirmed': False, 'freshness': 'November 4 export', 'refresh_pending': False,
      'reporting_start': '2026-03-09', 'reporting_end': '2026-11-04', 'audience_metric': 'subscribers',
      'audience_note': 'Uses the new export’s Subscribers field, not Subscribers gained or a current channel subscriber total. The export Total is 17,988; dated content accounts for 14,025. The difference is not assigned to a video or week.',
      'coverage_note': 'Reporting range Mar 9–Nov 4 comes from the original supplied folder name. Format labels are retained only for video IDs matched to September; new IDs are marked Format not supplied. Six rows lack publish dates. Shares and Subscribers gained were not supplied.',
      'metric_note': 'Exported views. Likes and comments are available separately; engagements are unavailable because shares were not supplied. Subscribers uses the export field, not gross subscriber gains.',
      'chart_metrics': ['value', 'likes', 'comments', 'subscribers', 'posts'], 'records_complete': False, 'weekly_records_complete': False,
      'records': yt, 'supported_metrics': ['value', 'views', 'watch_hours', 'subscribers', 'likes', 'comments', 'impressions']}

    apple = []
    for r in rows(args.apple):
        assert r['Show Name'] == 'Is This Really Legal?'
        day = r['Release Date']
        apple.append({'id': r['Episode ID'], 'title': r['Episode Title'], 'date': day, 'week_start': monday(day).isoformat(),
                      'url': None, 'category': 'Episodes', 'value': number(r['Plays']), 'plays': number(r['Plays']),
                      'listeners': number(r['Unique Listeners']), 'engaged_listeners': number(r['Unique Engaged Listeners']),
                      'average_consumption': number(r['Average Consumption']), 'engagements': None, 'weekly_eligible': True})
    apple_platform = {'id': 'apple', 'label': 'Apple Podcasts', 'color': '#34b6d5', 'unit': 'plays', 'metric': 'Plays',
      'cutoff': '2026-11-03', 'cutoff_confirmed': False, 'freshness': 'November 3 export', 'refresh_pending': False,
      'coverage_note': '18 episodes through Nov 3, using the date in the original Apple export filename. Apple plays remain separate from the older all-player download snapshot; the two measures must not be added together.',
      'metric_note': 'Apple Podcasts plays. Unique listeners are shown per episode and must not be summed across episodes.',
      'chart_metrics': ['value', 'posts'], 'records_complete': True, 'weekly_records_complete': True,
      'records': apple, 'supported_metrics': ['value', 'plays']}

    ig_rows = instagram_records(args.instagram)
    assert all(r['Date'] == 'Lifetime' for r in rows(args.instagram))
    assert {r['id'] for r in previous['instagram']['records']} <= {r['id'] for r in ig_rows}
    accounts = dict(Counter(r['source_account'] for r in ig_rows))
    ig = {'id': 'instagram', 'label': 'Instagram', 'color': '#c084fc', 'metric': 'Views', 'unit': 'views',
      'cutoff': '2026-11-04', 'cutoff_confirmed': False, 'freshness': 'November 4 intake', 'refresh_pending': False,
      'coverage_note': '44 supplied posts with lifetime metrics, including 38 credited to isthisreallylegal and 6 to lawyer_oyer. All 29 earlier posts are included with refreshed metrics. Snapshot date uses the Nov 4 file intake; latest published post is Nov 2.',
      'metric_note': 'Lifetime Instagram post views. Engagements = likes + comments + shares + saves. Follows are attributed to exported posts, not the account follower total.',
      'audience_note': 'Follows attributed to 44 exported posts: 46,244 from isthisreallylegal and 532 from lawyer_oyer. This is not the account’s current follower total.',
      'source_accounts': accounts, 'chart_metrics': ['value', 'engagements', 'follows', 'posts'], 'records_complete': True,
      'weekly_records_complete': True, 'records': ig_rows,
      'supported_metrics': ['value', 'views', 'engagements', 'reach', 'likes', 'shares', 'comments', 'saves', 'follows']}
    pod = previous['podcast']
    pod.update(refresh_pending=True, chart_metrics=['value', 'posts'],
               metric_note='All-player podcast downloads from the September Substack export. Downloads are not unique listeners and are not added to Apple plays.',
               supported_metrics=['value', 'downloads', 'downloads_first_30_days', 'shares'])
    platforms = [yt_platform, ig, pod, apple_platform]
    first = monday(min(r['date'] for p in platforms for r in p['records'] if r['date']))
    final = monday('2026-11-04')
    weeks = []
    while first <= final:
        end = first+timedelta(days=6)
        weeks.append({'start': first.isoformat(), 'end': end.isoformat(), 'label': f'{first:%b} {first.day} – {end:%b} {end.day}', 'iso_week': first.isocalendar().week})
        first += timedelta(days=7)
    for p in platforms:
        assert all(r['date'] <= p['cutoff'] for r in p['records'] if r['date'])
    platforms = [assemble_platform(p, weeks) for p in platforms]

    raw_tiktok = rows(args.tiktok)
    assert len(raw_tiktok) == 365
    current = date(2025, 11, 4)
    tt = []
    for r in raw_tiktok:
        assert r['Date'] == f'{current:%B} {current.day}', 'TikTok date sequence mismatch'
        tt.append({'date': current.isoformat(), **{key: number(r[field]) for key, field in
                  {'views': 'Video Views', 'profile_views': 'Profile Views', 'likes': 'Likes', 'comments': 'Comments', 'shares': 'Shares'}.items()}})
        current += timedelta(days=1)
    with args.substack.open(encoding='utf-8-sig', newline='') as f:
        email = [{'date': datetime.strptime(r[0], '%Y/%m/%d').date().isoformat(), 'count': int(r[1])} for r in csv.reader(f)]
    daily = [daily_series('tiktok', 'TikTok', 'activity', tt,
              {'views': 'Video views', 'profile_views': 'Profile views', 'likes': 'Likes', 'comments': 'Comments', 'shares': 'Shares'},
              'Daily activity, summed within each calendar week. The export omits years; Nov 4, 2025–Nov 3, 2026 is inferred from its 365-day sequence and Nov 4 intake. No post-level data or follower totals were supplied.', '#22a6a1'),
             daily_series('substack', 'Substack email count', 'snapshot', email, {'count': 'Email count'},
              'Daily counts from the supplied Substack email export. The file has no column headings, so the metric is labeled email count. Each week shows its last reported count, not a sum or emails sent. Apr 18–19 are missing; that week uses Apr 17 and is marked partial.', '#f18446')]
    sources = [s for s in baseline['qa']['sources'] if s['platform'] == 'podcast']
    sources += [provenance(args.youtube, platform='youtube', records=len(yt), reconciliation=reconciliation, reporting_range=['2026-03-09', '2026-11-04']),
                provenance(args.instagram, platform='instagram', records=len(ig_rows), snapshot_date='2026-11-04', snapshot_basis='intake date'),
                provenance(args.apple, platform='apple', records=len(apple), snapshot_date='2026-11-03', snapshot_basis='original filename'),
                provenance(args.tiktok, platform='tiktok', records=len(tt), date_years_inferred=True),
                provenance(args.substack, platform='substack', records=len(email), headerless=True)]
    data = {'version': 2, 'updated': '2026-11-04', 'weeks': weeks, 'platforms': platforms, 'daily_series': daily, 'pending_imports': [],
      'notes': ['Publication-week charts group exported content performance by publish date, not by when activity was earned. TikTok instead reports daily activity; its weekly chart sums activity dates.',
        'YouTube reporting range Mar 9–Nov 4 is inferred from the original folder name. The export has 73 detail rows, including six without publish dates.',
        'YouTube export Total: 1,935,172 views and 17,988 Subscribers. Detail rows: 1,933,293 views and 14,025 Subscribers. Differences remain unallocated: headline cards use source Totals, while weekly charts use dated detail rows. Comments also differ: 6,510 Total versus 6,532 in detail rows.',
        'The new YouTube export lacks shares and Subscribers gained. Older gains are not mixed into the new reporting range. New videos without source format labels remain Format not supplied.',
        'The earlier undated YouTube row j8WJ_lpWqwI is absent from this export; it remains in the September archive and is not added to current totals.',
        'Instagram now includes 44 posts: 38 credited to isthisreallylegal and 6 to lawyer_oyer. All 29 September posts are present with updated metrics. November 4 snapshot timing is based on file intake.',
        'All-player podcast downloads retain the September 18 snapshot. Apple Podcasts is refreshed separately through November 3. Apple plays and all-player downloads overlap and must not be added. Apple unique listeners are episode-level counts.',
        'TikTok’s 365 dates omit years. The inferred period is Nov 4, 2025–Nov 3, 2026. The renamed file contains the same records as the earlier Overview exports and is included only once. No TikTok top-post ranking is possible from daily aggregates.',
        'Substack contains 239 daily email-count observations, Mar 9–Nov 4, ending at 3,062. The headerless source is labeled email count; weekly values use the final observation and are never summed. This file does not refresh podcast downloads.'],
      'qa': {'sources': sources, 'youtube_missing_old_ids': missing_old, 'youtube_undated_ids': [r['id'] for r in yt if not r['date']],
             'youtube_export_totals': {key: number(control[0][field]) for key, field in fields.items()}}}
    (ROOT/'data/dashboard.json').write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps({'platforms': [{'id': p['id'], 'records': len(p['records']), 'total': p['totals']['value']} for p in platforms],
                      'daily_series': [{'id': s['id'], 'rows': len(s['rows']), 'weeks': len(s['weekly'])} for s in daily]}, indent=2))


if __name__ == '__main__':
    main()
