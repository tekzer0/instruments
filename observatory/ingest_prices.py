"""Sold-price ingestion via SoldComps (free tier: 50 req/mo).

Verified 2026-07-11 against the live API:
  GET https://api.sold-comps.com/v1/scrape?keyword=<query>
  Authorization: Bearer <key>

Budget: one request per card per run, 12 cards. Cron runs on the 1st and 15th
(24 req/mo), leaving ~half the free tier for manual runs and new cards.
"""
import hashlib

import requests

from common import config, db
from observatory import cardmap

PRICE_SANITY = (20, 6000)  # USD; outside this = junk listing, skip


def run() -> str:
    key = config.get("SOLDCOMPS_API_KEY")
    if not key:
        raise RuntimeError("SOLDCOMPS_API_KEY not set (free key: sold-comps.com)")
    url = config.get("SOLDCOMPS_URL")
    ids = cardmap.sync_catalog()
    inserted = skipped = 0
    first_sample_logged = False

    for card in cardmap.load_catalog():
        query = card["aliases"][0].strip()
        resp = requests.get(
            url,
            params={"keyword": query},
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        # Verified live 2026-07-11: {keyword, page, totalItems, hasNextPage, items:[...]}
        items = payload.get("items", []) if isinstance(payload, dict) else payload
        if items and not first_sample_logged:
            print("[prices] sample item keys:", sorted(items[0].keys()))
            first_sample_logged = True

        for it in items:
            title = str(it.get("title", ""))
            matched = cardmap.match(title)
            if matched != card["key"]:
                skipped += 1
                continue
            if (it.get("soldCurrency") or "USD") != "USD":
                skipped += 1
                continue
            try:
                price = float(it.get("soldPrice") or 0)
            except (TypeError, ValueError):
                skipped += 1
                continue
            if not (PRICE_SANITY[0] <= price <= PRICE_SANITY[1]):
                skipped += 1
                continue
            listing_url = it.get("url", "")
            dedupe = it.get("itemId") or hashlib.sha1(
                f"{title}|{price}|{it.get('endedAt', '')}".encode()
            ).hexdigest()
            with db.connect() as conn:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO price_obs "
                    "(card_id, source, price_usd, shipping_usd, condition, sold_at, url, dedupe_key) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        ids[card["key"]],
                        "soldcomps",
                        price,
                        float(it.get("shippingPrice") or 0),
                        it.get("condition"),
                        (it.get("endedAt") or "")[:10] or None,
                        listing_url,
                        f"soldcomps:{dedupe}",
                    ),
                )
                inserted += cur.rowcount
    return f"inserted={inserted} skipped={skipped}"
