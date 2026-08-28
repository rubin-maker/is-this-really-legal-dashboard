# Is This Really Legal? Social Performance Dashboard

A public, source-backed snapshot of the podcast's Apple Podcasts, Instagram, and YouTube performance through August 28, 2026.

## What is included

- Six headline metrics covering listening, discovery, conversion, and watch depth
- Weekly Instagram and YouTube publish-cohort trends
- Apple episode listener rankings
- Instagram acquisition-post rankings
- YouTube Long-Form versus Shorts detail
- Data-quality coverage and caveats

The dashboard is a cumulative snapshot, not a live API connection. Rankings use a seven-day maturity rule when recent content would otherwise distort the comparison.

## Run locally

```bash
npm start
```

Then open `http://localhost:3000`. The health endpoint is `/health`.

## Railway

Railway detects the Node server and starts it with `npm start`. The server listens on Railway's assigned `PORT` and serves the dashboard at `/`.

## Source and validation

The public repository contains the validated aggregate artifact, not the private source exports. The build reconciled 18 of 18 checks across the three exports, including the YouTube workbook Overview totals.
