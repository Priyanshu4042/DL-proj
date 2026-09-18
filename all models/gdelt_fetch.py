"""gdelt_fetch.py

Fetch daily headlines from the GDELT Document API and save them in the
same tabular format as the repo's `news.csv` (Date, News 1..News 10).

Features:
- Per-day fetch (start_date..end_date)
- Checkpointing to a JSON file so interrupted runs can resume
- Robust retries with exponential backoff
- Appends to output CSV and avoids re-fetching already-saved dates

Usage (example):
    python gdelt_fetch.py --start 2020-10-01 --end 2020-12-31 --out research/stock/news_gdelt.csv --checkpoint gdelt_checkpoint.json

NOTE: GDELT Document API may impose rate limits. This script uses a
small sleep between requests and retries on transient errors.
"""

import argparse
import datetime
import json
import os
import time
from typing import List

import pandas as pd
import requests


API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def daterange(start_date: datetime.date, end_date: datetime.date):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += datetime.timedelta(days=1)


def load_checkpoint(path: str):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_checkpoint(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def fetch_headlines_for_date(date: datetime.date, maxrecords: int = 10, timeout: int = 20) -> List[str]:
    """Query GDELT for the given date and return up to maxrecords headlines.

    Returns list of titles (strings). On any non-recoverable error raises.
    """
    startdatetime = date.strftime("%Y%m%d000000")
    enddatetime = date.strftime("%Y%m%d235959")

    params = {
        "query": "",  # empty query -> all coverage for the date window
        "mode": "ArtList",
        "maxrecords": maxrecords,
        "format": "json",
        "startdatetime": startdatetime,
        "enddatetime": enddatetime,
    }

    resp = requests.get(API_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    titles = []
    # GDELT responses vary; try known keys
    if isinstance(data, dict):
        # 'articles' is expected for ArtList
        articles = data.get("articles") or data.get("artlist") or []
        for a in articles:
            if not a:
                continue
            # Title keys may vary; try common ones
            title = a.get("title") or a.get("title_complete") or a.get("seentitle")
            if not title:
                # sometimes the payload uses 'url' and no title; skip if no title
                title = a.get("url")
            if title:
                titles.append(str(title))
            if len(titles) >= maxrecords:
                break

    return titles


def write_row_to_csv(out_path: str, date: datetime.date, titles: List[str], maxcols: int = 10):
    # Build row matching repo `news.csv` columns: Date, News 1..News 10
    row = {"Date": date.strftime("%Y-%m-%d")}
    for i in range(maxcols):
        key = f"News {i+1}"
        row[key] = titles[i] if i < len(titles) else "0"

    df_row = pd.DataFrame([row])

    # If file doesn't exist, write header; otherwise append without header.
    if not os.path.exists(out_path):
        df_row.to_csv(out_path, index=False)
    else:
        # Avoid duplicate dates: check if this date already present
        try:
            existing = pd.read_csv(out_path)
            if date.strftime("%Y-%m-%d") in existing['Date'].astype(str).tolist():
                print(f"Date {date} already exists in {out_path}, skipping append.")
                return
        except Exception:
            # If reading fails for any reason, fallback to append
            pass
        df_row.to_csv(out_path, index=False, header=False, mode='a')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--out", default="research/stock/news_gdelt.csv", help="Output CSV path")
    parser.add_argument("--checkpoint", default="gdelt_checkpoint.json", help="Checkpoint JSON file")
    parser.add_argument("--max", type=int, default=10, help="Max headlines per day")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between requests")
    parser.add_argument("--retries", type=int, default=4, help="Number of retries on transient failures")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint if available")
    args = parser.parse_args()

    start_date = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()

    checkpoint = load_checkpoint(args.checkpoint)
    last_date = checkpoint.get("last_date")
    if args.resume and last_date:
        try:
            last = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
            # resume _after_ last processed date
            if last >= start_date:
                start_date = last + datetime.timedelta(days=1)
                print(f"Resuming from checkpoint, new start: {start_date}")
        except Exception:
            pass

    # Read existing output dates to avoid duplicates
    existing_dates = set()
    if os.path.exists(args.out):
        try:
            df_existing = pd.read_csv(args.out)
            existing_dates = set(df_existing['Date'].astype(str).tolist())
        except Exception:
            existing_dates = set()

    for day in daterange(start_date, end_date):
        day_str = day.strftime("%Y-%m-%d")
        if day_str in existing_dates:
            print(f"{day_str} already fetched, skipping.")
            # update checkpoint so resume will skip these next time
            save_checkpoint(args.checkpoint, {"last_date": day_str})
            continue

        attempt = 0
        while attempt <= args.retries:
            try:
                titles = fetch_headlines_for_date(day, maxrecords=args.max)
                write_row_to_csv(args.out, day, titles, maxcols=args.max)
                # update checkpoint to this day (successfully processed)
                save_checkpoint(args.checkpoint, {"last_date": day_str})
                print(f"Fetched {len(titles)} headlines for {day_str}")
                break
            except requests.HTTPError as e:
                attempt += 1
                wait = 2 ** attempt
                print(f"HTTP error for {day_str}: {e} (attempt {attempt}/{args.retries}), retrying in {wait}s")
                time.sleep(wait)
            except Exception as e:
                attempt += 1
                wait = 2 ** attempt
                print(f"Error fetching {day_str}: {e} (attempt {attempt}/{args.retries}), retrying in {wait}s")
                time.sleep(wait)

        else:
            # All retries exhausted — write checkpoint to last successful day (previous day)
            prev = (day - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            save_checkpoint(args.checkpoint, {"last_date": prev})
            print(f"Failed to fetch {day_str} after retries. Checkpoint saved as {prev}. Exiting.")
            return

        time.sleep(args.sleep)

    print("Done fetching GDELT headlines.")


if __name__ == "__main__":
    main()
