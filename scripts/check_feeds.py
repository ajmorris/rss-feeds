#!/usr/bin/env python3
"""Feed health monitoring script.

Checks all generated RSS feeds for:
- Valid XML structure
- Presence of entries
- Entry freshness (warns if newest entry is older than threshold)
- Required fields (title, link, pubDate)

Usage:
    python scripts/check_feeds.py           # Check all feeds
    python scripts/check_feeds.py --verbose  # Show per-entry details
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"
STALE_DAYS = 30  # Warn if newest entry is older than this


def check_feed(feed_path, verbose=False):
    """Check a single feed file. Returns (ok, warnings, errors)."""
    warnings = []
    errors = []
    name = feed_path.name

    # 1. Parse XML
    try:
        tree = ET.parse(feed_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return False, [], [f"Invalid XML: {e}"]

    # 2. Find items
    items = root.findall(".//item")
    if not items:
        errors.append("No <item> entries found")
        return False, warnings, errors

    # 3. Check each item for required fields
    missing_titles = 0
    missing_links = 0
    missing_dates = 0
    newest_date = None

    for item in items:
        title = item.find("title")
        link = item.find("link")
        pub_date = item.find("pubDate")

        if title is None or not (title.text or "").strip():
            missing_titles += 1
        if link is None or not (link.text or "").strip():
            missing_links += 1
        if pub_date is None or not (pub_date.text or "").strip():
            missing_dates += 1
        elif pub_date.text:
            try:
                from email.utils import parsedate_to_datetime

                dt = parsedate_to_datetime(pub_date.text.strip())
                if newest_date is None or dt > newest_date:
                    newest_date = dt
            except Exception:
                pass

    if missing_titles:
        warnings.append(f"{missing_titles}/{len(items)} entries missing title")
    if missing_links:
        errors.append(f"{missing_links}/{len(items)} entries missing link")
    if missing_dates:
        warnings.append(f"{missing_dates}/{len(items)} entries missing pubDate")

    # 4. Check freshness
    if newest_date:
        now = datetime.now(timezone.utc)
        age = now - newest_date
        if age > timedelta(days=STALE_DAYS):
            warnings.append(
                f"Stale: newest entry is {age.days} days old ({newest_date.strftime('%Y-%m-%d')})"
            )

    if verbose:
        print(f"  Entries: {len(items)}")
        if newest_date:
            print(f"  Newest:  {newest_date.strftime('%Y-%m-%d %H:%M')}")

    ok = len(errors) == 0
    return ok, warnings, errors


def main():
    parser = argparse.ArgumentParser(description="Check RSS feed health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details")
    args = parser.parse_args()

    if not FEEDS_DIR.exists():
        print(f"Feeds directory not found: {FEEDS_DIR}")
        sys.exit(1)

    feeds = sorted(FEEDS_DIR.glob("feed_*.xml"))
    if not feeds:
        print("No feed files found.")
        sys.exit(1)

    total = len(feeds)
    healthy = 0
    warn_count = 0
    error_count = 0

    print(f"Checking {total} feeds in {FEEDS_DIR}\n")

    for feed_path in feeds:
        ok, warnings, errors = check_feed(feed_path, verbose=args.verbose)

        if ok and not warnings:
            status = "OK"
            healthy += 1
        elif ok and warnings:
            status = "WARN"
            warn_count += 1
        else:
            status = "FAIL"
            error_count += 1

        print(f"  [{status:4s}] {feed_path.name}")
        for w in warnings:
            print(f"         ^ {w}")
        for e in errors:
            print(f"         ! {e}")

    print(f"\n--- Summary ---")
    print(f"  Healthy: {healthy}/{total}")
    if warn_count:
        print(f"  Warnings: {warn_count}/{total}")
    if error_count:
        print(f"  Errors: {error_count}/{total}")

    sys.exit(1 if error_count else 0)


if __name__ == "__main__":
    main()
