"""Tombstone watcher: scans RSS feeds for cloud-shutdown language, queues
candidates, pings Telegram. You confirm with one tap (or ignore — queue waits).

Feeds are plain RSS/Atom parsed with stdlib regex — resilient, no dependencies.
Add/remove feeds freely in FEEDS.
"""
import hashlib
import re
import urllib.request

from common import db, notify

FEEDS = [
    "https://www.theverge.com/rss/smart-home/index.xml",
    "https://arstechnica.com/gadgets/feed/",
    "https://www.home-assistant.io/atom.xml",
    "https://hackaday.com/feed/",
]

KEYWORDS = re.compile(
    r"shut(?:ting)?\s*down|discontinu|end[- ]of[- ]life|sunset(?:ting)?|brick(?:ed|ing)?"
    r"|no longer (?:work|support)|kills? (?:its|the|off)|servers? (?:off|offline|close)",
    re.IGNORECASE,
)
ITEM = re.compile(r"<(?:item|entry)\b.*?</(?:item|entry)>", re.DOTALL | re.IGNORECASE)
TITLE = re.compile(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", re.DOTALL | re.IGNORECASE)
LINK = re.compile(r"<link[^>]*?href=[\"'](.*?)[\"']|<link[^>]*>(?:<!\[CDATA\[)?(https?://.*?)(?:\]\]>)?</link>",
                  re.DOTALL | re.IGNORECASE)


def run() -> str:
    found = 0
    for feed in FEEDS:
        try:
            req = urllib.request.Request(feed, headers={"User-Agent": "instruments-watcher/1.0"})
            xml = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - one dead feed must not kill the run
            print(f"[news] feed error {feed}: {e}")
            continue
        for item in ITEM.findall(xml):
            mt = TITLE.search(item)
            if not mt:
                continue
            title = re.sub(r"\s+", " ", mt.group(1)).strip()
            if not KEYWORDS.search(title):
                continue
            ml = LINK.search(item)
            link = (ml.group(1) or ml.group(2)) if ml else ""
            dedupe = "news:" + hashlib.sha1(title.lower().encode()).hexdigest()
            with db.connect() as conn:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO events_queue (kind, payload, dedupe_key) VALUES (?,?,?)",
                    ("tombstone_candidate", f"{title}\n{link}", dedupe),
                )
                if cur.rowcount:
                    found += 1
                    notify.send(f"🪦 Tombstone candidate:\n{title}\n{link}")
    return f"new_candidates={found}"
