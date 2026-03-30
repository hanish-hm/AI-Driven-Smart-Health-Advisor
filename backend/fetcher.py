"""
Periodic fetcher: pulls WHO & MoHFW RSS feeds and appends new entries to guidelines.json.
Local guidelines.json is always the primary source — this only adds, never removes.
"""

import json
import hashlib
import logging
import threading
import time
from pathlib import Path

import feedparser

logger = logging.getLogger(__name__)

GUIDELINES_PATH = Path(__file__).parent / "data" / "guidelines.json"

FEEDS = [
    {
        "url": "https://www.who.int/rss-feeds/news-releases.xml",
        "source_prefix": "WHO News",
        "country": None,
    },
    {
        "url": "https://www.who.int/rss-feeds/disease-outbreak-news.xml",
        "source_prefix": "WHO Disease Outbreak News",
        "country": None,
    },
    {
        "url": "https://mohfw.gov.in/rss.xml",
        "source_prefix": "MoHFW India",
        "country": "india",
    },
]

FETCH_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours


def _make_id(text: str) -> str:
    return "rss_" + hashlib.md5(text.encode()).hexdigest()[:12]


def _load_guidelines() -> list[dict]:
    with open(GUIDELINES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_guidelines(data: list[dict]) -> None:
    with open(GUIDELINES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_and_append() -> int:
    """Fetch all feeds and append new entries. Returns count of new entries added."""
    guidelines = _load_guidelines()
    existing_ids = {g["id"] for g in guidelines}
    new_entries = []

    for feed_cfg in FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            if feed.bozo:
                logger.warning("Feed parse issue for %s: %s", feed_cfg["url"], feed.bozo_exception)
        except Exception as e:
            logger.error("Failed to fetch feed %s: %s", feed_cfg["url"], e)
            continue

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            if not title or not summary:
                continue

            text = f"{title}. {summary}"
            entry_id = _make_id(text)

            if entry_id in existing_ids:
                continue

            item: dict = {
                "id": entry_id,
                "source": f"{feed_cfg['source_prefix']} — {title}",
                "text": text,
            }
            if feed_cfg["country"]:
                item["country"] = feed_cfg["country"]

            new_entries.append(item)
            existing_ids.add(entry_id)

    if new_entries:
        guidelines.extend(new_entries)
        _save_guidelines(guidelines)
        logger.info("Fetcher: added %d new guideline entries.", len(new_entries))
    else:
        logger.info("Fetcher: no new entries found.")

    return len(new_entries)


def _run_loop() -> None:
    while True:
        try:
            fetch_and_append()
        except Exception as e:
            logger.error("Fetcher loop error: %s", e)
        time.sleep(FETCH_INTERVAL_SECONDS)


def start_background_fetcher() -> None:
    """Start the periodic fetcher in a daemon thread."""
    t = threading.Thread(target=_run_loop, daemon=True, name="guideline-fetcher")
    t.start()
    logger.info("Background guideline fetcher started (interval: %dh).", FETCH_INTERVAL_SECONDS // 3600)
