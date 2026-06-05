# Watch-Backend

Auto-update pipeline for the [Watch](https://github.com/dhavalmotghare) Android app's IMDB ratings database.

## What it does

Every Sunday at 3am UTC, a GitHub Action:
1. Downloads the latest IMDB flat files (`title.basics.tsv.gz` + `title.ratings.tsv.gz`)
2. Builds a SQLite database with ~540K movie/TV entries (tconst, startYear, averageRating, numVotes, mediaType)
3. Publishes `imdb_ratings.db` + `imdb_manifest.json` to the `imdb-db-latest` release

## Release assets

| File | Description |
|---|---|
| `imdb_ratings.db` | ~40MB SQLite database |
| `imdb_manifest.json` | Version, SHA256, entry count |

## Manifest format

```json
{
  "version": 20260605,
  "sha256": "abc123...",
  "entries": 539271,
  "size_mb": 41.2
}
```

## Manual trigger

Go to **Actions → Update IMDB Database → Run workflow** to trigger a build outside the weekly schedule.
