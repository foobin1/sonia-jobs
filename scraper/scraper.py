#!/usr/bin/env python3
"""PRO360 job scraper — polls categories and ingests to sonia-jobs API."""

import argparse
import json
import os
import random
import time
import requests
from datetime import datetime, timedelta, timezone

from config import BASE_URL, CATEGORIES, POLL_INTERVAL_MIN, POLL_INTERVAL_MAX, \
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, USER_AGENTS
from parser import parse_jobs_page

API_URL = os.environ.get("API_URL", "http://localhost:3000")
INGEST_KEY = os.environ.get("INGEST_KEY", "")

# Pagination settings
MAX_PAGES = 50          # Safety cap per category
MAX_AGE_DAYS = 3        # Stop paginating when jobs are older than this
# On regular polls (not backfill), only check first few pages for new jobs
POLL_PAGES = 3

seen_urls: set[str] = set()


def get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }


def fetch_page(slug: str, path: str, page: int) -> list[dict]:
    """Fetch and parse a single page of a category."""
    url = BASE_URL + path
    if page > 1:
        url += f"?page={page}"

    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [fetch] Error fetching {slug} p{page}: {e}")
        return []

    jobs = parse_jobs_page(resp.text, slug)
    return jobs


def is_too_old(jobs: list[dict]) -> bool:
    """Check if any job in the list is older than MAX_AGE_DAYS."""
    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=MAX_AGE_DAYS)
    for job in jobs:
        if job.get("posted_at"):
            try:
                posted = datetime.fromisoformat(job["posted_at"])
                if posted < cutoff:
                    return True
            except (ValueError, TypeError):
                continue
    return False


def fetch_category(slug: str, cat: dict, max_pages: int = MAX_PAGES) -> list[dict]:
    """Fetch all pages of a category until jobs are too old or max pages reached."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        print(f"  [fetch] {slug} p{page}: {BASE_URL + cat['path']}{'?page=' + str(page) if page > 1 else ''}")
        jobs = fetch_page(slug, cat["path"], page)

        if not jobs:
            print(f"  [fetch] {slug} p{page}: no jobs found, stopping")
            break

        all_jobs.extend(jobs)
        print(f"  [fetch] {slug} p{page}: {len(jobs)} jobs")

        # Stop if we hit jobs older than 7 days
        if is_too_old(jobs):
            print(f"  [fetch] {slug} p{page}: reached jobs older than {MAX_AGE_DAYS} days, stopping")
            break

        # Anti-ban delay between pages
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    print(f"  [fetch] {slug}: total {len(all_jobs)} jobs across {min(page, max_pages)} pages")
    return all_jobs


def ingest_jobs(jobs: list[dict]) -> dict | None:
    """Send jobs to the ingest API."""
    if not jobs:
        return None

    try:
        resp = requests.post(
            f"{API_URL}/api/ingest",
            json={"jobs": jobs},
            headers={"x-ingest-key": INGEST_KEY, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"  [ingest] Inserted {result.get('inserted', 0)}/{result.get('total', 0)}")
        return result
    except Exception as e:
        print(f"  [ingest] Error: {e}")
        return None


def scrape_round(backfill: bool = False):
    """Scrape all categories once."""
    all_jobs = []
    categories = list(CATEGORIES.items())
    random.shuffle(categories)

    # Backfill: paginate deep. Regular poll: only first few pages.
    max_pages = MAX_PAGES if backfill else POLL_PAGES

    for slug, cat in categories:
        jobs = fetch_category(slug, cat, max_pages=max_pages)

        new_jobs = []
        for job in jobs:
            url = job["pro360_url"]
            if url not in seen_urls or backfill:
                new_jobs.append(job)
                seen_urls.add(url)

        if new_jobs:
            all_jobs.extend(new_jobs)
            print(f"  [{slug}] {len(new_jobs)} new jobs")
        else:
            print(f"  [{slug}] No new jobs")

        # Anti-ban delay between categories
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    if all_jobs:
        # Batch ingest (max 200 per request)
        for i in range(0, len(all_jobs), 200):
            batch = all_jobs[i:i + 200]
            ingest_jobs(batch)

    return len(all_jobs)


def main():
    parser = argparse.ArgumentParser(description="PRO360 Job Scraper")
    parser.add_argument("--backfill", action="store_true", help="Paginate deep to collect last 7 days of jobs")
    args = parser.parse_args()

    if not INGEST_KEY:
        print("[ERROR] INGEST_KEY environment variable is required")
        return

    print(f"[scraper] Starting PRO360 scraper")
    print(f"[scraper] API: {API_URL}")
    print(f"[scraper] Categories: {len(CATEGORIES)}")
    print(f"[scraper] Backfill: {args.backfill}")
    print(f"[scraper] Max pages: {MAX_PAGES if args.backfill else POLL_PAGES} per category")

    # First round — backfill paginates deep
    print(f"\n[scraper] === Round 1 (backfill={args.backfill}) ===")
    count = scrape_round(backfill=args.backfill)
    print(f"[scraper] Round 1 complete: {count} jobs found\n")

    # Polling loop — only checks first few pages for new jobs
    round_num = 2
    while True:
        interval = random.uniform(POLL_INTERVAL_MIN, POLL_INTERVAL_MAX)
        print(f"[scraper] Sleeping {interval:.0f}s until next round...")
        time.sleep(interval)

        print(f"\n[scraper] === Round {round_num} ===")
        count = scrape_round()
        print(f"[scraper] Round {round_num} complete: {count} new jobs\n")
        round_num += 1


if __name__ == "__main__":
    main()
