#!/usr/bin/env python3
"""Multi-platform job scraper — PRO360 + Tasker → sonia-jobs API."""
from __future__ import annotations

import argparse
import os
import random
import time
import requests
from datetime import datetime, timedelta, timezone

from config import BASE_URL, POLL_INTERVAL_MIN, POLL_INTERVAL_MAX, \
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, USER_AGENTS
from parser import parse_jobs_page
from tasker_parser import parse_tasker_page
from classifier import classify_pro360

API_URL = os.environ.get("API_URL", "http://localhost:3000")
INGEST_KEY = os.environ.get("INGEST_KEY", "")

# Pagination settings
MAX_PAGES = 50          # Safety cap per category (backfill)
MAX_AGE_DAYS = 3        # Stop paginating when jobs are older than this
POLL_PAGES = 3          # Regular poll: only first few pages

TASKER_URL = "https://www.tasker.com.tw"
TASKER_PAGES = 5        # Tasker pages to scrape on backfill
TASKER_POLL_PAGES = 2   # Regular poll

seen_urls: set[str] = set()


def get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }


# === PRO360 ===

def fetch_pro360_page(page: int) -> list[dict]:
    """Fetch and parse a single page of the PRO360 global feed."""
    # Scrape the main /case page which has ALL job categories mixed.
    # Individual /case/subgenre/* pages are unreliable (some filter, some don't).
    url = BASE_URL + "/case"
    if page > 1:
        url += f"?page={page}"

    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [pro360] Error fetching p{page}: {e}")
        return []

    # Parse with dummy category — we'll classify below
    jobs = parse_jobs_page(resp.text, "__unclassified__")
    for j in jobs:
        j['job_url'] = j.pop('pro360_url')
        j['source'] = 'pro360'
        # Classify using title + description keywords
        j['category'] = classify_pro360(j.get('title', ''), j.get('description'))
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


def scrape_pro360(max_pages: int) -> list[dict]:
    """Scrape PRO360 global feed (single URL, keyword-classified)."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        print(f"  [pro360] page {page}")
        jobs = fetch_pro360_page(page)

        if not jobs:
            break

        # Dedup
        new_jobs = [j for j in jobs if j['job_url'] not in seen_urls]
        for j in new_jobs:
            seen_urls.add(j['job_url'])
        all_jobs.extend(new_jobs)

        print(f"  [pro360] page {page}: {len(jobs)} jobs ({len(new_jobs)} new)")

        if is_too_old(jobs):
            print(f"  [pro360] page {page}: reached {MAX_AGE_DAYS}-day limit")
            break

        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    # Log category distribution
    cats = {}
    for j in all_jobs:
        cats[j['category']] = cats.get(j['category'], 0) + 1
    if cats:
        print(f"  [pro360] categories: {dict(sorted(cats.items(), key=lambda x: -x[1]))}")

    print(f"  [pro360] total: {len(all_jobs)} new jobs")
    return all_jobs


# === Tasker ===

def scrape_tasker(max_pages: int) -> list[dict]:
    """Scrape Tasker /cases/top pages."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = f"{TASKER_URL}/cases/top"
        if page > 1:
            url += f"?page={page}"

        print(f"  [tasker] page {page}: {url}")

        try:
            resp = requests.get(url, headers=get_headers(), timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [tasker] Error fetching page {page}: {e}")
            break

        jobs = parse_tasker_page(resp.text)

        if not jobs:
            print(f"  [tasker] page {page}: no jobs found, stopping")
            break

        # Dedup
        new_jobs = [j for j in jobs if j['job_url'] not in seen_urls]
        for j in new_jobs:
            seen_urls.add(j['job_url'])
        all_jobs.extend(new_jobs)

        print(f"  [tasker] page {page}: {len(jobs)} jobs ({len(new_jobs)} new)")

        if is_too_old(jobs):
            print(f"  [tasker] page {page}: reached {MAX_AGE_DAYS}-day limit")
            break

        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    print(f"  [tasker] total: {len(all_jobs)} new jobs")
    return all_jobs


# === Ingest ===

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
    """Scrape all platforms once."""
    pro360_pages = MAX_PAGES if backfill else POLL_PAGES
    tasker_pages = TASKER_PAGES if backfill else TASKER_POLL_PAGES

    # PRO360
    print(f"  --- PRO360 (max {pro360_pages} pages) ---")
    pro360_jobs = scrape_pro360(pro360_pages)

    # Tasker
    print(f"  --- Tasker (max {tasker_pages} pages) ---")
    tasker_jobs = scrape_tasker(tasker_pages)

    all_jobs = pro360_jobs + tasker_jobs

    if all_jobs:
        for i in range(0, len(all_jobs), 200):
            batch = all_jobs[i:i + 200]
            ingest_jobs(batch)

    print(f"  === Total: {len(pro360_jobs)} PRO360 + {len(tasker_jobs)} Tasker = {len(all_jobs)} jobs ===")
    return len(all_jobs)


def main():
    parser = argparse.ArgumentParser(description="Multi-Platform Job Scraper")
    parser.add_argument("--backfill", action="store_true", help="Paginate deep to collect last 3 days of jobs")
    args = parser.parse_args()

    if not INGEST_KEY:
        print("[ERROR] INGEST_KEY environment variable is required")
        return

    print(f"[scraper] Starting multi-platform scraper")
    print(f"[scraper] API: {API_URL}")
    print(f"[scraper] Platforms: PRO360 (keyword-classified) + Tasker")
    print(f"[scraper] Backfill: {args.backfill}")

    # First round
    print(f"\n[scraper] === Round 1 (backfill={args.backfill}) ===")
    count = scrape_round(backfill=args.backfill)
    print(f"[scraper] Round 1 complete: {count} jobs\n")

    # Polling loop
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
