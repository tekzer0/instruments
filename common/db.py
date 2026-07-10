"""SQLite layer. One file, additive migrations only — the dataset is the asset."""
import os
import sqlite3

from common import config

DB_PATH = config.path(config.get("DB_PATH", "data/instruments.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS gpu_cards (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,          -- canonical short key, e.g. 'rtx3090'
    name TEXT NOT NULL,
    vram_gb REAL,
    tdp_w REAL
);
CREATE TABLE IF NOT EXISTS price_obs (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES gpu_cards(id),
    source TEXT NOT NULL,              -- 'soldcomps' | 'hardwareswap' | ...
    price_usd REAL NOT NULL,
    shipping_usd REAL DEFAULT 0,
    condition TEXT,
    sold_at TEXT,                      -- ISO date from source
    url TEXT,
    dedupe_key TEXT UNIQUE,            -- source-specific id to avoid double counting
    ingested_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS bench_obs (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES gpu_cards(id),
    model_label TEXT NOT NULL,         -- e.g. 'llama 8B Q4_K_M'
    size_class TEXT NOT NULL,          -- '7-8B' | '13-14B' | '30-34B' | '70B+' | 'other'
    test TEXT NOT NULL,                -- 'tg128', 'pp512', ...
    tok_s REAL NOT NULL,
    backend TEXT,
    source TEXT,                       -- filename/url the numbers came from
    flagged INTEGER DEFAULT 0,         -- 1 = looks implausible, excluded from rankings
    ingested_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS registry_devices (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    vendor TEXT,
    category TEXT,
    protocol TEXT,                     -- wifi/zigbee/zwave/matter/thread/ble/proprietary
    local_control TEXT NOT NULL,       -- 'full' | 'degraded' | 'none'
    degrades_how TEXT,
    local_api TEXT,
    notes TEXT,
    sources TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tombstones (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    product TEXT NOT NULL,
    vendor TEXT NOT NULL,
    death_date TEXT,                   -- when service ended (approx ok, note in summary)
    what_died TEXT NOT NULL,
    owners_left_with TEXT,
    summary TEXT,
    sources TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS events_queue (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,                -- 'tombstone_candidate' | ...
    payload TEXT NOT NULL,
    status TEXT DEFAULT 'pending',     -- 'pending' | 'confirmed' | 'dismissed'
    created_at TEXT DEFAULT (datetime('now')),
    dedupe_key TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS scraper_runs (
    id INTEGER PRIMARY KEY,
    job TEXT NOT NULL,
    status TEXT NOT NULL,              -- 'ok' | 'fail'
    message TEXT,
    ran_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_price_card_date ON price_obs(card_id, sold_at);
CREATE INDEX IF NOT EXISTS idx_bench_card ON bench_obs(card_id, size_class, test);
CREATE INDEX IF NOT EXISTS idx_runs_job ON scraper_runs(job, ran_at);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # WAL is fastest but needs shared-memory mapping; DELETE needs the ability to
    # delete journal files. TRUNCATE works on ordinary disks, network shares, and
    # restricted mounts alike, so it's the fallback chain's safe end.
    for mode in ("WAL", "TRUNCATE"):
        try:
            conn.execute(f"PRAGMA journal_mode={mode}")
            conn.execute("CREATE TABLE IF NOT EXISTS _probe (x)")
            conn.execute("DROP TABLE _probe")
            conn.commit()
            break
        except sqlite3.OperationalError:
            continue
    return conn


def init() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
