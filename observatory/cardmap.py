"""Card catalog loader + title/model-string -> card matching."""
import os

import yaml

from common import db

CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards.yaml")


def load_catalog() -> list[dict]:
    with open(CARDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sync_catalog() -> dict:
    """Upsert cards.yaml into gpu_cards; return {key: card_id}."""
    ids = {}
    with db.connect() as conn:
        for c in load_catalog():
            conn.execute(
                "INSERT INTO gpu_cards (key,name,vram_gb,tdp_w) VALUES (?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET name=excluded.name, "
                "vram_gb=excluded.vram_gb, tdp_w=excluded.tdp_w",
                (c["key"], c["name"], c.get("vram_gb"), c.get("tdp_w")),
            )
            ids[c["key"]] = conn.execute(
                "SELECT id FROM gpu_cards WHERE key=?", (c["key"],)
            ).fetchone()["id"]
    return ids


def match(text: str) -> str | None:
    """Return card key whose alias appears in text (longest alias wins), else None."""
    t = f" {text.lower()} "
    best_key, best_len = None, 0
    for c in load_catalog():
        if any(x in t for x in c.get("exclude", [])):
            continue
        for a in c["aliases"]:
            if a in t and len(a) > best_len:
                best_key, best_len = c["key"], len(a)
    return best_key
