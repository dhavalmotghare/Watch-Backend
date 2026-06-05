#!/usr/bin/env python3
"""
Build the IMDB ratings SQLite database from flat files.
Expects title.basics.tsv and title.ratings.tsv in the current directory.
Outputs imdb_ratings.db in the current directory.
"""

import csv
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime

BASICS  = "title.basics.tsv"
RATINGS = "title.ratings.tsv"
OUT_DB  = "imdb_ratings.db"
MANIFEST = "imdb_manifest.json"

MOVIE_TYPES = {"movie", "tvMovie"}
TV_TYPES    = {"tvSeries", "tvMiniSeries"}
KEEP_TYPES  = MOVIE_TYPES | TV_TYPES


def build_basics_index():
    index = {}
    with open(BASICS, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            tt = row["titleType"]
            if tt not in KEEP_TYPES:
                continue
            year = row["startYear"]
            if year == "\\N":
                continue
            try:
                media_type = "m" if tt in MOVIE_TYPES else "t"
                index[row["tconst"]] = (int(year), media_type)
            except ValueError:
                pass
    return index


def build_database(basics_index):
    if os.path.exists(OUT_DB):
        os.remove(OUT_DB)

    conn = sqlite3.connect(OUT_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE imdb_ratings (
            tconst        TEXT    NOT NULL,
            startYear     INTEGER NOT NULL,
            averageRating REAL    NOT NULL,
            numVotes      INTEGER NOT NULL,
            mediaType     TEXT    NOT NULL,
            PRIMARY KEY (tconst)
        )
    """)
    cur.execute(
        "CREATE INDEX idx_imdb_discover ON imdb_ratings (mediaType, startYear, averageRating DESC, numVotes DESC)"
    )

    batch = []
    count = 0
    with open(RATINGS, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            tconst = row["tconst"]
            entry = basics_index.get(tconst)
            if entry is None:
                continue
            year, media_type = entry
            try:
                rating = float(row["averageRating"])
                votes  = int(row["numVotes"])
            except ValueError:
                continue
            batch.append((tconst, year, rating, votes, media_type))
            count += 1
            if len(batch) == 10_000:
                cur.executemany("INSERT INTO imdb_ratings VALUES (?,?,?,?,?)", batch)
                batch.clear()
                print(f"\r  {count:,} rows inserted...", end="", flush=True)

    if batch:
        cur.executemany("INSERT INTO imdb_ratings VALUES (?,?,?,?,?)", batch)

    conn.commit()
    conn.close()
    return count


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(count):
    version = int(datetime.utcnow().strftime("%Y%m%d"))
    checksum = sha256(OUT_DB)
    size_mb = os.path.getsize(OUT_DB) / 1_048_576
    manifest = {
        "version": version,
        "sha256": checksum,
        "entries": count,
        "size_mb": round(size_mb, 1)
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: version={version}, sha256={checksum[:16]}..., size={size_mb:.1f}MB")


def main():
    for fname in (BASICS, RATINGS):
        if not os.path.exists(fname):
            print(f"ERROR: {fname} not found.", file=sys.stderr)
            sys.exit(1)

    print("Step 1/2 — building basics index...")
    basics_index = build_basics_index()
    print(f"         {len(basics_index):,} titles in scope")

    print("Step 2/2 — building database...")
    count = build_database(basics_index)

    write_manifest(count)
    print(f"Done. {count:,} entries written to {OUT_DB}")


if __name__ == "__main__":
    main()
