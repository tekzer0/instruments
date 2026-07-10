"""The instrument's core metric: join price and performance.

For each card:
  price      = median sold price over last 30 days (fallback: all-time median)
  perf       = best unflagged tg tokens/sec per size class
  value      = tokens/sec per $100 spent
  vram_per_$ = GB per $100
  w_per_toks = watts per token/sec (efficiency)

Writes site_data/rankings.json (consumed by publish.py and, later, the paid API).
"""
import json
import statistics

from common import config, db
from observatory import cardmap

SIZE_CLASSES = ["7-8B", "13-14B", "30-34B", "70B+"]


def _median_price(conn, card_id: int) -> tuple[float | None, int, str]:
    recent = [r["price_usd"] for r in conn.execute(
        "SELECT price_usd FROM price_obs WHERE card_id=? AND ingested_at >= datetime('now','-30 days')",
        (card_id,),
    )]
    if recent:
        return statistics.median(recent), len(recent), "30d"
    alltime = [r["price_usd"] for r in conn.execute(
        "SELECT price_usd FROM price_obs WHERE card_id=?", (card_id,),
    )]
    if alltime:
        return statistics.median(alltime), len(alltime), "all-time"
    return None, 0, "none"


def run() -> str:
    ids = cardmap.sync_catalog()
    catalog = {c["key"]: c for c in cardmap.load_catalog()}
    out = {"generated_at": None, "cards": []}

    with db.connect() as conn:
        out["generated_at"] = conn.execute("SELECT datetime('now') d").fetchone()["d"]
        for key, card_id in ids.items():
            card = catalog[key]
            price, n_prices, price_window = _median_price(conn, card_id)
            perf = {}
            for sc in SIZE_CLASSES:
                row = conn.execute(
                    "SELECT MAX(tok_s) m, COUNT(*) n FROM bench_obs "
                    "WHERE card_id=? AND size_class=? AND test LIKE 'tg%' AND flagged=0",
                    (card_id, sc),
                ).fetchone()
                if row["m"]:
                    perf[sc] = {
                        "tok_s": round(row["m"], 2),
                        "n_obs": row["n"],
                        "toks_per_100usd": round(row["m"] / price * 100, 2) if price else None,
                        "w_per_toks": round(card["tdp_w"] / row["m"], 2) if card.get("tdp_w") else None,
                    }
            out["cards"].append({
                "key": key,
                "name": card["name"],
                "vram_gb": card.get("vram_gb"),
                "tdp_w": card.get("tdp_w"),
                "median_price_usd": round(price, 2) if price else None,
                "price_window": price_window,
                "n_price_obs": n_prices,
                "vram_gb_per_100usd": round(card["vram_gb"] / price * 100, 2)
                if price and card.get("vram_gb") else None,
                "perf": perf,
            })

    # rank by 7-8B value where computable
    def sort_key(c):
        v = c["perf"].get("7-8B", {}).get("toks_per_100usd")
        return -(v or -1)

    out["cards"].sort(key=sort_key)
    path = config.path("site_data/rankings.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    ranked = sum(1 for c in out["cards"] if c["perf"] and c["median_price_usd"])
    return f"cards={len(out['cards'])} fully_ranked={ranked} -> {path}"
