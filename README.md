# Is This Really Legal? Performance Dashboard

An independent dashboard for Is This Really Legal’s YouTube, Instagram, Apple Podcasts, TikTok, Substack email counts, and all-player podcast exports. Its visual layout follows the Home of the Brave reference, with no runtime or data dependency on that project.

## Features

- Platform-specific headline metrics
- Weekly graphs with date labels, format toggles, Show All / Deselect All, and clickable contributor details
- Weekly top-five posts and episodes, with desktop tabs and a mobile selector
- Eight-week comparison, Instagram follows and YouTube Subscribers by publish week, format tables, and searchable content
- Separate cutoff dates, partial weeks, and unavailable-data states for each platform

## Current data — November 4, 2026

The five named November files refresh YouTube (73 video rows), Instagram (44 posts), and Apple Podcasts (18 episodes), and add TikTok (365 daily observations) and Substack (239 email-count observations). The user-confirmed all-player podcast snapshot remains separate: 14 episodes and 92,470 downloads as of September 18. The new Substack file contains email counts and does not replace podcast downloads.

- YouTube source Total: 1,935,172 views and 17,988 Subscribers. Detail rows total 1,933,293 views and 14,025 Subscribers. Headlines use the source Total; weekly charts use dated rows, with differences left unallocated. Six rows lack publication dates. The new file has no Shares or Subscribers gained columns. Existing format classifications are retained for matching video IDs; 23 new IDs are labeled Format not supplied.
- Instagram: 3,952,653 lifetime views and 46,776 post-attributed follows. All 29 previous posts are present, plus 15 new posts. The supplied export includes 38 posts credited to isthisreallylegal and six to lawyer_oyer. Follows are not current account audience size.
- Apple Podcasts: 160,024 plays across 18 episodes, through November 3 based on the original filename. Unique listeners remain episode-level. Do not add Apple plays to overlapping all-player downloads or sum episode-level unique listeners.
- TikTok: 207,699 video views, 7,320 profile views, 39,814 likes, 1,230 comments, and 874 shares. Its 365 month/day labels omit years; November 4, 2025–November 3, 2026 is explicitly inferred from the sequence and intake date. The renamed file has the same records as the earlier Overview exports and is counted once. No post-level ranking or follower metric is available.
- Substack: the original email export is headerless; retain the first row. Label its metric email count, ending at 3,062 on November 4. Weekly charts take the last observation, never a sum. April 18–19 are absent, so that week uses April 17 and is marked partial. The file has no email addresses.

Weeks run Monday–Sunday. YouTube, Instagram and podcast charts group exported content performance by publication week. TikTok instead sums daily activity within calendar weeks; Substack shows the last reported count. Each chart preserves its own dates, incomplete weeks and source notes. The three removed miniature platform cards remain absent.

## Build and preview

The portable reviewed snapshot is `data/dashboard.json`. `data/history/2026-09-18.json` preserves the previous source records for the all-player podcast snapshot and established YouTube format labels. Raw CSVs and validation evidence under `work/` are excluded from Git and Railway uploads.

```sh
python3 scripts/refresh_november.py
python3 scripts/build_dashboard.py
npm start
```

The refresh script defaults to the five named CSVs in Downloads. Use its `--youtube`, `--instagram`, `--apple`, `--substack`, and `--tiktok` arguments to supply other paths. It is a dated November intake, not an automatic future refresh: new exports require renewed date/schema review. The legacy `scripts/build_data.py` builds the September snapshot and must not be used to regenerate the November release.

Open `http://localhost:3000`. The page uses self-contained SVG charts and no external scripts or data requests. Rebuild after changes to `src/dashboard.html`, `src/dashboard.css`, `src/dashboard.js`, or the reviewed snapshot. The TikTok and Substack charts support metric/range selection, Show All / Deselect All, keyboard navigation, clickable daily detail, and an inspectable source table for the selected range.

Validation checked source rows, totals, weekly reconciliation, missing-date treatment, unchanged all-player records, generated-file identity, browser controls and layout. YouTube headline/detail reconciliation and inferred source dates remain disclosed.

## Independent hosting

- GitHub repository: `rubin-maker/is-this-really-legal-dashboard`
- Railway project: `cf2ec980-d14f-475c-b6f0-04eddff4a43c`
- Railway environment: `db07cdf6-7f93-43a6-b3fc-a748ff30145a`
- Railway service: `594486d0-e9da-4628-8365-c4a546777aa9`
- Website: https://is-this-really-legal-dashboard-production.up.railway.app

The service currently uses explicit uploads rather than a connected GitHub source. Always pass these exact project, environment, and service IDs when deploying. Do not relink or deploy to a Home of the Brave resource.

The server exposes `/`, `/dashboard.html`, `/artifact.json`, and `/health`. Railway starts it with `npm start` and supplies `PORT`; `HOST` defaults to `0.0.0.0` and can be set to `127.0.0.1` for local preview.
