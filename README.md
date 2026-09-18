# Is This Really Legal? Performance Dashboard

An independent dashboard for Is This Really Legal’s YouTube, Instagram, and all-player podcast exports. Its visual layout follows the Home of the Brave reference, with no runtime or data dependency on that project.

## Features

- Platform-specific headline metrics and selectable weekly mini charts
- Weekly graphs with date labels, format toggles, Show All / Deselect All, and clickable contributor details
- Weekly top-five posts and episodes, with desktop tabs and a mobile selector
- Eight-week comparison, Instagram follower and YouTube subscriber gains by publish week, format tables, and searchable content
- Separate cutoff dates, partial weeks, and unavailable-data states for each platform

## Current data

The September 18 redesign uses the September 17 YouTube CSVs, September 18 Instagram export, and September 18 podcast snapshot from Substack. The user confirmed that the podcast export covers all podcast players: 14 episodes totaling 92,470 downloads. Downloads are not unique audience. Instagram includes all 20 previously displayed posts with refreshed metrics plus 9 new posts, for 29 posts and 2,547,364 lifetime views. Three supplied Instagram rows are credited to lawyer_oyer; these are retained as part of the user-provided export.

YouTube graphs and headline views use 41 dated uploads with 779,134 views. Ten undated Shorts are retained in the reviewed snapshot but excluded from publication-week allocation; they contain four additional known views and three missing view values. The CSV reporting range is unconfirmed, so YouTube metrics are labeled exported values. The YouTube Total rows differ from summed detail rows, and those differences are preserved in the snapshot’s QA metadata.

Weeks run Monday–Sunday. Values represent exported performance of content published in that week, not activity earned within the week. All-player podcast downloads are kept separate from social views. The podcast “First 30 days” column reports each episode’s exported downloads during its first 30 days; the format table sums those values. Subscriber gains use the explicit Subscribers gained field, with one missing dated-video value disclosed.

Instagram follows attributed to the 29 supplied posts total 45,385; known YouTube subscribers gained total 8,576. Both metrics appear in headline cards, weekly chart metric selectors with contributor details, the audience-gains table, and post tables. These exports do not provide current account-wide follower or subscriber counts. Instagram follows include 45,162 from rows credited to isthisreallylegal and 223 from rows credited to lawyer_oyer.

## Build and preview

The reviewed, portable data snapshot is `data/dashboard.json`. Source CSVs are kept outside the repository. Local intake outputs under `work/` are excluded from Git and Railway uploads.

```sh
python3 scripts/build_dashboard.py
npm start
```

Open `http://localhost:3000`. The self-contained page uses inline SVG charts and no external scripts or network data requests. Rebuild after changes to `src/dashboard.html`, `src/dashboard.css`, `src/dashboard.js`, or the reviewed snapshot.

`scripts/build_data.py --help` describes data refresh options. Reconcile source coverage and regenerate the reviewed snapshot before rebuilding; do not treat an unknown analytics date range as lifetime data.

## Independent hosting

- GitHub repository: `rubin-maker/is-this-really-legal-dashboard`
- Railway project: `cf2ec980-d14f-475c-b6f0-04eddff4a43c`
- Railway environment: `db07cdf6-7f93-43a6-b3fc-a748ff30145a`
- Railway service: `594486d0-e9da-4628-8365-c4a546777aa9`
- Website: https://is-this-really-legal-dashboard-production.up.railway.app

The service currently uses explicit uploads rather than a connected GitHub source. Always pass these exact project, environment, and service IDs when deploying. Do not relink or deploy to a Home of the Brave resource.

The server exposes `/`, `/dashboard.html`, `/artifact.json`, and `/health`. Railway starts it with `npm start` and supplies `PORT`; `HOST` defaults to `0.0.0.0` and can be set to `127.0.0.1` for local preview.
